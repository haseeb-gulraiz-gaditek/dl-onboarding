"""Per-launch analytics aggregations over the engagements collection.

Per spec-delta founder-dashboard-and-analytics F-DASH-1, F-DASH-4.

All helpers are scoped by `launch_id` and use the existing
`(launch_id, captured_at DESC)` index. Empty results return the
type's zero (int(0) or {}).

Anonymization (constitutional): these helpers count, group by
surface, group by community_slug. They NEVER return user_ids,
emails, or display names.
"""
from typing import Any

from bson import ObjectId

from app.db.engagements import engagements_collection


async def matched_count(launch_id: ObjectId) -> int:
    """Count of distinct users who got a concierge_nudge VIEW (the
    publish-time scan from F-PUB-2 step 4). One per matched user."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {
            "launch_id": launch_id,
            "surface": "concierge_nudge",
            "action": "view",
            "user_id": {"$ne": None},
        }},
        {"$group": {"_id": "$user_id"}},
        {"$count": "n"},
    ]
    cursor = engagements_collection().aggregate(pipeline)
    docs = await cursor.to_list(length=1)
    return int(docs[0]["n"]) if docs else 0


async def nudge_response_counts(launch_id: ObjectId) -> dict[str, int]:
    """Distinct-user counts of tell_me_more and skip responses on
    concierge_nudge surface. Returns {tell_me_more: N, skip: M}
    (always both keys, defaulting to 0)."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {
            "launch_id": launch_id,
            "surface": "concierge_nudge",
            "action": {"$in": ["tell_me_more", "skip"]},
            "user_id": {"$ne": None},
        }},
        {"$group": {
            "_id": {"action": "$action", "user": "$user_id"},
        }},
        {"$group": {
            "_id": "$_id.action",
            "count": {"$sum": 1},
        }},
    ]
    cursor = engagements_collection().aggregate(pipeline)
    docs = await cursor.to_list(length=None)
    out: dict[str, int] = {"tell_me_more": 0, "skip": 0}
    for d in docs:
        out[d["_id"]] = int(d["count"])
    return out


async def total_clicks(launch_id: ObjectId) -> int:
    """Count of click engagements for this launch (any surface)."""
    return await engagements_collection().count_documents({
        "launch_id": launch_id, "action": "click",
    })


async def clicks_by_community(launch_id: ObjectId) -> dict[str, int]:
    """Group community_post click engagements by metadata.community_slug."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {
            "launch_id": launch_id,
            "surface": "community_post",
            "action": "click",
        }},
        {"$group": {
            "_id": "$metadata.community_slug",
            "count": {"$sum": 1},
        }},
    ]
    cursor = engagements_collection().aggregate(pipeline)
    docs = await cursor.to_list(length=None)
    out: dict[str, int] = {}
    for d in docs:
        slug = d.get("_id")
        if slug:  # skip nulls
            out[slug] = int(d["count"])
    return out


async def clicks_by_surface(launch_id: ObjectId) -> dict[str, int]:
    """Group click engagements by surface across all surfaces."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {
            "launch_id": launch_id, "action": "click",
        }},
        {"$group": {
            "_id": "$surface",
            "count": {"$sum": 1},
        }},
    ]
    cursor = engagements_collection().aggregate(pipeline)
    docs = await cursor.to_list(length=None)
    out: dict[str, int] = {}
    for d in docs:
        surface = d.get("_id")
        if surface:
            out[surface] = int(d["count"])
    return out
