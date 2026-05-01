"""Onboarding question router.

Implements F-QB-2 (`GET /api/questions/next`) of spec-delta
question-bank-and-answer-capture.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.middleware import require_role
from app.db.answers import answered_question_ids
from app.db.profiles import get_or_create_profile
from app.db.questions import find_active_core_questions_in_order
from app.models.question import NextQuestionResponse, to_public


router = APIRouter(prefix="/api/questions", tags=["questions"])


async def compute_next_question(user: dict[str, Any]) -> NextQuestionResponse:
    """Shared helper: returns the next unanswered core question for the
    given user, or `done=true` if none remain. Reused by the answers
    router so a successful POST can return the next question without a
    second round-trip."""
    answered = await answered_question_ids(user["_id"])
    questions = await find_active_core_questions_in_order()
    for q in questions:
        if q["_id"] not in answered:
            return NextQuestionResponse(done=False, question=to_public(q))
    return NextQuestionResponse(done=True, question=None)


@router.get("/next", response_model=NextQuestionResponse)
async def next_question(
    user: dict[str, Any] = Depends(require_role("user")),
) -> NextQuestionResponse:
    """F-QB-2: return the next unanswered core question for the calling
    user, or `done=true` if all answered. Creates the user's profile on
    first call."""
    await get_or_create_profile(user)
    return await compute_next_question(user)
