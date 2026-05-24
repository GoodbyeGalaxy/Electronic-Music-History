# Genre Expansion — Ishkur Track-Struktur + Wikipedia/Wikidata Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the graph from 7 tracks / 20 genres to 20 tracks / 200+ genres by adopting Ishkur's track structure and auto-populating genre data from Wikipedia categories + Wikidata relationships.

**Architecture:** Three new pipeline scripts — `fetch_genres.py` (Wikipedia category discovery + Wikidata enrichment + candidate collection), `classify_genres.py` (BFS track assignment), `import_genres.py` (merge into YAML). Primary data source is `Category:Electronic_music_genres` on Wikipedia (editorially curated). Wikidata is used only for inception dates and parent QIDs. Related genres not in the Wikipedia category are written to `candidates.yaml` for manual review. Existing manually curated fields are never overwritten. `build.py` only changes its TRACKS list.

**Tech Stack:** Python 3.11+, pydantic v2, PyYAML, requests, pytest. MediaWiki API. Wikidata SPARQL endpoint. `uv run` for all Python commands.

---

## Status: ALL TASKS COMPLETE ✅

**Actual results (2026-05-24):**
- 20 tracks implemented
- Wikipedia crawl: 921 primary genres + 126 candidates
- Pipeline classification: 154 genres classified via BFS + keyword fallback
- After manual additions + unclassified review: **194 total genres**
- 40 Python tests + 6 JS tests passing
- Additional feature: ancestor-path highlight on node click (BFS upward traversal)

**Key implementation notes for future reference:**
- All original seed QIDs in this plan were wrong (Q48803 = horticulture, not techno). Corrected QIDs are in `data/track_seeds.yaml`.
- `fetch_genres.py` required Retry-After header handling for Wikipedia 429s and checkpoint-resume (`_cp_titles.yaml`, `_cp_wiki.yaml`, `_cp_wd.yaml`).
- `classify_genres.py` needed keyword fallback because 674/921 genres had no Wikidata parent_qids.
- Analog roots (soul, funk, blues, jazz, dub, reggae) added manually to pioneers/disco/bass tracks.
- Post-pipeline: 45 additional genres added from manual unclassified.yaml review.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pipeline/build.py` | Modify | Update TRACKS list (7 → 20) |
| `data/track_seeds.yaml` | Create | Maps Wikidata root QIDs to track IDs for classification |
| `pipeline/fetch_genres.py` | Create | Wikipedia category crawl + Wikidata enrichment + candidates |
| `pipeline/classify_genres.py` | Create | BFS track assignment from seed QIDs + keyword fallback |
| `pipeline/import_genres.py` | Create | Merge classified genres into `data/genres/` |
| `tests/pipeline/test_fetch_genres.py` | Create | Unit tests with mocked HTTP |
| `tests/pipeline/test_classify_genres.py` | Create | Unit tests with fixture data |
| `tests/pipeline/test_import_genres.py` | Create | Unit tests with tmp_path |
| `tests/pipeline/test_build.py` | Modify | Update TRACKS count assertion |
| `data/genres/early.yaml` | Rename → `pioneers.yaml` | Track field update |
| `data/genres/avantgarde.yaml` | Rename → `ambient.yaml` | Track field update |
| `src/graph/renderer.js` | Modify | Ancestor-path highlight on node click |

---

## Task 1: Update TRACKS in build.py ✅

**Files:**
- Modify: `pipeline/build.py:5-13`
- Modify: `tests/pipeline/test_build.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run tests to verify they fail**
- [x] **Step 3: Replace TRACKS in build.py**
- [x] **Step 4: Run all pipeline tests**
- [x] **Step 5: Commit**

---

## Task 2: Create data/track_seeds.yaml ✅

**Files:**
- Create: `data/track_seeds.yaml`

Note: QIDs were validated against Wikidata SPARQL on 2026-05-24. The QIDs in the original plan spec were all incorrect.

- [x] **Step 1: Create the file**
- [x] **Step 2: Verify it loads as valid YAML**
- [x] **Step 3: Commit**

---

## Task 3: Create fetch_genres.py ✅

Primary data source: Wikipedia `Category:Electronic_music_genres` (recursively traversed). Wikidata provides inception dates, parent QIDs, and cross-genre links. Genres referenced as Wikidata parents but absent from the Wikipedia category are written to `candidates.yaml` for manual review.

**Files:**
- Create: `pipeline/fetch_genres.py`
- Create: `tests/pipeline/test_fetch_genres.py`

**Implementation notes:**
- Uses iterative BFS (not recursive) to avoid stack overflow.
- `_SKIP_SUBCAT_WORDS` filter prevents recursing into musician/album/event subcategories.
- `_get_with_backoff()`: reads `Retry-After` header for 429 backoff, 6 retries, 2s base delay.
- Checkpoint-resume: saves `_cp_titles.yaml`, `_cp_wiki.yaml`, `_cp_wd.yaml` after each batch.
- `flush=True` on all `print()` for unbuffered output.

- [x] **Step 1: Write the tests**
- [x] **Step 2: Run tests to verify they fail**
- [x] **Step 3: Create pipeline/fetch_genres.py**
- [x] **Step 4: Run tests**
- [x] **Step 5: Run full pipeline test suite**
- [x] **Step 6: Commit**

---

## Task 4: Create classify_genres.py ✅

**Files:**
- Create: `pipeline/classify_genres.py`
- Create: `tests/pipeline/test_classify_genres.py`

**Implementation notes:**
- BFS classification alone yielded only 18/921 genres (flat Wikidata hierarchy problem).
- Added `_KEYWORD_RULES` ordered list as fallback: 20 rules, most-specific first, covering all 20 tracks.
- Final result: 154/921 classified (83 via BFS, 71 via keyword fallback).
- 6 tests total (added `test_classify_uses_keyword_fallback_when_no_qid_path`).

- [x] **Step 1: Write the tests**
- [x] **Step 2: Run tests to verify they fail**
- [x] **Step 3: Create pipeline/classify_genres.py**
- [x] **Step 4: Run tests**
- [x] **Step 5: Run full suite**
- [x] **Step 6: Commit**

---

## Task 5: Create import_genres.py ✅

**Files:**
- Create: `pipeline/import_genres.py`
- Create: `tests/pipeline/test_import_genres.py`

- [x] **Step 1: Write the tests**
- [x] **Step 2: Run tests to verify they fail**
- [x] **Step 3: Create pipeline/import_genres.py**
- [x] **Step 4: Run tests**
- [x] **Step 5: Run full suite**
- [x] **Step 6: Commit**

---

## Task 6: Migrate existing YAML data ✅

**Files:**
- Rename: `data/genres/early.yaml` → `data/genres/pioneers.yaml`
- Rename: `data/genres/avantgarde.yaml` → `data/genres/ambient.yaml`

- [x] **Step 1: Run apply_track_renames on live data**
- [x] **Step 2: Verify renamed files have correct track fields**
- [x] **Step 3: Run build.py to verify JSON output is valid**
- [x] **Step 4: Run all tests**
- [x] **Step 5: Commit**

---

## Task 7: End-to-end pipeline run ✅

**Files:**
- Created: `data/_wikidata/raw.yaml` (921 primary genres)
- Created: `data/_wikidata/candidates.yaml` (126 related genres)
- Created: `data/_wikidata/classified/<track>.yaml` (per track)
- Created: `data/_wikidata/unclassified.yaml` (767 unclassified)
- Modified: `data/genres/*.yaml` (89 new genres merged in via pipeline)

- [x] **Step 1: Fetch genres from Wikipedia + Wikidata**
- [x] **Step 2: Review candidates.yaml**
- [x] **Step 3: Classify genres to tracks**
- [x] **Step 4: Review unclassified.yaml**
- [x] **Step 5: Import classified genres into data/genres/**
- [x] **Step 6: Run build.py**
- [x] **Step 7: Verify genre distribution**
- [x] **Step 8: Run full test suite**
- [x] **Step 9: Commit and push**

---

## Task 8 (post-plan): Manual genre additions ✅

Analog root genres and quality fixes applied after pipeline run.

**Removed (data quality):**
- "Dogs On Acid" from `acid.yaml` (forum website, not a genre)
- "Paradise Garage" from `garage.yaml` (nightclub, not a genre)

**Added — analog roots:**
- `pioneers.yaml`: blues (1920), jazz (1920), gospel (1930)
- `disco.yaml`: soul (1955), funk (1965), philadelphia_soul (1971)
- `bass.yaml`: reggae (1960), dub (1968), dubstep (2000), grime (2002)

**Added — sparse tracks:**
- `progressive.yaml` (created): trance, progressive_trance, goa_trance, psytrance, eurodance, eurotrance, vocal_trance, uplifting_trance, hard_trance
- `tech_house.yaml` (created): tech_house, minimal_tech_house, deep_tech, micro_house
- `acid.yaml`: acid_house, acid_techno, acid_trance, acid_breaks
- `garage.yaml`: garage_house, new_jersey_garage, deep_house
- `drum_n_bass.yaml`: liquid_dnb, neurofunk, darkstep, jump_up
- `breakbeat.yaml`: nu_skool_breaks, baltimore_club, miami_bass
- `hardcore.yaml`: gabber, happy_hardcore, terrorcore

Result: 111 → 149 total genres.

- [x] **Remove data quality issues**
- [x] **Add analog roots to pioneers, disco, bass**
- [x] **Create progressive.yaml and tech_house.yaml**
- [x] **Fill remaining sparse tracks**
- [x] **Run full test suite (40 Python + 6 JS passing)**
- [x] **Commit**

---

## Task 9 (post-plan): Unclassified review + ancestor-path highlight ✅

**Genres added from unclassified.yaml review (+45):**
- `electroacoustic`: noise_music, no_wave, idm, glitch, algorave
- `ambient`: new_age, space_music, ethereal_wave, dungeon_synth, vaporwave, chillwave
- `downtempo`: illbient, broken_beat, nu_jazz, folktronica
- `industrial`: cold_wave, minimal_wave, dark_wave, power_noise, neue_deutsche_haerte, futurepop, new_beat
- `electro`: neue_deutsche_welle, new_wave, chiptune, synthwave, freestyle
- `techno`: free_tekno, future_rave
- `hardcore`: makina, hardbass, hard_nrg, lento_violento
- `breakbeat`: footwork, jersey_club, new_rave
- `disco`: eurobeat, italo_dance
- `house`: tribal_guarachero, moombahton
- `bass`: kuduro, uk_bass, reggaestep, singeli
- `pioneers`: krautrock

Result: 149 → 194 total genres.

**Ancestor-path highlight (renderer.js):**
- Clicking a node now BFS-traverses all parent edges upward
- Clicked node + all ancestors shown with `node--selected` glow
- All non-ancestor nodes and non-path edges dimmed
- Canvas click still clears selection

- [x] **Filter unclassified.yaml: identify genuine electronic genres**
- [x] **Add 45 genres to existing track files**
- [x] **Implement ancestor-path highlight in renderer.js**
- [x] **Run full test suite (40 Python + 6 JS passing)**
- [x] **Commit**
