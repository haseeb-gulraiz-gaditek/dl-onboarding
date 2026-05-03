"""GET /api/me/communities — list joined communities.

Per spec-delta frontend-core F-FE-2.

Used by the /home left rail and center "your communities" rows in
cycle #13's frontend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.middleware import require_role
from app.db.communities import find_by_id as find_community_by_id
from app.db.community_memberships import find_for_user_sorted
from app.models.community import (
    JoinedCommunityListResponse,
    to_joined_community_card,
)


router = APIRouter(prefix="/api/me/communities", tags=["me_communities"])


@router.get("", response_model=JoinedCommunityListResponse)
async def list_joined_communities(
    user: dict[str, Any] = Depends(require_role("user")),
) -> JoinedCommunityListResponse:
    """F-FE-2: own joined communities, joined_at DESC."""
    memberships = await find_for_user_sorted(user["_id"])
    cards = []
    for m in memberships:
        community = await find_community_by_id(m["community_id"])
        if community is None or not community.get("is_active", True):
            continue
        cards.append(to_joined_community_card(community, m["joined_at"]))
    return JoinedCommunityListResponse(communities=cards)
