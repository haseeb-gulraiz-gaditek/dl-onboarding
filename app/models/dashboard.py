"""Pydantic shapes for the founder dashboard + analytics endpoints.

Per spec-delta founder-dashboard-and-analytics F-DASH-2, F-DASH-3.

Anonymization invariant: NO field in this module names a user
identity (no user_id, email, display_name). Aggregate counts only.
"""
from datetime import datetime

from pydantic import BaseModel

from app.models.launch import VerificationStatus


class DashboardLaunchCard(BaseModel):
    """Inline-summary row for GET /api/founders/dashboard."""

    launch_id: str
    product_url: str
    approved_tool_slug: str | None
    verification_status: VerificationStatus
    created_at: datetime
    matched_count: int
    tell_me_more_count: int
    skip_count: int
    total_clicks: int


class DashboardResponse(BaseModel):
    dashboard: list[DashboardLaunchCard]


class LaunchAnalyticsResponse(BaseModel):
    """Per-launch detail view for GET /api/founders/launches/{id}/analytics."""

    launch_id: str
    approved_tool_slug: str | None
    verification_status: VerificationStatus
    matched_count: int
    tell_me_more_count: int
    skip_count: int
    total_clicks: int
    clicks_by_community: dict[str, int]
    clicks_by_surface: dict[str, int]
