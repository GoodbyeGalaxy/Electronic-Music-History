import yaml
from pathlib import Path
from pipeline.classify_genres import classify, load_seeds


def test_classify_assigns_seed_qid_to_its_track():
    genres = [{
        "qid": "Q48803", "name": "Techno", "year_start": 1985,
        "parent_qids": [], "enwiki_slug": "Techno", "description": "",
    }]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert "techno" in classified
    assert len(classified["techno"]) == 1
    assert unclassified == []


def test_classify_assigns_genre_via_parent_chain():
    genres = [
        {
            "qid": "Q48803", "name": "Techno", "year_start": 1985,
            "parent_qids": [], "enwiki_slug": "Techno", "description": "",
        },
        {
            "qid": "Q1195085", "name": "Minimal Techno", "year_start": 1994,
            "parent_qids": ["Q48803"], "enwiki_slug": "Minimal_techno", "description": "",
        },
    ]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert len(classified["techno"]) == 2
    assert {g["qid"] for g in classified["techno"]} == {"Q48803", "Q1195085"}
    assert unclassified == []


def test_classify_puts_unreachable_genres_in_unclassified():
    genres = [{
        "qid": "Q999999", "name": "Unknown Genre", "year_start": 2000,
        "parent_qids": [], "enwiki_slug": "", "description": "",
    }]
    seeds = {"techno": ["Q48803"]}
    classified, unclassified = classify(genres, seeds)
    assert classified == {}
    assert len(unclassified) == 1


def test_classify_handles_multi_hop_ancestor():
    genres = [
        {"qid": "Q1", "name": "Root", "year_start": 1970, "parent_qids": [], "enwiki_slug": "", "description": ""},
        {"qid": "Q2", "name": "Mid", "year_start": 1980, "parent_qids": ["Q1"], "enwiki_slug": "", "description": ""},
        {"qid": "Q3", "name": "Leaf", "year_start": 1990, "parent_qids": ["Q2"], "enwiki_slug": "", "description": ""},
    ]
    seeds = {"house": ["Q1"]}
    classified, unclassified = classify(genres, seeds)
    assert len(classified["house"]) == 3
    assert unclassified == []


def test_load_seeds_reads_yaml(tmp_path):
    seeds_file = tmp_path / "track_seeds.yaml"
    seeds_file.write_text(yaml.dump({
        "techno": {"qids": ["Q48803"]},
        "house":  {"qids": ["Q11399"]},
        "pioneers": {"qids": []},
    }))
    result = load_seeds(seeds_file)
    assert result == {"techno": ["Q48803"], "house": ["Q11399"], "pioneers": []}
