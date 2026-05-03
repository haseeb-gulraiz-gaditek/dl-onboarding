"""`community_memberships` collection access layer.

Per spec-delta communities-and-flat-comments F-COM-2.

One row per (user_id, community_id). Idempotent join/leave.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "community_memberships"


def community_memberships_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    await community_memberships_collection().create_index(
        [("user_id", ASCENDING), ("community_id", ASCENDING)],
        unique=True,
        name="memberships_user_community_unique",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def is_member(user_id: ObjectId, community_id: ObjectId) -> bool:
    doc = await community_memberships_collection().find_one(
        {"user_id": user_id, "community_id": community_id},
        {"_id": 1},
    )
    return doc is not None


async def add(
    user_id: ObjectId,
    community_id: ObjectId,
    joined_via: str = "manual",
) -> bool:
    """Insert membership; returns True if inserted, False if it already
    existed. Caller is responsible for bumping community.member_count
    only when this returns True.

    Check-then-insert (rather than insert + catch DuplicateKeyError)
    because mongomock-motor's compound-unique index enforcement is
    inconsistent. Production race window between check and insert is
    closed by the unique index; this helper trusts the index to be
    the final guarantee.
    """
    coll = community_memberships_collection()
    existing = await coll.find_one(
        {"user_id": user_id, "community_id": community_id}, {"_id": 1}
    )
    if existing is not None:
        return False
    try:
        await coll.insert_one({
            "user_id": user_id,
            "community_id": community_id,
            "joined_at": _now(),
            "joined_via": joined_via,
        })
        return True
    except Exception:
        # Lost the race in production — index caught it.
        return False


async def remove(user_id: ObjectId, community_id: ObjectId) -> bool:
    """Delete membership; returns True if a row was removed."""
    result = await community_memberships_collection().delete_one(
        {"user_id": user_id, "community_id": community_id}
    )
    return result.deleted_count > 0


async def find_for_user(user_id: ObjectId) -> list[dict[str, Any]]:
    cursor = community_memberships_collection().find({"user_id": user_id})
    return await cursor.to_list(length=None)


async def find_for_user_sorted(user_id: ObjectId) -> list[dict[str, Any]]:
    """F-FE-2: list memberships newest-first by joined_at for the
    /api/me/communities endpoint."""
    from pymongo import DESCENDING

    cursor = community_memberships_collection().find(
        {"user_id": user_id}
    ).sort([("joined_at", DESCENDING), ("_id", DESCENDING)])
    return await cursor.to_list(length=None)
