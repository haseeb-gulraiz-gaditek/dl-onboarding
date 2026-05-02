"""`comments` collection access layer.

Per spec-delta communities-and-flat-comments F-COM-5.

Flat in V1 — `parent_comment_id` is reserved for V1.5 threading and
always stored as None regardless of client input.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "comments"


def comments_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    await comments_collection().create_index(
        [("post_id", ASCENDING), ("created_at", DESCENDING)],
        name="comments_post_created",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert(
    *,
    post_id: ObjectId,
    author_user_id: ObjectId,
    body_md: str,
) -> dict[str, Any]:
    """Insert a flat comment. parent_comment_id is forced to None."""
    doc = {
        "post_id": post_id,
        "parent_comment_id": None,
        "author_user_id": author_user_id,
        "body_md": body_md,
        "vote_score": 0,
        "flagged": False,
        "flag_reasons": [],
        "created_at": _now(),
    }
    result = await comments_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_id(comment_id: ObjectId) -> dict[str, Any] | None:
    return await comments_collection().find_one({"_id": comment_id})


async def for_post(post_id: ObjectId, limit: int = 200) -> list[dict[str, Any]]:
    # _id DESC tie-breaks bursts of comments inside the same microsecond.
    cursor = comments_collection().find(
        {"post_id": post_id}
    ).sort([("created_at", DESCENDING), ("_id", DESCENDING)]).limit(limit)
    return await cursor.to_list(length=limit)


async def bump_vote_score(comment_id: ObjectId, delta: int) -> None:
    await comments_collection().update_one(
        {"_id": comment_id}, {"$inc": {"vote_score": delta}}
    )
