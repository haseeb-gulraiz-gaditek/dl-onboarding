"""/api/me/tools endpoints (the /tools/mine backing).

Per spec-delta my-tools-explore-new-tabs F-TOOL-3..6.
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.middleware import require_role
from app.db.user_tools import (
    delete as ut_delete,
    list_for_user,
    update_status,
    upsert_explicit,
)
from app.models.tool_card import to_tool_card_with_flags
from app.models.user_tool import (
    DeleteToolResponse,
    UserToolCard,
    UserToolListResponse,
    UserToolPatchRequest,
    UserToolSaveRequest,
    to_user_tool_card,
)
from app.tools_resolver import find_tool_anywhere


router = APIRouter(prefix="/api/me/tools", tags=["me_tools"])


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


@router.post("", response_model=UserToolCard)
async def save_tool(
    payload: UserToolSaveRequest,
    user: dict[str, Any] = Depends(require_role("user")),
):
    """F-TOOL-3: explicit save. Returns 201 on insert, 200 on update."""
    tool_doc, is_fl = await find_tool_anywhere(payload.tool_slug)
    if tool_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )

    row, was_inserted = await upsert_explicit(
        user_id=user["_id"],
        tool_id=tool_doc["_id"],
        status=payload.status,
    )
    card = to_tool_card_with_flags(tool_doc, is_fl)
    response = to_user_tool_card(row, card)
    return response


@router.delete("/{tool_id}", response_model=DeleteToolResponse)
async def unsave_tool(
    tool_id: str,
    user: dict[str, Any] = Depends(require_role("user")),
) -> DeleteToolResponse:
    """F-TOOL-4: idempotent unbookmark."""
    oid = _parse_oid(tool_id)
    if oid is None:
        return DeleteToolResponse(deleted=False)
    deleted = await ut_delete(user_id=user["_id"], tool_id=oid)
    return DeleteToolResponse(deleted=deleted)


@router.patch("/{tool_id}", response_model=UserToolCard)
async def patch_status(
    tool_id: str,
    payload: UserToolPatchRequest,
    user: dict[str, Any] = Depends(require_role("user")),
):
    """F-TOOL-5: flip status; preserve source."""
    oid = _parse_oid(tool_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_in_mine"},
        )
    updated = await update_status(
        user_id=user["_id"], tool_id=oid, status=payload.status
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_in_mine"},
        )
    tool_doc, is_fl = await find_tool_anywhere(oid)
    if tool_doc is None:
        # Orphaned row — shouldn't happen given the row exists, but guard.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )
    return to_user_tool_card(updated, to_tool_card_with_flags(tool_doc, is_fl))


@router.get("", response_model=UserToolListResponse)
async def list_my_tools(
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict[str, Any] = Depends(require_role("user")),
) -> UserToolListResponse:
    """F-TOOL-6: list with optional status filter; orphans dropped."""
    rows = await list_for_user(user["_id"], status=status_filter)
    cards: list[UserToolCard] = []
    for row in rows:
        tool_doc, is_fl = await find_tool_anywhere(row["tool_id"])
        if tool_doc is None:
            continue
        if tool_doc.get("curation_status") != "approved":
            continue
        cards.append(
            to_user_tool_card(
                row, to_tool_card_with_flags(tool_doc, is_fl)
            )
        )
    return UserToolListResponse(tools=cards)
