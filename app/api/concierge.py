"""Concierge respond endpoint.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-5.

User responds tell_me_more / skip on a concierge nudge. Writes an
engagement; for tell_me_more returns the redirect URL with an HMAC
user-hash so the redirect endpoint (F-PUB-3) can resolve the user.
"""
from typing import Any, Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.middleware import require_role
from app.db.engagements import insert as insert_engagement
from app.db.launches import find_by_id as find_launch_by_id
from app.launches.redirect import make_user_hash


router = APIRouter(prefix="/api/concierge", tags=["concierge"])


class ConciergeRespondRequest(BaseModel):
    launch_id: str
    action: Literal["tell_me_more", "skip"]


class ConciergeRespondResponse(BaseModel):
    accepted: bool
    redirect_url: str | None  # only on tell_me_more


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


@router.post("/respond", response_model=ConciergeRespondResponse)
async def respond_to_nudge(
    payload: ConciergeRespondRequest,
    user: dict[str, Any] = Depends(require_role("user")),
) -> ConciergeRespondResponse:
    """F-PUB-5: log engagement, return redirect_url for tell_me_more."""
    oid = _parse_oid(payload.launch_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )
    launch = await find_launch_by_id(oid)
    if launch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )

    await insert_engagement(
        launch_id=oid,
        surface="concierge_nudge",
        action=payload.action,
        user_id=user["_id"],
    )

    if payload.action == "tell_me_more":
        u_hash = make_user_hash(user["_id"])
        return ConciergeRespondResponse(
            accepted=True,
            redirect_url=f"/r/{payload.launch_id}?u={u_hash}&s=concierge_nudge",
        )
    return ConciergeRespondResponse(accepted=True, redirect_url=None)
