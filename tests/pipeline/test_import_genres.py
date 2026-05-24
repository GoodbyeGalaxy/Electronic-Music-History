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
