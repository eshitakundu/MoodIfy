"""MoodIfy API + static web page."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .matcher import best_capsule
from .moods import MOODS, Mood, target_mood
from .reader import LLMReader, in_crisis
from .store import Capsule, Store

WEB = Path(__file__).resolve().parent.parent / "web"
URL = re.compile(r"https?://|www\.", re.I)

SUPPORT = (
    "It sounds like you're carrying something really heavy. You don't have to handle it alone. "
    "In India you can call Tele-MANAS, free and 24/7, on 14416 or 1-800-891-4416. "
    "Elsewhere, findahelpline.com lists free, confidential lines in your country."
)


class MatchRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    mode: Literal["relate", "lift"] = "relate"
    seen: list[int] = Field(default_factory=list, max_length=200)


class MatchResponse(BaseModel):
    mood: str
    target_mood: str
    source: str
    capsule: Capsule | None
    support: str | None = None


class NewCapsule(BaseModel):
    song: str = Field(min_length=1, max_length=120)
    artist: str = Field(min_length=1, max_length=120)
    mood: Mood
    note: str = Field(min_length=10, max_length=280)
    name: str = Field(default="", max_length=40)

    @field_validator("song", "artist", "note", "name")
    @classmethod
    def no_links(cls, value: str) -> str:
        value = value.strip()
        if URL.search(value):
            raise ValueError("links aren't allowed in capsules")
        return value


def create_app(db_path: str | None = None, reader: LLMReader | None = None) -> FastAPI:
    store = Store(db_path or os.getenv("MOODIFY_DB", "data/moodify.db"))
    mood_reader = reader or LLMReader()
    app = FastAPI(title="MoodIfy", version="1.0.0")

    @app.post("/api/match", response_model=MatchResponse)
    def match(request: MatchRequest) -> MatchResponse:
        if in_crisis(request.text):
            # Never send this text to a model; answer with support first.
            capsule = best_capsule(request.text, store.all("hopeful"), set(request.seen))
            return MatchResponse(mood="sad", target_mood="hopeful", source="safety",
                                 capsule=capsule, support=SUPPORT)
        reading = mood_reader.read(request.text)
        target = target_mood(reading.mood, request.mode)
        capsule = best_capsule(request.text, store.all(target), set(request.seen))
        return MatchResponse(mood=reading.mood, target_mood=target, source=reading.source,
                             capsule=capsule)

    @app.get("/api/capsules", response_model=list[Capsule])
    def list_capsules(mood: str | None = None) -> list[Capsule]:
        if mood and mood not in MOODS:
            raise HTTPException(status_code=422, detail=f"mood must be one of {', '.join(MOODS)}")
        return store.all(mood)

    @app.post("/api/capsules", response_model=Capsule, status_code=201)
    def add_capsule(capsule: NewCapsule) -> Capsule:
        return store.add(capsule.song, capsule.artist, capsule.mood, capsule.note,
                         capsule.name or "Anonymous")

    @app.get("/api/moods")
    def moods() -> list[str]:
        return list(MOODS)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(WEB / "index.html")

    app.mount("/static", StaticFiles(directory=WEB), name="static")
    return app
