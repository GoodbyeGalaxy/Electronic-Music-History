"""Fragt Wikidata nach elektronischen Musikgenres und schreibt YAML-Rohdaten."""
from __future__ import annotations
import re
import requests
import yaml
from pathlib import Path

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "ElectronicMusicHistoryBot/0.1 (research project)"


def build_sparql_query() -> str:
    return """
SELECT DISTINCT ?genre ?genreLabel ?parentLabel ?inception WHERE {
  ?genre wdt:P31 wd:Q188451.
  OPTIONAL { ?genre wdt:P279 ?parent. }
  OPTIONAL { ?genre wdt:P571 ?inception. }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en".
  }
}
ORDER BY ?genreLabel
LIMIT 500
"""


def parse_results(data: dict) -> list[dict]:
    results = []
    for binding in data["results"]["bindings"]:
        qid = binding["genre"]["value"].rsplit("/", 1)[-1]
        name = binding.get("genreLabel", {}).get("value", "")
        parent = binding.get("parentLabel", {}).get("value", "")
        inception_raw = binding.get("inception", {}).get("value", "")
        year = None
        if inception_raw:
            m = re.match(r"(\d{4})", inception_raw)
            if m:
                year = int(m.group(1))
        results.append({"id": qid, "name": name, "year_start": year, "wikidata_parent": parent})
    return results


def fetch(output_dir: Path) -> None:
    """Fragt Wikidata ab und schreibt Rohdaten nach output_dir/wikidata_raw.yaml."""
    print("Querying Wikidata SPARQL...")
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": build_sparql_query(), "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    parsed = parse_results(resp.json())
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "wikidata_raw.yaml"
    out_file.write_text(yaml.dump(parsed, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {len(parsed)} entries -> {out_file}")
    print("Review wikidata_raw.yaml and manually map to genre YAML files.")


if __name__ == "__main__":
    fetch(Path("data/_wikidata"))
