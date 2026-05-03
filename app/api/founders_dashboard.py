"""Founder dashboard + per-launch analytics endpoints.

Per spec-delta founder-dashboard-and-analytics F-DASH-2, F-DASH-3.
"""
import asyncio
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import require_role
from app.db.launches import find_by_id, find_for_founder
from app.founders.analytics import (
    clicks_by_community,
    clicks_by_surface,
    matched_count,
    nudge_response_counts,
    total_clicks,
)
from app.models.dashboard import (
    DashboardLaunchCard,
    DashboardResponse,
    LaunchAnalyticsResponse,
)


router = APIRouter(prefix="/api/founders", tags=["founders_dashboard"])


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


async def _summary_for(launch_doc: dict[str, Any]) -> DashboardLaunchCard:
    """Run the four headline aggregations concurrently and project."""
    lid = launch_doc["_id"]
    matched, nudges, clicks = await asyncio.gather(
        matched_count(lid),
        nudge_response_counts(lid),
        total_clicks(lid),
    )
    return DashboardLaunchCard(
        launch_id=str(lid),
        product_url=launch_doc.get("product_url", ""),
        approved_tool_slug=launch_doc.get("approved_tool_slug"),
        verification_status=launch_doc["verification_status"],
        created_at=launch_doc["created_at"],
        matched_count=matched,
        tell_me_more_count=nudges.get("tell_me_more", 0),
        skip_count=nudges.get("skip", 0),
        total_clicks=clicks,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    user: dict[str, Any] = Depends(require_role("founder")),
) -> DashboardResponse:
    """F-DASH-2: own launches with inline summary metrics."""
    docs = await find_for_founder(user["_id"])
    cards = await asyncio.gather(*(_summary_for(d) for d in docs))
    return DashboardResponse(dashboard=list(cards))


@router.get(
    "/launches/{launch_id}/analytics",
    response_model=LaunchAnalyticsResponse,
)
async def launch_analytics(
    launch_id: str,
    user: dict[str, Any] = Depends(require_role("founder")),
) -> LaunchAnalyticsResponse:
    """F-DASH-3: per-launch detail. Ownership-gated 404 (no
    existence leak to non-owner founders)."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )
    launch = await find_by_id(oid)
    if launch is None or launch.get("founder_user_id") != user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )

    matched, nudges, clicks, by_community, by_surface = await asyncio.gather(
        matched_count(oid),
        nudge_response_counts(oid),
        total_clicks(oid),
        clicks_by_community(oid),
        clicks_by_surface(oid),
    )

    return LaunchAnalyticsResponse(
        launch_id=str(oid),
        approved_tool_slug=launch.get("approved_tool_slug"),
        verification_status=launch["verification_status"],
        matched_count=matched,
        tell_me_more_count=nudges.get("tell_me_more", 0),
        skip_count=nudges.get("skip", 0),
        total_clicks=clicks,
        clicks_by_community=by_community,
        clicks_by_surface=by_surface,
    )
