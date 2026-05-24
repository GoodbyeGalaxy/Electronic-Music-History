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


def test_tracks_has_20_entries():
    assert len(TRACKS) == 20


def test_tracks_includes_ishkur_categories():
    track_ids = {t.id for t in TRACKS}
    required = {"pioneers", "ambient", "hip_hop", "techno", "hardcore",
                "drum_n_bass", "breakbeat", "acid", "house", "tech_house",
                "progressive", "garage", "uk_garage", "bass", "electro",
                "downtempo", "urban", "industrial", "electroacoustic", "disco"}
    assert required == track_ids
