# Design: Genre-Expansion — Ishkur Track-Struktur + Wikidata-Vollbefüllung

**Datum:** 2026-05-24  
**Status:** Approved

---

## Ziel

Die aktuellen 7 Tracks / 20 Genres auf ~20 Tracks / 200+ Genres erweitern. Track-Struktur orientiert sich an Ishkur's Guide to Electronic Music. Neue Genre-Daten werden automatisch via Wikidata SPARQL geholt, Beschreibungen via Wikipedia MediaWiki API. Bestehende manuell kuratierte Daten bleiben erhalten.

---

## Track-Struktur (20 Tracks)

| id | Label | Herkunft |
|---|---|---|
| `pioneers` | Pioneers | bisher `early` |
| `electroacoustic` | Electroacoustic | unverändert |
| `ambient` | Ambient / Chill Out | bisher `avantgarde` |
| `industrial` | Industrial / EBM | unverändert |
| `downtempo` | Downtempo | neu (Ishkur) |
| `hip_hop` | Hip Hop | neu (Ishkur) |
| `urban` | Urban | neu (Ishkur) |
| `electro` | Electro | neu (Ishkur) |
| `techno` | Techno | unverändert |
| `hardcore` | Hardcore | neu (Ishkur) |
| `drum_n_bass` | Drum n Bass | neu (Ishkur) |
| `breakbeat` | Breakbeat | neu (Ishkur) |
| `acid` | Acid | neu (Ishkur) |
| `house` | House | unverändert |
| `tech_house` | Tech House | neu (Ishkur) |
| `progressive` | Progressive | neu (Ishkur) |
| `garage` | Garage / Deep House | neu (Ishkur) |
| `uk_garage` | UK Garage | neu (Ishkur) |
| `bass` | Bass | neu (Ishkur) |
| `disco` | Disco / Funk | unverändert |

---

## Pipeline-Architektur

### Neue Dateien

```
data/
  _wikidata/
    raw.yaml          # fetch_wikidata.py output
    enriched.yaml     # fetch_wikipedia.py output
    classified/
      techno.yaml     # classify_genres.py output (per track)
      house.yaml
      ...
    unclassified.yaml # Genres ohne Track-Zuweisung
  track_seeds.yaml    # manuell: Root-QIDs pro Track

pipeline/
  fetch_wikidata.py   # rewrite: electronic music SPARQL
  fetch_wikipedia.py  # neu: Wikipedia abstract per Genre
  classify_genres.py  # neu: QID-Ancestor-Traversal → Track
  import_genres.py    # neu: merge classified → data/genres/
  build.py            # update: TRACKS-Liste
```

### Workflow

```
fetch_wikidata.py
  → data/_wikidata/raw.yaml

fetch_wikipedia.py
  → data/_wikidata/enriched.yaml

classify_genres.py
  → data/_wikidata/classified/<track>.yaml
  → data/_wikidata/unclassified.yaml

import_genres.py
  → data/genres/<track>.yaml  (merge, kein Überschreiben kuratierter Felder)

build.py → public/data/genres.json
```

---

## Script-Spezifikationen

### 1. `pipeline/fetch_wikidata.py` (Rewrite)

**SPARQL-Query:** Genres die via `P279+` (Subklasse) zu einem der Track-Root-QIDs gehören oder `P31 wd:Q188451` (Musikgenre) sind UND einen elektronischen Vorfahren haben.

**Konkret:** Startet von QIDs in `track_seeds.yaml` und holt alle direkten + indirekten Subklassen via:
```sparql
SELECT DISTINCT ?genre ?genreLabel ?inception ?sitelink WHERE {
  VALUES ?root { wd:Q207648 wd:Q11399 ... }  # aus track_seeds.yaml
  ?genre wdt:P279+ ?root.
  OPTIONAL { ?genre wdt:P571 ?inception. }
  OPTIONAL {
    ?article schema:about ?genre;
             schema:isPartOf <https://en.wikipedia.org/>.
    BIND(?article AS ?sitelink)
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

**Output** (`data/_wikidata/raw.yaml`):
```yaml
- qid: Q207648
  name: Techno
  year_start: 1985
  parent_qids: [Q9778]
  enwiki_slug: Techno
```

Schreibt ~200–400 Einträge. Keine Genres ohne QID.

### 2. `pipeline/fetch_wikipedia.py` (neu)

- Liest `data/_wikidata/raw.yaml`
- Für jedes Genre mit `enwiki_slug`: GET `https://en.wikipedia.org/w/api.php?action=query&titles=SLUG&prop=extracts&exintro=1&explaintext=1&sentences=3&format=json`
- Extrahiert ersten Absatz (max. 500 Zeichen)
- Rate-limit: 1 Request/Sekunde (`time.sleep(1)`)
- Schreibt `data/_wikidata/enriched.yaml` (alle Felder aus raw.yaml + `description`)
- Genres ohne enwiki-Slug: `description: null`

### 3. `pipeline/classify_genres.py` (neu)

**Input:** `data/_wikidata/enriched.yaml` + `data/track_seeds.yaml`

**Algorithmus:**
1. Baue Index: `qid → {parent_qids, track}` aus enriched.yaml
2. Für jedes Genre: BFS/DFS durch `parent_qids` bis ein Ancestor-QID in `track_seeds` gefunden wird
3. Weise Track zu; bei mehreren Matches: der spezifischere Ancestor gewinnt (kürzerer Pfad)
4. Schreibe klassifizierte Genres nach `data/_wikidata/classified/<track>.yaml`
5. Schreibe nicht klassifizierte Genres nach `data/_wikidata/unclassified.yaml`

**`data/track_seeds.yaml`:**
```yaml
techno:          { qids: [Q207648] }
house:           { qids: [Q11399] }
hip_hop:         { qids: [Q11401] }
drum_n_bass:     { qids: [Q193709] }
hardcore:        { qids: [Q584435] }
breakbeat:       { qids: [Q846291] }
ambient:         { qids: [Q56733] }
electro:         { qids: [Q1062303] }
garage:          { qids: [Q848882] }
uk_garage:       { qids: [Q487956] }
downtempo:       { qids: [Q1088840] }
urban:           { qids: [Q11369] }
bass:            { qids: [Q3839300] }
disco:           { qids: [Q11606] }
industrial:      { qids: [Q179012] }
progressive:     { qids: [Q3029199] }
tech_house:      { qids: [Q1362808] }
acid:            { qids: [Q219639] }
electroacoustic: { qids: [Q207436] }
pioneers:        { qids: [] }
```

### 4. `pipeline/import_genres.py` (neu)

**Input:** `data/_wikidata/classified/<track>.yaml` pro Track

**Merge-Policy per Genre:**
- Genre existiert noch nicht in `data/genres/<track>.yaml` → anhängen
- Genre existiert bereits (Match via `wikidata_id` oder `id`) → nur leere Felder befüllen; `description`, `key_artists`, `audio_examples`, `key_labels`, `subvariants` werden nicht überschrieben wenn sie bereits gesetzt sind
- Track-ID-Remap: `early` → `pioneers`, `avantgarde` → `ambient`; YAML-Dateien entsprechend umbenennen

**ID-Generierung für neue Genres:** `snake_case(name)`, Sonderzeichen entfernen, max 40 Zeichen. Kollisionen: Suffix `_2`, `_3`.

**Output:** Aktualisierte `data/genres/<track>.yaml` Dateien.

### 5. `pipeline/build.py` (Update)

Nur TRACKS-Liste erweitern auf die 20 neuen Tracks mit passenden Farben:

```python
TRACKS = [
    Track(id="pioneers",        label="Pioneers",           color="#546e7a", order=0),
    Track(id="electroacoustic", label="Electroacoustic",    color="#388e3c", order=1),
    Track(id="ambient",         label="Ambient / Chill Out",color="#7b1fa2", order=2),
    Track(id="downtempo",       label="Downtempo",          color="#795548", order=3),
    Track(id="industrial",      label="Industrial / EBM",   color="#c62828", order=4),
    Track(id="urban",           label="Urban",              color="#ff8f00", order=5),
    Track(id="hip_hop",         label="Hip Hop",            color="#f57f17", order=6),
    Track(id="bass",            label="Bass",               color="#37474f", order=7),
    Track(id="electro",         label="Electro",            color="#0288d1", order=8),
    Track(id="techno",          label="Techno",             color="#00695c", order=9),
    Track(id="hardcore",        label="Hardcore",           color="#b71c1c", order=10),
    Track(id="drum_n_bass",     label="Drum n Bass",        color="#ad1457", order=11),
    Track(id="breakbeat",       label="Breakbeat",          color="#6a1b9a", order=12),
    Track(id="acid",            label="Acid",               color="#f9a825", order=13),
    Track(id="disco",           label="Disco / Funk",       color="#e65100", order=14),
    Track(id="house",           label="House",              color="#1565c0", order=15),
    Track(id="tech_house",      label="Tech House",         color="#01579b", order=16),
    Track(id="progressive",     label="Progressive",        color="#283593", order=17),
    Track(id="garage",          label="Garage / Deep House",color="#004d40", order=18),
    Track(id="uk_garage",       label="UK Garage",          color="#006064", order=19),
]
```

---

## Migration bestehender Daten

`import_genres.py` führt beim ersten Run folgende Renames durch:
- `data/genres/early.yaml` → `data/genres/pioneers.yaml` (alle `track: early` → `track: pioneers`)
- `data/genres/avantgarde.yaml` → `data/genres/ambient.yaml` (alle `track: avantgarde` → `track: ambient`)
- Alle anderen bestehenden Dateien bleiben unverändert

---

## Nicht im Scope

- Automatische Audio-Beispiele für neue Genres (bleibt manuell via `resolve_commons.py`)
- Frontend-Änderungen (Tracks werden dynamisch aus `genres.json` geladen)
- Genres ohne Wikidata-QID (nur manuell in YAML-Dateien ergänzbar)
- Vollständige manuelle Kuration aller 200+ Genres (Wikipedia-Abstracts sind ausreichend für den Graph)
