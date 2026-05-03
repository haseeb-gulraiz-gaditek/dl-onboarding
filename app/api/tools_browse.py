"""/api/tools (the /tools/explore backing).

Per spec-delta my-tools-explore-new-tabs F-TOOL-8.

Reads tools_seed ONLY — constitutional separation: organic catalog
only. Founder-launched browsing happens via /api/launches (F-TOOL-9).
"""
import re
from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.auth.middleware import require_role
from app.db.tools_seed import tools_seed_collection
from app.models.tool_card import to_tool_card_with_flags
from app.models.tools_browse import ToolsBrowseResponse
from pymongo import ASCENDING


router = APIRouter(prefix="/api/tools", tags=["tools_browse"])


MAX_LIMIT = 50
DEFAULT_LIMIT = 20


@router.get("", response_model=ToolsBrowseResponse)
async def list_catalog(
    category: str | None = Query(default=None),
    label: str | None = Query(default=None),
    q: str | None = Query(default=None),
    before: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    _user: dict[str, Any] = Depends(require_role("user")),
) -> ToolsBrowseResponse:
    """F-TOOL-8: alphabetical browse with cursor + filters."""
    query: dict[str, Any] = {"curation_status": "approved"}

    if category:
        query["category"] = category
    if label:
        query["labels"] = label  # array membership
    if q:
        # Case-insensitive substring on name OR tagline.
        pattern = re.escape(q)
        query["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"tagline": {"$regex": pattern, "$options": "i"}},
        ]
    if before:
        # Cursor on `name`. Combine with q's $or via $and.
        cursor_clause = {"name": {"$gt": before}}
        if "$or" in query:
            existing_or = query.pop("$or")
            query["$and"] = [{"$or": existing_or}, cursor_clause]
        else:
            query["name"] = {"$gt": before}

    cursor = tools_seed_collection().find(query).sort(
        [("name", ASCENDING), ("_id", ASCENDING)]
    ).limit(limit)
    docs = await cursor.to_list(length=limit)

    tools = [to_tool_card_with_flags(d, is_founder_launched=False) for d in docs]
    next_before = docs[-1]["name"] if len(docs) == limit else None
    return ToolsBrowseResponse(tools=tools, next_before=next_before)
