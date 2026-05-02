"""`votes` collection access layer.

Per spec-delta communities-and-flat-comments F-COM-6.

target_type ∈ {"post", "comment", "tool"}. Unique compound index on
(user_id, target_type, target_id) enforces one vote per user per
target. Re-voting the same direction toggles OFF; opposite direction
flips the vote in place.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "votes"


def votes_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    await votes_collection().create_index(
        [
            ("user_id", ASCENDING),
            ("target_type", ASCENDING),
            ("target_id", ASCENDING),
        ],
        unique=True,
        name="votes_user_target_unique",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def find_for_user_and_target(
    user_id: ObjectId, target_type: str, target_id: ObjectId
) -> dict[str, Any] | None:
    return await votes_collection().find_one({
        "user_id": user_id,
        "target_type": target_type,
        "target_id": target_id,
    })


async def insert_vote(
    user_id: ObjectId, target_type: str, target_id: ObjectId, direction: int
) -> None:
    await votes_collection().insert_one({
        "user_id": user_id,
        "target_type": target_type,
        "target_id": target_id,
        "direction": direction,
        "cast_at": _now(),
    })


async def update_direction(vote_id: ObjectId, direction: int) -> None:
    await votes_collection().update_one(
        {"_id": vote_id},
        {"$set": {"direction": direction, "cast_at": _now()}},
    )


async def delete_vote(vote_id: ObjectId) -> None:
    await votes_collection().delete_one({"_id": vote_id})


async def find_user_votes_for_targets(
    user_id: ObjectId, target_type: str, target_ids: list[ObjectId]
) -> dict[ObjectId, int]:
    """Return a {target_id: direction} map for the user's votes on the
    given targets. Used to populate `user_vote` in feed/detail responses."""
    if not target_ids:
        return {}
    cursor = votes_collection().find({
        "user_id": user_id,
        "target_type": target_type,
        "target_id": {"$in": target_ids},
    })
    out: dict[ObjectId, int] = {}
    async for row in cursor:
        out[row["target_id"]] = row["direction"]
    return out
