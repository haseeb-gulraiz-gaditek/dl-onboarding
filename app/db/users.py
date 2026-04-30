"""`users` collection access layer.

Encapsulates all reads and writes against the users collection so
the rest of the app cannot accidentally mutate role_type (F-AUTH-4).
The exposed update helpers do not accept a role_type parameter.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db
from app.models.user import RoleType


COLLECTION_NAME = "users"


def users_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Create the unique email index. Idempotent.

    Email is stored lowercased; the unique constraint enforces case-
    insensitive uniqueness at the storage layer.
    """
    await users_collection().create_index(
        [("email", ASCENDING)], unique=True, name="users_email_unique"
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert_user(
    *,
    email: str,
    password_hash: str,
    role_type: RoleType,
    display_name: str,
) -> dict[str, Any]:
    """Insert a new user row. Returns the inserted document.

    Caller is responsible for normalizing email (lowercased) before
    calling. The unique index on email rejects duplicates with a
    pymongo DuplicateKeyError, which the API layer translates to
    HTTP 409.
    """
    now = _now()
    doc: dict[str, Any] = {
        "email": email,
        "password_hash": password_hash,
        "role_type": role_type,
        "display_name": display_name,
        "created_at": now,
        "last_active_at": now,
    }
    result = await users_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_user_by_email(email: str) -> dict[str, Any] | None:
    return await users_collection().find_one({"email": email})


async def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await users_collection().find_one({"_id": oid})


async def touch_last_active(user_id: ObjectId) -> None:
    """Update last_active_at on the given user.

    NOTE: this is the ONLY field the auth flow updates after insert.
    There is intentionally no helper to update role_type — see
    F-AUTH-4 in spec-delta auth-role-split.
    """
    await users_collection().update_one(
        {"_id": user_id}, {"$set": {"last_active_at": _now()}}
    )
