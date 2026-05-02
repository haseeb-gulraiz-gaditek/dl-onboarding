"""HMAC user-hash for unauthenticated redirects.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-3.

The /r/{launch_id} endpoint can't carry an Authorization header (it's
followed in the browser via plain navigation), so we encode the user
identity in a query param. HMAC-SHA256 keyed on JWT_SECRET, truncated
to 16 hex chars (64 bits) — enough collision-resistance for click
attribution; not crypto-grade for V1 (an attacker forging clicks
gains nothing meaningful).
"""
import hashlib
import hmac
import os
from typing import Iterable

from bson import ObjectId

from app.db.users import users_collection


HASH_LENGTH = 16  # hex chars (64 bits of HMAC)


def _secret() -> bytes:
    secret = os.environ.get("JWT_SECRET", "")
    return secret.encode("utf-8")


def make_user_hash(user_id: ObjectId | str) -> str:
    """Return a 16-hex-char HMAC of user_id keyed on JWT_SECRET."""
    payload = str(user_id).encode("utf-8")
    digest = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()
    return digest[:HASH_LENGTH]


async def resolve_user_hash(
    user_hash: str | None,
    candidate_ids: Iterable[ObjectId] | None = None,
) -> ObjectId | None:
    """Reverse-lookup a hash by scanning users.

    For V1 the user count is small enough that scanning the whole
    `users` collection on a redirect click is acceptable. If a
    `candidate_ids` shortlist is provided (e.g., users who were
    nudged for this launch), we scan only those for speed.

    Returns the matching user_id or None if no match (or input is
    missing/invalid).
    """
    if not user_hash or len(user_hash) != HASH_LENGTH:
        return None

    if candidate_ids is not None:
        for uid in candidate_ids:
            if make_user_hash(uid) == user_hash:
                return uid
        return None

    cursor = users_collection().find({}, {"_id": 1})
    async for row in cursor:
        if make_user_hash(row["_id"]) == user_hash:
            return row["_id"]
    return None
