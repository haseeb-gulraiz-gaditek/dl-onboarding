"""Vote endpoint.

Per spec-delta communities-and-flat-comments F-COM-6, F-COM-7.

Single endpoint dispatches the three-way insert/toggle/flip via
`apply_vote`.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import require_role
from app.community.voting import apply_vote
from app.models.vote import VoteRequest, VoteResponse


router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.post("", response_model=VoteResponse)
async def post_vote(
    payload: VoteRequest,
    user: dict[str, Any] = Depends(require_role("user")),
) -> VoteResponse:
    """F-COM-6, F-COM-7: vote on post / comment / tool."""
    result = await apply_vote(
        user_id=user["_id"],
        target_type=payload.target_type,
        target_id_str=payload.target_id,
        direction=payload.direction,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "target_invalid"},
        )
    return VoteResponse(**result)
