"""`profiles` collection access layer.

Per spec-delta question-bank-and-answer-capture F-QB-4 and F-QB-5.

One profile per user-role account, created lazily on first onboarding
endpoint hit. Founder accounts are structurally barred from having a
profile — the `get_or_create_profile` helper rejects them as a defense-
in-depth measure (the principle "Never let founder accounts post in
user communities" survives even if a future handler is misconfigured).

Constitutional invariant: `profiles.exportable` is always True. Opaque
data (vector embeddings, ML state) lives in other systems and is
referenced by id; the profile itself is JSON-exportable.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "profiles"


def profiles_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create indexes on the profiles collection. Idempotent."""
    await profiles_collection().create_index(
        [("user_id", ASCENDING)], unique=True, name="profiles_user_id_unique"
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_profile_doc(user_id: ObjectId) -> dict[str, Any]:
    """Default-value factory matching the F-QB-4 schema exactly."""
    now = _now()
    return {
        "user_id": user_id,
        "role": None,
        "current_tools": [],
        "workflows": [],
        "tools_tried_bounced": [],
        "counterfactual_wishes": [],
        "budget_tier": None,
        "embedding_vector_id": None,
        "last_recompute_at": None,
        "last_invalidated_at": now,
        "exportable": True,
        "created_at": now,
    }


async def get_or_create_profile(user: dict[str, Any]) -> dict[str, Any]:
    """Return the profile for this user, creating one if missing.

    Per F-QB-5: refuses to create profiles for founder accounts. Raises
    ValueError. This guard exists in addition to the require_role("user")
    middleware on the calling endpoints — even if a future handler is
    mounted without that dependency, this helper still refuses.
    """
    role_type = user.get("role_type")
    if role_type != "user":
        raise ValueError(
            f"profiles are user-role only; got role_type={role_type!r}"
        )
    user_id = user["_id"]
    existing = await profiles_collection().find_one({"user_id": user_id})
    if existing is not None:
        return existing
    doc = _new_profile_doc(user_id)
    await profiles_collection().insert_one(doc)
    return doc


async def find_profile_by_user_id(user_id: ObjectId) -> dict[str, Any] | None:
    return await profiles_collection().find_one({"user_id": user_id})


async def touch_invalidated(user_id: ObjectId) -> None:
    """Bump `last_invalidated_at` to now for the given user's profile.

    Called by POST /api/answers (F-QB-3) so downstream cycles
    (weaviate-pipeline #4) know the profile embedding is stale.
    """
    await profiles_collection().update_one(
        {"user_id": user_id}, {"$set": {"last_invalidated_at": _now()}}
    )
