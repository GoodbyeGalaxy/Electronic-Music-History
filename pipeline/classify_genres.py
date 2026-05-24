"""Assigns genres to tracks by traversing Wikidata parent QID chains.

Fallback: genres whose parent chain doesn't reach a seed QID are matched
by keywords in their name. This handles genres with flat Wikidata hierarchies
(many electronic genres only list Q851213 / Q9778 as parents).
"""
from __future__ import annotations
from collections import deque
from pathlib import Path
import re
import yaml

# Ordered from most-specific to least-specific so the first match wins.
# Each entry: (track_id, set_of_lowercase_keywords)
# A keyword matches if it appears as a whole word in the lowercased genre name.
_KEYWORD_RULES: list[tuple[str, frozenset[str]]] = [
    ("electroacoustic", frozenset(["electroacoustic", "musique concrète", "musique concrete", "acousmatic", "spectral"])),
    ("uk_garage",       frozenset(["uk garage", "uk-garage"])),
    ("drum_n_bass",     frozenset(["drum and bass", "drum n bass", "drum'n'bass", "dnb", "jungle", "liquid funk"])),
    ("hardcore",        frozenset(["hardcore", "gabber", "hardstyle", "happy hardcore", "terrorcore", "speedcore"])),
    ("breakbeat",       frozenset(["breakbeat", "break beat", "breaks", "big beat", "nu skool"])),
    ("tech_house",      frozenset(["tech house", "tech-house"])),
    ("progressive",     frozenset(["progressive house", "progressive trance", "progressive techno"])),
    ("acid",            frozenset(["acid house", "acid techno", "acid jazz", "acid"])),
    ("ambient",         frozenset(["ambient", "chill-out", "chill out", "chillout", "new age", "drone", "dark ambient"])),
    ("downtempo",       frozenset(["downtempo", "trip hop", "trip-hop", "triphop", "lo-fi", "lofi", "lo fi", "chillhop"])),
    ("industrial",      frozenset(["industrial", "ebm", "electronic body", "power electronics", "dark electro", "aggrotech"])),
    ("electro",         frozenset(["electro", "electroclash", "synthpop", "synth-pop"])),
    ("techno",          frozenset(["techno", "minimal techno", "detroit techno", "dub techno", "berlin techno"])),
    ("hip_hop",         frozenset(["hip hop", "hip-hop", "hiphop", "rap", "trap", "grime", "cloud rap", "phonk"])),
    ("urban",           frozenset(["r&b", "rnb", "rhythm and blues", "neo soul", "neo-soul", "funk"])),
    ("disco",           frozenset(["disco", "funk", "nu-disco", "nu disco", "post-disco"])),
    ("house",           frozenset(["house", "deep house", "chicago house", "soul house", "soulful house"])),
    ("garage",          frozenset(["garage", "new jersey garage", "deep house"])),
    ("bass",            frozenset(["bass music", "bassline", "bass house", "future bass", "riddim", "brostep"])),
    ("uk_garage",       frozenset(["speed garage", "2-step", "two-step"])),
    ("drum_n_bass",     frozenset(["neurofunk", "darkstep", "junglist"])),
]

_WORD_RE = re.compile(r"\b\w[\w\s\-']*\w\b|\b\w\b")


def _keyword_classify(name: str) -> str | None:
    """Returns a track_id if any keyword rule matches the lowercased genre name."""
    lower = name.lower()
    for track_id, keywords in _KEYWORD_RULES:
        for kw in keywords:
            # Full-phrase match: keyword appears in the name
            if kw in lower:
                return track_id
    return None


def load_seeds(seeds_path: Path) -> dict[str, list[str]]:
    """Returns {track_id: [qid, ...]} from track_seeds.yaml."""
    raw = yaml.safe_load(seeds_path.read_text(encoding="utf-8")) or {}
    return {track: (data.get("qids") or []) for track, data in raw.items()}


def classify(
    genres: list[dict],
    seeds: dict[str, list[str]],
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Assigns each genre to a track via BFS + keyword fallback.

    1. BFS through parent_qids until a seed QID is found.
    2. If no seed reached, fall back to keyword matching on the genre name.
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

    def find_track_by_qid(start_qid: str) -> str | None:
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
        track = find_track_by_qid(genre["qid"]) or _keyword_classify(genre["name"])
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
