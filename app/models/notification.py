"""Pydantic shapes for the inbox endpoints.

Per spec-delta notifications-in-app F-NOTIF-2..6.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationCard(BaseModel):
    """A single inbox row as seen by the requesting user.

    `read` is the projection of `read_at != null` — the timestamp
    itself is intentionally NOT shipped to clients (no need)."""

    id: str
    kind: str
    payload: dict[str, Any]
    read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationCard]
    next_before: datetime | None       # cursor on created_at; null on last page


class UnreadCountResponse(BaseModel):
    count: int


class BannerResponse(BaseModel):
    notification: NotificationCard | None


class MarkReadResponse(BaseModel):
    updated: bool


class MarkAllReadResponse(BaseModel):
    updated: int


def to_notification_card(doc: dict[str, Any]) -> NotificationCard:
    return NotificationCard(
        id=str(doc["_id"]),
        kind=doc["kind"],
        payload=doc.get("payload") or {},
        read=doc.get("read_at") is not None,
        created_at=doc["created_at"],
    )
