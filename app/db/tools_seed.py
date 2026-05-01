"""`tools_seed` collection access layer (Mesh-curated tools).

Per spec-delta catalog-seed-and-curation F-CAT-1.

Founder-launched tools live in a SEPARATE `tools_founder_launched`
collection (created by cycle #8). The `upsert_tool_by_slug` helper
in this module refuses to touch any row whose `source` is
`"founder_launch"` -- defense-in-depth across the collection
boundary.
"""
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "tools_seed"


def tools_seed_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create indexes on tools_seed. Idempotent."""
    coll = tools_seed_collection()
    await coll.create_index(
        [("slug", ASCENDING)], unique=True, name="tools_seed_slug_unique"
    )
    await coll.create_index(
        [("curation_status", ASCENDING), ("category", ASCENDING)],
        name="tools_seed_status_category",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def upsert_tool_by_slug(entry: dict[str, Any]) -> tuple[bool, bool]:
    """Insert or update a tool keyed by slug, with founder-launched
    protection.

    Refuses to touch any row where `source == "founder_launch"` --
    such rows belong to `tools_founder_launched` (cycle #8) and only
    end up here through a bug. Returns (False, False) silently on
    such a collision -- caller cannot distinguish "skipped due to
    founder_launch" from "no change", which is fine for V1; if the
    loader needs to surface skipped slugs, the helper can return a
    third tuple element later.

    Defaults applied on insert:
      - `curation_status` -> "pending" if absent
      - `source` -> "manual" if absent
      - `created_at` -> now (only on insert; preserved on update)
      - `embedding_vector_id`, `last_reviewed_at`, `reviewed_by`,
        `rejection_comment` -> None
    """
    slug = entry["slug"]
    coll = tools_seed_collection()

    # Founder-launched protection: check existence first. We can't
    # express this as a single Mongo `update_one` with upsert because
    # a non-matching filter + upsert tries to INSERT, which collides
    # with the unique slug index when the founder row exists. The
    # check-then-upsert pattern is two round trips but exactly one
    # logical operation per call.
    existing = await coll.find_one({"slug": slug})
    if existing is not None and existing.get("source") == "founder_launch":
        return False, False

    update_set = {
        "name": entry["name"],
        "tagline": entry["tagline"],
        "description": entry["description"],
        "url": entry["url"],
        "pricing_summary": entry["pricing_summary"],
        "category": entry["category"],
        "labels": entry.get("labels", []),
    }
    insert_only = {
        "slug": slug,
        # Per cycle #4 spec-delta MODIFIED: seed default flips from
        # "pending" to "approved". Founder-launched tools (cycle #8)
        # still go through pending->approved review elsewhere.
        "curation_status": entry.get("curation_status", "approved"),
        "source": entry.get("source", "manual"),
        "created_at": _now(),
        "embedding": None,
        "last_reviewed_at": None,
        "reviewed_by": None,
        "rejection_comment": None,
    }

    result = await coll.update_one(
        {"slug": slug},
        {"$set": update_set, "$setOnInsert": insert_only},
        upsert=True,
    )
    inserted = result.upserted_id is not None
    updated = (not inserted) and result.modified_count > 0
    return inserted, updated


async def find_tool_by_slug(slug: str) -> dict[str, Any] | None:
    return await tools_seed_collection().find_one({"slug": slug})


async def list_tools_by_status(
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List tools, optionally filtered by curation_status. `status=None`
    or `status='all'` returns every entry.

    Sorted by category then name for predictable admin-UI ordering.
    """
    query: dict[str, Any] = {}
    if status and status != "all":
        query["curation_status"] = status
    cursor = tools_seed_collection().find(query).sort(
        [("category", ASCENDING), ("name", ASCENDING)]
    )
    return await cursor.to_list(length=None)


async def set_status(
    *,
    slug: str,
    status: str,
    reviewer_email: str,
    rejection_comment: str | None = None,
) -> dict[str, Any] | None:
    """Set curation_status + reviewer metadata on a tool.

    On approve: rejection_comment is cleared.
    On reject: rejection_comment is required.

    Returns the updated document, or None if the slug doesn't exist.
    """
    update_doc: dict[str, Any] = {
        "curation_status": status,
        "last_reviewed_at": _now(),
        "reviewed_by": reviewer_email,
        "rejection_comment": rejection_comment,
    }
    coll = tools_seed_collection()
    result = await coll.find_one_and_update(
        {"slug": slug},
        {"$set": update_doc},
        return_document=True,  # ReturnDocument.AFTER
    )
    return result
