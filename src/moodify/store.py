"""SQLite storage for capsules. Seeds the starter capsules, adding new ones as the set grows.

A capsule is either a starter (song + artist, no link) or a community capsule
(a link, with a title found from the link or typed by the person). Every capsule
has a moderation status; only "visible" ones are matched or shown on the wall.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, computed_field

from .links import search_link

SEED_FILE = Path(__file__).resolve().parents[2] / "seeds" / "starter_capsules.json"
STARTER_AUTHOR = "MoodIfy starter set"
STATUSES = ("visible", "held", "hidden", "crisis")

SCHEMA = """
create table if not exists capsules (
    id integer primary key autoincrement,
    song text,
    artist text,
    url text,
    site text,
    thumbnail text,
    mood text not null,
    note text not null,
    author text not null,
    source text not null check (source in ('starter', 'community')),
    status text not null default 'visible' check (status in ('visible', 'held', 'hidden', 'crisis')),
    moderation text not null default '',
    submitter text not null default '',
    created_at text not null
)
"""
COLUMNS = ("song, artist, url, site, thumbnail, mood, note, author, source, "
           "status, moderation, submitter, created_at")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Capsule(BaseModel):
    """What the public API returns. Moderation details and submitter stay private."""
    id: int
    song: str | None
    artist: str | None
    url: str | None
    site: str | None
    thumbnail: str | None
    mood: str
    note: str
    author: str
    source: str
    created_at: str

    @computed_field
    @property
    def title(self) -> str:
        return self.song or self.site or "A shared song"

    @computed_field
    @property
    def listen_url(self) -> str:
        return self.url or search_link(self.song or "", self.artist or "")


class StoredCapsule(Capsule):
    status: str
    moderation: str


class Store:
    """Local SQLite store. The Worker uses a D1 store with the same methods (see src/worker.py)."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            self._migrate(con)
            con.execute(SCHEMA)
            self._seed(con)

    def _connect(self) -> sqlite3.Connection:
        import sqlite3  # not shipped with the Worker runtime, which uses D1

        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _migrate(self, con: sqlite3.Connection) -> None:
        """Upgrade a v1 table (song/artist required, no status) by copying it into v2."""
        columns = {row["name"] for row in con.execute("pragma table_info(capsules)")}
        if not columns or "status" in columns:
            return
        con.execute("alter table capsules rename to capsules_v1")
        con.execute(SCHEMA)
        con.execute("insert into capsules (id, song, artist, mood, note, author, source, created_at) "
                    "select id, song, artist, mood, note, author, source, created_at from capsules_v1")
        con.execute("drop table capsules_v1")

    def _seed(self, con: sqlite3.Connection) -> None:
        """Add any starter capsules this database doesn't have yet, so new seeds reach old databases."""
        starters = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        have = {(row["song"], row["artist"]) for row in
                con.execute("select song, artist from capsules where source = 'starter'")}
        con.executemany(
            "insert into capsules (song, artist, mood, note, author, source, created_at) "
            "values (?, ?, ?, ?, ?, 'starter', ?)",
            [(c["song"], c["artist"], c["mood"], c["note"], STARTER_AUTHOR, now())
             for c in starters if (c["song"], c["artist"]) not in have],
        )

    # ---- reads ----
    def all(self, mood: str | None = None) -> list[Capsule]:
        """Visible capsules, used for matching and channels."""
        query, args = "select * from capsules where status = 'visible'", ()
        if mood:
            query, args = query + " and mood = ?", (mood,)
        with self._connect() as con:
            return [Capsule(**dict(row)) for row in con.execute(query + " order by id", args)]

    def wall(self, before: int | None = None, limit: int = 20) -> list[Capsule]:
        """Community messages for the public wall, newest first."""
        query = "select * from capsules where status = 'visible' and source = 'community'"
        args: tuple = ()
        if before:
            query, args = query + " and id < ?", (before,)
        with self._connect() as con:
            rows = con.execute(query + " order by id desc limit ?", (*args, limit))
            return [Capsule(**dict(row)) for row in rows]

    def by_status(self, status: str) -> list[StoredCapsule]:
        with self._connect() as con:
            rows = con.execute("select * from capsules where status = ? order by id desc", (status,))
            return [StoredCapsule(**dict(row)) for row in rows]

    def submissions_since(self, submitter: str, hours: float) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        with self._connect() as con:
            return con.execute("select count(*) from capsules where submitter = ? and created_at >= ?",
                               (submitter, cutoff)).fetchone()[0]

    # ---- writes ----
    def add(self, *, mood: str, note: str, author: str, song: str | None = None, artist: str | None = None,
            url: str | None = None, site: str | None = None, thumbnail: str | None = None,
            status: str = "visible", moderation: str = "", submitter: str = "") -> StoredCapsule:
        with self._connect() as con:
            cursor = con.execute(
                f"insert into capsules ({COLUMNS}) values (?, ?, ?, ?, ?, ?, ?, ?, 'community', ?, ?, ?, ?)",
                (song, artist, url, site, thumbnail, mood, note, author, status, moderation, submitter, now()),
            )
            row = con.execute("select * from capsules where id = ?", (cursor.lastrowid,)).fetchone()
        return StoredCapsule(**dict(row))

    def set_status(self, capsule_id: int, status: str) -> bool:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        with self._connect() as con:
            return con.execute("update capsules set status = ? where id = ?", (status, capsule_id)).rowcount == 1
