"""Pydantic shapes for the founder-launch endpoints.

Per spec-delta founder-launch-submission-and-verification
F-LAUNCH-1..5.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal["pending", "approved", "rejected"]


class LaunchSubmitRequest(BaseModel):
    """POST /api/founders/launch body."""

    product_url: str = Field(..., min_length=1)
    problem_statement: str = Field(..., min_length=1, max_length=280)
    icp_description: str = Field(..., min_length=1, max_length=500)
    existing_presence_links: list[str] = Field(default_factory=list, max_length=6)
    target_community_slugs: list[str] = Field(..., min_length=1, max_length=6)


class LaunchRejectRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=500)


class LaunchResponse(BaseModel):
    """Founder-facing launch view."""

    id: str
    product_url: str
    problem_statement: str
    icp_description: str
    existing_presence_links: list[str]
    target_community_slugs: list[str]
    verification_status: VerificationStatus
    rejection_comment: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    approved_tool_slug: str | None
    created_at: datetime
    publish_summary: dict | None = None  # populated only on the approve response


class LaunchListResponse(BaseModel):
    launches: list[LaunchResponse]


class LaunchAdminCard(BaseModel):
    """Admin queue list item — joined with founder email."""

    id: str
    founder_email: str
    product_url: str
    problem_statement: str
    verification_status: VerificationStatus
    created_at: datetime


class LaunchAdminListResponse(BaseModel):
    launches: list[LaunchAdminCard]


class LaunchAdminDetail(BaseModel):
    """Admin detail — full launch + founder email."""

    id: str
    founder_email: str
    founder_user_id: str
    product_url: str
    problem_statement: str
    icp_description: str
    existing_presence_links: list[str]
    target_community_slugs: list[str]
    verification_status: VerificationStatus
    rejection_comment: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    approved_tool_slug: str | None
    created_at: datetime


def to_launch_response(
    doc: dict[str, Any], publish_summary: dict | None = None
) -> LaunchResponse:
    return LaunchResponse(
        id=str(doc["_id"]),
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
        publish_summary=publish_summary,
    )
