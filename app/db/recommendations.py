"""`recommendations` collection access layer.

Per spec-delta recommendation-engine F-REC-3, F-REC-6.

One row per user. The cache is invalidated when:
  - cache_expires_at <= now (TTL expired), OR
  - profile.last_invalidated_at > rec.generated_at (profile mutated
    since the rec was generated -- cycle #2's invalidation contract).
"""
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "recommendations"


def recommendations_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create indexes. Idempotent."""
    await recommendations_collection().create_index(
        [("user_id", ASCENDING)], unique=True, name="recs_user_id_unique"
    )


async def find_for_user(user_id) -> dict[str, Any] | None:
    return await recommendations_collection().find_one({"user_id": user_id})


async def upsert_for_user(user_id, doc: dict[str, Any]) -> None:
    """Replace the user's rec doc entirely (if it exists), else insert."""
    await recommendations_collection().replace_one(
        {"user_id": user_id},
        doc,
        upsert=True,
    )


async def is_cache_valid(rec_doc: dict[str, Any], profile_doc: dict[str, Any] | None) -> bool:
    """Cache is valid iff TTL has not elapsed AND the profile has not
    been invalidated since the rec was generated."""
    now = datetime.now(timezone.utc)
    expires_at = rec_doc.get("cache_expires_at")
    if expires_at is None or expires_at <= now:
        return False

    if profile_doc is None:
        return True

    invalidated_at = profile_doc.get("last_invalidated_at")
    generated_at = rec_doc.get("generated_at")
    if invalidated_at is None or generated_at is None:
        return True
    return invalidated_at <= generated_at
