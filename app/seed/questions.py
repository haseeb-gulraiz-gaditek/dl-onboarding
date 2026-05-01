"""Question-bank seed loader.

Validates `app/seed/questions.json` end-to-end, then upserts each
entry into the `questions` collection by stable `key` (idempotent).

Per F-QB-1: validate the WHOLE file before any DB writes — partial
loads are not allowed.

Public surface:
  - load_seed_file(path)      pure file-loading + JSON parsing
  - apply_questions_seed(...) validate-then-upsert; raises on bad input
  - seed_questions()          CLI orchestrator (loads .env, owns mongo
                              lifecycle); used by `python -m app.seed
                              questions`. Tests call the inner functions
                              directly to avoid lifecycle interference.
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


def load_seed_file(path: Path) -> list[dict[str, Any]]:
    """Read and parse a seed JSON file. Raises ValueError on bad input."""
    if not path.exists():
        raise ValueError(f"seed file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(entries, list):
        raise ValueError(f"{path}: root must be a JSON array")
    return entries


async def apply_questions_seed(
    entries: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Validate then upsert. Returns (inserted, updated, total).

    Validation runs over the WHOLE list before any DB write, per F-QB-1.
    Raises ValueError if any entry is invalid OR if there are duplicate
    keys. Does NOT touch the mongo lifecycle — caller manages init/close.
    """
    for i, entry in enumerate(entries):
        err = _validate_entry(entry, i)
        if err is not None:
            raise ValueError(err)

    keys = [e["key"] for e in entries]
    if len(keys) != len(set(keys)):
        dups = sorted({k for k in keys if keys.count(k) > 1})
        raise ValueError(f"duplicate keys: {dups}")

    await ensure_question_indexes()

    inserted = 0
    updated = 0
    for entry in entries:
        if "options" not in entry:
            entry["options"] = []
        was_inserted, was_updated = await upsert_question_by_key(entry)
        if was_inserted:
            inserted += 1
        elif was_updated:
            updated += 1

    return inserted, updated, len(entries)


async def seed_questions() -> int:
    """CLI entrypoint. Returns process exit code."""
    try:
        entries = load_seed_file(SEED_PATH)
    except ValueError as exc:
        print(f"[seed] {exc}", file=sys.stderr)
        return 2

    load_dotenv()
    await init_mongo()

    try:
        inserted, updated, total = await apply_questions_seed(entries)
    except ValueError as exc:
        print(f"[seed] validation failed: {exc}", file=sys.stderr)
        await close_mongo()
        return 2

    print(f"[seed] inserted: {inserted}, updated: {updated}, total: {total}")
    await close_mongo()
    return 0


def main() -> None:
    sys.exit(asyncio.run(seed_questions()))


if __name__ == "__main__":
    main()
