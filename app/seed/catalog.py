"""Catalog seed loader.

Validates `app/seed/catalog.json` end-to-end then upserts every entry
into `tools_seed` keyed by `slug`. Idempotent.

Per spec-delta catalog-seed-and-curation F-CAT-3.

Public surface mirrors the question-bank seed loader so the pattern
is consistent:
  - load_catalog_file(path)      pure file-load + JSON parse
  - apply_catalog_seed(entries)  validate-then-upsert; raises on bad
                                 input; does NOT touch mongo lifecycle
  - seed_catalog()               CLI orchestrator (loads .env, owns
                                 mongo lifecycle); used by `python -m
                                 app.seed catalog`. Tests call the
                                 inner functions directly.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.db.mongo import close_mongo, init_mongo
from app.db.tools_seed import (
    ensure_indexes as ensure_tools_seed_indexes,
    upsert_tool_by_slug,
)


SEED_PATH = Path(__file__).parent / "catalog.json"

_REQUIRED_FIELDS = {
    "slug", "name", "tagline", "description", "url", "pricing_summary",
    "category", "labels",
}

_ALLOWED_CATEGORIES = {
    "productivity", "writing", "design", "engineering", "research_browsing",
    "meetings", "marketing", "sales", "analytics_data", "finance",
    "education", "creative_video", "automation_agents",
}

_ALLOWED_LABELS = {"new", "all_time_best", "gaining_traction"}

# slug must be lowercase alphanumerics separated by single hyphens
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_entry(entry: dict[str, Any], idx: int) -> str | None:
    """Return None if valid, else an error string."""
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

    labels = entry["labels"]
    if not isinstance(labels, list) or len(labels) == 0:
        return (
            f"entry [{idx}] (slug={slug!r}) labels must be a non-empty list"
        )
    bad_labels = [l for l in labels if l not in _ALLOWED_LABELS]
    if bad_labels:
        return (
            f"entry [{idx}] (slug={slug!r}) unknown labels: {sorted(set(bad_labels))}"
        )

    for fld in ("name", "tagline", "description", "pricing_summary"):
        val = entry[fld]
        if not isinstance(val, str) or not val.strip():
            return (
                f"entry [{idx}] (slug={slug!r}) {fld} must be a non-empty string"
            )

    url = entry["url"]
    if not isinstance(url, str) or not (
        url.startswith("http://") or url.startswith("https://")
    ):
        return f"entry [{idx}] (slug={slug!r}) url must be an http(s) URL"

    return None


def load_catalog_file(path: Path) -> list[dict[str, Any]]:
    """Read and parse a catalog JSON file. Raises ValueError on bad input."""
    if not path.exists():
        raise ValueError(f"catalog file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(entries, list):
        raise ValueError(f"{path}: root must be a JSON array")
    return entries


async def apply_catalog_seed(
    entries: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Validate then upsert. Returns (inserted, updated, total).

    Validates the WHOLE list before any DB write. Raises ValueError if
    any entry is invalid OR if there are duplicate slugs. Does NOT
    touch mongo lifecycle -- caller manages init/close.

    Defense-in-depth: per upsert_tool_by_slug, founder-launched rows
    (`source: "founder_launch"`) are never touched here.
    """
    for i, entry in enumerate(entries):
        err = _validate_entry(entry, i)
        if err is not None:
            raise ValueError(err)

    slugs = [e["slug"] for e in entries]
    if len(slugs) != len(set(slugs)):
        dups = sorted({s for s in slugs if slugs.count(s) > 1})
        raise ValueError(f"duplicate slugs: {dups}")

    await ensure_tools_seed_indexes()

    inserted = 0
    updated = 0
    for entry in entries:
        was_inserted, was_updated = await upsert_tool_by_slug(entry)
        if was_inserted:
            inserted += 1
        elif was_updated:
            updated += 1

    return inserted, updated, len(entries)


async def seed_catalog() -> int:
    """CLI entrypoint. Returns process exit code."""
    try:
        entries = load_catalog_file(SEED_PATH)
    except ValueError as exc:
        print(f"[seed] {exc}", file=sys.stderr)
        return 2

    load_dotenv()
    await init_mongo()

    try:
        inserted, updated, total = await apply_catalog_seed(entries)
    except ValueError as exc:
        print(f"[seed] validation failed: {exc}", file=sys.stderr)
        await close_mongo()
        return 2

    print(f"[seed] inserted: {inserted}, updated: {updated}, total: {total}")
    await close_mongo()
    return 0


def main() -> None:
    sys.exit(asyncio.run(seed_catalog()))


if __name__ == "__main__":
    main()
