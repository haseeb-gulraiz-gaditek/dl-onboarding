"""`notifications` collection access layer.

Per spec-delta founder-launch-submission-and-verification F-LAUNCH-8
(write helpers) and notifications-in-app F-NOTIF-2..6 (read helpers).

Cycle #8 wrote launch_approved/launch_rejected. Cycle #9 wrote
concierge_nudge. Cycle #12 added community_reply (write trigger
inside POST /api/comments) plus the read surface in
app/api/me_notifications.py.
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


# ---- Read helpers (F-NOTIF-2..6) ----


async def find_by_id(notification_id: ObjectId) -> dict[str, Any] | None:
    return await notifications_collection().find_one({"_id": notification_id})


async def list_for_user(
    user_id: ObjectId,
    unread_only: bool = False,
    before: datetime | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """F-NOTIF-2: newest-first list with cursor pagination on
    created_at; _id DESC tie-breaker for consistency under bursts."""
    query: dict[str, Any] = {"user_id": user_id}
    if unread_only:
        query["read_at"] = None
    if before is not None:
        query["created_at"] = {"$lt": before}
    cursor = notifications_collection().find(query).sort(
        [("created_at", DESCENDING), ("_id", DESCENDING)]
    ).limit(limit)
    return await cursor.to_list(length=limit)


async def count_unread(user_id: ObjectId) -> int:
    """F-NOTIF-3: bell badge count."""
    return await notifications_collection().count_documents({
        "user_id": user_id,
        "read_at": None,
    })


async def find_latest_unread_banner(
    user_id: ObjectId,
) -> dict[str, Any] | None:
    """F-NOTIF-4: most-recent unread concierge_nudge for the banner."""
    cursor = notifications_collection().find({
        "user_id": user_id,
        "kind": "concierge_nudge",
        "read_at": None,
    }).sort([("created_at", DESCENDING), ("_id", DESCENDING)]).limit(1)
    docs = await cursor.to_list(length=1)
    return docs[0] if docs else None


async def mark_read(
    user_id: ObjectId, notification_id: ObjectId
) -> str:
    """F-NOTIF-5: mark a single notification read.

    Returns one of:
      - "updated" — row was unread, now marked read
      - "noop"    — row was already read
      - "missing" — row doesn't exist OR belongs to another user
    """
    coll = notifications_collection()
    existing = await coll.find_one(
        {"_id": notification_id, "user_id": user_id}
    )
    if existing is None:
        return "missing"
    if existing.get("read_at") is not None:
        return "noop"
    await coll.update_one(
        {"_id": notification_id, "user_id": user_id, "read_at": None},
        {"$set": {"read_at": _now()}},
    )
    return "updated"


async def mark_all_read(user_id: ObjectId) -> int:
    """F-NOTIF-6: bulk mark unread → read. Returns count updated."""
    result = await notifications_collection().update_many(
        {"user_id": user_id, "read_at": None},
        {"$set": {"read_at": _now()}},
    )
    return result.modified_count
