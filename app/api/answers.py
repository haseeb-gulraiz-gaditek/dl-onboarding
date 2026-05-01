"""Answer-capture router.

Implements F-QB-3 (`POST /api/answers`) of spec-delta
question-bank-and-answer-capture.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.questions import compute_next_question
from app.auth.middleware import require_role
from app.db.answers import insert_answer
from app.db.profiles import get_or_create_profile, touch_invalidated
from app.db.questions import find_question_by_id
from app.models.answer import AnswerCreate, validate_answer_value
from app.models.question import NextQuestionResponse


router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("", response_model=NextQuestionResponse)
async def submit_answer(
    payload: AnswerCreate,
    user: dict[str, Any] = Depends(require_role("user")),
) -> NextQuestionResponse:
    """F-QB-3: write an answer (append-only), bump profile invalidation,
    return the next unanswered question."""
    await get_or_create_profile(user)

    question = await find_question_by_id(payload.question_id)
    if question is None or not question.get("active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "question_not_found"},
        )

    err = validate_answer_value(question, payload.value)
    if err is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": err},
        )

    await insert_answer(
        user_id=user["_id"],
        question_id=question["_id"],
        value=payload.value,
    )
    await touch_invalidated(user["_id"])

    return await compute_next_question(user)
