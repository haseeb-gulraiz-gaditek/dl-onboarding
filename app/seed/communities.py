"""Communities seed loader.

Per spec-delta communities-and-flat-comments F-COM-9.

Loads `app/seed/communities.json` into the `communities` collection,
upsert-by-slug. Idempotent. Mirrors the catalog seeder's structure.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.db.communities import (
    ensure_indexes as ensure_community_indexes,
    upsert_by_slug,
)
from app.db.mongo import close_mongo, init_mongo


SEED_PATH = Path(__file__).parent / "communities.json"

_REQUIRED_FIELDS = {"slug", "name", "description", "category"}
_ALLOWED_CATEGORIES = {"role", "stack", "outcome"}
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_entry(entry: dict[str, Any], idx: int) -> str | None:
    if not isinstance(entry, dict):
        return f"entry [{idx}] is not an object"
    missing = _REQUIRED_FIELDS - set(entry.keys())
    if missing:
        return (
            f"entry [{idx}] (slug={entry.get('slug')!r}) "
            f"missing fields: {sorted(missing)}"
        )
    slug = entry["slug"]
    if not isinstance(slug, str) or not _SLUG_RE.match(slug):
        return (
            f"entry [{idx}] slug={slug!r} must be lowercase alphanumeric "
            f"with single hyphens"
        )
    if entry["category"] not in _ALLOWED_CATEGORIES:
        return (
            f"entry [{idx}] (slug={slug!r}) unknown category={entry['category']!r}"
        )
    for fld in ("name", "description"):
        val = entry[fld]
        if not isinstance(val, str) or not val.strip():
            return (
                f"entry [{idx}] (slug={slug!r}) {fld} must be a non-empty string"
            )
    return None


def load_communities_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"communities file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(entries, list):
        raise ValueError(f"{path}: root must be a JSON array")
    return entries


async def apply_communities_seed(
    entries: list[dict[str, Any]],
) -> tuple[int, int, int]:
    for i, entry in enumerate(entries):
        err = _validate_entry(entry, i)
        if err is not None:
            raise ValueError(err)
    slugs = [e["slug"] for e in entries]
    if len(slugs) != len(set(slugs)):
        dups = sorted({s for s in slugs if slugs.count(s) > 1})
        raise ValueError(f"duplicate slugs: {dups}")

    await ensure_community_indexes()

    inserted = 0
    updated = 0
    for entry in entries:
        was_inserted, was_updated = await upsert_by_slug(entry)
        if was_inserted:
            inserted += 1
        elif was_updated:
            updated += 1
    return inserted, updated, len(entries)


async def seed_communities() -> int:
    try:
        entries = load_communities_file(SEED_PATH)
    except ValueError as exc:
        print(f"[seed-communities] {exc}", file=sys.stderr)
        return 2

    load_dotenv()
    await init_mongo()

    try:
        inserted, updated, total = await apply_communities_seed(entries)
    except ValueError as exc:
        print(f"[seed-communities] validation failed: {exc}", file=sys.stderr)
        await close_mongo()
        return 2

    print(
        f"[seed-communities] inserted: {inserted}, updated: {updated}, total: {total}"
    )
    await close_mongo()
    return 0


def main() -> None:
    sys.exit(asyncio.run(seed_communities()))


if __name__ == "__main__":
    main()
