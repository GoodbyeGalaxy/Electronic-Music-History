# Electronic Music History Graph — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Interaktive Web-App, die die Geschichte der elektronischen Musik (1900–2025) als navigierbaren Graphen mit Zeitachse, Genre-Spuren, Ableitungskanten und CC-lizenzierten Audiobeispielen darstellt.

**Architecture:** Python-Datenpipeline liest YAML-Quelldateien, fragt Wikidata via SPARQL ab und exportiert `public/data/genres.json`. Das Vite+D3.js-Frontend lädt diese JSON-Datei und rendert den Graphen als SVG — kein Server erforderlich. Deployment via GitHub Actions auf GitHub Pages.

**Tech Stack:** Python 3.11+, pydantic v2, PyYAML, requests · Vite 5, D3.js 7, Vitest · pnpm · uv · GitHub Pages

---

## Dateistruktur

```
electronic-music-history/
├── data/
│   ├── genres/
│   │   ├── early.yaml
│   │   ├── electroacoustic.yaml
│   │   ├── avantgarde.yaml
│   │   ├── industrial.yaml
│   │   ├── techno.yaml
│   │   ├── house.yaml
│   │   └── disco.yaml
│   └── edges.yaml
├── pipeline/
│   ├── __init__.py
│   ├── schema.py          # pydantic-Modelle (Genre, Edge, Track, AudioExample)
│   ├── build.py           # YAML laden → validieren → genres.json exportieren
│   ├── fetch_wikidata.py  # Wikidata SPARQL → YAML-Seed schreiben
│   └── resolve_commons.py # Wikimedia Commons API → audio_examples ergänzen
├── tests/
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── test_build.py
│   │   ├── test_fetch_wikidata.py
│   │   └── test_resolve_commons.py
│   └── graph/
│       └── layout.test.js
├── src/
│   ├── main.js            # Einstiegspunkt: genres.json laden, Graph initialisieren
│   ├── graph/
│   │   ├── layout.js      # Datenpositionen berechnen (x/y aus Jahr/Track)
│   │   └── renderer.js    # D3.js SVG: Tracks, Knoten, Kanten, Zoom/Pan
│   ├── panels/
│   │   ├── detail.js      # Slide-in Genre-Detail-Panel
│   │   └── audio.js       # Audio-Player für Wikimedia Commons Dateien
│   ├── controls/
│   │   ├── filters.js     # Track-Toggles + Zeitraum-Slider
│   │   └── search.js      # Freitextsuche über Genre-Namen/Künstler
│   └── styles/
│       └── main.css       # Dunkles Theme, Knoten-States, Panel-Animationen
├── public/
│   └── data/
│       └── genres.json    # generiert durch pipeline/build.py (gitignored)
├── index.html
├── vite.config.js
├── package.json
├── pyproject.toml
├── .gitignore
└── .github/
    └── workflows/
        └── deploy.yml
```

---

## Task 1: Projekt-Scaffold

**Files:**
- Create: `package.json`
- Create: `vite.config.js`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `index.html`

- [ ] **Step 1: package.json schreiben**

```json
{
  "name": "electronic-music-history",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "d3": "^7.9.0"
  },
  "devDependencies": {
    "vite": "^5.4.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: vite.config.js schreiben**

```javascript
import { defineConfig } from 'vite';

export default defineConfig({
  base: '/electronic-music-history/',
  build: { outDir: 'dist' },
  test: { environment: 'node' },
});
```

- [ ] **Step 3: pyproject.toml schreiben**

```toml
[project]
name = "emh-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.0",
  "PyYAML>=6.0",
  "requests>=2.32",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-mock>=3.14"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 4: .gitignore schreiben**

```
node_modules/
dist/
.venv/
__pycache__/
*.pyc
public/data/genres.json
.superpowers/
```

- [ ] **Step 5: index.html schreiben**

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Electronic Music History</title>
  <link rel="stylesheet" href="/src/styles/main.css" />
</head>
<body>
  <div id="app">
    <div id="toolbar"></div>
    <div id="graph-container">
      <div id="track-labels"></div>
      <div id="canvas-wrapper"></div>
    </div>
    <div id="detail-panel" class="panel panel--closed"></div>
  </div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 6: Dependencies installieren**

```bash
pnpm install
uv venv
uv sync --extra dev
```

Expected: `node_modules/` und `.venv/` erstellt.

- [ ] **Step 7: Commit**

```bash
git init
git add package.json vite.config.js pyproject.toml .gitignore index.html
git commit -m "chore: project scaffold — Vite + D3.js + Python pipeline"
```

---

## Task 2: Python-Schema

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/schema.py`
- Create: `tests/pipeline/__init__.py`
- Create: `tests/pipeline/test_build.py`

- [ ] **Step 1: Failing-Test schreiben**

`tests/pipeline/test_build.py`:

```python
import pytest
from pipeline.schema import Genre, Edge, AudioExample

def test_genre_requires_id_name_track_year():
    g = Genre(
        id="theremin", name="Theremin", track="early",
        year_start=1920, parents=[]
    )
    assert g.id == "theremin"
    assert g.year_end is None

def test_genre_rejects_invalid_year():
    with pytest.raises(Exception):
        Genre(id="x", name="X", track="y", year_start="not-a-year", parents=[])

def test_edge_from_yaml_maps_from_field():
    e = Edge.from_yaml({"from": "disco", "to": "house", "type": "influence", "label": ""})
    assert e.from_ == "disco"
    assert e.to == "house"

def test_audio_example_defaults_source():
    a = AudioExample(file="test.ogg", title="Test", artist="Artist")
    assert a.source == "wikimedia_commons"
```

- [ ] **Step 2: Test ausführen — erwartet FAIL**

```bash
uv run pytest tests/pipeline/test_build.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline'`

- [ ] **Step 3: Schema implementieren**

`pipeline/__init__.py`: (leere Datei)

`pipeline/schema.py`:

```python
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


class AudioExample(BaseModel):
    file: str
    source: str = "wikimedia_commons"
    title: str
    artist: str


class Genre(BaseModel):
    id: str
    name: str
    track: str
    year_start: int
    year_end: Optional[int] = None
    origin: str = ""
    parents: list[str] = []
    description: str = ""
    key_artists: list[str] = []
    key_labels: list[str] = []
    subvariants: list[str] = []
    wikidata_id: str = ""
    wikipedia_slug: str = ""
    audio_examples: list[AudioExample] = []

    @field_validator("year_start")
    @classmethod
    def year_must_be_int(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("year_start must be an integer")
        return v


class Edge(BaseModel):
    from_: str
    to: str
    type: str = "influence"
    label: str = ""

    model_config = {"populate_by_name": True}

    @classmethod
    def from_yaml(cls, data: dict) -> "Edge":
        return cls(
            from_=data["from"],
            to=data["to"],
            type=data.get("type", "influence"),
            label=data.get("label", ""),
        )


class Track(BaseModel):
    id: str
    label: str
    color: str
    order: int
```

- [ ] **Step 4: Test ausführen — erwartet PASS**

```bash
uv run pytest tests/pipeline/test_build.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/__init__.py pipeline/schema.py tests/pipeline/__init__.py tests/pipeline/test_build.py
git commit -m "feat: pipeline schema — Genre, Edge, AudioExample pydantic models"
```

---

## Task 3: Seed-YAML-Daten

**Files:**
- Create: `data/genres/early.yaml`
- Create: `data/genres/electroacoustic.yaml`
- Create: `data/genres/avantgarde.yaml`
- Create: `data/genres/industrial.yaml`
- Create: `data/genres/techno.yaml`
- Create: `data/genres/house.yaml`
- Create: `data/genres/disco.yaml`
- Create: `data/edges.yaml`

- [ ] **Step 1: data/genres/early.yaml schreiben**

```yaml
- id: theremin
  name: Theremin
  track: early
  year_start: 1920
  origin: "Petrograd, RU"
  parents: []
  description: >
    Das Theremin, erfunden von Leon Theremin 1920, ist eines der ersten
    elektronischen Instrumente. Es wird beruehrungslos durch Handbewegungen
    in elektromagnetischen Feldern gespielt und beeinflusste sowohl
    Science-Fiction-Filmmusik als auch spaetere experimentelle Elektronik.
  key_artists: [Leon Theremin, Clara Rockmore]
  key_labels: []
  subvariants: []
  wikidata_id: Q193433
  wikipedia_slug: Theremin
  audio_examples: []

- id: ondes_martenot
  name: Ondes Martenot
  track: early
  year_start: 1928
  origin: "Paris, FR"
  parents: []
  description: >
    Von Maurice Martenot 1928 entwickeltes elektronisches Instrument mit
    einer einzigartigen Spieltechnik ueber Keyboard und Ring. Wurde von
    Messiaen, Boulez und spaeter Radiohead eingesetzt.
  key_artists: [Maurice Martenot, Jeanne Loriod, Jonny Greenwood]
  key_labels: []
  subvariants: []
  wikidata_id: Q190744
  wikipedia_slug: Ondes_Martenot
  audio_examples: []

- id: hammond_organ
  name: Hammond Organ
  track: early
  year_start: 1935
  origin: "Evanston, USA"
  parents: []
  description: >
    Die Hammond-Orgel (1935) nutzt Tonradgeneratoren zur Klangerzeugung
    und wurde zum wichtigsten Tastenhintergrund von Jazz, Gospel und Rock.
    Der Leslie-Lautsprecher mit rotierendem Horn praegt ihren charakteristischen Klang.
  key_artists: [Jimmy Smith, Keith Emerson, Jon Lord]
  key_labels: []
  subvariants: [Tonewheel Organ]
  wikidata_id: Q188248
  wikipedia_slug: Hammond_organ
  audio_examples: []
```

- [ ] **Step 2: data/genres/electroacoustic.yaml schreiben**

```yaml
- id: musique_concrete
  name: "Musique Concrete"
  track: electroacoustic
  year_start: 1948
  origin: "Paris, FR"
  parents: []
  description: >
    Pierre Schaeffer entwickelte 1948 im franzoesischen Rundfunk (RTF) eine
    Kompositionsmethode, die aufgenommene Alltagsklaenge als musikalisches
    Material verwendet. Etudes de bruits (1948) gilt als erste Veroeffentlichung.
  key_artists: [Pierre Schaeffer, Pierre Henry, Luc Ferrari]
  key_labels: [INA-GRM]
  subvariants: [Acousmatic Music]
  wikidata_id: Q207436
  wikipedia_slug: "Musique_concrete"
  audio_examples:
    - file: "Pierre_Schaeffer_-_Etudes_de_bruits_(1948).ogg"
      source: wikimedia_commons
      title: "Etudes de bruits (1948)"
      artist: Pierre Schaeffer

- id: elektronische_musik
  name: Elektronische Musik
  track: electroacoustic
  year_start: 1953
  origin: "Koeln, DE"
  parents: []
  description: >
    Am Studio fuer elektronische Musik des WDR Koeln entwickelten Stockhausen,
    Eimert und Nono ab 1953 eine Musik aus rein synthetischen Klaengen.
    Studien I und II (Stockhausen, 1953/54) sind Schluesselwerke.
  key_artists: [Karlheinz Stockhausen, Herbert Eimert, Luigi Nono]
  key_labels: [WDR]
  subvariants: []
  wikidata_id: Q816980
  wikipedia_slug: Electronic_music
  audio_examples: []

- id: tape_music
  name: Tape Music
  track: electroacoustic
  year_start: 1951
  origin: "New York, USA"
  parents: [musique_concrete]
  description: >
    In den USA entwickelten Louis und Bebe Barron sowie die New York School
    (Cage, Tudor) ab den fruehen 1950ern eine eigene Tradition mit Tonband
    als Kompositionswerkzeug. Forbidden Planet (1956) war der erste vollstaendig
    elektronische Filmsoundtrack.
  key_artists: [Louis Barron, Bebe Barron, John Cage, David Tudor]
  key_labels: []
  subvariants: []
  wikidata_id: Q1145220
  wikipedia_slug: Tape_music
  audio_examples: []
```

- [ ] **Step 3: data/genres/avantgarde.yaml schreiben**

```yaml
- id: ambient
  name: Ambient
  track: avantgarde
  year_start: 1978
  origin: "London, UK"
  parents: [tape_music]
  description: >
    Brian Eno pragte 1978 mit Ambient 1: Music for Airports sowohl den Begriff
    als auch das Genre. Charakteristisch sind langsame Entwicklungen, Atmosphaere
    und bewusste Indifferenz gegenueber aktiver Aufmerksamkeit.
  key_artists: [Brian Eno, Harold Budd, William Basinski]
  key_labels: [EG Records, Opal]
  subvariants: [Ambient Techno, Ambient House]
  wikidata_id: Q205718
  wikipedia_slug: Ambient_music
  audio_examples: []

- id: dark_ambient
  name: Dark Ambient
  track: avantgarde
  year_start: 1989
  origin: Europa
  parents: [ambient]
  description: >
    Dark Ambient entstand aus der Schnittmenge von Ambient und Industrial und
    zeichnet sich durch duestere, bedrohliche oder atmosphaerisch dichte Klangwelten aus.
    Gruppen wie Lustmord, Coil und Deutsch Nepal praegten das Genre.
  key_artists: [Lustmord, Coil, Deutsch Nepal, Robert Rich]
  key_labels: [Cold Meat Industry, Cyclic Law]
  subvariants: [Isolationism, Ritual Ambient]
  wikidata_id: Q1188920
  wikipedia_slug: Dark_ambient
  audio_examples: []

- id: drone
  name: Drone
  track: avantgarde
  year_start: 1960
  origin: "New York, USA"
  parents: [tape_music]
  description: >
    Aus La Monte Youngs minimalistischer Praxis der 1960er entstanden,
    basiert Drone auf lang gehaltenen Toenen oder Klangmassen. Terry Riley,
    Tony Conrad und spaeter Sunn O))) gehoeren zu den wichtigsten Vertretern.
  key_artists: [La Monte Young, Tony Conrad, "Sunn O)))", Earth]
  key_labels: [Table of the Elements]
  subvariants: [Drone Metal, Lowercase]
  wikidata_id: Q1164901
  wikipedia_slug: Drone_music
  audio_examples: []
```

- [ ] **Step 4: data/genres/industrial.yaml schreiben**

```yaml
- id: industrial
  name: Industrial
  track: industrial
  year_start: 1977
  origin: "London, UK"
  parents: [tape_music]
  description: >
    Throbbing Gristle gruendeten 1975 Industrial Records und praegten
    mit ihrer Musik einen Stil der bewussten Provokation, Noise und
    konzeptuellen Konfrontation. The Second Annual Report (1977) ist das
    Debuetalbuem.
  key_artists: [Throbbing Gristle, "Einstürzende Neubauten", SPK, Nurse with Wound]
  key_labels: [Industrial Records, Some Bizzare]
  subvariants: [Power Electronics, Noise, Post-Industrial]
  wikidata_id: Q185816
  wikipedia_slug: Industrial_music
  audio_examples: []

- id: ebm
  name: EBM
  track: industrial
  year_start: 1981
  origin: "Bruessel, BE"
  parents: [industrial]
  description: >
    Electronic Body Music entstand in Belgien mit Gruppen wie Front 242
    und Nitzer Ebb als tanzbare Hybride aus Industrial-Aggression und
    Synthesizer-Pop. Der Begriff wurde von Front 242 selbst gepragt.
  key_artists: [Front 242, Nitzer Ebb, Skinny Puppy, DAF]
  key_labels: [Play It Again Sam, "Wax Trax!"]
  subvariants: [Aggrotech, Futurepop, Dark Electro]
  wikidata_id: Q578643
  wikipedia_slug: Electronic_body_music
  audio_examples: []
```

- [ ] **Step 5: data/genres/techno.yaml schreiben**

```yaml
- id: techno
  name: Techno
  track: techno
  year_start: 1985
  origin: "Detroit, USA"
  parents: [industrial]
  description: >
    Die Belleville Three (Juan Atkins, Derrick May, Kevin Saunderson)
    entwickelten Mitte der 1980er in Detroit einen Stil aus europaeischer
    Elektronik (Kraftwerk, Giorgio Moroder), Funk und Chicago House.
    Strings of Life (Derrick May, 1987) ist das bekannteste Schlusselwerk.
  key_artists: [Juan Atkins, Derrick May, Kevin Saunderson, Jeff Mills, Underground Resistance]
  key_labels: [Transmat, Metroplex, KMS, Underground Resistance]
  subvariants: []
  wikidata_id: Q48803
  wikipedia_slug: Techno
  audio_examples: []

- id: acid_techno
  name: Acid Techno
  track: techno
  year_start: 1991
  origin: London/Berlin
  parents: [techno]
  description: >
    Acid Techno kombiniert den harten Groove des Detroit Techno mit dem
    verzerrenden TB-303-Bassklang des Acid House. In London und Berlin
    entstanden in den fruehen 1990ern pragende Tracks auf Labels wie
    Evolution und T&D.
  key_artists: [Emmanuel Top, Liberator DJs, Simon F]
  key_labels: [Evolution Records, T&D Records]
  subvariants: []
  wikidata_id: Q830399
  wikipedia_slug: Acid_techno
  audio_examples: []

- id: minimal_techno
  name: Minimal Techno
  track: techno
  year_start: 1994
  origin: Detroit/Berlin
  parents: [techno]
  description: >
    Robert Hood und Daniel Bell schufen Mitte der 1990er einen reduzierten,
    hypnotischen Stil. In Berlin entwickelten Richie Hawtin und Ricardo Villalobos
    zu Beginn der 2000er eine Hoehzeit des Subgenres.
  key_artists: [Robert Hood, Daniel Bell, Richie Hawtin, Ricardo Villalobos]
  key_labels: [Axis, Minimise, Minus]
  subvariants: [Microhouse]
  wikidata_id: Q1195085
  wikipedia_slug: Minimal_techno
  audio_examples: []

- id: dub_techno
  name: Dub Techno
  track: techno
  year_start: 1993
  origin: "Berlin, DE"
  parents: [techno]
  description: >
    Basic Channel (Mark Ernestus und Moritz von Oswald) praegten in Berlin
    ab 1993 einen tiefen, dubbigen Techno-Stil mit Schallplattenecho und
    dichter Atmosphaere. Das Label Chain Reaction wurde zum Zentrum.
  key_artists: [Basic Channel, Maurizio, Deepchord]
  key_labels: [Basic Channel, Chain Reaction]
  subvariants: []
  wikidata_id: Q1228038
  wikipedia_slug: Dub_techno
  audio_examples: []
```

- [ ] **Step 6: data/genres/house.yaml schreiben**

```yaml
- id: house
  name: House
  track: house
  year_start: 1983
  origin: "Chicago, USA"
  parents: []
  description: >
    Aus den Chicagoer Clubs Warehouse und Music Box hervorgegangen,
    verbanden DJs wie Frankie Knuckles und Ron Hardy Disco-Rhythmen
    mit Synthesizern und Drum-Machines. Jesse Saunders On and On (1984)
    gilt als erste Veroeffentlichung des Genres.
  key_artists: [Frankie Knuckles, Larry Heard, Marshall Jefferson, Ron Hardy]
  key_labels: [Trax Records, DJ International]
  subvariants: []
  wikidata_id: Q1647099
  wikipedia_slug: House_music
  audio_examples: []

- id: deep_house
  name: Deep House
  track: house
  year_start: 1986
  origin: "Chicago/New York, USA"
  parents: [house]
  description: >
    Larry Heard (Mr. Fingers) praegte mit Tracks wie Can You Feel It (1986)
    einen soulreicheren, atmosphaerisch tieferen House-Stil. New Yorker
    Labels wie Strictly Rhythm und Nervous Records trugen zur Verbreitung bei.
  key_artists: [Larry Heard, Larry Levan, Kerri Chandler]
  key_labels: [Trax Records, Strictly Rhythm, Nervous Records]
  subvariants: []
  wikidata_id: Q1067317
  wikipedia_slug: Deep_house
  audio_examples: []

- id: acid_house
  name: Acid House
  track: house
  year_start: 1986
  origin: "Chicago, USA"
  parents: [house]
  description: >
    Die zufaellig entdeckten Klaenge der Roland TB-303 Bassmaschine —
    verwendet auf Phuture Acid Tracks (1987) — definierten das Subgenre.
    In Grossbritannien loeste Acid House 1988 den Second Summer of Love aus.
  key_artists: [Phuture, DJ Pierre, Armando, "808 State"]
  key_labels: [Trax Records, FFRR]
  subvariants: []
  wikidata_id: Q376670
  wikipedia_slug: Acid_house
  audio_examples: []

- id: tech_house
  name: Tech House
  track: house
  year_start: 1994
  origin: UK/Deutschland
  parents: [house]
  description: >
    Tech House verbindet die Rhythmik und Energie des Techno mit den
    Harmonieelementen und dem Groove des House. Labels wie Turbo und
    Hot Creations praegten den internationalen Stil.
  key_artists: [Ricardo Villalobos, Tiga, Green Velvet, Jamie Jones]
  key_labels: [Turbo Recordings, Hot Creations, Relief]
  subvariants: []
  wikidata_id: Q1662199
  wikipedia_slug: Tech_house
  audio_examples: []
```

- [ ] **Step 7: data/genres/disco.yaml schreiben**

```yaml
- id: disco
  name: Disco
  track: disco
  year_start: 1974
  origin: "New York, USA"
  parents: []
  description: >
    Disco entstand in den New Yorker Underground-Clubs der fruehen 1970er
    als Musik fuer queere und afroamerikanische Communities. Giorgio Moroder,
    Nile Rodgers (Chic) und die Produzenten von Philly Soul definierten
    den Klang mit Streichern und pumpenden Rhythmen.
  key_artists: [Giorgio Moroder, Nile Rodgers, Donna Summer, Gloria Gaynor]
  key_labels: [Casablanca Records, Philadelphia International]
  subvariants: []
  wikidata_id: Q10484
  wikipedia_slug: Disco
  audio_examples: []

- id: hi_nrg
  name: Hi-NRG
  track: disco
  year_start: 1982
  origin: San Francisco/London
  parents: [disco]
  description: >
    Hi-NRG entwickelte sich aus Disco in den fruehen 1980ern mit schnellerem
    Tempo (140-160 BPM), synthetischeren Klaengen und Fokus auf Gay Clubs.
    Bobby O und Pete Waterman (PWL) praegten den US- und UK-Stil.
  key_artists: [Bobby O, Sylvester, Dead or Alive, Pet Shop Boys]
  key_labels: [PWL, Mirage Records]
  subvariants: []
  wikidata_id: Q737838
  wikipedia_slug: Hi-NRG
  audio_examples: []

- id: italo_disco
  name: Italo Disco
  track: disco
  year_start: 1977
  origin: Italien
  parents: [disco]
  description: >
    Italienische Produzenten wie Giorgio Moroder entwickelten ab Ende der 1970er
    einen synthetischeren, melodischeren Disco-Stil. Charakter: Vocoder,
    Synthesizer-Melodien, oft englische Texte mit deutlichem Akzent.
  key_artists: [Giorgio Moroder, Den Harrow, Ryan Paris, Spagna]
  key_labels: [Discomagic, Durium]
  subvariants: []
  wikidata_id: Q848916
  wikipedia_slug: Italo_disco
  audio_examples: []
```

- [ ] **Step 8: data/edges.yaml schreiben**

```yaml
# Quereinflüsse — nicht als direkte Ableitungen modellierbar
- from: disco
  to: house
  type: influence
  label: "Chicago Clubs, 1983"

- from: elektronische_musik
  to: techno
  type: influence
  label: "Kraftwerk, Giorgio Moroder"

- from: ebm
  to: techno
  type: influence
  label: "Detroit, 1985"
```

- [ ] **Step 9: Commit**

```bash
git add data/
git commit -m "feat: seed YAML data — 20 Genres, 3 Quereinflüsse, 7 Familien"
```

---

## Task 4: build.py

**Files:**
- Create: `pipeline/build.py`
- Modify: `tests/pipeline/test_build.py`

- [ ] **Step 1: Erweiterte Tests schreiben**

`tests/pipeline/test_build.py` (Inhalt ersetzen):

```python
import json
import pytest
import yaml
from pathlib import Path
from pipeline.build import load_genres, load_edges, build, TRACKS


@pytest.fixture
def data_dir(tmp_path):
    genres_dir = tmp_path / "genres"
    genres_dir.mkdir()
    (genres_dir / "test.yaml").write_text(yaml.dump([
        {
            "id": "theremin", "name": "Theremin", "track": "early",
            "year_start": 1920, "parents": [], "description": "Test",
            "key_artists": [], "key_labels": [], "subvariants": [],
            "wikidata_id": "Q1", "wikipedia_slug": "Theremin", "audio_examples": [],
        },
        {
            "id": "musique_concrete", "name": "Musique Concrete",
            "track": "electroacoustic", "year_start": 1948,
            "parents": ["theremin"], "description": "Test",
            "key_artists": [], "key_labels": [], "subvariants": [],
            "wikidata_id": "Q207436", "wikipedia_slug": "Musique_concrete",
            "audio_examples": [],
        },
    ]))
    (tmp_path / "edges.yaml").write_text(yaml.dump([
        {"from": "theremin", "to": "musique_concrete", "type": "influence", "label": "test"}
    ]))
    return tmp_path


def test_load_genres_returns_all(data_dir):
    genres = load_genres(data_dir)
    assert len(genres) == 2
    assert {g.id for g in genres} == {"theremin", "musique_concrete"}


def test_load_edges_maps_from_field(data_dir):
    edges = load_edges(data_dir)
    assert len(edges) == 1
    assert edges[0].from_ == "theremin"
    assert edges[0].type == "influence"


def test_build_creates_output_file(data_dir, tmp_path):
    output = tmp_path / "out" / "genres.json"
    build(data_dir, output)
    assert output.exists()


def test_build_json_has_required_keys(data_dir, tmp_path):
    output = tmp_path / "genres.json"
    build(data_dir, output)
    data = json.loads(output.read_text())
    assert set(data.keys()) == {"genres", "edges", "tracks"}


def test_build_derives_edges_from_parents(data_dir, tmp_path):
    output = tmp_path / "genres.json"
    build(data_dir, output)
    data = json.loads(output.read_text())
    derives = [e for e in data["edges"] if e["type"] == "derives"]
    assert any(
        e["from"] == "theremin" and e["to"] == "musique_concrete"
        for e in derives
    )


def test_build_includes_influence_edges(data_dir, tmp_path):
    output = tmp_path / "genres.json"
    build(data_dir, output)
    data = json.loads(output.read_text())
    assert any(e["type"] == "influence" for e in data["edges"])


def test_build_raises_on_unknown_parent(data_dir):
    (data_dir / "genres" / "broken.yaml").write_text(yaml.dump([{
        "id": "broken", "name": "Broken", "track": "early",
        "year_start": 2000, "parents": ["ghost"], "description": "",
        "key_artists": [], "key_labels": [], "subvariants": [],
        "wikidata_id": "", "wikipedia_slug": "", "audio_examples": [],
    }]))
    with pytest.raises(ValueError, match="unknown parent"):
        build(data_dir, data_dir / "out.json")


def test_tracks_are_ordered_by_order_field():
    orders = [t.order for t in TRACKS]
    assert orders == sorted(orders)
```

- [ ] **Step 2: Tests ausführen — erwartet FAIL**

```bash
uv run pytest tests/pipeline/test_build.py -v
```

Expected: `ImportError: cannot import name 'load_genres'`

- [ ] **Step 3: build.py implementieren**

`pipeline/build.py`:

```python
from __future__ import annotations
import json
import yaml
from pathlib import Path
from pipeline.schema import Genre, Edge, Track

TRACKS = [
    Track(id="early",           label="Fruehgeschichte",       color="#4fc3f7", order=0),
    Track(id="electroacoustic", label="Elektroakustik",        color="#388e3c", order=1),
    Track(id="avantgarde",      label="Avantgarde / Ambient",  color="#7b1fa2", order=2),
    Track(id="industrial",      label="Industrial / EBM",      color="#c62828", order=3),
    Track(id="techno",          label="Techno",                color="#2e7d32", order=4),
    Track(id="house",           label="House",                 color="#1565c0", order=5),
    Track(id="disco",           label="Disco / Funk",          color="#e65100", order=6),
]


def load_genres(data_dir: Path) -> list[Genre]:
    genres: list[Genre] = []
    for yaml_file in sorted((data_dir / "genres").glob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        for item in raw:
            genres.append(Genre(**item))
    return genres


def load_edges(data_dir: Path) -> list[Edge]:
    edges_file = data_dir / "edges.yaml"
    raw = yaml.safe_load(edges_file.read_text(encoding="utf-8")) or []
    return [Edge.from_yaml(e) for e in raw]


def build(data_dir: Path, output_path: Path) -> None:
    genres = load_genres(data_dir)
    edges = load_edges(data_dir)

    genre_ids = {g.id for g in genres}
    for genre in genres:
        for parent_id in genre.parents:
            if parent_id not in genre_ids:
                raise ValueError(
                    f"Genre '{genre.id}' references unknown parent '{parent_id}'"
                )

    derived_edges = [
        {"from": parent_id, "to": genre.id, "type": "derives", "label": ""}
        for genre in genres
        for parent_id in genre.parents
    ]
    influence_edges = [
        {"from": e.from_, "to": e.to, "type": e.type, "label": e.label}
        for e in edges
    ]

    output = {
        "genres": [g.model_dump() for g in genres],
        "edges": derived_edges + influence_edges,
        "tracks": [t.model_dump() for t in TRACKS],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(genres)} genres, {len(output['edges'])} edges -> {output_path}")


if __name__ == "__main__":
    build(Path("data"), Path("public/data/genres.json"))
```

- [ ] **Step 4: Tests ausführen — erwartet PASS**

```bash
uv run pytest tests/pipeline/test_build.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Build gegen echte Daten testen**

```bash
uv run python pipeline/build.py
```

Expected: `Wrote N genres, M edges -> public/data/genres.json`

- [ ] **Step 6: Commit**

```bash
git add pipeline/build.py tests/pipeline/test_build.py
git commit -m "feat: pipeline build — YAML->JSON export mit Validierung"
```

---

## Task 5: fetch_wikidata.py

**Files:**
- Create: `pipeline/fetch_wikidata.py`
- Create: `tests/pipeline/test_fetch_wikidata.py`

- [ ] **Step 1: Failing-Test schreiben**

`tests/pipeline/test_fetch_wikidata.py`:

```python
from unittest.mock import patch, MagicMock
from pipeline.fetch_wikidata import build_sparql_query, parse_results, WIKIDATA_ENDPOINT


def test_sparql_query_contains_subgenre_predicate():
    query = build_sparql_query()
    assert "wdt:P279" in query   # subclass of
    assert "wdt:P571" in query   # inception date


def test_parse_results_extracts_genres():
    mock_response = {
        "results": {"bindings": [{
            "genre": {"value": "http://www.wikidata.org/entity/Q48803"},
            "genreLabel": {"value": "techno"},
            "inception": {"value": "1985-01-01T00:00:00Z"},
            "parentLabel": {"value": "electronic music"},
        }]}
    }
    results = parse_results(mock_response)
    assert len(results) == 1
    assert results[0]["id"] == "Q48803"
    assert results[0]["name"] == "techno"
    assert results[0]["year_start"] == 1985


def test_parse_results_handles_missing_inception():
    mock_response = {
        "results": {"bindings": [{
            "genre": {"value": "http://www.wikidata.org/entity/Q999"},
            "genreLabel": {"value": "test genre"},
        }]}
    }
    results = parse_results(mock_response)
    assert results[0]["year_start"] is None


def test_wikidata_endpoint_contains_sparql():
    assert "wikidata.org" in WIKIDATA_ENDPOINT
    assert "sparql" in WIKIDATA_ENDPOINT
```

- [ ] **Step 2: Tests ausführen — erwartet FAIL**

```bash
uv run pytest tests/pipeline/test_fetch_wikidata.py -v
```

Expected: `ImportError`

- [ ] **Step 3: fetch_wikidata.py implementieren**

`pipeline/fetch_wikidata.py`:

```python
"""Fragt Wikidata nach elektronischen Musikgenres und schreibt YAML-Rohdaten."""
from __future__ import annotations
import re
import requests
import yaml
from pathlib import Path

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "ElectronicMusicHistoryBot/0.1 (research project)"


def build_sparql_query() -> str:
    return """
SELECT DISTINCT ?genre ?genreLabel ?parentLabel ?inception WHERE {
  ?genre wdt:P31 wd:Q188451.
  OPTIONAL { ?genre wdt:P279 ?parent. }
  OPTIONAL { ?genre wdt:P571 ?inception. }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en".
  }
}
ORDER BY ?genreLabel
LIMIT 500
"""


def parse_results(data: dict) -> list[dict]:
    results = []
    for binding in data["results"]["bindings"]:
        qid = binding["genre"]["value"].rsplit("/", 1)[-1]
        name = binding.get("genreLabel", {}).get("value", "")
        parent = binding.get("parentLabel", {}).get("value", "")
        inception_raw = binding.get("inception", {}).get("value", "")
        year = None
        if inception_raw:
            m = re.match(r"(\d{4})", inception_raw)
            if m:
                year = int(m.group(1))
        results.append({"id": qid, "name": name, "year_start": year, "wikidata_parent": parent})
    return results


def fetch(output_dir: Path) -> None:
    """Fragt Wikidata ab und schreibt Rohdaten nach output_dir/wikidata_raw.yaml."""
    print("Querying Wikidata SPARQL...")
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": build_sparql_query(), "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    parsed = parse_results(resp.json())
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "wikidata_raw.yaml"
    out_file.write_text(yaml.dump(parsed, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {len(parsed)} entries -> {out_file}")
    print("Review wikidata_raw.yaml and manually map to genre YAML files.")


if __name__ == "__main__":
    fetch(Path("data/_wikidata"))
```

- [ ] **Step 4: Tests ausführen — erwartet PASS**

```bash
uv run pytest tests/pipeline/test_fetch_wikidata.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/fetch_wikidata.py tests/pipeline/test_fetch_wikidata.py
git commit -m "feat: pipeline fetch_wikidata — SPARQL query + Ergebnis-Parser"
```

---

## Task 6: resolve_commons.py

**Files:**
- Create: `pipeline/resolve_commons.py`
- Create: `tests/pipeline/test_resolve_commons.py`

- [ ] **Step 1: Failing-Test schreiben**

`tests/pipeline/test_resolve_commons.py`:

```python
from unittest.mock import patch, MagicMock
from pipeline.resolve_commons import build_commons_url, parse_audio_result, search_audio


def test_build_commons_url_returns_file_path_url():
    url = build_commons_url("Pierre_Schaeffer.ogg")
    assert "commons.wikimedia.org" in url
    assert "Special:FilePath" in url
    assert "Pierre_Schaeffer.ogg" in url


def test_parse_audio_result_extracts_fields():
    mock_page = {
        "title": "File:Test_audio.ogg",
        "imageinfo": [{"extmetadata": {
            "ObjectName": {"value": "Test Audio"},
            "Artist": {"value": "Test Artist"},
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
        }}],
    }
    result = parse_audio_result(mock_page)
    assert result is not None
    assert result["file"] == "Test_audio.ogg"
    assert result["artist"] == "Test Artist"
    assert result["source"] == "wikimedia_commons"


def test_parse_audio_result_rejects_non_cc():
    mock_page = {
        "title": "File:Test_audio.ogg",
        "imageinfo": [{"extmetadata": {
            "LicenseShortName": {"value": "All rights reserved"},
        }}],
    }
    assert parse_audio_result(mock_page) is None


def test_search_audio_calls_commons_api():
    with patch("pipeline.resolve_commons.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"query": {"pages": {}}}
        mock_get.return_value.raise_for_status = MagicMock()
        search_audio("techno music")
        assert mock_get.called
        assert "commons.wikimedia.org" in mock_get.call_args[0][0]
```

- [ ] **Step 2: Tests ausführen — erwartet FAIL**

```bash
uv run pytest tests/pipeline/test_resolve_commons.py -v
```

Expected: `ImportError`

- [ ] **Step 3: resolve_commons.py implementieren**

`pipeline/resolve_commons.py`:

```python
"""Sucht CC-lizenzierte Audiodateien auf Wikimedia Commons."""
from __future__ import annotations
import re
import requests
from pathlib import Path

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ElectronicMusicHistoryBot/0.1 (research project)"
CC_MARKERS = {"cc-by", "cc-by-sa", "cc0", "pd", "public domain"}


def build_commons_url(filename: str) -> str:
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"


def parse_audio_result(page: dict) -> dict | None:
    title = page.get("title", "")
    filename = title.removeprefix("File:")
    if not any(filename.lower().endswith(ext) for ext in (".ogg", ".flac", ".wav", ".mp3")):
        return None
    meta = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
    license_short = meta.get("LicenseShortName", {}).get("value", "").lower()
    if not any(marker in license_short for marker in CC_MARKERS):
        return None
    artist_raw = meta.get("Artist", {}).get("value", "")
    artist = re.sub(r"<[^>]+>", "", artist_raw).strip()
    object_name = meta.get("ObjectName", {}).get("value", filename)
    return {"file": filename, "source": "wikimedia_commons", "title": object_name, "artist": artist}


def search_audio(query: str, limit: int = 5) -> list[dict]:
    resp = requests.get(
        COMMONS_API,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:audio {query}",
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "extmetadata",
            "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName",
            "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    return [r for page in pages.values() if (r := parse_audio_result(page))]


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "electronic music"
    for r in search_audio(query):
        print(r)
```

- [ ] **Step 4: Tests ausführen — erwartet PASS**

```bash
uv run pytest tests/pipeline/test_resolve_commons.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/resolve_commons.py tests/pipeline/test_resolve_commons.py
git commit -m "feat: pipeline resolve_commons — Wikimedia Commons CC-Audio-Suche"
```

---

## Task 7: layout.js

**Files:**
- Create: `src/graph/layout.js`
- Create: `tests/graph/layout.test.js`

- [ ] **Step 1: Failing-Test schreiben**

`tests/graph/layout.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { computeLayout } from '../../src/graph/layout.js';

const MOCK_DATA = {
  genres: [
    { id: 'theremin', name: 'Theremin', track: 'early', year_start: 1920,
      year_end: null, parents: [], key_artists: [], audio_examples: [] },
    { id: 'musique_concrete', name: 'Musique Concrete', track: 'electroacoustic',
      year_start: 1948, year_end: null, parents: ['theremin'],
      key_artists: [], audio_examples: [] },
  ],
  edges: [
    { from: 'theremin', to: 'musique_concrete', type: 'derives', label: '' },
  ],
  tracks: [
    { id: 'early', label: 'Fruehgeschichte', color: '#4fc3f7', order: 0 },
    { id: 'electroacoustic', label: 'Elektroakustik', color: '#388e3c', order: 1 },
  ],
};

describe('computeLayout', () => {
  it('places theremin at ~16% of width for year 1920', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    const n = nodes.find(n => n.id === 'theremin');
    // (1920 - 1900) / (2025 - 1900) * 1000 = 160
    expect(n.x).toBeCloseTo(160, 0);
  });

  it('places musique_concrete below theremin (track order 1 > track order 0)', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    const t = nodes.find(n => n.id === 'theremin');
    const m = nodes.find(n => n.id === 'musique_concrete');
    expect(m.y).toBeGreaterThan(t.y);
  });

  it('assigns positive width and fixed height to every node', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    for (const n of nodes) {
      expect(n.width).toBeGreaterThan(0);
      expect(n.height).toBe(36);
    }
  });

  it('resolves edge source and target to node objects', () => {
    const { edges } = computeLayout(MOCK_DATA, 1000, 400);
    expect(edges).toHaveLength(1);
    expect(edges[0].source.id).toBe('theremin');
    expect(edges[0].target.id).toBe('musique_concrete');
  });

  it('drops edges where source or target is not found', () => {
    const data = {
      ...MOCK_DATA,
      edges: [{ from: 'ghost', to: 'theremin', type: 'derives', label: '' }],
    };
    const { edges } = computeLayout(data, 1000, 400);
    expect(edges).toHaveLength(0);
  });

  it('sets trackHeight = svgHeight / trackCount', () => {
    const { trackHeight } = computeLayout(MOCK_DATA, 1000, 400);
    expect(trackHeight).toBe(200);
  });
});
```

- [ ] **Step 2: Test ausführen — erwartet FAIL**

```bash
pnpm test
```

Expected: `Cannot find module '../../src/graph/layout.js'`

- [ ] **Step 3: layout.js implementieren**

`src/graph/layout.js`:

```javascript
const YEAR_START = 1900;
const YEAR_END = 2025;
const NODE_HEIGHT = 36;
const CHAR_WIDTH = 7;      // px pro Zeichen bei 10px font-size
const NODE_PADDING_X = 20; // horizontales Padding links+rechts gesamt

/**
 * Berechnet x/y-Positionen fuer jeden Knoten und loest Kantenreferenzen auf.
 *
 * @param {object} data      - genres.json ({ genres, edges, tracks })
 * @param {number} svgWidth  - Breite des SVG-Canvas in px
 * @param {number} svgHeight - Hoehe des SVG-Canvas in px
 * @returns {{ nodes, edges, tracks, trackHeight }}
 */
export function computeLayout(data, svgWidth, svgHeight) {
  const { genres, edges, tracks } = data;

  const sortedTracks = [...tracks].sort((a, b) => a.order - b.order);
  const trackIndex = Object.fromEntries(sortedTracks.map((t, i) => [t.id, i]));
  const trackCount = sortedTracks.length;
  const trackHeight = svgHeight / trackCount;

  const xScale = year => ((year - YEAR_START) / (YEAR_END - YEAR_START)) * svgWidth;
  const yScale = trackId => (trackIndex[trackId] + 0.5) * trackHeight;

  const nodes = genres.map(genre => {
    const width = Math.max(genre.name.length * CHAR_WIDTH + NODE_PADDING_X * 2, 60);
    return { ...genre, x: xScale(genre.year_start), y: yScale(genre.track), width, height: NODE_HEIGHT };
  });

  const nodeById = Object.fromEntries(nodes.map(n => [n.id, n]));

  const resolvedEdges = edges
    .map(edge => {
      const source = nodeById[edge.from];
      const target = nodeById[edge.to];
      if (!source || !target) return null;
      return { ...edge, source, target };
    })
    .filter(Boolean);

  return { nodes, edges: resolvedEdges, tracks: sortedTracks, trackHeight };
}
```

- [ ] **Step 4: Tests ausführen — erwartet PASS**

```bash
pnpm test
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/graph/layout.js tests/graph/layout.test.js
git commit -m "feat: graph layout — Jahr/Track -> x/y-Positionen, Kanten-Auflosung"
```

---

## Task 8: renderer.js + CSS

**Files:**
- Create: `src/graph/renderer.js`
- Create: `src/styles/main.css`

- [ ] **Step 1: main.css schreiben**

`src/styles/main.css`:

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0a0a0f;
  color: #e6edf3;
  font-family: system-ui, -apple-system, sans-serif;
  height: 100vh;
  overflow: hidden;
}

#app { display: flex; flex-direction: column; height: 100vh; }

/* Toolbar */
#toolbar {
  background: #0d1117;
  border-bottom: 1px solid #30363d;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  z-index: 10;
}

#toolbar input {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e6edf3;
  font-size: 12px;
  padding: 5px 10px;
  width: 200px;
}

/* Graph Container */
#graph-container { display: flex; flex: 1; overflow: hidden; position: relative; }

#track-labels {
  width: 120px;
  flex-shrink: 0;
  background: #0d1117;
  border-right: 1px solid #1e1e1e;
  display: flex;
  flex-direction: column;
  z-index: 5;
}

.track-label {
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.3;
  border-bottom: 1px dashed #1a1a1a;
}

#canvas-wrapper { flex: 1; overflow: hidden; position: relative; }

svg.graph-canvas { display: block; width: 100%; height: 100%; cursor: grab; }
svg.graph-canvas:active { cursor: grabbing; }

/* Edges */
.edge { fill: none; stroke-width: 1.5; opacity: 0.65; transition: opacity 0.2s; }
.edge--dimmed { opacity: 0.08; }
.track-separator { stroke: #1a1a1a; stroke-width: 1; stroke-dasharray: 4 6; }

/* Nodes */
.node { cursor: pointer; }
.node rect { transition: stroke-width 0.15s; }
.node:hover rect { stroke-width: 2.5; }
.node--selected rect { stroke-width: 3; filter: drop-shadow(0 0 6px currentColor); }
.node--dimmed { opacity: 0.12; }
.node-name { font-size: 10px; font-weight: 600; fill: #e6edf3; pointer-events: none; }
.node-year { font-size: 8.5px; fill: #555; pointer-events: none; }

/* Detail Panel */
#detail-panel {
  position: fixed;
  top: 0; right: 0;
  width: 380px;
  height: 100vh;
  background: #0d1117;
  border-left: 1px solid #30363d;
  transform: translateX(100%);
  transition: transform 0.25s ease;
  z-index: 20;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#detail-panel.panel--open { transform: translateX(0); }

.panel-header {
  background: #161b22;
  border-bottom: 1px solid #30363d;
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-shrink: 0;
}

.panel-close {
  background: none; border: none; color: #555;
  cursor: pointer; font-size: 18px; line-height: 1;
}
.panel-close:hover { color: #e6edf3; }

.panel-body {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 16px;
}

.panel-section-label {
  color: #555; font-size: 10px;
  text-transform: uppercase; letter-spacing: 1px;
  margin-bottom: 6px;
}

.tag {
  display: inline-block;
  font-size: 10px; padding: 3px 8px;
  border-radius: 4px; cursor: pointer;
  border: 1px solid transparent;
}
.tag:hover { opacity: 0.8; }

/* Audio Player */
.audio-player {
  background: #161b22; border: 1px solid #30363d;
  border-radius: 6px; padding: 10px 12px;
  display: flex; align-items: center; gap: 12px;
}

.audio-play-btn {
  width: 32px; height: 32px; border-radius: 50%;
  border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 14px;
}

/* Filter Badges */
.filter-badge {
  font-size: 10px; padding: 3px 8px;
  border-radius: 4px; cursor: pointer;
  border: 1px solid transparent;
  opacity: 0.5; transition: opacity 0.15s;
  background: none;
}
.filter-badge.active { opacity: 1; }
```

- [ ] **Step 2: renderer.js schreiben**

`src/graph/renderer.js`:

```javascript
import * as d3 from 'd3';
import { computeLayout } from './layout.js';

/**
 * Erstellt den D3-SVG-Graphen.
 *
 * @param {HTMLElement} wrapper     - #canvas-wrapper
 * @param {HTMLElement} labelsEl    - #track-labels
 * @param {object}      data        - genres.json
 * @param {Function}    onNodeClick - callback(genreObject | null)
 * @returns {{ highlight, clearHighlight, filterTracks, filterYears }}
 */
export function createRenderer(wrapper, labelsEl, data, onNodeClick) {
  const width = wrapper.clientWidth;
  const height = wrapper.clientHeight;
  const layout = computeLayout(data, width, height);

  // Track-Labels aufbauen (DOM, kein innerHTML)
  while (labelsEl.firstChild) labelsEl.removeChild(labelsEl.firstChild);
  layout.tracks.forEach(track => {
    const div = document.createElement('div');
    div.className = 'track-label';
    div.style.height = `${layout.trackHeight}px`;
    div.style.color = track.color;
    div.textContent = track.label;
    labelsEl.appendChild(div);
  });

  // SVG erstellen
  const svg = d3.select(wrapper)
    .append('svg')
    .attr('class', 'graph-canvas')
    .attr('width', width)
    .attr('height', height);

  const zoomGroup = svg.append('g').attr('class', 'zoom-group');

  svg.call(
    d3.zoom().scaleExtent([0.2, 4])
      .on('zoom', e => zoomGroup.attr('transform', e.transform))
  );

  // Spur-Trennlinien
  layout.tracks.forEach((_, i) => {
    if (i === 0) return;
    zoomGroup.append('line')
      .attr('class', 'track-separator')
      .attr('x1', 0).attr('y1', i * layout.trackHeight)
      .attr('x2', width).attr('y2', i * layout.trackHeight);
  });

  // Kanten
  const edgeGroup = zoomGroup.append('g').attr('class', 'edges');
  const edgeSel = edgeGroup.selectAll('path')
    .data(layout.edges)
    .join('path')
    .attr('class', d => `edge edge--${d.type}`)
    .attr('stroke', d => {
      if (d.type === 'influence') return '#ffa657';
      const track = layout.tracks.find(t => t.id === d.target.track);
      return track ? track.color : '#4fc3f7';
    })
    .attr('stroke-dasharray', d => d.type === 'influence' ? '5,3' : null)
    .attr('d', edgePath);

  // Knoten
  const nodeGroup = zoomGroup.append('g').attr('class', 'nodes');
  const nodeSel = nodeGroup.selectAll('g.node')
    .data(layout.nodes)
    .join('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.x - d.width / 2},${d.y - d.height / 2})`)
    .on('click', (event, d) => { event.stopPropagation(); onNodeClick(d); });

  nodeSel.append('rect')
    .attr('width', d => d.width)
    .attr('height', d => d.height)
    .attr('rx', 6)
    .attr('fill', d => {
      const track = layout.tracks.find(t => t.id === d.track);
      return track ? hexToFill(track.color) : '#111';
    })
    .attr('stroke', d => {
      const track = layout.tracks.find(t => t.id === d.track);
      return track ? track.color : '#888';
    })
    .attr('stroke-width', 1.5);

  nodeSel.append('text').attr('class', 'node-name')
    .attr('x', d => d.width / 2).attr('y', d => d.height / 2 - 4)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
    .text(d => d.name);

  nodeSel.append('text').attr('class', 'node-year')
    .attr('x', d => d.width / 2).attr('y', d => d.height / 2 + 10)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
    .text(d => d.year_start);

  svg.on('click', () => { clearHighlight(); onNodeClick(null); });

  function highlight(nodeId) {
    const neighborIds = new Set(
      layout.edges
        .filter(e => e.source.id === nodeId || e.target.id === nodeId)
        .flatMap(e => [e.source.id, e.target.id])
    );
    nodeSel
      .classed('node--dimmed', d => d.id !== nodeId && !neighborIds.has(d.id))
      .classed('node--selected', d => d.id === nodeId);
    edgeSel.classed('edge--dimmed',
      d => d.source.id !== nodeId && d.target.id !== nodeId);
  }

  function clearHighlight() {
    nodeSel.classed('node--dimmed node--selected', false);
    edgeSel.classed('edge--dimmed', false);
  }

  function filterTracks(visibleTrackIds) {
    const visible = new Set(visibleTrackIds);
    nodeSel.style('display', d => visible.has(d.track) ? null : 'none');
    edgeSel.style('display',
      d => visible.has(d.source.track) && visible.has(d.target.track) ? null : 'none');
  }

  function filterYears(minYear, maxYear) {
    nodeSel.style('display', d => d.year_start >= minYear && d.year_start <= maxYear ? null : 'none');
    edgeSel.style('display',
      d => d.source.year_start >= minYear && d.target.year_start <= maxYear ? null : 'none');
  }

  return { highlight, clearHighlight, filterTracks, filterYears };
}

function edgePath(d) {
  const sx = d.source.x + d.source.width / 2;
  const sy = d.source.y;
  const tx = d.target.x - d.target.width / 2;
  const ty = d.target.y;
  if (Math.abs(sy - ty) < 2) return `M ${sx},${sy} L ${tx},${ty}`;
  const cx = (sx + tx) / 2;
  return `M ${sx},${sy} C ${cx},${sy} ${cx},${ty} ${tx},${ty}`;
}

function hexToFill(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${Math.round(r * 0.12)},${Math.round(g * 0.12)},${Math.round(b * 0.12)})`;
}
```

- [ ] **Step 3: Commit**

```bash
git add src/graph/renderer.js src/styles/main.css
git commit -m "feat: D3.js renderer — Tracks, Knoten, Kanten, Zoom/Pan, Highlight"
```

---

## Task 9: detail.js + audio.js

**Files:**
- Create: `src/panels/audio.js`
- Create: `src/panels/detail.js`

- [ ] **Step 1: audio.js schreiben**

`src/panels/audio.js`:

```javascript
const COMMONS_FILE_URL = 'https://commons.wikimedia.org/wiki/Special:FilePath/';

/**
 * Erstellt einen Audio-Player fuer eine Wikimedia Commons Datei.
 * Verwendet nur sichere DOM-Methoden — kein innerHTML.
 *
 * @param {object} example    - { file, title, artist, source }
 * @param {string} trackColor - Hex-Farbe fuer Play-Button
 * @returns {HTMLElement}
 */
export function createAudioPlayer(example, trackColor) {
  const audio = new Audio(`${COMMONS_FILE_URL}${encodeURIComponent(example.file)}`);

  const container = document.createElement('div');
  container.className = 'audio-player';

  const btn = document.createElement('button');
  btn.className = 'audio-play-btn';
  btn.style.background = `${trackColor}33`;
  btn.style.color = trackColor;
  btn.textContent = '▶'; // ▶

  const info = document.createElement('div');
  info.style.cssText = 'flex:1;min-width:0;';

  const titleEl = document.createElement('div');
  titleEl.style.cssText = 'color:#e6edf3;font-size:11px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
  titleEl.textContent = example.title;

  const metaEl = document.createElement('div');
  metaEl.style.cssText = 'color:#555;font-size:10px;margin-top:2px;';
  metaEl.textContent = example.artist;

  const link = document.createElement('a');
  link.href = `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(example.file)}`;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.style.cssText = 'color:#4fc3f7;font-size:10px;flex-shrink:0;';
  link.textContent = 'Commons ↗'; // ↗

  info.appendChild(titleEl);
  info.appendChild(metaEl);
  container.appendChild(btn);
  container.appendChild(info);
  container.appendChild(link);

  let playing = false;
  btn.addEventListener('click', () => {
    if (playing) { audio.pause(); btn.textContent = '▶'; }
    else         { audio.play(); btn.textContent = '⏸'; } // ⏸
    playing = !playing;
  });
  audio.addEventListener('ended', () => { btn.textContent = '▶'; playing = false; });

  return container;
}
```

- [ ] **Step 2: detail.js schreiben**

`src/panels/detail.js`:

```javascript
import { createAudioPlayer } from './audio.js';

/**
 * Verwaltet das Slide-in Genre-Detail-Panel.
 * Alle DOM-Operationen ueber createElement — kein innerHTML.
 *
 * @param {HTMLElement} panelEl    - #detail-panel
 * @param {object[]}    tracks     - aus genres.json
 * @param {Function}    onTagClick - callback(genreId)
 */
export function createDetailPanel(panelEl, tracks, onTagClick) {
  function trackColor(trackId) {
    return tracks.find(t => t.id === trackId)?.color ?? '#888';
  }

  function open(genre) {
    // Panel leeren
    while (panelEl.firstChild) panelEl.removeChild(panelEl.firstChild);

    const color = trackColor(genre.track);

    // ── Header ──────────────────────────────────────
    const header = document.createElement('div');
    header.className = 'panel-header';

    const headerLeft = document.createElement('div');

    const badge = document.createElement('span');
    badge.className = 'tag';
    badge.style.cssText = `background:${color}22;border-color:${color};color:${color};margin-bottom:6px;display:inline-block;`;
    badge.textContent = genre.track;

    const nameEl = document.createElement('h3');
    nameEl.style.cssText = 'color:#e6edf3;font-size:16px;margin:6px 0 2px;';
    nameEl.textContent = genre.name;

    const metaEl = document.createElement('div');
    metaEl.style.cssText = 'color:#888;font-size:11px;';
    const yearRange = genre.year_end ? `${genre.year_start}–${genre.year_end}` : `${genre.year_start} – heute`;
    metaEl.textContent = genre.origin ? `${yearRange} · ${genre.origin}` : yearRange;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'panel-close';
    closeBtn.textContent = '✕'; // ✕
    closeBtn.addEventListener('click', close);

    headerLeft.appendChild(badge);
    headerLeft.appendChild(nameEl);
    headerLeft.appendChild(metaEl);
    header.appendChild(headerLeft);
    header.appendChild(closeBtn);
    panelEl.appendChild(header);

    // ── Body ─────────────────────────────────────────
    const body = document.createElement('div');
    body.className = 'panel-body';

    if (genre.description) {
      body.appendChild(makeSection('Beschreibung', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#cdd9e5;font-size:12px;line-height:1.6;';
        p.textContent = genre.description;
        return p;
      }));
    }

    if (genre.parents?.length) {
      body.appendChild(makeSection('Herkunft', () =>
        makeTagList(genre.parents, color, onTagClick)
      ));
    }

    if (genre.key_artists?.length) {
      body.appendChild(makeSection('Schluesselkuenstler:innen', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#cdd9e5;font-size:11px;line-height:1.8;';
        p.textContent = genre.key_artists.join(' · ');
        return p;
      }));
    }

    if (genre.subvariants?.length) {
      body.appendChild(makeSection('Subvarianten', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#888;font-size:11px;';
        p.textContent = genre.subvariants.join(', ');
        return p;
      }));
    }

    if (genre.audio_examples?.length) {
      body.appendChild(makeSection('Audiobeispiel (CC)', () => {
        const wrap = document.createElement('div');
        wrap.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
        genre.audio_examples.forEach(ex => wrap.appendChild(createAudioPlayer(ex, color)));
        return wrap;
      }));
    }

    const links = [];
    if (genre.wikipedia_slug) {
      links.push({ label: '📖 Wikipedia', href: `https://en.wikipedia.org/wiki/${genre.wikipedia_slug}` });
    }
    if (genre.wikidata_id) {
      links.push({ label: `🔗 Wikidata ${genre.wikidata_id}`, href: `https://www.wikidata.org/wiki/${genre.wikidata_id}` });
    }
    if (links.length) {
      body.appendChild(makeSection('Links', () => {
        const wrap = document.createElement('div');
        wrap.style.cssText = 'display:flex;gap:12px;';
        links.forEach(({ label, href }) => {
          const a = document.createElement('a');
          a.href = href;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.style.cssText = 'color:#4fc3f7;font-size:11px;text-decoration:none;';
          a.textContent = label;
          wrap.appendChild(a);
        });
        return wrap;
      }));
    }

    panelEl.appendChild(body);
    panelEl.classList.add('panel--open');
    panelEl.classList.remove('panel--closed');
  }

  function close() {
    panelEl.classList.remove('panel--open');
    panelEl.classList.add('panel--closed');
  }

  return { open, close };
}

function makeSection(label, contentFn) {
  const wrap = document.createElement('div');
  const lbl = document.createElement('div');
  lbl.className = 'panel-section-label';
  lbl.textContent = label;
  wrap.appendChild(lbl);
  wrap.appendChild(contentFn());
  return wrap;
}

function makeTagList(ids, color, onClick) {
  const wrap = document.createElement('div');
  wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;';
  ids.forEach(id => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.style.cssText = `background:${color}11;border-color:${color};color:${color};`;
    tag.textContent = id;
    tag.addEventListener('click', () => onClick(id));
    wrap.appendChild(tag);
  });
  return wrap;
}
```

- [ ] **Step 3: Commit**

```bash
git add src/panels/audio.js src/panels/detail.js
git commit -m "feat: detail panel + audio player — Slide-in mit CC-Audio, sicheres DOM"
```

---

## Task 10: controls/filters.js + controls/search.js

**Files:**
- Create: `src/controls/filters.js`
- Create: `src/controls/search.js`

- [ ] **Step 1: filters.js schreiben**

`src/controls/filters.js`:

```javascript
/**
 * Erstellt Track-Toggle-Badges und Zeitraum-Slider im Toolbar.
 *
 * @param {HTMLElement} toolbarEl
 * @param {object[]}    tracks    - aus genres.json
 * @param {object[]}    genres    - aus genres.json
 * @param {object}      renderer  - { filterTracks, filterYears }
 */
export function createFilters(toolbarEl, tracks, genres, renderer) {
  const activeTrackIds = new Set(tracks.map(t => t.id));

  // Track-Toggle-Badges
  const badgeWrap = document.createElement('div');
  badgeWrap.style.cssText = 'display:flex;gap:6px;align-items:center;margin-left:auto;';

  tracks.forEach(track => {
    const badge = document.createElement('button');
    badge.className = 'filter-badge active';
    badge.style.cssText = `background:${track.color}22;border-color:${track.color};color:${track.color};`;
    badge.textContent = track.label;
    badge.addEventListener('click', () => {
      if (activeTrackIds.has(track.id)) {
        activeTrackIds.delete(track.id);
        badge.classList.remove('active');
      } else {
        activeTrackIds.add(track.id);
        badge.classList.add('active');
      }
      renderer.filterTracks([...activeTrackIds]);
    });
    badgeWrap.appendChild(badge);
  });

  // Zeitraum-Slider
  const years = genres.map(g => g.year_start).filter(Boolean);
  const minYear = Math.min(...years);
  const maxYear = new Date().getFullYear();

  const sliderWrap = document.createElement('div');
  sliderWrap.style.cssText = 'display:flex;align-items:center;gap:8px;';

  const label = document.createElement('span');
  label.style.cssText = 'color:#888;font-size:11px;white-space:nowrap;';
  label.textContent = `${minYear} – ${maxYear}`;

  const slider = document.createElement('input');
  slider.type = 'range';
  slider.min = minYear;
  slider.max = maxYear;
  slider.value = minYear;
  slider.style.width = '120px';

  slider.addEventListener('input', () => {
    const from = parseInt(slider.value, 10);
    label.textContent = `${from} – ${maxYear}`;
    renderer.filterYears(from, maxYear);
  });

  sliderWrap.appendChild(label);
  sliderWrap.appendChild(slider);
  toolbarEl.appendChild(sliderWrap);
  toolbarEl.appendChild(badgeWrap);
}
```

- [ ] **Step 2: search.js schreiben**

`src/controls/search.js`:

```javascript
/**
 * Freitextsuche ueber Genre-Namen, Kuenstler und Subvarianten.
 *
 * @param {HTMLInputElement} inputEl
 * @param {object[]}         nodes    - aus computeLayout()
 * @param {object}           renderer - { highlight, clearHighlight }
 */
export function createSearch(inputEl, nodes, renderer) {
  inputEl.addEventListener('input', () => {
    const q = inputEl.value.trim().toLowerCase();
    if (!q) { renderer.clearHighlight(); return; }

    const matches = nodes.filter(n =>
      n.name.toLowerCase().includes(q) ||
      n.key_artists?.some(a => a.toLowerCase().includes(q)) ||
      n.subvariants?.some(s => s.toLowerCase().includes(q))
    );

    if (matches.length === 0) { renderer.clearHighlight(); return; }
    // Ersten Treffer hervorheben; bei mehreren Treffern wird der erste selektiert
    renderer.highlight(matches[0].id);
  });
}
```

- [ ] **Step 3: Commit**

```bash
git add src/controls/filters.js src/controls/search.js
git commit -m "feat: filters + search — Track-Toggles, Zeitraum-Slider, Freitextsuche"
```

---

## Task 11: main.js — Einstiegspunkt

**Files:**
- Create: `src/main.js`

- [ ] **Step 1: main.js schreiben**

`src/main.js`:

```javascript
import { createRenderer } from './graph/renderer.js';
import { computeLayout } from './graph/layout.js';
import { createDetailPanel } from './panels/detail.js';
import { createFilters } from './controls/filters.js';
import { createSearch } from './controls/search.js';

async function init() {
  const res = await fetch('./data/genres.json');
  if (!res.ok) throw new Error(`Failed to load genres.json: ${res.status}`);
  const data = await res.json();

  const wrapper  = document.getElementById('canvas-wrapper');
  const labelsEl = document.getElementById('track-labels');
  const toolbarEl = document.getElementById('toolbar');
  const panelEl  = document.getElementById('detail-panel');

  // Suchfeld in Toolbar einfuegen
  const searchInput = document.createElement('input');
  searchInput.type = 'search';
  searchInput.placeholder = 'Genre suchen…';
  toolbarEl.appendChild(searchInput);

  // Detail-Panel
  const panel = createDetailPanel(panelEl, data.tracks, genreId => {
    renderer.highlight(genreId);
    const genre = data.genres.find(g => g.id === genreId);
    if (genre) panel.open(genre);
  });

  // Graph
  const renderer = createRenderer(wrapper, labelsEl, data, genre => {
    if (!genre) { panel.close(); renderer.clearHighlight(); return; }
    renderer.highlight(genre.id);
    panel.open(genre);
  });

  // Suche + Filter
  const layout = computeLayout(data, wrapper.clientWidth, wrapper.clientHeight);
  createSearch(searchInput, layout.nodes, renderer);
  createFilters(toolbarEl, data.tracks, data.genres, renderer);
}

init().catch(err => {
  const pre = document.createElement('pre');
  pre.style.cssText = 'color:red;padding:20px;';
  pre.textContent = `Error: ${err.message}`;
  document.body.appendChild(pre);
  console.error(err);
});
```

- [ ] **Step 2: Build-Skript ausfuehren**

```bash
uv run python pipeline/build.py
```

Expected: `Wrote N genres, M edges -> public/data/genres.json`

- [ ] **Step 3: Dev-Server starten und im Browser testen**

```bash
pnpm dev
```

Öffne `http://localhost:5173` im Browser. Erwartetes Verhalten:
- Graph mit Zeitachse und farbigen Spur-Labels erscheint
- Knoten als abgerundete Rechtecke mit Genre-Name und Jahr (zweizeilig)
- Kanten zwischen verbundenen Genres (solid = Ableitung, dashed = Einfluss)
- Klick auf Knoten: Detail-Panel slide-in von rechts
- Klick auf leeren Bereich: Panel schliesst sich, Highlight wird aufgehoben
- Suchfeld: Genre-Namen eingeben filtert und hebt ersten Treffer hervor
- Track-Badges oben rechts: an/ausschalten einzelner Genre-Familien
- Zeitraum-Slider: blendet Genres vor dem gewaehlten Jahr aus

- [ ] **Step 4: Commit**

```bash
git add src/main.js
git commit -m "feat: main.js — App-Einstiegspunkt, alle Module verkabelt"
```

---

## Task 12: GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Deploy-Workflow schreiben**

`.github/workflows/deploy.yml`:

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install Python dependencies
        run: uv sync --extra dev

      - name: Run Python tests
        run: uv run pytest tests/pipeline/ -v

      - name: Run pipeline build
        run: uv run python pipeline/build.py

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install JS dependencies
        run: pnpm install

      - name: Run JS tests
        run: pnpm test

      - name: Build Vite app
        run: pnpm build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: GitHub Pages aktivieren**

`Settings -> Pages -> Source` -> `GitHub Actions` auswaehlen.

- [ ] **Step 3: Alle Tests final ausfuehren**

```bash
uv run pytest tests/ -v
pnpm test
```

Expected: Alle Tests gruen.

- [ ] **Step 4: Commit und Push**

```bash
git add .github/
git commit -m "ci: GitHub Actions — Python + JS Tests + GitHub Pages Deployment"
git push -u origin main
```

Expected: GitHub Actions laeuft durch, App deployed unter `https://<user>.github.io/electronic-music-history/`.

---

## Spec-Abdeckungscheck

| Spec-Anforderung | Task |
|---|---|
| Zeitraum 1900–2025 | Task 7 (YEAR_START/YEAR_END in layout.js) |
| Hybrid-Layout: Zeitachse + Spuren | Task 7 + 8 |
| Abgerundete Rechtecke, 2-zeilig | Task 8 (renderer.js) |
| Direkte Ableitung (solid) + Quereinfluss (dashed) | Task 4 (build.py edge types) + Task 8 |
| Wikidata SPARQL Seed | Task 5 |
| Wikimedia Commons CC-Audio | Task 6 + Task 9 (audio.js) |
| Detail-Panel (Beschreibung, Kuenstler, Links, Audio) | Task 9 (detail.js) |
| Filter + Zeitraum-Slider | Task 10 |
| Freitextsuche | Task 10 |
| YAML-Quelldaten kuratiert | Task 3 |
| build.py Validierung + Fehler bei unbekanntem Parent | Task 4 |
| GitHub Pages Deployment | Task 12 |
