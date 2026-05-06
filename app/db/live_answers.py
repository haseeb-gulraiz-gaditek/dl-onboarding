"""`live_answers` collection access layer.

Per spec-delta `live-narrowing-onboarding` F-LIVE-2 step 1.

Separate collection from `answers` so the existing classic-flow
question-bank schema (which requires a real `question_id` ObjectId
pointing at the seeded `questions` collection) stays intact. Live
questions are code-only constants in `app/onboarding/live_questions`,
so they don't have a seeded ObjectId to reference.

Schema (one row per (user_id, q_index) — upsert semantics):
    {
        "_id": ObjectId,
        "user_id": ObjectId,
        "q_index": int,            # 1..4
        "value": Any,              # role-agnostic answer payload
        "updated_at": datetime,
        "created_at": datetime,
    }
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "live_answers"


def live_answers_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """One row per (user, q_index). Idempotent."""
    await live_answers_collection().create_index(
        [("user_id", ASCENDING), ("q_index", ASCENDING)],
        name="live_answers_user_q",
        unique=True,
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def upsert_live_answer(
    *,
    user_id: ObjectId,
    q_index: int,
    value: Any,
) -> dict[str, Any]:
    """Upsert one row per (user_id, q_index). Replaces the previous
    answer to the same step (live flow is overwriting, not append-
    only — there's no audit need for sub-Q1 revisions during a single
    onboarding session)."""
    now = _now()
    await live_answers_collection().update_one(
        {"user_id": user_id, "q_index": q_index},
        {
            "$set": {"value": value, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    doc = await live_answers_collection().find_one(
        {"user_id": user_id, "q_index": q_index}
    )
    return doc or {}


async def get_user_live_answers(user_id: ObjectId) -> dict[int, Any]:
    """Return {q_index: value} for the user's live answers so far."""
    cursor = live_answers_collection().find({"user_id": user_id})
    out: dict[int, Any] = {}
    async for row in cursor:
        out[row["q_index"]] = row.get("value")
    return out
