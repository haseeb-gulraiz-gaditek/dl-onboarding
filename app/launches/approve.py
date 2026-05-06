"""Launch approval service.

Encapsulates the approval logic so callers can be:
  - the admin endpoint (POST /admin/launches/{id}/approve)
  - the auto-approver background task (test/demo only)

Returns the updated launch doc + publish summary, or raises a
small set of typed errors.
"""
from typing import Any

from bson import ObjectId

from app.db.launches import find_by_id, update_resolution
from app.db.notifications import insert as insert_notification
from app.db.tools_founder_launched import insert as insert_fl_tool
from app.launches.publish import publish_launch
from app.launches.slug import derive_tool_slug, find_available_slug


class LaunchNotFound(Exception):
    pass


class LaunchAlreadyResolved(Exception):
    pass


async def approve_launch(
    *,
    launch_id: ObjectId,
    reviewed_by: str,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Approve a pending launch. Returns (updated_launch_doc,
    publish_summary).

    Raises LaunchNotFound when the id doesn't resolve, or
    LaunchAlreadyResolved when status != 'pending'."""
    existing = await find_by_id(launch_id)
    if existing is None:
        raise LaunchNotFound(str(launch_id))
    if existing.get("verification_status") != "pending":
        raise LaunchAlreadyResolved(str(launch_id))

    base_slug = derive_tool_slug(existing["product_url"])
    slug = await find_available_slug(base_slug)

    tagline = existing["problem_statement"][:100]
    description = (
        f"{existing['problem_statement']}\n\n"
        f"Ideal customer: {existing['icp_description']}"
    )
    name = (
        " ".join(seg.capitalize() for seg in slug.split("-") if seg)
        if slug else "Launch"
    )

    await insert_fl_tool({
        "slug": slug,
        "name": name,
        "tagline": tagline,
        "description": description,
        "url": existing["product_url"],
        "pricing_summary": "Free",
        "category": "automation_agents",
        "labels": ["new"],
        "source": "founder_launch",
        "is_founder_launched": True,
        "launched_via_id": existing["_id"],
        "last_reviewed_at": existing.get("reviewed_at"),
        "reviewed_by": reviewed_by,
    })

    updated = await update_resolution(
        launch_id=launch_id,
        status="approved",
        reviewed_by=reviewed_by,
        approved_tool_slug=slug,
    )
    if updated is None:
        # Lost the race — somebody else resolved this launch between
        # our check and the find_one_and_update.
        raise LaunchAlreadyResolved(str(launch_id))

    await insert_notification(
        user_id=existing["founder_user_id"],
        kind="launch_approved",
        payload={"launch_id": str(launch_id), "tool_slug": slug},
    )

    publish_summary: dict[str, int] = {
        "community_posts_count": 0,
        "nudge_count": 0,
    }
    try:
        publish_summary = await publish_launch(
            launch_doc=updated, tool_slug=slug,
        )
    except Exception as exc:
        print(f"[approve_launch] publish_launch raised: {exc}")

    return updated, publish_summary
