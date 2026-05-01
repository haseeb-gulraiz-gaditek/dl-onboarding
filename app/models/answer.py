"""Pydantic schemas for the `answers` collection plus value-validation
logic that ties an answer to its question's `kind` and `options`.

Per spec-delta question-bank-and-answer-capture F-QB-3.
"""
from typing import Any

from pydantic import BaseModel


class AnswerCreate(BaseModel):
    """Request body for POST /api/answers.

    `value` is intentionally typed `Any` here -- the shape is validated
    against the question's `kind` and `options` server-side via
    `validate_answer_value` below, since the rules depend on data we
    only have after looking up the question.
    """

    question_id: str
    value: Any


def validate_answer_value(question: dict[str, Any], value: Any) -> str | None:
    """Validate `value` against the rules implied by the question.

    Returns None if the value is acceptable.
    Returns the spec-delta-mandated error code string ("value_invalid")
    on any failure.
    """
    kind = question.get("kind")
    options = question.get("options") or []
    valid_values = {opt.get("value") for opt in options if isinstance(opt, dict)}

    if kind == "single_select":
        if not isinstance(value, str):
            return "value_invalid"
        if value not in valid_values:
            return "value_invalid"
        return None

    if kind == "multi_select":
        if not isinstance(value, list) or len(value) == 0:
            return "value_invalid"
        if not all(isinstance(v, str) for v in value):
            return "value_invalid"
        if not all(v in valid_values for v in value):
            return "value_invalid"
        return None

    if kind == "free_text":
        if not isinstance(value, str) or len(value.strip()) == 0:
            return "value_invalid"
        return None

    return "value_invalid"
