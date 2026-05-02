"""`communities` collection access layer.

Per spec-delta communities-and-flat-comments F-COM-1.

Mesh-staff-spawned only in V1; user-created communities deferred.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "communities"


def communities_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    coll = communities_collection()
    await coll.create_index(
        [("slug", ASCENDING)], unique=True, name="communities_slug_unique"
    )
    await coll.create_index(
        [("is_active", ASCENDING), ("category", ASCENDING)],
        name="communities_active_category",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def find_by_slug(slug: str) -> dict[str, Any] | None:
    return await communities_collection().find_one({"slug": slug})


async def find_by_id(community_id: ObjectId) -> dict[str, Any] | None:
    return await communities_collection().find_one({"_id": community_id})


async def list_active() -> list[dict[str, Any]]:
    cursor = communities_collection().find(
        {"is_active": True}
    ).sort("name", ASCENDING)
    return await cursor.to_list(length=None)


async def bump_member_count(community_id: ObjectId, delta: int) -> None:
    """Atomic counter bump. Floors at 0 on decrement (uses two-step
    update to avoid going negative under concurrent leaves)."""
    if delta >= 0:
        await communities_collection().update_one(
            {"_id": community_id}, {"$inc": {"member_count": delta}}
        )
        return
    # Decrement: only if member_count > 0.
    await communities_collection().update_one(
        {"_id": community_id, "member_count": {"$gt": 0}},
        {"$inc": {"member_count": delta}},
    )


async def upsert_by_slug(entry: dict[str, Any]) -> tuple[bool, bool]:
    """Insert or update by slug. Returns (inserted, updated).

    Required keys: slug, name, description, category. Defaults
    applied on insert: is_active=True, mod_user_ids=[], member_count=0,
    created_at=now.
    """
    slug = entry["slug"]
    now = _now()
    set_fields: dict[str, Any] = {
        "name": entry["name"],
        "description": entry["description"],
        "category": entry["category"],
    }
    if "is_active" in entry:
        set_fields["is_active"] = entry["is_active"]
    set_on_insert: dict[str, Any] = {
        "slug": slug,
        "is_active": entry.get("is_active", True),
        "mod_user_ids": entry.get("mod_user_ids", []),
        "member_count": 0,
        "created_at": now,
    }
    # Don't double-write fields present in both.
    for key in list(set_on_insert.keys()):
        if key in set_fields:
            del set_on_insert[key]

    result = await communities_collection().update_one(
        {"slug": slug},
        {"$set": set_fields, "$setOnInsert": set_on_insert},
        upsert=True,
    )
    inserted = result.upserted_id is not None
    updated = (not inserted) and result.modified_count > 0
    return inserted, updated
