"""`answers` collection access layer.

Per spec-delta question-bank-and-answer-capture F-QB-3.

Answers is append-only: each tap produces one row, with a captured_at
timestamp. The most-recent answer for a (user, question) pair is the
"current" answer; older rows are preserved for audit and export.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "answers"


def answers_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create indexes on the answers collection. Idempotent."""
    # `user_id` lookups dominate (find all questions answered by a user).
    await answers_collection().create_index(
        [("user_id", ASCENDING)], name="answers_user_id"
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert_answer(
    *,
    user_id: ObjectId,
    question_id: ObjectId,
    value: Any,
    is_typed_other: bool = False,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "user_id": user_id,
        "question_id": question_id,
        "value": value,
        "is_typed_other": is_typed_other,
        "captured_at": _now(),
    }
    result = await answers_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def answered_question_ids(user_id: ObjectId) -> set[ObjectId]:
    """Return the set of question_ids the user has at least one answer for."""
    cursor = answers_collection().find(
        {"user_id": user_id}, {"question_id": 1}
    )
    return {row["question_id"] async for row in cursor}
