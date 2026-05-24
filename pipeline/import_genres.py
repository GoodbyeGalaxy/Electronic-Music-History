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
