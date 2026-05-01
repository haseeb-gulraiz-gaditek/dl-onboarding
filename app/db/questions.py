"""`questions` collection access layer.

Per spec-delta question-bank-and-answer-capture F-QB-1, F-QB-2.

Questions have a stable `key` for upsert by the seed loader, plus an
`order: int` field that determines the sequence in which they're shown
to users (V1: linear; `next_logic` branching deferred to V1.5+).
"""
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "questions"


def questions_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create indexes on the questions collection. Idempotent."""
    coll = questions_collection()
    # Stable key for seed upsert.
    await coll.create_index(
        [("key", ASCENDING)], unique=True, name="questions_key_unique"
    )
    # Sorted lookup of active questions in display order.
    await coll.create_index(
        [("is_core", ASCENDING), ("active", ASCENDING), ("order", ASCENDING)],
        name="questions_core_active_order",
    )


async def find_active_core_questions_in_order() -> list[dict[str, Any]]:
    cursor = questions_collection().find(
        {"is_core": True, "active": True}
    ).sort("order", ASCENDING)
    return await cursor.to_list(length=None)


async def find_question_by_id(question_id: str) -> dict[str, Any] | None:
    try:
        oid = ObjectId(question_id)
    except Exception:
        return None
    return await questions_collection().find_one({"_id": oid})


async def upsert_question_by_key(doc: dict[str, Any]) -> tuple[bool, bool]:
    """Insert or update a question keyed by its stable `key`.

    Returns (inserted, updated).
    """
    key = doc["key"]
    result = await questions_collection().update_one(
        {"key": key},
        {"$set": doc},
        upsert=True,
    )
    inserted = result.upserted_id is not None
    updated = (not inserted) and result.modified_count > 0
    return inserted, updated
