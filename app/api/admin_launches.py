"""Admin-side launch verification endpoints.

Per spec-delta founder-launch-submission-and-verification
F-LAUNCH-3, F-LAUNCH-4, F-LAUNCH-5.
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.admin import require_admin
from app.db.launches import find_by_id, list_for_admin, update_resolution
from app.db.notifications import insert as insert_notification
from app.db.tools_founder_launched import insert as insert_fl_tool
from app.db.users import find_user_by_id
from app.launches.publish import publish_launch
from app.launches.slug import derive_tool_slug, find_available_slug
from app.models.launch import (
    LaunchAdminCard,
    LaunchAdminDetail,
    LaunchAdminListResponse,
    LaunchRejectRequest,
    LaunchResponse,
    to_launch_response,
)


router = APIRouter(prefix="/admin/launches", tags=["admin"])


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


async def _founder_email(founder_user_id: ObjectId) -> str:
    user = await find_user_by_id(str(founder_user_id))
    if user is None:
        return ""
    return user.get("email", "")


@router.get("", response_model=LaunchAdminListResponse)
async def admin_list(
    status_filter: str | None = Query(default="pending", alias="status"),
    _admin: dict[str, Any] = Depends(require_admin()),
) -> LaunchAdminListResponse:
    """F-LAUNCH-3: admin queue, defaults to pending."""
    docs = await list_for_admin(status=status_filter)
    cards: list[LaunchAdminCard] = []
    for d in docs:
        cards.append(
            LaunchAdminCard(
                id=str(d["_id"]),
                founder_email=await _founder_email(d["founder_user_id"]),
                product_url=d["product_url"],
                problem_statement=d["problem_statement"],
                verification_status=d["verification_status"],
                created_at=d["created_at"],
            )
        )
    return LaunchAdminListResponse(launches=cards)


@router.get("/{launch_id}", response_model=LaunchAdminDetail)
async def admin_detail(
    launch_id: str,
    _admin: dict[str, Any] = Depends(require_admin()),
) -> LaunchAdminDetail:
    """F-LAUNCH-3: full launch + founder email."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    doc = await find_by_id(oid)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    return LaunchAdminDetail(
        id=str(doc["_id"]),
        founder_email=await _founder_email(doc["founder_user_id"]),
        founder_user_id=str(doc["founder_user_id"]),
        product_url=doc["product_url"],
        problem_statement=doc["problem_statement"],
        icp_description=doc["icp_description"],
        existing_presence_links=doc.get("existing_presence_links") or [],
        target_community_slugs=doc.get("target_community_slugs") or [],
        verification_status=doc["verification_status"],
        rejection_comment=doc.get("rejection_comment"),
        reviewed_by=doc.get("reviewed_by"),
        reviewed_at=doc.get("reviewed_at"),
        approved_tool_slug=doc.get("approved_tool_slug"),
        created_at=doc["created_at"],
    )


def _resolved_409():
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"error": "launch_already_resolved"},
    )


@router.post("/{launch_id}/approve", response_model=LaunchResponse)
async def admin_approve(
    launch_id: str,
    admin: dict[str, Any] = Depends(require_admin()),
) -> LaunchResponse:
    """F-LAUNCH-4: derive slug, create founder-launched tool, mark
    launch approved, write notification."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    existing = await find_by_id(oid)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    if existing.get("verification_status") != "pending":
        raise _resolved_409()

    base_slug = derive_tool_slug(existing["product_url"])
    slug = await find_available_slug(base_slug)

    tagline = existing["problem_statement"][:100]
    description = (
        f"{existing['problem_statement']}\n\nIdeal customer: {existing['icp_description']}"
    )
    # Friendly name: capitalized first segment of slug.
    name = slug.split("-")[0].capitalize() if slug else "Launch"

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
        "reviewed_by": admin.get("email"),
    })

    updated = await update_resolution(
        launch_id=oid,
        status="approved",
        reviewed_by=admin.get("email", ""),
        approved_tool_slug=slug,
    )
    if updated is None:
        # Lost the race — someone else resolved between our check and
        # the find_one_and_update. Surface the same 409.
        raise _resolved_409()

    await insert_notification(
        user_id=existing["founder_user_id"],
        kind="launch_approved",
        payload={"launch_id": str(oid), "tool_slug": slug},
    )

    # F-PUB-2: synchronous publish (community posts + concierge nudges).
    publish_summary: dict[str, int] = {
        "community_posts_count": 0, "nudge_count": 0,
    }
    try:
        publish_summary = await publish_launch(
            launch_doc=updated, tool_slug=slug,
        )
    except Exception as exc:
        # Defensive: the orchestrator already swallows per-step
        # exceptions; an exception here means the orchestrator itself
        # blew up. Log and return the launch as approved anyway.
        print(f"[admin_launches] publish_launch raised: {exc}")

    return to_launch_response(updated, publish_summary=publish_summary)


@router.post("/{launch_id}/reject", response_model=LaunchResponse)
async def admin_reject(
    launch_id: str,
    payload: LaunchRejectRequest,
    admin: dict[str, Any] = Depends(require_admin()),
) -> LaunchResponse:
    """F-LAUNCH-5: store rejection comment + write notification."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    existing = await find_by_id(oid)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    if existing.get("verification_status") != "pending":
        raise _resolved_409()

    comment = payload.comment.strip()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "field_required", "field": "comment"},
        )

    updated = await update_resolution(
        launch_id=oid,
        status="rejected",
        reviewed_by=admin.get("email", ""),
        rejection_comment=comment,
    )
    if updated is None:
        raise _resolved_409()

    await insert_notification(
        user_id=existing["founder_user_id"],
        kind="launch_rejected",
        payload={"launch_id": str(oid), "comment": comment},
    )

    return to_launch_response(updated)
