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
