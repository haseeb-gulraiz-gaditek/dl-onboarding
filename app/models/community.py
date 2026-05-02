"""Pydantic shapes for the communities endpoints.

Per spec-delta communities-and-flat-comments F-COM-1, F-COM-2.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


CommunityCategory = Literal["role", "stack", "outcome"]


class CommunityCard(BaseModel):
    """One community as it appears in lists and details."""

    id: str
    slug: str
    name: str
    description: str
    category: CommunityCategory
    member_count: int


class CommunityListResponse(BaseModel):
    communities: list[CommunityCard]


class CommunityDetailResponse(BaseModel):
    community: CommunityCard
    is_member: bool


class JoinResponse(BaseModel):
    joined: bool        # True if newly joined, False if already a member
    is_member: bool     # True after the call


class LeaveResponse(BaseModel):
    left: bool          # True if a row was removed, False if not a member
    is_member: bool     # False after the call


def to_community_card(doc: dict[str, Any]) -> CommunityCard:
    return CommunityCard(
        id=str(doc["_id"]),
        slug=doc["slug"],
        name=doc["name"],
        description=doc["description"],
        category=doc["category"],
        member_count=doc.get("member_count", 0),
    )
