"""Onboarding match router.

Implements F-MATCH-1..5 of spec-delta fast-onboarding-match-and-graph.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.middleware import require_role
from app.models.onboarding import MatchResponse, tool_to_card
from app.onboarding.match import (
    GENERIC_MODE_MAX_ANSWERS,
    count_distinct_answers,
    embedding_match,
    generic_match,
)


router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


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
