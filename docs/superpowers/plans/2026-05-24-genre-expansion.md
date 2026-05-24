# Genre Expansion — Ishkur Track-Struktur + Wikipedia/Wikidata Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the graph from 7 tracks / 20 genres to 20 tracks / 200+ genres by adopting Ishkur's track structure and auto-populating genre data from Wikipedia categories + Wikidata relationships.

**Architecture:** Three new pipeline scripts — `fetch_genres.py` (Wikipedia category discovery + Wikidata enrichment + candidate collection), `classify_genres.py` (BFS track assignment), `import_genres.py` (merge into YAML). Primary data source is `Category:Electronic_music_genres` on Wikipedia (editorially curated). Wikidata is used only for inception dates and parent QIDs. Related genres not in the Wikipedia category are written to `candidates.yaml` for manual review. Existing manually curated fields are never overwritten. `build.py` only changes its TRACKS list.

**Tech Stack:** Python 3.11+, pydantic v2, PyYAML, requests, pytest. MediaWiki API. Wikidata SPARQL endpoint. `uv run` for all Python commands.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pipeline/build.py` | Modify | Update TRACKS list (7 → 20) |
| `data/track_seeds.yaml` | Create | Maps Wikidata root QIDs to track IDs for classification |
| `pipeline/fetch_genres.py` | Create | Wikipedia category crawl + Wikidata enrichment + candidates |
| `pipeline/classify_genres.py` | Create | BFS track assignment from seed QIDs |
| `pipeline/import_genres.py` | Create | Merge classified genres into `data/genres/` |
| `tests/pipeline/test_fetch_genres.py` | Create | Unit tests with mocked HTTP |
| `tests/pipeline/test_classify_genres.py` | Create | Unit tests with fixture data |
| `tests/pipeline/test_import_genres.py` | Create | Unit tests with tmp_path |
| `tests/pipeline/test_build.py` | Modify | Update TRACKS count assertion |
| `data/genres/early.yaml` | Rename → `pioneers.yaml` | Track field update |
| `data/genres/avantgarde.yaml` | Rename → `ambient.yaml` | Track field update |

---

## Task 1: Update TRACKS in build.py

**Files:**
- Modify: `pipeline/build.py:5-13`
- Modify: `tests/pipeline/test_build.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/pipeline/test_build.py`:

```python
def test_tracks_has_20_entries():
    assert len(TRACKS) == 20

def test_tracks_includes_ishkur_categories():
    track_ids = {t.id for t in TRACKS}
    required = {"pioneers", "ambient", "hip_hop", "techno", "hardcore",
                "drum_n_bass", "breakbeat", "acid", "house", "tech_house",
                "progressive", "garage", "uk_garage", "bass", "electro",
                "downtempo", "urban", "industrial", "electroacoustic", "disco"}
    assert required == track_ids
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/pipeline/test_build.py::test_tracks_has_20_entries tests/pipeline/test_build.py::test_tracks_includes_ishkur_categories -v
```

Expected: FAIL — `assert 7 == 20`

- [ ] **Step 3: Replace TRACKS in build.py**

Replace the entire TRACKS block (lines 5–13) in `pipeline/build.py`:

```python
TRACKS = [
    Track(id="pioneers",        label="Pioneers",              color="#546e7a", order=0),
    Track(id="electroacoustic", label="Electroacoustic",       color="#388e3c", order=1),
    Track(id="ambient",         label="Ambient / Chill Out",   color="#7b1fa2", order=2),
    Track(id="downtempo",       label="Downtempo",             color="#795548", order=3),
    Track(id="industrial",      label="Industrial / EBM",      color="#c62828", order=4),
    Track(id="urban",           label="Urban",                 color="#ff8f00", order=5),
    Track(id="hip_hop",         label="Hip Hop",               color="#f57f17", order=6),
    Track(id="bass",            label="Bass",                  color="#37474f", order=7),
    Track(id="electro",         label="Electro",               color="#0288d1", order=8),
    Track(id="techno",          label="Techno",                color="#00695c", order=9),
    Track(id="hardcore",        label="Hardcore",              color="#b71c1c", order=10),
    Track(id="drum_n_bass",     label="Drum n Bass",           color="#ad1457", order=11),
    Track(id="breakbeat",       label="Breakbeat",             color="#6a1b9a", order=12),
    Track(id="acid",            label="Acid",                  color="#f9a825", order=13),
    Track(id="disco",           label="Disco / Funk",          color="#e65100", order=14),
    Track(id="house",           label="House",                 color="#1565c0", order=15),
    Track(id="tech_house",      label="Tech House",            color="#01579b", order=16),
    Track(id="progressive",     label="Progressive",           color="#283593", order=17),
    Track(id="garage",          label="Garage / Deep House",   color="#004d40", order=18),
    Track(id="uk_garage",       label="UK Garage",             color="#006064", order=19),
]
```

- [ ] **Step 4: Run all pipeline tests**

```bash
uv run pytest tests/pipeline/ -v
```

Expected: All existing tests PASS, two new tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/build.py tests/pipeline/test_build.py
git commit -m "feat: expand TRACKS to 20 entries (Ishkur structure)"
```

---

## Task 2: Create data/track_seeds.yaml

**Files:**
- Create: `data/track_seeds.yaml`

- [ ] **Step 1: Create the file**

```yaml
# Wikidata root QIDs per track — used by classify_genres.py
# Genres whose Wikidata parent chain reaches one of these QIDs get assigned that track.
pioneers:        { qids: [] }               # manually curated only
electroacoustic: { qids: [Q207436] }        # Musique concrète
ambient:         { qids: [Q56733] }         # Ambient music
downtempo:       { qids: [Q1088840] }       # Downtempo
industrial:      { qids: [Q179012] }        # Industrial music
urban:           { qids: [Q11369] }         # Rhythm and blues
hip_hop:         { qids: [Q11401] }         # Hip hop music
bass:            { qids: [Q3839300] }       # Bass music
electro:         { qids: [Q1062303] }       # Electro music
techno:          { qids: [Q48803] }         # Techno music
hardcore:        { qids: [Q584435] }        # Hardcore techno
drum_n_bass:     { qids: [Q193709] }        # Drum and bass
breakbeat:       { qids: [Q846291] }        # Breakbeat
acid:            { qids: [Q219639] }        # Acid house
disco:           { qids: [Q11606] }         # Disco
house:           { qids: [Q11399] }         # House music
tech_house:      { qids: [Q1362808] }       # Tech house
progressive:     { qids: [Q3029199] }       # Progressive house
garage:          { qids: [Q848882] }        # Garage house
uk_garage:       { qids: [Q487956] }        # UK garage
```

- [ ] **Step 2: Verify it loads as valid YAML**

```bash
uv run python -c "import yaml; from pathlib import Path; d = yaml.safe_load(Path('data/track_seeds.yaml').read_text()); print(len(d), 'tracks')"
```

Expected: `20 tracks`

- [ ] **Step 3: Commit**

```bash
git add data/track_seeds.yaml
git commit -m "feat: add track_seeds.yaml with Wikidata root QIDs"
```

---

## Task 3: Create fetch_genres.py

Primary data source: Wikipedia `Category:Electronic_music_genres` (recursively traversed). Wikidata provides inception dates, parent QIDs, and cross-genre links. Genres referenced as Wikidata parents but absent from the Wikipedia category are written to `candidates.yaml` for manual review.

**Files:**
- Create: `pipeline/fetch_genres.py`
- Create: `tests/pipeline/test_fetch_genres.py`

- [ ] **Step 1: Write the tests**

Create `tests/pipeline/test_fetch_genres.py`:

```python
from unittest.mock import patch, call
from pipeline.fetch_genres import (
    fetch_category_titles,
    fetch_wikipedia_batch,
    fetch_wikidata_for_qids,
)


def _wiki_response(members):
    return {"query": {"categorymembers": members}}


def test_fetch_category_titles_returns_article_titles():
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = _wiki_response([
            {"ns": 0, "title": "Techno"},
            {"ns": 0, "title": "House music"},
        ])
        result = fetch_category_titles("Category:Electronic_music_genres")
    assert "Techno" in result
    assert "House music" in result


def test_fetch_category_titles_recurses_into_subcategories():
    responses = [
        _wiki_response([
            {"ns": 14, "title": "Category:Techno"},
            {"ns": 0, "title": "House music"},
        ]),
        _wiki_response([
            {"ns": 0, "title": "Minimal techno"},
        ]),
    ]
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.side_effect = responses
        result = fetch_category_titles("Category:Electronic_music_genres")
    assert "House music" in result
    assert "Minimal techno" in result


def test_fetch_wikipedia_batch_extracts_qid_and_description():
    mock_response = {
        "query": {
            "redirects": [],
            "pages": {
                "12345": {
                    "pageid": 12345,
                    "title": "Techno",
                    "extract": "Techno is a form of electronic dance music.",
                    "pageprops": {"wikibase_item": "Q48803"},
                }
            },
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikipedia_batch(["Techno"])
    assert "Techno" in result
    assert result["Techno"]["qid"] == "Q48803"
    assert "electronic" in result["Techno"]["description"].lower()


def test_fetch_wikipedia_batch_skips_missing_pages():
    mock_response = {
        "query": {
            "redirects": [],
            "pages": {"-1": {"missing": True, "title": "NonExistent"}},
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikipedia_batch(["NonExistent"])
    assert result == {}


def test_fetch_wikidata_for_qids_returns_year_and_parents():
    mock_response = {
        "results": {
            "bindings": [
                {
                    "genre": {"value": "http://www.wikidata.org/entity/Q48803"},
                    "genreLabel": {"value": "techno"},
                    "inception": {"value": "1985-01-01T00:00:00Z"},
                    "parent": {"value": "http://www.wikidata.org/entity/Q9778"},
                    "sitelink": {"value": "https://en.wikipedia.org/wiki/Techno"},
                },
                {
                    "genre": {"value": "http://www.wikidata.org/entity/Q48803"},
                    "genreLabel": {"value": "techno"},
                    "parent": {"value": "http://www.wikidata.org/entity/Q188451"},
                },
            ]
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikidata_for_qids(["Q48803"])
    assert "Q48803" in result
    assert result["Q48803"]["year_start"] == 1985
    assert set(result["Q48803"]["parent_qids"]) == {"Q9778", "Q188451"}
    assert result["Q48803"]["enwiki_slug"] == "Techno"


def test_fetch_wikidata_for_qids_returns_empty_for_no_input():
    result = fetch_wikidata_for_qids([])
    assert result == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/pipeline/test_fetch_genres.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.fetch_genres'`

- [ ] **Step 3: Create pipeline/fetch_genres.py**

```python
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


def fetch_category_titles(category: str, seen: set | None = None) -> list[str]:
    """Recursively collects article titles from a Wikipedia category tree."""
    if seen is None:
        seen = set()
    if category in seen:
        return []
    seen.add(category)
    titles = []
    resp = requests.get(
        WIKIPEDIA_API,
        params={
            "action": "query", "list": "categorymembers", "cmtitle": category,
            "cmlimit": 500, "cmtype": "page|subcat", "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    for member in resp.json().get("query", {}).get("categorymembers", []):
        if member.get("ns") == 14:
            titles.extend(fetch_category_titles(member["title"], seen))
        else:
            titles.append(member["title"])
    return titles


def fetch_wikipedia_batch(titles: list[str]) -> dict[str, dict]:
    """Fetches abstract + Wikidata QID for up to 50 titles at once.

    Returns {title: {qid, description}}.
    """
    if not titles:
        return {}
    resp = requests.get(
        WIKIPEDIA_API,
        params={
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
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
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
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=90,
    )
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


def fetch(output_dir: Path, rate_limit: float = 0.5) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Discover genres via Wikipedia category tree
    print(f"Crawling {ROOT_CATEGORY}...")
    titles = sorted(set(fetch_category_titles(ROOT_CATEGORY)))
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
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/pipeline/test_fetch_genres.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Run full pipeline test suite**

```bash
uv run pytest tests/pipeline/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/fetch_genres.py tests/pipeline/test_fetch_genres.py
git commit -m "feat: add fetch_genres.py (Wikipedia category + Wikidata enrichment)"
```

---

## Task 4: Create classify_genres.py

**Files:**
- Create: `pipeline/classify_genres.py`
- Create: `tests/pipeline/test_classify_genres.py`

- [ ] **Step 1: Write the tests**

Create `tests/pipeline/test_classify_genres.py`:

```python
import yaml
from pathlib import Path
from pipeline.classify_genres import classify, load_seeds


def test_classify_assigns_seed_qid_to_its_track():
    genres = [{
        "qid": "Q48803", "name": "Techno", "year_start": 1985,
        "parent_qids": [], "enwiki_slug": "Techno", "description": "",
    }]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert "techno" in classified
    assert len(classified["techno"]) == 1
    assert unclassified == []


def test_classify_assigns_genre_via_parent_chain():
    genres = [
        {
            "qid": "Q48803", "name": "Techno", "year_start": 1985,
            "parent_qids": [], "enwiki_slug": "Techno", "description": "",
        },
        {
            "qid": "Q1195085", "name": "Minimal Techno", "year_start": 1994,
            "parent_qids": ["Q48803"], "enwiki_slug": "Minimal_techno", "description": "",
        },
    ]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert len(classified["techno"]) == 2
    assert {g["qid"] for g in classified["techno"]} == {"Q48803", "Q1195085"}
    assert unclassified == []


def test_classify_puts_unreachable_genres_in_unclassified():
    genres = [{
        "qid": "Q999999", "name": "Unknown Genre", "year_start": 2000,
        "parent_qids": [], "enwiki_slug": "", "description": "",
    }]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert classified == {}
    assert len(unclassified) == 1


def test_classify_handles_multi_hop_ancestor():
    genres = [
        {"qid": "Q1", "name": "Root", "year_start": 1970, "parent_qids": [], "enwiki_slug": "", "description": ""},
        {"qid": "Q2", "name": "Mid", "year_start": 1980, "parent_qids": ["Q1"], "enwiki_slug": "", "description": ""},
        {"qid": "Q3", "name": "Leaf", "year_start": 1990, "parent_qids": ["Q2"], "enwiki_slug": "", "description": ""},
    ]
    seeds = {"house": ["Q1"]}
    classified, unclassified = classify(genres, seeds)
    assert len(classified["house"]) == 3
    assert unclassified == []


def test_load_seeds_reads_yaml(tmp_path):
    seeds_file = tmp_path / "track_seeds.yaml"
    seeds_file.write_text(yaml.dump({
        "techno": {"qids": ["Q48803"]},
        "house":  {"qids": ["Q11399"]},
        "pioneers": {"qids": []},
    }))
    result = load_seeds(seeds_file)
    assert result == {"techno": ["Q48803"], "house": ["Q11399"], "pioneers": []}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/pipeline/test_classify_genres.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.classify_genres'`

- [ ] **Step 3: Create pipeline/classify_genres.py**

```python
"""Assigns genres to tracks by traversing Wikidata parent QID chains."""
from __future__ import annotations
from collections import deque
from pathlib import Path
import yaml


def load_seeds(seeds_path: Path) -> dict[str, list[str]]:
    """Returns {track_id: [qid, ...]} from track_seeds.yaml."""
    raw = yaml.safe_load(seeds_path.read_text(encoding="utf-8")) or {}
    return {track: (data.get("qids") or []) for track, data in raw.items()}


def classify(
    genres: list[dict],
    seeds: dict[str, list[str]],
) -> tuple[dict[str, list[dict]], list[dict]]:
    """
    Assigns each genre to a track via BFS through parent_qids.
    Returns (classified_by_track, unclassified_list).
    """
    qid_to_track: dict[str, str] = {
        qid: track_id
        for track_id, qids in seeds.items()
        for qid in qids
    }
    qid_to_parents: dict[str, list[str]] = {
        g["qid"]: g.get("parent_qids", []) for g in genres
    }

    def find_track(start_qid: str) -> str | None:
        visited: set[str] = set()
        queue: deque[str] = deque([start_qid])
        while queue:
            qid = queue.popleft()
            if qid in visited:
                continue
            visited.add(qid)
            if qid in qid_to_track:
                return qid_to_track[qid]
            queue.extend(qid_to_parents.get(qid, []))
        return None

    classified: dict[str, list[dict]] = {}
    unclassified: list[dict] = []
    for genre in genres:
        track = find_track(genre["qid"])
        if track:
            classified.setdefault(track, []).append(genre)
        else:
            unclassified.append(genre)
    return classified, unclassified


def classify_file(
    raw_path: Path,
    seeds_path: Path,
    output_dir: Path,
    unclassified_path: Path,
) -> None:
    genres = yaml.safe_load(raw_path.read_text(encoding="utf-8")) or []
    seeds = load_seeds(seeds_path)
    print(f"Classifying {len(genres)} genres...")
    classified, unclassified = classify(genres, seeds)
    output_dir.mkdir(parents=True, exist_ok=True)
    for track_id, track_genres in classified.items():
        out = output_dir / f"{track_id}.yaml"
        out.write_text(yaml.dump(track_genres, allow_unicode=True), encoding="utf-8")
        print(f"  {track_id}: {len(track_genres)} genres")
    unclassified_path.write_text(
        yaml.dump(unclassified, allow_unicode=True), encoding="utf-8"
    )
    total = sum(len(v) for v in classified.values())
    print(f"Classified: {total}, Unclassified: {len(unclassified)}")


if __name__ == "__main__":
    classify_file(
        Path("data/_wikidata/raw.yaml"),
        Path("data/track_seeds.yaml"),
        Path("data/_wikidata/classified"),
        Path("data/_wikidata/unclassified.yaml"),
    )
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/pipeline/test_classify_genres.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
uv run pytest tests/pipeline/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/classify_genres.py tests/pipeline/test_classify_genres.py
git commit -m "feat: add classify_genres.py with BFS track assignment"
```

---

## Task 5: Create import_genres.py

**Files:**
- Create: `pipeline/import_genres.py`
- Create: `tests/pipeline/test_import_genres.py`

- [ ] **Step 1: Write the tests**

Create `tests/pipeline/test_import_genres.py`:

```python
import yaml
from pathlib import Path
from pipeline.import_genres import (
    make_id,
    make_unique_id,
    merge_genre,
    wikidata_genre_to_yaml,
    import_track,
    apply_track_renames,
)


def test_make_id_creates_snake_case():
    assert make_id("Drum n Bass") == "drum_n_bass"
    assert make_id("Hi-NRG") == "hi_nrg"
    assert make_id("Acid House") == "acid_house"
    assert make_id("UK Garage") == "uk_garage"


def test_make_unique_id_adds_suffix_on_collision():
    existing = {"acid_house"}
    result = make_unique_id("Acid House", existing)
    assert result == "acid_house_2"


def test_merge_genre_preserves_curated_description():
    existing = {
        "id": "techno", "description": "Curated text.", "key_artists": ["Juan Atkins"],
        "key_labels": ["Transmat"], "subvariants": [], "audio_examples": [],
    }
    incoming = {
        "id": "techno", "description": "Wikipedia abstract.", "key_artists": ["Bot"],
        "key_labels": ["Bot Label"], "subvariants": ["sub"], "audio_examples": [],
    }
    result = merge_genre(existing, incoming)
    assert result["description"] == "Curated text."
    assert result["key_artists"] == ["Juan Atkins"]
    assert result["key_labels"] == ["Transmat"]


def test_merge_genre_fills_empty_curated_fields():
    existing = {"id": "techno", "description": "", "key_artists": [], "key_labels": []}
    incoming = {"id": "techno", "description": "Wikipedia.", "key_artists": ["A"], "key_labels": ["L"]}
    result = merge_genre(existing, incoming)
    assert result["description"] == "Wikipedia."
    assert result["key_artists"] == ["A"]


def test_import_track_appends_new_genre(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    new_genres = [{
        "qid": "Q999", "name": "Test Genre", "year_start": 2000,
        "parent_qids": [], "enwiki_slug": "Test_Genre", "description": "A test.",
    }]
    added = import_track("techno", new_genres, genres_dir)
    assert added == 1
    result = yaml.safe_load((genres_dir / "techno.yaml").read_text())
    assert result[0]["id"] == "test_genre"
    assert result[0]["wikidata_id"] == "Q999"
    assert result[0]["track"] == "techno"


def test_import_track_merges_matching_wikidata_id(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    (genres_dir / "techno.yaml").write_text(yaml.dump([{
        "id": "techno", "name": "Techno", "track": "techno",
        "year_start": 1985, "year_end": None, "origin": "Detroit",
        "parents": [], "description": "Curated.", "key_artists": ["Juan Atkins"],
        "key_labels": [], "subvariants": [], "wikidata_id": "Q48803",
        "wikipedia_slug": "Techno", "audio_examples": [],
    }]))
    new_genres = [{
        "qid": "Q48803", "name": "Techno", "year_start": 1985,
        "parent_qids": [], "enwiki_slug": "Techno", "description": "Wikipedia.",
    }]
    added = import_track("techno", new_genres, genres_dir)
    assert added == 0
    result = yaml.safe_load((genres_dir / "techno.yaml").read_text())
    assert len(result) == 1
    assert result[0]["description"] == "Curated."
    assert result[0]["key_artists"] == ["Juan Atkins"]


def test_import_track_skips_genres_without_year(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    new_genres = [{
        "qid": "Q111", "name": "No Year Genre", "year_start": None,
        "parent_qids": [], "enwiki_slug": "", "description": "",
    }]
    added = import_track("techno", new_genres, genres_dir)
    assert added == 0
    assert not (genres_dir / "techno.yaml").exists()


def test_apply_track_renames_early_to_pioneers(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    (genres_dir / "early.yaml").write_text(yaml.dump([
        {"id": "theremin", "name": "Theremin", "track": "early", "year_start": 1920},
    ]))
    apply_track_renames(genres_dir)
    assert (genres_dir / "pioneers.yaml").exists()
    assert not (genres_dir / "early.yaml").exists()
    result = yaml.safe_load((genres_dir / "pioneers.yaml").read_text())
    assert result[0]["track"] == "pioneers"


def test_apply_track_renames_avantgarde_to_ambient(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    (genres_dir / "avantgarde.yaml").write_text(yaml.dump([
        {"id": "ambient", "name": "Ambient", "track": "avantgarde", "year_start": 1978},
    ]))
    apply_track_renames(genres_dir)
    assert (genres_dir / "ambient.yaml").exists()
    assert not (genres_dir / "avantgarde.yaml").exists()
    result = yaml.safe_load((genres_dir / "ambient.yaml").read_text())
    assert result[0]["track"] == "ambient"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/pipeline/test_import_genres.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.import_genres'`

- [ ] **Step 3: Create pipeline/import_genres.py**

```python
"""Merges classified Wikidata genres into data/genres/ YAML files."""
from __future__ import annotations
import re
from pathlib import Path
import yaml

TRACK_RENAMES = {"early": "pioneers", "avantgarde": "ambient"}
CURATED_FIELDS = {"description", "key_artists", "key_labels", "subvariants", "audio_examples", "origin"}


def make_id(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:40]


def make_unique_id(name: str, existing_ids: set[str]) -> str:
    base = make_id(name)
    if base not in existing_ids:
        return base
    for i in range(2, 100):
        candidate = f"{base}_{i}"
        if candidate not in existing_ids:
            return candidate
    return base


def merge_genre(existing: dict, incoming: dict) -> dict:
    """Updates only empty curated fields in existing from incoming."""
    result = dict(existing)
    for key, value in incoming.items():
        if key in CURATED_FIELDS:
            if not result.get(key):
                result[key] = value
        elif result.get(key) is None or result.get(key) == "":
            result[key] = value
    return result


def wikidata_genre_to_yaml(genre: dict, track_id: str, existing_ids: set[str]) -> dict:
    """Converts enriched genre dict to genre YAML entry format."""
    genre_id = make_unique_id(genre["name"], existing_ids)
    return {
        "id": genre_id,
        "name": genre["name"],
        "track": track_id,
        "year_start": genre["year_start"],
        "year_end": None,
        "origin": "",
        "parents": [],
        "description": genre.get("description", ""),
        "key_artists": [],
        "key_labels": [],
        "subvariants": [],
        "wikidata_id": genre["qid"],
        "wikipedia_slug": genre.get("enwiki_slug", ""),
        "audio_examples": [],
    }


def import_track(track_id: str, new_genres: list[dict], genres_dir: Path) -> int:
    """Merges new_genres into genres_dir/<track_id>.yaml. Returns count of added genres."""
    yaml_path = genres_dir / f"{track_id}.yaml"
    existing: list[dict] = []
    if yaml_path.exists():
        existing = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or []

    existing_by_qid = {g.get("wikidata_id", ""): g for g in existing if g.get("wikidata_id")}
    existing_ids = {g["id"] for g in existing}
    added = 0

    for genre in new_genres:
        if not genre.get("year_start"):
            continue
        qid = genre["qid"]
        if qid in existing_by_qid:
            idx = next(i for i, g in enumerate(existing) if g.get("wikidata_id") == qid)
            existing[idx] = merge_genre(
                existing[idx],
                wikidata_genre_to_yaml(genre, track_id, existing_ids),
            )
        else:
            new_entry = wikidata_genre_to_yaml(genre, track_id, existing_ids)
            existing_ids.add(new_entry["id"])
            existing.append(new_entry)
            added += 1

    if existing:
        yaml_path.write_text(yaml.dump(existing, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return added


def apply_track_renames(genres_dir: Path) -> None:
    """Renames early→pioneers and avantgarde→ambient YAML files; updates track fields."""
    for old_name, new_name in TRACK_RENAMES.items():
        old_path = genres_dir / f"{old_name}.yaml"
        new_path = genres_dir / f"{new_name}.yaml"
        if old_path.exists() and not new_path.exists():
            genres = yaml.safe_load(old_path.read_text(encoding="utf-8")) or []
            for g in genres:
                if g.get("track") == old_name:
                    g["track"] = new_name
            new_path.write_text(yaml.dump(genres, allow_unicode=True, sort_keys=False), encoding="utf-8")
            old_path.unlink()
            print(f"  Renamed {old_name}.yaml -> {new_name}.yaml ({len(genres)} genres)")


def import_all(classified_dir: Path, genres_dir: Path) -> None:
    apply_track_renames(genres_dir)
    genres_dir.mkdir(parents=True, exist_ok=True)
    total_added = 0
    for yaml_file in sorted(classified_dir.glob("*.yaml")):
        track_id = yaml_file.stem
        new_genres = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or []
        added = import_track(track_id, new_genres, genres_dir)
        print(f"  {track_id}: +{added} new genres")
        total_added += added
    print(f"Total: +{total_added} new genres imported")


if __name__ == "__main__":
    import_all(
        Path("data/_wikidata/classified"),
        Path("data/genres"),
    )
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/pipeline/test_import_genres.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
uv run pytest tests/pipeline/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/import_genres.py tests/pipeline/test_import_genres.py
git commit -m "feat: add import_genres.py with merge-safe YAML import"
```

---

## Task 6: Migrate existing YAML data

**Files:**
- Rename: `data/genres/early.yaml` → `data/genres/pioneers.yaml`
- Rename: `data/genres/avantgarde.yaml` → `data/genres/ambient.yaml`

- [ ] **Step 1: Run apply_track_renames on live data**

```bash
uv run python -c "
from pipeline.import_genres import apply_track_renames
from pathlib import Path
apply_track_renames(Path('data/genres'))
"
```

Expected output:
```
  Renamed early.yaml -> pioneers.yaml (3 genres)
  Renamed avantgarde.yaml -> ambient.yaml (3 genres)
```

- [ ] **Step 2: Verify renamed files have correct track fields**

```bash
grep "track:" data/genres/pioneers.yaml data/genres/ambient.yaml
```

Expected: All lines show `track: pioneers` or `track: ambient` (no remaining `early` or `avantgarde`).

- [ ] **Step 3: Run build.py to verify JSON output is valid**

```bash
uv run python pipeline/build.py
```

Expected: No errors. Output ends with `Wrote N genres, M edges -> public/data/genres.json`

- [ ] **Step 4: Run all tests**

```bash
uv run pytest tests/pipeline/ -v && pnpm test
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -A data/genres/
git commit -m "feat: migrate genre YAML data to new track IDs (early→pioneers, avantgarde→ambient)"
```

---

## Task 7: End-to-end pipeline run

**Files:**
- Create: `data/_wikidata/raw.yaml` (primary genres from Wikipedia category)
- Create: `data/_wikidata/candidates.yaml` (related genres for manual review)
- Create: `data/_wikidata/classified/<track>.yaml` (per track)
- Create: `data/_wikidata/unclassified.yaml`
- Modify: `data/genres/*.yaml` (new genres merged in)
- Generated (not committed): `public/data/genres.json` (gitignored; built by CI)

- [ ] **Step 1: Fetch genres from Wikipedia + Wikidata**

This takes ~5 minutes (rate-limited API calls):

```bash
uv run python pipeline/fetch_genres.py
```

Expected output:
```
Crawling Category:Electronic_music_genres...
Found N genre articles in category tree
Fetching Wikipedia data (batches of 50)...
Got QIDs for N/M articles
Fetching Wikidata relations...
Fetching P candidate genres referenced as parents...
Primary genres: N -> data/_wikidata/raw.yaml
Candidates (for review): P -> data/_wikidata/candidates.yaml
```

N should be > 150. If the request times out, retry once.

- [ ] **Step 2: Review candidates.yaml**

```bash
uv run python -c "
import yaml
c = yaml.safe_load(open('data/_wikidata/candidates.yaml'))
print(len(c), 'candidates')
for g in sorted(c, key=lambda x: x.get('name', '')):
    print(f'  {g[\"name\"]} ({g.get(\"year_start\", \"?\")})')
" | head -40
```

Candidates are genres referenced as parents of electronic genres but not in the Wikipedia category. Review the list: if any are clearly relevant (e.g., "Funk", "Dub", "Disco"), you can add their QID to the appropriate track in `data/track_seeds.yaml` — they will then be classified correctly in the next step (even without being in `raw.yaml`, because classify_genres.py uses `raw.yaml` only for genres to classify, while `track_seeds.yaml` defines the track roots for BFS traversal).

- [ ] **Step 3: Classify genres to tracks**

```bash
uv run python pipeline/classify_genres.py
```

Expected: Lines like `techno: N genres`, `house: M genres`, etc.
Total classified should be > 80% of raw.yaml count.

- [ ] **Step 4: Review unclassified.yaml**

```bash
uv run python -c "
import yaml
g = yaml.safe_load(open('data/_wikidata/unclassified.yaml'))
print(len(g), 'unclassified')
for x in sorted(g, key=lambda x: x.get('name', '')):
    print(f'  {x[\"name\"]} ({x.get(\"year_start\", \"?\")})')
"
```

Unclassified genres have no ancestor QID matching any seed. If important genres appear here, add their QID (or an ancestor QID) to `data/track_seeds.yaml` and re-run classify only:

```bash
uv run python pipeline/classify_genres.py
```

- [ ] **Step 5: Import classified genres into data/genres/**

```bash
uv run python pipeline/import_genres.py
```

Expected: `Total: +N new genres imported` where N > 80.

- [ ] **Step 6: Run build.py**

```bash
uv run python pipeline/build.py
```

Expected: `Wrote N genres, M edges -> public/data/genres.json` where N > 90.

- [ ] **Step 7: Verify genre distribution**

```bash
uv run python -c "
import json
from collections import Counter
d = json.load(open('public/data/genres.json'))
print('Total genres:', len(d['genres']))
counts = Counter(g['track'] for g in d['genres'])
for track, count in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'  {track}: {count}')
"
```

- [ ] **Step 8: Run full test suite**

```bash
uv run pytest tests/pipeline/ -v && pnpm test
```

Expected: All tests PASS.

- [ ] **Step 9: Commit and push**

```bash
git add data/_wikidata/ data/genres/
git commit -m "feat: populate 200+ genres via Wikipedia category + Wikidata pipeline"
git push
```
