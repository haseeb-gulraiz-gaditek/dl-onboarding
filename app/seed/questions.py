"""Question-bank seed loader.

Validates `app/seed/questions.json` end-to-end, then upserts each
entry into the `questions` collection by stable `key` (idempotent).

Per F-QB-1: validate the WHOLE file before any DB writes — partial
loads are not allowed.

Run via:  python -m app.seed questions
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.db.mongo import close_mongo, init_mongo
from app.db.questions import (
    ensure_indexes as ensure_question_indexes,
    upsert_question_by_key,
)


SEED_PATH = Path(__file__).parent / "questions.json"

_ALLOWED_KINDS = {"single_select", "multi_select", "free_text"}
_ALLOWED_CATEGORIES = {"role", "stack", "workflow", "friction", "wishlist", "budget"}
_REQUIRED_FIELDS = {
    "key", "text", "kind", "category", "order", "version", "active", "is_core"
}


def _validate_entry(entry: dict[str, Any], idx: int) -> str | None:
    """Return None if valid, else an error string describing the failure."""
    if not isinstance(entry, dict):
        return f"entry [{idx}] is not an object"

    missing = _REQUIRED_FIELDS - set(entry.keys())
    if missing:
        return f"entry [{idx}] (key={entry.get('key')!r}) missing fields: {sorted(missing)}"

    if entry["kind"] not in _ALLOWED_KINDS:
        return (
            f"entry [{idx}] (key={entry['key']!r}) has unknown kind={entry['kind']!r}; "
            f"must be one of {sorted(_ALLOWED_KINDS)}"
        )

    if entry["category"] not in _ALLOWED_CATEGORIES:
        return (
            f"entry [{idx}] (key={entry['key']!r}) has unknown category={entry['category']!r}; "
            f"must be one of {sorted(_ALLOWED_CATEGORIES)}"
        )

    if not isinstance(entry["order"], int):
        return f"entry [{idx}] (key={entry['key']!r}) order must be int"

    if not isinstance(entry["active"], bool) or not isinstance(entry["is_core"], bool):
        return f"entry [{idx}] (key={entry['key']!r}) active/is_core must be boolean"

    options = entry.get("options")
    if entry["kind"] in {"single_select", "multi_select"}:
        if not isinstance(options, list) or len(options) == 0:
            return (
                f"entry [{idx}] (key={entry['key']!r}) "
                f"is {entry['kind']} but has no options"
            )
        for j, opt in enumerate(options):
            if not isinstance(opt, dict) or "value" not in opt or "label" not in opt:
                return (
                    f"entry [{idx}] (key={entry['key']!r}) option[{j}] "
                    f"must be {{value, label}}"
                )
    else:
        # free_text: options must be empty (or absent)
        if options not in (None, []):
            return (
                f"entry [{idx}] (key={entry['key']!r}) "
                f"is free_text but has options"
            )

    return None


async def seed_questions() -> int:
    """Load and apply the seed file. Returns process exit code."""
    if not SEED_PATH.exists():
        print(f"[seed] missing {SEED_PATH}", file=sys.stderr)
        return 2

    raw = SEED_PATH.read_text(encoding="utf-8")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[seed] {SEED_PATH} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(entries, list):
        print("[seed] root must be a JSON array", file=sys.stderr)
        return 2

    # Validate ALL entries before any DB write (per F-QB-1).
    for i, entry in enumerate(entries):
        err = _validate_entry(entry, i)
        if err is not None:
            print(f"[seed] validation failed: {err}", file=sys.stderr)
            return 2

    # Validate cross-entry constraint: keys are unique.
    keys = [e["key"] for e in entries]
    if len(keys) != len(set(keys)):
        dups = sorted({k for k in keys if keys.count(k) > 1})
        print(f"[seed] duplicate keys in seed file: {dups}", file=sys.stderr)
        return 2

    # All valid -- proceed with DB writes.
    load_dotenv()
    await init_mongo()
    await ensure_question_indexes()

    inserted = 0
    updated = 0
    for entry in entries:
        # Normalize options for free_text (json may have empty list or omit).
        if "options" not in entry:
            entry["options"] = []
        was_inserted, was_updated = await upsert_question_by_key(entry)
        if was_inserted:
            inserted += 1
        elif was_updated:
            updated += 1

    total = len(entries)
    print(f"[seed] inserted: {inserted}, updated: {updated}, total: {total}")

    await close_mongo()
    return 0


def main() -> None:
    sys.exit(asyncio.run(seed_questions()))


if __name__ == "__main__":
    main()
