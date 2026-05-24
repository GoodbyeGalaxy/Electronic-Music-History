from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


class AudioExample(BaseModel):
    file: str
    source: str = "wikimedia_commons"
    title: str
    artist: str


class Genre(BaseModel):
    id: str
    name: str
    track: str
    year_start: int
    year_end: Optional[int] = None
    origin: str = ""
    parents: list[str] = []
    description: str = ""
    key_artists: list[str] = []
    key_labels: list[str] = []
    subvariants: list[str] = []
    wikidata_id: str = ""
    wikipedia_slug: str = ""
    audio_examples: list[AudioExample] = []

    @field_validator("year_start", mode="before")
    @classmethod
    def year_must_be_int(cls, v: object) -> int:
        if not isinstance(v, int):
            raise ValueError("year_start must be an integer")
        return v


class Edge(BaseModel):
    from_: str
    to: str
    type: str = "influence"
    label: str = ""

    model_config = {"populate_by_name": True}

    @classmethod
    def from_yaml(cls, data: dict) -> "Edge":
        return cls(
            from_=data["from"],
            to=data["to"],
            type=data.get("type", "influence"),
            label=data.get("label", ""),
        )


class Track(BaseModel):
    id: str
    label: str
    color: str
    order: int
