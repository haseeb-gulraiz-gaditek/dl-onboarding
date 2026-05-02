"""`posts` collection access layer.

Per spec-delta communities-and-flat-comments F-COM-3, F-COM-4.

A post has one home `community_id` and may be cross-posted to up to
2 additional communities (total ≤3) via `cross_posted_to`. The post
is a single canonical row — votes/comments are not duplicated across
the cross-post fan-out.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "posts"


def posts_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    coll = posts_collection()
    await coll.create_index(
        [("community_id", ASCENDING), ("created_at", DESCENDING)],
        name="posts_community_created",
    )
    await coll.create_index(
        [("cross_posted_to", ASCENDING), ("created_at", DESCENDING)],
        name="posts_crosspost_created",
    )
    await coll.create_index(
        [("author_user_id", ASCENDING)], name="posts_author"
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert(
    *,
    community_id: ObjectId,
    cross_posted_to: list[ObjectId],
    author_user_id: ObjectId,
    title: str,
    body_md: str,
    attached_launch_id: ObjectId | None = None,
) -> dict[str, Any]:
    now = _now()
    doc = {
        "community_id": community_id,
        "cross_posted_to": cross_posted_to,
        "author_user_id": author_user_id,
        "title": title,
        "body_md": body_md,
        "attached_launch_id": attached_launch_id,
        "vote_score": 0,
        "comment_count": 0,
        "flagged": False,
        "flag_reasons": [],
        "created_at": now,
        "last_activity_at": now,
    }
    result = await posts_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_id(post_id: ObjectId) -> dict[str, Any] | None:
    return await posts_collection().find_one({"_id": post_id})


async def feed_for_community(
    community_id: ObjectId,
    before: datetime | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Newest-first feed including posts whose home is `community_id`
    OR who cross-posted INTO `community_id`."""
    query: dict[str, Any] = {
        "$or": [
            {"community_id": community_id},
            {"cross_posted_to": community_id},
        ],
    }
    if before is not None:
        query["created_at"] = {"$lt": before}
    # Secondary sort on _id DESC is a deterministic tie-breaker when
    # several posts share the same created_at (rapid bursts; tests).
    cursor = posts_collection().find(query).sort(
        [("created_at", DESCENDING), ("_id", DESCENDING)]
    ).limit(limit)
    return await cursor.to_list(length=limit)


async def bump_comment_count(post_id: ObjectId, delta: int) -> None:
    await posts_collection().update_one(
        {"_id": post_id},
        {
            "$inc": {"comment_count": delta},
            "$set": {"last_activity_at": _now()},
        },
    )


async def bump_vote_score(post_id: ObjectId, delta: int) -> None:
    await posts_collection().update_one(
        {"_id": post_id}, {"$inc": {"vote_score": delta}}
    )
