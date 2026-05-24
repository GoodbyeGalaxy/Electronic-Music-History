"""Discovers electronic music genres via Wikipedia categories + enriches with Wikidata."""
from __future__ import annotations
import re
import time
import yaml
import requests
from pathlib import Path
from collections import defaultdict

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "ElectronicMusicHistoryBot/0.1 (research project)"
ROOT_CATEGORY = "Category:Electronic_music_genres"

# Subcategory names containing these words are skipped during recursion —
# they are artist/album/event lists, not genre taxonomy branches.
_SKIP_SUBCAT_WORDS = frozenset([
    "musician", "artist", "band", "group", "singer", "singer-songwriter",
    "album", "song", "single", "record", "label", "discograph",
    "by nationality", "by country", "by city", "festival", "event",
    "film", "television", "video", "compilation",
])


def _wiki_get(params: dict, rate_limit: float) -> dict:
    """Makes a single Wikipedia API call with rate limiting and 429 backoff."""
    time.sleep(rate_limit)
    for attempt in range(6):
        resp = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        if resp.status_code == 429:
            wait = 10 * (attempt + 1)
            print(f"  429 rate-limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return {}


def fetch_category_titles(
    root_category: str,
    rate_limit: float = 1.0,
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
        data = _wiki_get(
            {
                "action": "query", "list": "categorymembers", "cmtitle": category,
                "cmlimit": 500, "cmtype": "page|subcat", "format": "json",
            },
            rate_limit,
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


def fetch_wikipedia_batch(titles: list[str]) -> dict[str, dict]:
    """Fetches abstract + Wikidata QID for up to 50 titles at once.

    Returns {title: {qid, description}}.
    """
    if not titles:
        return {}
    params = {
        "action": "query",
        "titles": "|".join(titles[:50]),
        "prop": "extracts|pageprops",
        "exintro": 1,
        "explaintext": 1,
        "sentences": 3,
        "ppprop": "wikibase_item",
        "format": "json",
        "redirects": 1,
    }
    for attempt in range(6):
        resp = requests.get(
            WIKIPEDIA_API, params=params,
            headers={"User-Agent": USER_AGENT}, timeout=30,
        )
        if resp.status_code == 429:
            wait = 10 * (attempt + 1)
            print(f"  wiki batch 429, waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        resp.raise_for_status()
    data = resp.json()
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
    for attempt in range(6):
        resp = requests.get(
            WIKIDATA_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=90,
        )
        if resp.status_code == 429:
            wait = 15 * (attempt + 1)
            print(f"  wikidata 429, waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        resp.raise_for_status()

    grouped: dict[str, dict] = {}
    parent_map: dict[str, set] = defaultdict(set)

    for binding in resp.json()["results"]["bindings"]:
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


def fetch(output_dir: Path, rate_limit: float = 1.5) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Discover genres via Wikipedia category tree
    print(f"Crawling {ROOT_CATEGORY}...")
    titles = sorted(set(fetch_category_titles(ROOT_CATEGORY, rate_limit=rate_limit)))
    print(f"Found {len(titles)} genre articles in category tree")

    # Phase 2: Wikipedia abstracts + Wikidata QIDs in batches of 50
    print("Fetching Wikipedia data (batches of 50)...")
    wiki_data: dict[str, dict] = {}
    for i in range(0, len(titles), 50):
        wiki_data.update(fetch_wikipedia_batch(titles[i:i + 50]))
        time.sleep(rate_limit)
        if i % 200 == 0 and i > 0:
            print(f"  {i}/{len(titles)} processed")

    primary_qids = [v["qid"] for v in wiki_data.values()]
    primary_qid_set = set(primary_qids)
    print(f"Got QIDs for {len(primary_qids)}/{len(titles)} articles")

    # Phase 3: Wikidata dates + parent relations in batches of 100
    print("Fetching Wikidata relations...")
    wd_data: dict[str, dict] = {}
    for i in range(0, len(primary_qids), 100):
        wd_data.update(fetch_wikidata_for_qids(primary_qids[i:i + 100]))
        time.sleep(rate_limit)

    # Build primary genre list; collect candidate QIDs (parents not in category)
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

    # Phase 4: Fetch Wikidata data for candidate genres (no Wikipedia abstract needed)
    print(f"Fetching {len(candidate_qids)} candidate genres referenced as parents...")
    cand_wd: dict[str, dict] = {}
    cand_list = list(candidate_qids)
    for i in range(0, len(cand_list), 100):
        cand_wd.update(fetch_wikidata_for_qids(cand_list[i:i + 100]))
        time.sleep(rate_limit)

    candidates: list[dict] = []
    for qid in sorted(candidate_qids):
        wd = cand_wd.get(qid, {})
        candidates.append({
            "qid": qid,
            "name": wd.get("name", qid),
            "year_start": wd.get("year_start"),
            "enwiki_slug": wd.get("enwiki_slug", ""),
            "description": "",
            "parent_qids": wd.get("parent_qids", []),
        })

    raw_path = output_dir / "raw.yaml"
    raw_path.write_text(yaml.dump(genres, allow_unicode=True), encoding="utf-8")
    print(f"Primary genres: {len(genres)} -> {raw_path}")

    candidates_path = output_dir / "candidates.yaml"
    candidates_path.write_text(yaml.dump(candidates, allow_unicode=True), encoding="utf-8")
    print(f"Candidates (for review): {len(candidates)} -> {candidates_path}")


if __name__ == "__main__":
    fetch(Path("data/_wikidata"))
