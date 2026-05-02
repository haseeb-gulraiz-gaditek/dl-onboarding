"""`launches` collection access layer.

Per spec-delta founder-launch-submission-and-verification F-LAUNCH-1..5.

Append-only from the founder's perspective: rejected launches stay
as historical record; founder must POST a new submission to retry.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.db.mongo import get_db


COLLECTION_NAME = "launches"


def launches_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    coll = launches_collection()
    await coll.create_index(
        [("founder_user_id", ASCENDING)], name="launches_founder"
    )
    await coll.create_index(
        [("verification_status", ASCENDING), ("created_at", ASCENDING)],
        name="launches_status_created",
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert(
    *,
    founder_user_id: ObjectId,
    product_url: str,
    problem_statement: str,
    icp_description: str,
    existing_presence_links: list[str],
) -> dict[str, Any]:
    doc = {
        "founder_user_id": founder_user_id,
        "product_url": product_url,
        "problem_statement": problem_statement,
        "icp_description": icp_description,
        "existing_presence_links": existing_presence_links,
        "verification_status": "pending",
        "rejection_comment": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "approved_tool_slug": None,
        "created_at": _now(),
    }
    result = await launches_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_id(launch_id: ObjectId) -> dict[str, Any] | None:
    return await launches_collection().find_one({"_id": launch_id})


async def find_for_founder(
    founder_user_id: ObjectId, status: str | None = None
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"founder_user_id": founder_user_id}
    if status:
        query["verification_status"] = status
    cursor = launches_collection().find(query).sort(
        [("created_at", DESCENDING), ("_id", DESCENDING)]
    )
    return await cursor.to_list(length=None)


async def list_for_admin(status: str | None = "pending") -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if status:
        query["verification_status"] = status
    # Oldest pending first — admin works queue head-first.
    cursor = launches_collection().find(query).sort(
        [("created_at", ASCENDING), ("_id", ASCENDING)]
    )
    return await cursor.to_list(length=None)


async def update_resolution(
    *,
    launch_id: ObjectId,
    status: str,
    reviewed_by: str,
    rejection_comment: str | None = None,
    approved_tool_slug: str | None = None,
) -> dict[str, Any] | None:
    """Resolve a pending launch. Returns the updated document, or None
    if the row doesn't exist OR is no longer pending.
    Concurrency-safe via filter on verification_status="pending"."""
    update_fields: dict[str, Any] = {
        "verification_status": status,
        "reviewed_by": reviewed_by,
        "reviewed_at": _now(),
    }
    if rejection_comment is not None:
        update_fields["rejection_comment"] = rejection_comment
    if approved_tool_slug is not None:
        update_fields["approved_tool_slug"] = approved_tool_slug

    result = await launches_collection().find_one_and_update(
        {"_id": launch_id, "verification_status": "pending"},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    return result
