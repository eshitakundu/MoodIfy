"""Cloudflare Python Worker entry point.

The page in web/ is served by Workers Assets; /api/* runs the same FastAPI app as
local development, with capsules in D1 instead of SQLite. The table and the 50
starter capsules come from migrations/ (`wrangler d1 migrations apply`).
Secrets: OPENROUTER_API_KEY, MOODIFY_ADMIN_TOKEN, MOODIFY_SALT (`wrangler secret put`).
"""
import os
from datetime import datetime, timedelta, timezone

from workers import WorkerEntrypoint

from moodify.app import create_app
from moodify.store import COLUMNS, STATUSES, Capsule, StoredCapsule, now

SETTINGS = ("OPENROUTER_API_KEY", "MOODIFY_MODEL", "MOODIFY_ADMIN_TOKEN", "MOODIFY_SALT", "MOODIFY_REQUIRE_MODERATION")


class D1Store:
    """The Store interface (see moodify/store.py) on a D1 binding."""

    def __init__(self, db):
        self.db = db

    async def _rows(self, query, *args):
        return (await self.db.prepare(query).bind(*args).all()).results

    async def all(self, mood=None):
        if mood:
            rows = await self._rows("select * from capsules where status = 'visible' and mood = ? order by id", mood)
        else:
            rows = await self._rows("select * from capsules where status = 'visible' order by id")
        return [Capsule(**dict(row)) for row in rows]

    async def wall(self, before=None, limit=20):
        query = "select * from capsules where status = 'visible' and source = 'community'"
        if before:
            rows = await self._rows(query + " and id < ? order by id desc limit ?", before, limit)
        else:
            rows = await self._rows(query + " order by id desc limit ?", limit)
        return [Capsule(**dict(row)) for row in rows]

    async def by_status(self, status):
        rows = await self._rows("select * from capsules where status = ? order by id desc", status)
        return [StoredCapsule(**dict(row)) for row in rows]

    async def submissions_since(self, submitter, hours):
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        rows = await self._rows("select count(*) as n from capsules where submitter = ? and created_at >= ?",
                                submitter, cutoff)
        return rows[0]["n"]

    async def add(self, *, mood, note, author, song=None, artist=None, url=None, site=None, thumbnail=None,
                  status="visible", moderation="", submitter="", color=None):
        values = (song, artist, url, site, thumbnail, mood, note, author, "community",
                  status, moderation, submitter, now(), color)
        # Python None reaches D1 as undefined, which it rejects, so empty fields are written as SQL null.
        slots = ", ".join("null" if value is None else "?" for value in values)
        rows = await self._rows(f"insert into capsules ({COLUMNS}) values ({slots}) returning *",
                                *(value for value in values if value is not None))
        return StoredCapsule(**dict(rows[0]))

    async def set_status(self, capsule_id, status):
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        rows = await self._rows("update capsules set status = ? where id = ? returning id", status, capsule_id)
        return len(rows) == 1


_app = None


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        global _app
        if _app is None:
            for name in SETTINGS:
                value = getattr(self.env, name, None)
                if value:
                    os.environ[name] = str(value)
            _app = create_app(store=D1Store(self.env.DB))
        return await asgi.fetch(_app, request, self.env)
