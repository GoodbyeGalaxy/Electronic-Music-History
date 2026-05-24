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
