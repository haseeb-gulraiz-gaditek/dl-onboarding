"""Click-tracking redirect endpoint.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-3.

Unauthenticated. Resolves the optional ?u= HMAC user-hash, writes
an `engagements` row, 302s to the launch's product_url.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.db.engagements import insert as insert_engagement
from app.db.launches import find_by_id
from app.launches.redirect import resolve_user_hash


router = APIRouter(prefix="/r", tags=["redirect"])


_VALID_SURFACES = {
    "concierge_nudge",
    "community_post",
    "recommendation_slot",
    "product_page",
    "redirect",
}


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


@router.get("/{launch_id}")
async def click_redirect(
    launch_id: str,
    u: str | None = Query(default=None),
    s: str | None = Query(default=None),
):
    """F-PUB-3: log engagement, 302 to product_url."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )
    launch = await find_by_id(oid)
    if launch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "launch_not_found"},
        )

    surface = s if s in _VALID_SURFACES else "redirect"
    user_id = await resolve_user_hash(u)

    await insert_engagement(
        launch_id=oid,
        surface=surface,
        action="click",
        user_id=user_id,
        metadata={"u_hash": u} if u else {},
    )

    return RedirectResponse(
        url=launch["product_url"], status_code=status.HTTP_302_FOUND
    )
