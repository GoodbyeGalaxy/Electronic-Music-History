from unittest.mock import patch, MagicMock
from pipeline.resolve_commons import build_commons_url, parse_audio_result, search_audio


def test_build_commons_url_returns_file_path_url():
    url = build_commons_url("Pierre_Schaeffer.ogg")
    assert "commons.wikimedia.org" in url
    assert "Special:FilePath" in url
    assert "Pierre_Schaeffer.ogg" in url


def test_parse_audio_result_extracts_fields():
    mock_page = {
        "title": "File:Test_audio.ogg",
        "imageinfo": [{"extmetadata": {
            "ObjectName": {"value": "Test Audio"},
            "Artist": {"value": "Test Artist"},
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
        }}],
    }
    result = parse_audio_result(mock_page)
    assert result is not None
    assert result["file"] == "Test_audio.ogg"
    assert result["artist"] == "Test Artist"
    assert result["source"] == "wikimedia_commons"


def test_parse_audio_result_rejects_non_cc():
    mock_page = {
        "title": "File:Test_audio.ogg",
        "imageinfo": [{"extmetadata": {
            "LicenseShortName": {"value": "All rights reserved"},
        }}],
    }
    assert parse_audio_result(mock_page) is None


def test_search_audio_calls_commons_api():
    with patch("pipeline.resolve_commons.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"query": {"pages": {}}}
        mock_get.return_value.raise_for_status = MagicMock()
        search_audio("techno music")
        assert mock_get.called
        assert "commons.wikimedia.org" in mock_get.call_args[0][0]
