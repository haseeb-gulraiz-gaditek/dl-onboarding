"""Community endpoints.

Per spec-delta communities-and-flat-comments F-COM-1, F-COM-2.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import current_user, require_role
from app.db.communities import (
    bump_member_count,
    find_by_slug,
    list_active,
)
from app.db.community_memberships import add as add_membership, is_member, remove as remove_membership
from app.models.community import (
    CommunityDetailResponse,
    CommunityListResponse,
    JoinResponse,
    LeaveResponse,
    to_community_card,
)


router = APIRouter(prefix="/api/communities", tags=["communities"])


@router.get("", response_model=CommunityListResponse)
async def list_communities(
    _: dict[str, Any] = Depends(current_user),
) -> CommunityListResponse:
    """F-COM-1: list active communities, sorted by name. Open to any
    authenticated caller (user OR founder)."""
    docs = await list_active()
    return CommunityListResponse(
        communities=[to_community_card(d) for d in docs]
    )


@router.get("/{slug}", response_model=CommunityDetailResponse)
async def get_community(
    slug: str,
    user: dict[str, Any] = Depends(current_user),
) -> CommunityDetailResponse:
    """F-COM-1: community details + the requesting user's is_member flag.
    Open to any authenticated caller."""
    doc = await find_by_slug(slug)
    if doc is None or not doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "community_not_found"},
        )
    member = False
    if user.get("role_type") == "user":
        member = await is_member(user["_id"], doc["_id"])
    return CommunityDetailResponse(
        community=to_community_card(doc), is_member=member
    )


@router.post("/{slug}/join", response_model=JoinResponse)
async def join_community(
    slug: str,
    user: dict[str, Any] = Depends(require_role("user")),
) -> JoinResponse:
    """F-COM-2: idempotent join. Founders → 403 (constitutional)."""
    doc = await find_by_slug(slug)
    if doc is None or not doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "community_not_found"},
        )
    inserted = await add_membership(user["_id"], doc["_id"])
    if inserted:
        await bump_member_count(doc["_id"], 1)
    return JoinResponse(joined=inserted, is_member=True)


@router.post("/{slug}/leave", response_model=LeaveResponse)
async def leave_community(
    slug: str,
    user: dict[str, Any] = Depends(require_role("user")),
) -> LeaveResponse:
    """F-COM-2: idempotent leave."""
    doc = await find_by_slug(slug)
    if doc is None or not doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "community_not_found"},
        )
    removed = await remove_membership(user["_id"], doc["_id"])
    if removed:
        await bump_member_count(doc["_id"], -1)
    return LeaveResponse(left=removed, is_member=False)
