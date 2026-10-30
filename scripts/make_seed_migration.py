"""Write migrations/0001_capsules.sql (table + starter capsules) for Cloudflare D1.

Run again after editing seeds/starter_capsules.json; the local SQLite store seeds itself.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from moodify.store import SCHEMA, SEED_FILE, STARTER_AUTHOR, now  # noqa: E402


def sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    stamp = now()
    lines = [SCHEMA.strip() + ";", ""]
    for capsule in json.loads(SEED_FILE.read_text(encoding="utf-8")):
        fields = (capsule["song"], capsule["artist"], capsule["mood"], capsule["note"], STARTER_AUTHOR, stamp)
        lines.append("insert into capsules (song, artist, mood, note, author, source, created_at) values ("
                     + ", ".join(sql(f) for f in fields[:5]) + f", 'starter', {sql(stamp)});")
    lines += ["", "create index if not exists capsules_wall on capsules (status, source, id);",
              "create index if not exists capsules_submitter on capsules (submitter, created_at);", ""]
    out = ROOT / "migrations" / "0001_capsules.sql"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
