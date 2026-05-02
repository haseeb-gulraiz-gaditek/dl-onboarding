"""`notifications` collection access layer.

Per spec-delta founder-launch-submission-and-verification F-LAUNCH-8.

Write-only in V1: cycle #8 writes launch_approved / launch_rejected
rows on admin resolution. Cycle #11 will add the read endpoint and
inbox UI.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "notifications"


def notifications_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    await notifications_collection().create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        name="notifications_user_created",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert(
    user_id: ObjectId, kind: str, payload: dict[str, Any]
) -> dict[str, Any]:
    doc = {
        "user_id": user_id,
        "kind": kind,
        "payload": payload,
        "read_at": None,
        "created_at": _now(),
    }
    result = await notifications_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
