"""Discovers electronic music genres via Wikipedia categories + enriches with Wikidata.

Resume-fähig: Zwischenergebnisse werden nach jeder Phase in Checkpoint-Dateien gespeichert.
Bei Neustart werden bereits abgeschlossene Phasen übersprungen.
"""
from __future__ import annotations
import re
import time
import yaml
import requests
from pathlib import Path
from collections import defaultdict

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
# Wikimedia requires a descriptive User-Agent with contact info for automated scripts.
USER_AGENT = (
    "ElectronicMusicHistoryBot/1.0 "
    "(https://github.com/zuperzee/Electronic-Music-History; research project)"
)
ROOT_CATEGORY = "Category:Electronic_music_genres"

# Subcategory names containing these words are non-genre branches and skipped.
_SKIP_SUBCAT_WORDS = frozenset([
    "musician", "artist", "band", "group", "singer", "singer-songwriter",
    "album", "song", "single", "record", "label", "discograph",
    "by nationality", "by country", "by city", "festival", "event",
    "film", "television", "video", "compilation",
])


# ---------------------------------------------------------------------------
# Low-level HTTP helpers
# ---------------------------------------------------------------------------

def _retry_after(resp: requests.Response, fallback: float = 60.0) -> float:
    """Parse Retry-After header value; fall back to `fallback` seconds."""
    try:
        return float(resp.headers.get("Retry-After", fallback))
    except (ValueError, TypeError):
        return fallback


def _get_with_backoff(
    url: str,
    params: dict,
    timeout: int = 30,
    rate_limit: float = 0.0,
) -> dict:
    """GET request with pre-sleep, 429 backoff via Retry-After, and 6 retries."""
    if rate_limit:
        time.sleep(rate_limit)
    for attempt in range(6):
        resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code == 429:
            wait = _retry_after(resp)
            print(f"  429 – waiting {wait:.0f}s (Retry-After)...", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return {}


# ---------------------------------------------------------------------------
# Phase 1 – Wikipedia category crawl
# ---------------------------------------------------------------------------

def fetch_category_titles(
    root_category: str,
    rate_limit: float = 2.0,
    max_depth: int = 2,
) -> list[str]:
    """Iterative BFS over Wikipedia category tree; returns article titles."""
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(root_category, 0)]
    titles: list[str] = []

    while queue:
        category, depth = queue.pop(0)
        if category in seen:
            continue
        seen.add(category)
        data = _get_with_backoff(
            WIKIPEDIA_API,
            {
                "action": "query", "list": "categorymembers", "cmtitle": category,
                "cmlimit": 500, "cmtype": "page|subcat", "format": "json",
            },
            rate_limit=rate_limit,
        )
        for member in data.get("query", {}).get("categorymembers", []):
            if member.get("ns") == 14:
                if depth >= max_depth:
                    continue
                lower = member["title"].lower()
                if any(w in lower for w in _SKIP_SUBCAT_WORDS):
                    continue
                queue.append((member["title"], depth + 1))
            else:
                titles.append(member["title"])

    return titles


# ---------------------------------------------------------------------------
# Phase 2 – Wikipedia batch (abstracts + QIDs)
# ---------------------------------------------------------------------------

def fetch_wikipedia_batch(titles: list[str]) -> dict[str, dict]:
    """Fetches abstract + Wikidata QID for up to 50 titles at once.

    Returns {title: {qid, description}}.
    """
    if not titles:
        return {}
    data = _get_with_backoff(
        WIKIPEDIA_API,
        {
            "action": "query",
            "titles": "|".join(titles[:50]),
            "prop": "extracts|pageprops",
            "exintro": 1,
            "explaintext": 1,
            "sentences": 3,
            "ppprop": "wikibase_item",
            "format": "json",
            "redirects": 1,
        },
    )
    result: dict[str, dict] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        if page.get("missing"):
            continue
        qid = page.get("pageprops", {}).get("wikibase_item", "")
        title = page.get("title", "")
        if qid and title:
            result[title] = {
                "qid": qid,
                "description": page.get("extract", "")[:500].strip(),
            }
    return result


# ---------------------------------------------------------------------------
# Phase 3 / 4 – Wikidata SPARQL (inception + parents)
# ---------------------------------------------------------------------------

def fetch_wikidata_for_qids(qids: list[str]) -> dict[str, dict]:
    """Returns {qid: {name, year_start, parent_qids, enwiki_slug}} for the given QIDs."""
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids)
    query = f"""
SELECT ?genre ?genreLabel ?inception ?parent ?sitelink WHERE {{
  VALUES ?genre {{ {values} }}
  OPTIONAL {{ ?genre wdt:P571 ?inception. }}
  OPTIONAL {{ ?genre wdt:P279 ?parent. }}
  OPTIONAL {{
    ?sitelink schema:about ?genre;
              schema:isPartOf <https://en.wikipedia.org/>.
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""
    data = _get_with_backoff(
        WIKIDATA_ENDPOINT,
        {"query": query, "format": "json"},
        timeout=90,
    )
    grouped: dict[str, dict] = {}
    parent_map: dict[str, set] = defaultdict(set)

    for binding in data["results"]["bindings"]:
        qid = binding["genre"]["value"].rsplit("/", 1)[-1]
        if qid not in grouped:
            name = binding.get("genreLabel", {}).get("value", "")
            inception_raw = binding.get("inception", {}).get("value", "")
            year = None
            if inception_raw:
                m = re.match(r"(\d{4})", inception_raw)
                if m:
                    year = int(m.group(1))
            sitelink = binding.get("sitelink", {}).get("value", "")
            slug = sitelink.rsplit("/wiki/", 1)[-1] if "/wiki/" in sitelink else ""
            grouped[qid] = {"name": name, "year_start": year, "enwiki_slug": slug}
        parent_uri = binding.get("parent", {}).get("value", "")
        if parent_uri:
            parent_map[qid].add(parent_uri.rsplit("/", 1)[-1])

    for qid in grouped:
        grouped[qid]["parent_qids"] = sorted(parent_map[qid])

    return grouped


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> object:
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or None
    return None


def _save_yaml(path: Path, data: object) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def fetch(output_dir: Path, rate_limit: float = 2.0) -> None:
    """Full pipeline with checkpoint-resume support.

    Checkpoints (skipped if already present):
      _cp_titles.yaml   – list[str] of Wikipedia titles from category crawl
      _cp_wiki.yaml     – dict[title, {qid, description}]
      _cp_wd.yaml       – dict[qid, {name, year_start, parent_qids, enwiki_slug}]
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cp_titles = output_dir / "_cp_titles.yaml"
    cp_wiki   = output_dir / "_cp_wiki.yaml"
    cp_wd     = output_dir / "_cp_wd.yaml"

    # Phase 1: Category crawl
    titles_raw = _load_yaml(cp_titles)
    if titles_raw:
        titles: list[str] = titles_raw
        print(f"Phase 1 skipped (checkpoint): {len(titles)} titles", flush=True)
    else:
        print(f"Phase 1: crawling {ROOT_CATEGORY}...", flush=True)
        titles = sorted(set(fetch_category_titles(ROOT_CATEGORY, rate_limit=rate_limit)))
        _save_yaml(cp_titles, titles)
        print(f"Phase 1 done: {len(titles)} genre articles found", flush=True)

    # Phase 2: Wikipedia abstracts + QIDs
    wiki_raw = _load_yaml(cp_wiki)
    if wiki_raw:
        wiki_data: dict[str, dict] = wiki_raw
        print(f"Phase 2 skipped (checkpoint): {len(wiki_data)} wiki entries", flush=True)
    else:
        print(f"Phase 2: fetching Wikipedia data ({len(titles)} titles, batches of 50)...", flush=True)
        wiki_data = {}
        for i in range(0, len(titles), 50):
            batch = fetch_wikipedia_batch(titles[i:i + 50])
            wiki_data.update(batch)
            _save_yaml(cp_wiki, wiki_data)          # checkpoint after every batch
            time.sleep(rate_limit)
            print(f"  {min(i + 50, len(titles))}/{len(titles)} processed", flush=True)
        print(f"Phase 2 done: QIDs for {len(wiki_data)}/{len(titles)} articles", flush=True)

    primary_qids = [v["qid"] for v in wiki_data.values()]
    primary_qid_set = set(primary_qids)

    # Phase 3: Wikidata dates + parent relations
    wd_raw = _load_yaml(cp_wd)
    if wd_raw:
        wd_data: dict[str, dict] = wd_raw
        print(f"Phase 3 skipped (checkpoint): {len(wd_data)} wikidata entries", flush=True)
    else:
        print(f"Phase 3: fetching Wikidata relations ({len(primary_qids)} QIDs)...", flush=True)
        wd_data = {}
        for i in range(0, len(primary_qids), 100):
            wd_data.update(fetch_wikidata_for_qids(primary_qids[i:i + 100]))
            _save_yaml(cp_wd, wd_data)              # checkpoint after every batch
            time.sleep(rate_limit)
            print(f"  {min(i + 100, len(primary_qids))}/{len(primary_qids)} QIDs done", flush=True)
        print(f"Phase 3 done: {len(wd_data)} entries", flush=True)

    # Build primary genre list + collect candidate QIDs
    genres: list[dict] = []
    candidate_qids: set[str] = set()
    for title, wiki in wiki_data.items():
        qid = wiki["qid"]
        wd = wd_data.get(qid, {})
        parent_qids = wd.get("parent_qids", [])
        for pqid in parent_qids:
            if pqid not in primary_qid_set:
                candidate_qids.add(pqid)
        genres.append({
            "qid": qid,
            "name": title,
            "year_start": wd.get("year_start"),
            "enwiki_slug": title.replace(" ", "_"),
            "description": wiki.get("description", ""),
            "parent_qids": parent_qids,
        })

    # Phase 4: Wikidata for candidate genres (parents not in Wikipedia category)
    print(f"Phase 4: fetching {len(candidate_qids)} candidate genres...", flush=True)
    cand_list = sorted(candidate_qids)
    cand_wd: dict[str, dict] = {}
    for i in range(0, len(cand_list), 100):
        cand_wd.update(fetch_wikidata_for_qids(cand_list[i:i + 100]))
        time.sleep(rate_limit)

    candidates: list[dict] = [
        {
            "qid": qid,
            "name": cand_wd.get(qid, {}).get("name", qid),
            "year_start": cand_wd.get(qid, {}).get("year_start"),
            "enwiki_slug": cand_wd.get(qid, {}).get("enwiki_slug", ""),
            "description": "",
            "parent_qids": cand_wd.get(qid, {}).get("parent_qids", []),
        }
        for qid in cand_list
    ]

    raw_path = output_dir / "raw.yaml"
    _save_yaml(raw_path, genres)
    print(f"Primary genres: {len(genres)} → {raw_path}", flush=True)

    candidates_path = output_dir / "candidates.yaml"
    _save_yaml(candidates_path, candidates)
    print(f"Candidates: {len(candidates)} → {candidates_path}", flush=True)

    print("Done. Checkpoints kept in _cp_*.yaml (delete to force re-fetch).", flush=True)


if __name__ == "__main__":
    fetch(Path("data/_wikidata"))
