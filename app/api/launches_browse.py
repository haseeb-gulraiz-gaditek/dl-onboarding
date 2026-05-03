"""/api/launches (the /tools/new backing).

Per spec-delta my-tools-explore-new-tabs F-TOOL-9.

Reads tools_founder_launched joined with launches. Default filter:
only launches whose target_community_slugs intersect the user's
joined community slugs. ?all=true removes the filter.
"""
from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, Query

from app.auth.middleware import require_role
from app.db.communities import find_by_id as find_community_by_id
from app.db.community_memberships import find_for_user as memberships_for_user
from app.db.launches import launches_collection
from app.db.tools_founder_launched import find_by_slug as fl_find_by_slug
from app.db.users import find_user_by_id
from app.models.tool_card import to_tool_card_with_flags
from app.models.tools_browse import (
    BrowsedLaunchCard,
    LaunchesBrowseResponse,
    LaunchMeta,
)
from pymongo import ASCENDING, DESCENDING


router = APIRouter(prefix="/api/launches", tags=["launches_browse"])


MAX_LIMIT = 50
DEFAULT_LIMIT = 20


async def _user_community_slugs(user_id: ObjectId) -> set[str]:
    """Resolve the user's joined community slugs."""
    memberships = await memberships_for_user(user_id)
    slugs: set[str] = set()
    for m in memberships:
        community = await find_community_by_id(m["community_id"])
        if community is not None:
            slugs.add(community["slug"])
    return slugs


@router.get("", response_model=LaunchesBrowseResponse)
async def list_launches(
    all_: bool = Query(default=False, alias="all"),
    before: datetime | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    user: dict[str, Any] = Depends(require_role("user")),
) -> LaunchesBrowseResponse:
    """F-TOOL-9: newest-first launches, default-filtered to joined
    communities; ?all=true escape hatch."""
    my_slugs = await _user_community_slugs(user["_id"])

    query: dict[str, Any] = {"verification_status": "approved"}
    if not all_ and my_slugs:
        query["target_community_slugs"] = {"$in": list(my_slugs)}
    elif not all_ and not my_slugs:
        # User has zero memberships AND not asking for all → empty list.
        return LaunchesBrowseResponse(launches=[], next_before=None)

    if before is not None:
        query["reviewed_at"] = {"$lt": before}

    cursor = launches_collection().find(query).sort(
        [("reviewed_at", DESCENDING), ("_id", DESCENDING)]
    ).limit(limit)
    launch_docs = await cursor.to_list(length=limit)

    cards: list[BrowsedLaunchCard] = []
    for launch in launch_docs:
        slug = launch.get("approved_tool_slug")
        if not slug:
            continue
        tool_doc = await fl_find_by_slug(slug)
        if tool_doc is None or tool_doc.get("curation_status") != "approved":
            continue

        founder = await find_user_by_id(str(launch["founder_user_id"]))
        intersection = sorted(
            my_slugs.intersection(launch.get("target_community_slugs") or [])
        )
        cards.append(BrowsedLaunchCard(
            tool=to_tool_card_with_flags(tool_doc, is_founder_launched=True),
            launch_meta=LaunchMeta(
                founder_display_name=(
                    founder.get("display_name", "") if founder else ""
                ),
                problem_statement=launch.get("problem_statement", ""),
                approved_at=launch.get("reviewed_at"),
            ),
            in_my_communities=intersection,
        ))

    next_before = launch_docs[-1]["reviewed_at"] if len(launch_docs) == limit else None
    return LaunchesBrowseResponse(launches=cards, next_before=next_before)
