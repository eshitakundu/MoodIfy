"""MoodIfy API + static web page."""
from __future__ import annotations

import hashlib
import hmac
import inspect
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from .links import LinkError, LinkInfo, SongLink, lookup, parse_link
from .matcher import best_capsule
from .moderation import Moderator
from .moods import MOODS, Mood, target_mood
from .reader import LLMReader, in_crisis
from .store import CASSETTE_COLORS, Capsule, StoredCapsule, Store

WEB = Path(__file__).resolve().parents[2] / "web"
URL = re.compile(r"https?://|www\.", re.I)
PER_HOUR, PER_DAY = 3, 10

SUPPORT = (
    "It sounds like you're carrying something really heavy. You don't have to handle it alone. "
    "In India you can call Tele-MANAS, free and 24/7, on 14416 or 1-800-891-4416. "
    "Elsewhere, findahelpline.com lists free, confidential lines in your country."
)
STATUS_MESSAGES = {
    "visible": "It's on the wall. Someone who feels this way will find it.",
    "held": "Thanks. Your song will appear once it's been checked.",
    "crisis": "Thank you for sharing this. Your note won't be posted, but please read the message below.",
}


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
    """Two shapes are accepted:
    new:    {url, message, title?, name?, mood?}   mood is read from the message if missing
    legacy: {song, artist, mood, note, name?}      the original form
    """
    url: str | None = Field(default=None, max_length=500)
    message: str | None = Field(default=None, min_length=10, max_length=400)
    title: str | None = Field(default=None, max_length=120)
    song: str | None = Field(default=None, min_length=1, max_length=120)
    artist: str | None = Field(default=None, min_length=1, max_length=120)
    note: str | None = Field(default=None, min_length=10, max_length=280)
    mood: Mood | None = None
    name: str = Field(default="", max_length=40)
    color: Literal[CASSETTE_COLORS] | None = None

    @field_validator("message", "title", "song", "artist", "note", "name")
    @classmethod
    def no_links_in_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if URL.search(value):
            raise ValueError("links go in the link field, not in your message")
        return value

    @model_validator(mode="after")
    def one_shape(self) -> "NewCapsule":
        if self.url:
            if not self.message:
                raise ValueError("write a message to go with your song")
        elif not (self.song and self.artist and self.note and self.mood):
            raise ValueError("add a link to the song and a message")
        return self

    @property
    def text(self) -> str:
        return self.message or self.note or ""


class SubmitResponse(BaseModel):
    status: str
    message: str
    capsule: Capsule | None
    support: str | None = None


class StatusChange(BaseModel):
    status: Literal["visible", "hidden", "held"]


def client_key(request: Request, salt: str) -> str:
    """A salted hash of the visitor's IP, so limits work without storing addresses."""
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:24]


async def done(value: Any) -> Any:
    """The SQLite store answers directly and the D1 store with awaitables; accept both."""
    return await value if inspect.isawaitable(value) else value


def create_app(db_path: str | None = None, reader: LLMReader | None = None,
               moderator: Moderator | None = None,
               link_lookup: Callable[[SongLink], Awaitable[LinkInfo] | LinkInfo] = lookup,
               store: Any = None) -> FastAPI:
    store = store or Store(db_path or os.getenv("MOODIFY_DB", "data/moodify.db"))
    mood_reader = reader or LLMReader()
    moderation = moderator or Moderator()
    salt = os.getenv("MOODIFY_SALT", "moodify-local")
    admin_token = os.getenv("MOODIFY_ADMIN_TOKEN", "")
    app = FastAPI(title="MoodIfy", version="2.0.0")

    def require_admin(authorization: str | None) -> None:
        supplied = (authorization or "").removeprefix("Bearer ").strip()
        if not admin_token or not hmac.compare_digest(supplied, admin_token):
            raise HTTPException(status_code=404, detail="Not found")

    @app.post("/api/match", response_model=MatchResponse)
    async def match(request: MatchRequest) -> MatchResponse:
        if in_crisis(request.text):
            # Never send this text to a model; answer with support first.
            capsule = best_capsule(request.text, await done(store.all("hopeful")), set(request.seen))
            return MatchResponse(mood="sad", target_mood="hopeful", source="safety",
                                 capsule=capsule, support=SUPPORT)
        reading = await mood_reader.read(request.text)
        target = target_mood(reading.mood, request.mode)
        capsule = best_capsule(request.text, await done(store.all(target)), set(request.seen))
        return MatchResponse(mood=reading.mood, target_mood=target, source=reading.source, capsule=capsule)

    @app.get("/api/capsules", response_model=list[Capsule])
    async def list_capsules(mood: str | None = None) -> list[Capsule]:
        if mood and mood not in MOODS:
            raise HTTPException(status_code=422, detail=f"mood must be one of {', '.join(MOODS)}")
        return await done(store.all(mood))

    @app.post("/api/capsules", response_model=SubmitResponse, status_code=201)
    async def add_capsule(body: NewCapsule, request: Request) -> SubmitResponse:
        submitter = client_key(request, salt)
        if (await done(store.submissions_since(submitter, 1)) >= PER_HOUR
                or await done(store.submissions_since(submitter, 24)) >= PER_DAY):
            raise HTTPException(status_code=429, detail="You've shared a lot today. Try again a little later.")

        link, info = None, LinkInfo(None, None, None)
        if body.url:
            try:
                link = parse_link(body.url)
            except LinkError as error:
                raise HTTPException(status_code=422, detail=str(error)) from None
            info = await done(link_lookup(link))

        song = body.song or body.title or info.title
        artist = body.artist or info.artist
        # Titles and names are public too, so they're moderated with the message.
        verdict = await moderation.check(" \n".join(filter(None, [body.text, body.title, body.name])))
        mood = body.mood or ("sad" if verdict.status == "crisis" else (await mood_reader.read(body.text)).mood)

        saved: StoredCapsule = await done(store.add(
            song=song, artist=artist, url=link.url if link else None, site=link.site if link else None,
            thumbnail=info.thumbnail, mood=mood, note=body.text, author=body.name or "Anonymous",
            status=verdict.status, moderation=f"{verdict.checked_by}: {verdict.reason}", submitter=submitter,
            color=body.color,
        ))
        public = Capsule(**saved.model_dump(include=set(Capsule.model_fields)))
        return SubmitResponse(
            status=verdict.status, message=STATUS_MESSAGES[verdict.status],
            capsule=public if verdict.status == "visible" else None,
            support=SUPPORT if verdict.status == "crisis" else None,
        )

    @app.get("/api/wall", response_model=list[Capsule])
    async def wall(before: int | None = Query(default=None, ge=1), limit: int = Query(default=20, ge=1, le=50)):
        return await done(store.wall(before=before, limit=limit))

    @app.get("/api/moods")
    def moods() -> list[str]:
        return list(MOODS)

    # ---- maintainer only (needs MOODIFY_ADMIN_TOKEN; returns 404 otherwise) ----
    @app.get("/api/admin/capsules", response_model=list[StoredCapsule], include_in_schema=False)
    async def admin_list(status: str = "held", authorization: str | None = Header(default=None)):
        require_admin(authorization)
        return await done(store.by_status(status))

    @app.post("/api/admin/capsules/{capsule_id}", include_in_schema=False)
    async def admin_set(capsule_id: int, change: StatusChange, authorization: str | None = Header(default=None)):
        require_admin(authorization)
        if not await done(store.set_status(capsule_id, change.status)):
            raise HTTPException(status_code=404, detail="No such capsule")
        return {"id": capsule_id, "status": change.status}

    # On Cloudflare the page is served by Workers Assets; locally FastAPI serves it.
    if WEB.is_dir():
        app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app
