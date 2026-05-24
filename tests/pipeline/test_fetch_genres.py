from unittest.mock import patch, MagicMock
from pipeline.fetch_genres import (
    fetch_category_titles,
    fetch_wikipedia_batch,
    fetch_wikidata_for_qids,
)


def _wiki_response(members):
    return {"query": {"categorymembers": members}}


def _mock_get(json_data):
    m = MagicMock()
    m.status_code = 200
    m.raise_for_status.return_value = None
    m.json.return_value = json_data
    return m


def test_fetch_category_titles_returns_article_titles():
    with patch("pipeline.fetch_genres.requests.get") as mock_get, \
         patch("pipeline.fetch_genres.time.sleep"):
        mock_get.return_value = _mock_get(_wiki_response([
            {"ns": 0, "title": "Techno"},
            {"ns": 0, "title": "House music"},
        ]))
        result = fetch_category_titles("Category:Electronic_music_genres")
    assert "Techno" in result
    assert "House music" in result


def test_fetch_category_titles_recurses_into_subcategories():
    responses = [
        _mock_get(_wiki_response([
            {"ns": 14, "title": "Category:Techno"},
            {"ns": 0, "title": "House music"},
        ])),
        _mock_get(_wiki_response([
            {"ns": 0, "title": "Minimal techno"},
        ])),
    ]
    with patch("pipeline.fetch_genres.requests.get") as mock_get, \
         patch("pipeline.fetch_genres.time.sleep"):
        mock_get.side_effect = responses
        result = fetch_category_titles("Category:Electronic_music_genres")
    assert "House music" in result
    assert "Minimal techno" in result


def test_fetch_wikipedia_batch_extracts_qid_and_description():
    mock_response = {
        "query": {
            "redirects": [],
            "pages": {
                "12345": {
                    "pageid": 12345,
                    "title": "Techno",
                    "extract": "Techno is a form of electronic dance music.",
                    "pageprops": {"wikibase_item": "Q48803"},
                }
            },
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikipedia_batch(["Techno"])
    assert "Techno" in result
    assert result["Techno"]["qid"] == "Q48803"
    assert "electronic" in result["Techno"]["description"].lower()


def test_fetch_wikipedia_batch_skips_missing_pages():
    mock_response = {
        "query": {
            "redirects": [],
            "pages": {"-1": {"missing": True, "title": "NonExistent"}},
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikipedia_batch(["NonExistent"])
    assert result == {}


def test_fetch_wikidata_for_qids_returns_year_and_parents():
    mock_response = {
        "results": {
            "bindings": [
                {
                    "genre": {"value": "http://www.wikidata.org/entity/Q48803"},
                    "genreLabel": {"value": "techno"},
                    "inception": {"value": "1985-01-01T00:00:00Z"},
                    "parent": {"value": "http://www.wikidata.org/entity/Q9778"},
                    "sitelink": {"value": "https://en.wikipedia.org/wiki/Techno"},
                },
                {
                    "genre": {"value": "http://www.wikidata.org/entity/Q48803"},
                    "genreLabel": {"value": "techno"},
                    "parent": {"value": "http://www.wikidata.org/entity/Q188451"},
                },
            ]
        }
    }
    with patch("pipeline.fetch_genres.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = mock_response
        result = fetch_wikidata_for_qids(["Q48803"])
    assert "Q48803" in result
    assert result["Q48803"]["year_start"] == 1985
    assert set(result["Q48803"]["parent_qids"]) == {"Q9778", "Q188451"}
    assert result["Q48803"]["enwiki_slug"] == "Techno"


def test_fetch_wikidata_for_qids_returns_empty_for_no_input():
    result = fetch_wikidata_for_qids([])
    assert result == {}
