"""POST /api/recommendations.

Per spec-delta recommendation-engine F-REC-1, F-REC-2, F-REC-5.
"""
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.auth.middleware import require_role
from app.models.recommendation import RecommendationsResponse
from app.onboarding.match import count_distinct_answers
from app.recommendations.engine import generate_recommendations


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


MIN_ANSWERS_FOR_RECS = 3
MAX_COUNT = 5
DEFAULT_COUNT = 3


@router.post("", response_model=RecommendationsResponse)
async def get_recommendations(
    payload: dict = Body(default_factory=dict),
    user: dict[str, Any] = Depends(require_role("user")),
) -> RecommendationsResponse:
    """F-REC-1, F-REC-2: gate on >=3 answers, dispatch to engine."""
    answered = await count_distinct_answers(user["_id"])
    if answered < MIN_ANSWERS_FOR_RECS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "no_profile_yet",
                "min_answers": MIN_ANSWERS_FOR_RECS,
            },
        )

    count_raw = payload.get("count", DEFAULT_COUNT)
    try:
        count = int(count_raw)
    except (TypeError, ValueError):
        count = DEFAULT_COUNT
    if count <= 0:
        count = DEFAULT_COUNT
    count = min(MAX_COUNT, count)

    return await generate_recommendations(user, count)
