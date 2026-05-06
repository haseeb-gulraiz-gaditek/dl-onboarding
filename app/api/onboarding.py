"""Onboarding match router.

Implements F-MATCH-1..5 of spec-delta fast-onboarding-match-and-graph.
Also hosts the live-flow question schema endpoints from cycle #15
(spec-delta live-narrowing-onboarding F-LIVE-1).
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.middleware import require_role
from app.models.onboarding import MatchResponse, tool_to_card
from app.onboarding.live_questions import (
    LIVE_QUESTIONS,
    LiveQuestion,
    Option,
    get_question,
    options_for,
)
from app.onboarding.match import (
    GENERIC_MODE_MAX_ANSWERS,
    count_distinct_answers,
    embedding_match,
    generic_match,
)
from pydantic import BaseModel


router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class LiveQuestionsResponse(BaseModel):
    questions: list[LiveQuestion]


class LiveOptionsResponse(BaseModel):
    options: list[Option]
    role_key_resolved: str  # the canonical key actually used (or "other")


@router.get("/live-questions", response_model=LiveQuestionsResponse)
async def get_live_questions(
    _user: dict[str, Any] = Depends(require_role("user")),
) -> LiveQuestionsResponse:
    """F-LIVE-1: return the locked 4-question schema for the live flow."""
    return LiveQuestionsResponse(questions=LIVE_QUESTIONS)


@router.get(
    "/live-questions/{q_index}/options",
    response_model=LiveOptionsResponse,
)
async def get_live_options(
    q_index: int,
    role: str = Query(..., min_length=1, max_length=64),
    _user: dict[str, Any] = Depends(require_role("user")),
) -> LiveOptionsResponse:
    """F-LIVE-1: role-conditioned options for Q2 / Q3.

    400 if the question doesn't exist or isn't role-conditioned
    (Q1 / Q4 don't accept this endpoint)."""
    q = get_question(q_index)
    if q is None:
        raise HTTPException(status_code=404, detail={"error": "question_not_found"})
    if q.options_per_role is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "question_not_role_conditioned"},
        )
    opts = options_for(q_index, role) or []
    # Reflect the resolved key so the frontend can show "showing options
    # for: {role_key}" if it wants.
    from app.onboarding.live_questions import role_key_for
    return LiveOptionsResponse(options=opts, role_key_resolved=role_key_for(role))


@router.post("/match", response_model=MatchResponse)
async def match(
    user: dict[str, Any] = Depends(require_role("user")),
) -> MatchResponse:
    """F-MATCH-1: dispatch to generic or embedding match by answered-
    question count.

    Generic-mode failures are unrecoverable -- they're pure Mongo
    queries -- so any exception there propagates as 500. Embedding-mode
    failures (OpenAI down, Weaviate down) are caught and we degrade to
    generic mode so the user still sees tools (F-MATCH-4 graceful
    degradation).
    """
    answered = await count_distinct_answers(user["_id"])

    if answered < GENERIC_MODE_MAX_ANSWERS:
        tools = await generic_match(user)
        return MatchResponse(
            mode="generic",
            tools=[tool_to_card(t) for t in tools],
        )

    try:
        tools = await embedding_match(user)
        return MatchResponse(
            mode="embedding",
            tools=[tool_to_card(t) for t in tools],
        )
    except Exception as exc:
        print(f"[onboarding/match] embedding mode failed, falling back to generic: {exc}")
        tools = await generic_match(user)
        return MatchResponse(
            mode="generic",
            tools=[tool_to_card(t) for t in tools],
        )
