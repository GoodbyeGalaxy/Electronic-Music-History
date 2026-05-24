"""Sucht CC-lizenzierte Audiodateien auf Wikimedia Commons."""
from __future__ import annotations
import re
import requests
from pathlib import Path

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ElectronicMusicHistoryBot/0.1 (research project)"
CC_MARKERS = {"cc-by", "cc-by-sa", "cc0", "pd", "public domain"}


def build_commons_url(filename: str) -> str:
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"


def parse_audio_result(page: dict) -> dict | None:
    title = page.get("title", "")
    filename = title.removeprefix("File:")
    if not any(filename.lower().endswith(ext) for ext in (".ogg", ".flac", ".wav", ".mp3")):
        return None
    meta = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
    license_short = meta.get("LicenseShortName", {}).get("value", "").lower().replace(" ", "-")
    if not any(marker in license_short for marker in CC_MARKERS):
        return None
    artist_raw = meta.get("Artist", {}).get("value", "")
    artist = re.sub(r"<[^>]+>", "", artist_raw).strip()
    object_name = meta.get("ObjectName", {}).get("value", filename)
    return {"file": filename, "source": "wikimedia_commons", "title": object_name, "artist": artist}


def search_audio(query: str, limit: int = 5) -> list[dict]:
    resp = requests.get(
        COMMONS_API,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:audio {query}",
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "extmetadata",
            "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName",
            "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    return [r for page in pages.values() if (r := parse_audio_result(page))]


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "electronic music"
    for r in search_audio(query):
        print(r)
