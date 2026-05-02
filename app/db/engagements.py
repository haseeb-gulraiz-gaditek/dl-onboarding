"""`engagements` collection access layer.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-1.

Per-event log for clicks / dwell / skip / tell_me_more / view across
launch surfaces. Write-only in V1 (no GET endpoint exposes it).
CPA-ready schema for V1.5 billing.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "engagements"


def engagements_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    coll = engagements_collection()
    await coll.create_index(
        [("launch_id", ASCENDING), ("captured_at", DESCENDING)],
        name="engagements_launch_captured",
    )
    await coll.create_index(
        [("user_id", ASCENDING), ("captured_at", DESCENDING)],
        name="engagements_user_captured",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert(
    *,
    launch_id: ObjectId,
    surface: str,
    action: str,
    user_id: ObjectId | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc = {
        "user_id": user_id,
        "launch_id": launch_id,
        "surface": surface,
        "action": action,
        "metadata": metadata or {},
        "captured_at": _now(),
    }
    result = await engagements_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
