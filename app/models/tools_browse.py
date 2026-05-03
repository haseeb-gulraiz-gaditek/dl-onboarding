"""Pydantic shapes for /api/tools (explore) and /api/launches (new).

Per spec-delta my-tools-explore-new-tabs F-TOOL-8, F-TOOL-9.
"""
from datetime import datetime

from pydantic import BaseModel

from app.models.tool_card import ToolCardWithFlags


class ToolsBrowseResponse(BaseModel):
    tools: list[ToolCardWithFlags]
    next_before: str | None        # cursor on `name`


class LaunchMeta(BaseModel):
    founder_display_name: str
    problem_statement: str
    approved_at: datetime | None


class BrowsedLaunchCard(BaseModel):
    tool: ToolCardWithFlags
    launch_meta: LaunchMeta
    in_my_communities: list[str]


class LaunchesBrowseResponse(BaseModel):
    launches: list[BrowsedLaunchCard]
    next_before: datetime | None
