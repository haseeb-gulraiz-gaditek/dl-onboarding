"""/api/me/notifications endpoints (the inbox).

Per spec-delta notifications-in-app F-NOTIF-2..6.

Role-agnostic: any authenticated user reads their own notifications,
regardless of role_type. Founders see launch_*; users see
concierge_nudge / community_reply.
"""
from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.middleware import current_user
from app.db.notifications import (
    count_unread,
    find_latest_unread_banner,
    list_for_user,
    mark_all_read,
    mark_read,
)
from app.models.notification import (
    BannerResponse,
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListResponse,
    UnreadCountResponse,
    to_notification_card,
)


router = APIRouter(prefix="/api/me/notifications", tags=["notifications"])


MAX_LIMIT = 50
DEFAULT_LIMIT = 20


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(default=False),
    before: datetime | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    user: dict[str, Any] = Depends(current_user),
) -> NotificationListResponse:
    """F-NOTIF-2: paginated inbox; newest-first."""
    docs = await list_for_user(
        user_id=user["_id"],
        unread_only=unread_only,
        before=before,
        limit=limit,
    )
    cards = [to_notification_card(d) for d in docs]
    next_before = docs[-1]["created_at"] if len(docs) == limit else None
    return NotificationListResponse(notifications=cards, next_before=next_before)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user: dict[str, Any] = Depends(current_user),
) -> UnreadCountResponse:
    """F-NOTIF-3: bell badge count."""
    n = await count_unread(user["_id"])
    return UnreadCountResponse(count=n)


@router.get("/banner", response_model=BannerResponse)
async def banner(
    user: dict[str, Any] = Depends(current_user),
) -> BannerResponse:
    """F-NOTIF-4: most-recent unread concierge_nudge or null."""
    doc = await find_latest_unread_banner(user["_id"])
    if doc is None:
        return BannerResponse(notification=None)
    return BannerResponse(notification=to_notification_card(doc))


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_one_read(
    notification_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> MarkReadResponse:
    """F-NOTIF-5: idempotent single mark; 404 on non-owner."""
    oid = _parse_oid(notification_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "notification_not_found"},
        )
    outcome = await mark_read(user["_id"], oid)
    if outcome == "missing":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "notification_not_found"},
        )
    return MarkReadResponse(updated=(outcome == "updated"))


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_everything_read(
    user: dict[str, Any] = Depends(current_user),
) -> MarkAllReadResponse:
    """F-NOTIF-6: bulk mark unread → read."""
    n = await mark_all_read(user["_id"])
    return MarkAllReadResponse(updated=n)
