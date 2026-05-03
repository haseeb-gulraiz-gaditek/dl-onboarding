"""`user_tools` collection access layer.

Per spec-delta my-tools-explore-new-tabs F-TOOL-1.

One row per (user_id, tool_id). Idempotent inserts via the unique
compound index. Source precedence: explicit_save > manual_add >
auto_from_profile (auto never demotes a stronger source).
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.db.mongo import get_db


COLLECTION_NAME = "user_tools"

# Source precedence — higher wins. F-TOOL-3 / F-TOOL-7.
_SOURCE_RANK = {
    "auto_from_profile": 0,
    "manual_add": 1,
    "explicit_save": 2,
}


def user_tools_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    coll = user_tools_collection()
    await coll.create_index(
        [("user_id", ASCENDING), ("tool_id", ASCENDING)],
        unique=True,
        name="user_tools_user_tool_unique",
    )
    await coll.create_index(
        [("user_id", ASCENDING), ("last_updated_at", DESCENDING)],
        name="user_tools_user_updated",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def find(
    user_id: ObjectId, tool_id: ObjectId
) -> dict[str, Any] | None:
    return await user_tools_collection().find_one(
        {"user_id": user_id, "tool_id": tool_id}
    )


async def list_for_user(
    user_id: ObjectId, status: str | None = None
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"user_id": user_id}
    if status:
        query["status"] = status
    cursor = user_tools_collection().find(query).sort(
        [("last_updated_at", DESCENDING), ("_id", DESCENDING)]
    )
    return await cursor.to_list(length=None)


async def upsert_auto_from_profile(
    user_id: ObjectId, tool_id: ObjectId
) -> dict[str, Any]:
    """F-TOOL-7: insert as auto_from_profile/using if absent.
    On existing row with weaker source, just touches last_updated_at.
    On existing row with explicit_save/manual_add, NO-OP (returns
    the existing row unchanged)."""
    now = _now()
    coll = user_tools_collection()
    existing = await coll.find_one(
        {"user_id": user_id, "tool_id": tool_id}
    )
    if existing is None:
        doc = {
            "user_id": user_id,
            "tool_id": tool_id,
            "source": "auto_from_profile",
            "status": "using",
            "added_at": now,
            "last_updated_at": now,
        }
        result = await coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    existing_rank = _SOURCE_RANK.get(existing.get("source", ""), 0)
    if existing_rank > _SOURCE_RANK["auto_from_profile"]:
        # Stronger source already present; no demotion.
        return existing
    # Same source — just touch last_updated_at.
    await coll.update_one(
        {"_id": existing["_id"]},
        {"$set": {"last_updated_at": now}},
    )
    existing["last_updated_at"] = now
    return existing


async def upsert_explicit(
    user_id: ObjectId, tool_id: ObjectId, status: str
) -> tuple[dict[str, Any], bool]:
    """F-TOOL-3: explicit save. Returns (doc, was_inserted).

    On insert: source=explicit_save, status, added_at=last_updated_at=now.
    On existing row: source promoted to explicit_save, status updated,
    last_updated_at = now.
    """
    now = _now()
    coll = user_tools_collection()
    existing = await coll.find_one(
        {"user_id": user_id, "tool_id": tool_id}
    )
    if existing is None:
        doc = {
            "user_id": user_id,
            "tool_id": tool_id,
            "source": "explicit_save",
            "status": status,
            "added_at": now,
            "last_updated_at": now,
        }
        result = await coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc, True

    await coll.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "source": "explicit_save",
                "status": status,
                "last_updated_at": now,
            }
        },
    )
    existing["source"] = "explicit_save"
    existing["status"] = status
    existing["last_updated_at"] = now
    return existing, False


async def update_status(
    user_id: ObjectId, tool_id: ObjectId, status: str
) -> dict[str, Any] | None:
    """F-TOOL-5: flip status; preserve source. Returns updated doc
    or None if no row exists."""
    now = _now()
    coll = user_tools_collection()
    result = await coll.find_one_and_update(
        {"user_id": user_id, "tool_id": tool_id},
        {"$set": {"status": status, "last_updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    return result


async def delete(user_id: ObjectId, tool_id: ObjectId) -> bool:
    """F-TOOL-4: returns True if a row was removed, False if not present."""
    result = await user_tools_collection().delete_one(
        {"user_id": user_id, "tool_id": tool_id}
    )
    return result.deleted_count > 0
