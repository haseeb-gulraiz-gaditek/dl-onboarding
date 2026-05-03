"""Pydantic shapes for the /api/me/tools endpoints.

Per spec-delta my-tools-explore-new-tabs F-TOOL-3..6.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.tool_card import ToolCardWithFlags


UserToolSource = Literal["auto_from_profile", "explicit_save", "manual_add"]
UserToolStatus = Literal["using", "saved"]


class UserToolSaveRequest(BaseModel):
    """POST /api/me/tools body."""

    tool_slug: str = Field(..., min_length=1)
    status: UserToolStatus = "saved"


class UserToolPatchRequest(BaseModel):
    """PATCH /api/me/tools/{tool_id} body."""

    status: UserToolStatus


class UserToolCard(BaseModel):
    """Hydrated row in GET /api/me/tools list / save responses."""

    id: str                         # user_tools._id
    tool: ToolCardWithFlags
    source: UserToolSource
    status: UserToolStatus
    added_at: datetime
    last_updated_at: datetime


class UserToolListResponse(BaseModel):
    tools: list[UserToolCard]


class DeleteToolResponse(BaseModel):
    deleted: bool


def to_user_tool_card(
    row: dict[str, Any], tool_card: ToolCardWithFlags
) -> UserToolCard:
    return UserToolCard(
        id=str(row["_id"]),
        tool=tool_card,
        source=row["source"],
        status=row["status"],
        added_at=row["added_at"],
        last_updated_at=row["last_updated_at"],
    )
