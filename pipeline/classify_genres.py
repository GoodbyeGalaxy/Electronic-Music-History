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
