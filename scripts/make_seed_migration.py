"""Write a D1 migration that adds starter capsules from seeds/starter_capsules.json.

Applied migrations never change, so each run writes the next numbered file. Every insert
skips songs the database already has, so a migration is safe whatever came before it.
The local SQLite store tops itself up on start and needs none of this.

    python scripts/make_seed_migration.py more_starters
    npx wrangler d1 migrations apply moodify --remote
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from moodify.store import SEED_FILE, STARTER_AUTHOR, now  # noqa: E402

MIGRATIONS = ROOT / "migrations"


def sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main(name: str) -> None:
    stamp = sql(now())
    lines = []
    for capsule in json.loads(SEED_FILE.read_text(encoding="utf-8")):
        song, artist = sql(capsule["song"]), sql(capsule["artist"])
        lines.append(
            "insert into capsules (song, artist, mood, note, author, source, created_at) "
            f"select {song}, {artist}, {sql(capsule['mood'])}, {sql(capsule['note'])}, {sql(STARTER_AUTHOR)}, "
            f"'starter', {stamp} where not exists (select 1 from capsules where source = 'starter' "
            f"and song = {song} and artist = {artist});")
    number = max((int(p.name[:4]) for p in MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql")), default=0) + 1
    out = MIGRATIONS / f"{number:04d}_{name}.sql"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)} ({len(lines)} starters, existing ones skipped)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "starters")
