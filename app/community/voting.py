"""Shared vote application logic.

Per spec-delta communities-and-flat-comments F-COM-6, F-COM-7.

Three-way semantics on POST /api/votes:
  1. No existing vote → INSERT, target.vote_score += direction.
  2. Existing vote, same direction → DELETE (toggle off),
     target.vote_score -= direction.
  3. Existing vote, opposite direction → UPDATE,
     target.vote_score += 2 * direction (one swing of magnitude 2).

The target row's `vote_score` is denormalized:
  - posts.vote_score
  - comments.vote_score
  - tools_seed.vote_score (added by F-COM-7; missing field reads as 0)
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from app.db.comments import comments_collection, find_by_id as find_comment
from app.db.posts import find_by_id as find_post, posts_collection
from app.db.tools_seed import find_tool_by_slug, tools_seed_collection
from app.db.votes import (
    delete_vote,
    find_for_user_and_target,
    insert_vote,
    update_direction,
)


VALID_TARGET_TYPES = {"post", "comment", "tool"}


def _parse_object_id(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


async def _resolve_target(target_type: str, target_id_str: str) -> ObjectId | None:
    """Confirm the target exists and return its canonical ObjectId.
    Returns None if the target is unknown (caller maps to 400)."""
    oid = _parse_object_id(target_id_str)
    if oid is None:
        return None

    if target_type == "post":
        doc = await find_post(oid)
        return doc["_id"] if doc else None
    if target_type == "comment":
        doc = await find_comment(oid)
        return doc["_id"] if doc else None
    if target_type == "tool":
        doc = await tools_seed_collection().find_one({"_id": oid})
        if doc:
            return doc["_id"]
        # Fall through to founder-launched collection (cycle #15).
        from app.db.tools_founder_launched import (
            tools_founder_launched_collection,
        )
        doc = await tools_founder_launched_collection().find_one({"_id": oid})
        return doc["_id"] if doc else None
    return None


async def _bump_target_score(target_type: str, target_id: ObjectId, delta: int) -> None:
    if target_type == "post":
        await posts_collection().update_one(
            {"_id": target_id}, {"$inc": {"vote_score": delta}}
        )
    elif target_type == "comment":
        await comments_collection().update_one(
            {"_id": target_id}, {"$inc": {"vote_score": delta}}
        )
    elif target_type == "tool":
        # Update whichever collection holds the row (try seed first,
        # fall back to founder-launched). matched_count tells us
        # whether the update hit; if not, try the other collection.
        result = await tools_seed_collection().update_one(
            {"_id": target_id}, {"$inc": {"vote_score": delta}}
        )
        if result.matched_count == 0:
            from app.db.tools_founder_launched import (
                tools_founder_launched_collection,
            )
            await tools_founder_launched_collection().update_one(
                {"_id": target_id}, {"$inc": {"vote_score": delta}}
            )


async def apply_vote(
    *,
    user_id: ObjectId,
    target_type: str,
    target_id_str: str,
    direction: int,
) -> dict[str, Any] | None:
    """Apply the vote. Returns:
      None if target_type/target_id is invalid or target not found.
      {"voted": bool, "current_direction": int} otherwise.
    """
    if target_type not in VALID_TARGET_TYPES or direction not in (-1, 1):
        return None

    target_oid = await _resolve_target(target_type, target_id_str)
    if target_oid is None:
        return None

    existing = await find_for_user_and_target(user_id, target_type, target_oid)

    if existing is None:
        # Case 1: insert.
        await insert_vote(user_id, target_type, target_oid, direction)
        await _bump_target_score(target_type, target_oid, direction)
        return {"voted": True, "current_direction": direction}

    if existing["direction"] == direction:
        # Case 2: toggle off.
        await delete_vote(existing["_id"])
        await _bump_target_score(target_type, target_oid, -direction)
        return {"voted": False, "current_direction": 0}

    # Case 3: flip.
    await update_direction(existing["_id"], direction)
    await _bump_target_score(target_type, target_oid, 2 * direction)
    return {"voted": True, "current_direction": direction}
