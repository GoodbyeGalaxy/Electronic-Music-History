# Design: Electronic Music History Graph

**Datum:** 2026-05-23  
**Status:** Approved

---

## Ziel

Eine interaktive Web-App, die die Geschichte der elektronischen Musik von 1900 bis heute als navigierbaren Graphen darstellt. Genres sind Knoten, Ableitungsbeziehungen sind Kanten. Musikbeispiele stammen ausschließlich aus Wikimedia Commons (CC-lizenziert).

---

## Architektur

Das System besteht aus zwei klar getrennten Schichten, die nur über eine statische JSON-Datei kommunizieren:

### Python-Datenpipeline (`pipeline/`)

1. **`fetch_wikidata.py`** — Fragt Wikidata via SPARQL nach Musikgenres ab (Inception-Dates, `subgenre of`-Relationen, Wikidata-IDs). Schreibt den initialen Seed als YAML-Dateien in `data/genres/`.
2. **`resolve_commons.py`** — Löst CC-lizenzierte Audiodateien auf Wikimedia Commons via API auf und ergänzt die YAML-Quellen mit `audio_examples`.
3. **Manuelle Kuration** — YAML-Quelldateien werden manuell um Beschreibungen, fehlende Genres, Korrekturen und kulturellen Kontext ergänzt.
4. **`build.py`** — Validiert alle Quellen, merged Genres und Kanten, exportiert `public/data/genres.json`.

### Vite + D3.js Frontend (`src/`)

- **Graph Canvas** (`src/graph/`): D3.js rendert das Hybrid-Layout auf einem SVG-Element. Zoom und Pan via `d3-zoom`.
- **Detail Panel** (`src/panels/`): HTML-Overlay, slide-in beim Klick auf einen Knoten.
- **Filter & Suche** (`src/controls/`): Zeitraum-Slider, Genre-Familien ein/ausblenden, Freitextsuche.
- **Deployment**: `vite build` erzeugt statische Dateien → GitHub Pages via CI/CD. Kein Server erforderlich.

---

## Graph-Layout

**Typ:** Hybrid — Zeitachse horizontal, Genre-Familien als vertikale Spuren.

- **X-Achse:** Jahr (1900–2025), linear skaliert auf die SVG-Breite.
- **Y-Achse:** Vertikale Spuren, eine pro Obergenre-Familie (z.B. Elektroakustik, Ambient, Techno, House, Industrial). Spur-Label links fixiert.
- **Knoten:** Abgerundete Rechtecke (`rx=6`). Zweizeilige Beschriftung: Genre-Name (weiß, bold) + Entstehungsjahr (kleiner, gedimmt). Farbkodierung nach Genre-Familie.
- **Kanten:**
  - *Direkte Ableitung* — durchgezogene Linie, Farbe der Ziel-Familie. Verbindet rechten Rand des Eltern-Knotens mit linkem Rand des Kind-Knotens (gleiche Spur) bzw. über Bezier-Kurve (spur-übergreifend).
  - *Quereinfluss* — gestrichelte Linie (`stroke-dasharray`), orange. Verbindet Ober-/Unterkanten bei spur-übergreifenden Einflüssen.
- **Interaktion:** Zoom und Pan via Maus/Touch. Klick auf Knoten öffnet Detail-Panel. Angeklickter Knoten und seine direkten Kanten werden hervorgehoben.

---

## Datenmodell

### Genre-Eintrag (`data/genres/<familie>.yaml`)

```yaml
- id: musique_concrete              # eindeutiger Bezeichner (snake_case)
  name: Musique Concrète            # Anzeigename
  track: electroacoustic            # vertikale Spur
  year_start: 1948                  # Entstehungsjahr (X-Position)
  year_end: null                    # null = noch aktiv
  origin: "Paris, FR"               # geografische Herkunft
  parents:                          # direkte Eltern-Genres (IDs)
    - electroacoustic
  description: >                    # 2–4 Sätze, kuratiert
    Pionierform der elektronischen Komposition ...
  key_artists:
    - Pierre Schaeffer
    - Pierre Henry
  key_labels:
    - INA-GRM
  subvariants:
    - Acousmatic Music
  wikidata_id: Q207436
  wikipedia_slug: Musique_concrète
  audio_examples:
    - file: Études_de_bruits.ogg    # Wikimedia Commons Dateiname
      source: wikimedia_commons
      title: "Étude aux chemins de fer (1948)"
      artist: Pierre Schaeffer
```

### Quereinflüsse (`data/edges.yaml`)

Nur für genre-übergreifende Einflüsse, die sich nicht als einfache Eltern-Kind-Beziehung ausdrücken lassen:

```yaml
- from: disco
  to: house
  type: influence       # gestrichelte Kante
  label: "Chicago, ~1983"

- from: dub
  to: drum_and_bass
  type: influence
```

### Generiertes `public/data/genres.json`

Das Build-Skript merged beide Quellen zu einem flachen JSON:

```json
{
  "genres": [ { "id": "...", "name": "...", "track": "...", ... } ],
  "edges":  [ { "from": "...", "to": "...", "type": "..." } ],
  "tracks": [ { "id": "electroacoustic", "label": "Elektroakustik", "color": "#388e3c" } ]
}
```

---

## Detail-Panel

Slide-in von rechts, beim Klick auf Knoten. Inhalt:

| Bereich | Inhalt |
|---|---|
| Header | Genre-Name, Entstehungszeitraum, geografische Herkunft, Spur-Badge |
| Beschreibung | 2–4 Sätze (kuratiert) |
| Herkunft & Einflüsse | Eltern-Genres als klickbare Tags (navigiert zu diesem Knoten) |
| Abgeleitete Genres | Kind-Genres als klickbare Tags |
| Schlüsselkünstler | Kommagetrennte Liste |
| Audiobeispiel | Play-Button + Dateiname + Dauer + Link zu Wikimedia Commons. Nur CC-lizenzierte Dateien. |
| Externe Links | Wikipedia-Artikel, Wikidata-Eintrag |

---

## Filter & Suche

- **Zeitraum-Slider:** Blendet Knoten und Kanten außerhalb des gewählten Zeitfensters aus.
- **Genre-Familien-Toggle:** Buttons pro Spur — ein/ausblenden einzelner Familien.
- **Freitextsuche:** Filtert Knoten nach Genre-Name, Künstlern, Subvarianten. Treffer werden hervorgehoben, Rest gedimmt.

---

## Repo-Struktur

```
electronic-music-history/
├── data/
│   ├── genres/              # eine YAML-Datei pro Genre-Familie
│   │   ├── electroacoustic.yaml
│   │   ├── ambient.yaml
│   │   ├── techno.yaml
│   │   └── ...
│   └── edges.yaml           # genre-übergreifende Quereinflüsse
├── pipeline/
│   ├── fetch_wikidata.py    # SPARQL-Seed von Wikidata
│   ├── resolve_commons.py   # Wikimedia Commons Audio-Auflösung
│   └── build.py             # Validierung + JSON-Export
├── src/
│   ├── graph/               # D3.js Rendering, Layout, Zoom/Pan
│   ├── panels/              # Detail-Panel, Audio-Player
│   ├── controls/            # Filter, Suche, Zeitraum-Slider
│   └── main.js              # Einstiegspunkt
├── public/
│   └── data/
│       └── genres.json      # generiert durch build.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-23-electronic-music-history-design.md
└── .gitignore               # enthält: .superpowers/
```

---

## Datenpipeline-Workflow

1. `uv run python pipeline/fetch_wikidata.py` — erzeugt initialen YAML-Seed
2. Manuelle Kuration der YAML-Dateien (Beschreibungen, Korrekturen, fehlende Genres)
3. `uv run python pipeline/resolve_commons.py` — ergänzt Audio-Beispiele
4. `uv run python pipeline/build.py` — validiert und exportiert `public/data/genres.json`
5. `pnpm dev` — lokale Entwicklung
6. Git Push → GitHub Actions: `build.py` + `vite build` → GitHub Pages

---

## Nicht im Scope

- Eigene Audio-Hosting-Infrastruktur (nur Wikimedia Commons-Links)
- User-Accounts oder Community-Bearbeitung
- Echtzeit-Daten oder Live-API-Backend
- Einbettung von YouTube/Spotify (Lizenzproblematik)
