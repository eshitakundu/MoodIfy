"""SQLite storage for capsules. Seeds the 50 starter capsules on first run."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

SEED_FILE = Path(__file__).resolve().parent.parent / "seeds" / "starter_capsules.json"
STARTER_AUTHOR = "MoodIfy starter set"

SCHEMA = """
create table if not exists capsules (
    id integer primary key autoincrement,
    song text not null,
    artist text not null,
    mood text not null,
    note text not null,
    author text not null,
    source text not null check (source in ('starter', 'community')),
    created_at text not null
)
"""


class Capsule(BaseModel):
    id: int
    song: str
    artist: str
    mood: str
    note: str
    author: str
    source: str
    created_at: str


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(SCHEMA)
            if con.execute("select count(*) from capsules").fetchone()[0] == 0:
                self._seed(con)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _seed(self, con: sqlite3.Connection) -> None:
        starters = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        con.executemany(
            "insert into capsules (song, artist, mood, note, author, source, created_at) "
            "values (?, ?, ?, ?, ?, 'starter', ?)",
            [(c["song"], c["artist"], c["mood"], c["note"], STARTER_AUTHOR, now) for c in starters],
        )

    def all(self, mood: str | None = None) -> list[Capsule]:
        query, args = "select * from capsules", ()
        if mood:
            query, args = query + " where mood = ?", (mood,)
        with self._connect() as con:
            return [Capsule(**dict(row)) for row in con.execute(query + " order by id", args)]

    def add(self, song: str, artist: str, mood: str, note: str, author: str) -> Capsule:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as con:
            cursor = con.execute(
                "insert into capsules (song, artist, mood, note, author, source, created_at) "
                "values (?, ?, ?, ?, ?, 'community', ?)",
                (song, artist, mood, note, author, now),
            )
            row = con.execute("select * from capsules where id = ?", (cursor.lastrowid,)).fetchone()
        return Capsule(**dict(row))
