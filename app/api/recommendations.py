"""POST /api/recommendations.

Per spec-delta recommendation-engine F-REC-1, F-REC-2, F-REC-5.
Also hosts the live-narrowing onboarding endpoint per cycle #15
spec-delta `live-narrowing-onboarding` F-LIVE-2.
"""
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.middleware import require_role
from app.db.live_answers import get_user_live_answers, upsert_live_answer
from app.db.profiles import get_or_create_profile
from app.models.recommendation import RecommendationsResponse
from app.onboarding.match import count_distinct_answers
from app.recommendations.engine import generate_recommendations
from app.recommendations.live_engine import K_SCHEDULE, live_match


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


# ---- F-LIVE-2: per-tap narrowing endpoint ----

class LiveStepRequest(BaseModel):
    q_index: int = Field(..., ge=1, le=4)
    answer_value: dict[str, Any]


class LiveStepTool(BaseModel):
    slug: str
    name: str
    tagline: str | None = None
    category: str | None = None
    score: float
    layer: str | None = None
    reasoning_hook: str


class LiveStepResponse(BaseModel):
    step: int
    top: list[LiveStepTool]
    wildcard: LiveStepTool | None = None
    count_kept: int
    degraded: bool = False


@router.post("/live-step", response_model=LiveStepResponse)
async def live_step(
    payload: LiveStepRequest,
    user: dict[str, Any] = Depends(require_role("user")),
) -> LiveStepResponse:
    """F-LIVE-2: persist answer + re-embed + hybrid query → ranked
    list with score-band layers + wildcard. Founders → 403."""
    # Ensure the user has a profiles row (the live flow doesn't go
    # through /api/questions/next which is what classic onboarding
    # uses to lazy-create profiles). Without this, ensure_profile_
    # embedding bails silently and live_match falls back to a zero-
    # vector similarity_search that returns tools in Mongo insertion
    # order — i.e., garbage for ranking.
    await get_or_create_profile(user)

    # Persist this step's answer (upsert per (user, q_index)).
    await upsert_live_answer(
        user_id=user["_id"],
        q_index=payload.q_index,
        value=payload.answer_value,
    )

    # Read all live answers for the user (so live_match builds the
    # full accumulated profile_text).
    live_answers = await get_user_live_answers(user["_id"])

    try:
        result = await live_match(
            user=user,
            q_index=payload.q_index,
            live_answers=live_answers,
        )
    except Exception as exc:
        # The OpenAI embed inside live_match is the most likely failure
        # mode (rate limit, network blip). Surface as 503 — the answer
        # is already persisted so the user can retry.
        print(f"[live-step] pipeline failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "live_step_unavailable"},
        )

    return LiveStepResponse(
        step=result.step,
        top=[LiveStepTool(**t) for t in result.top],
        wildcard=LiveStepTool(**result.wildcard) if result.wildcard else None,
        count_kept=result.count_kept,
        degraded=result.degraded,
    )
