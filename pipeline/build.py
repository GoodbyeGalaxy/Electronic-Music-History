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
