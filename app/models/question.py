"""Pydantic schemas for the `questions` collection.

Per spec-delta question-bank-and-answer-capture F-QB-1, F-QB-2.
"""
from typing import Literal

from pydantic import BaseModel, Field


KindLiteral = Literal["single_select", "multi_select", "free_text"]
"""How a question is answered. V1 supports these three; LLM-driven
follow-ups in V1.5 may introduce more."""


CategoryLiteral = Literal[
    "role", "stack", "workflow", "friction", "wishlist", "budget"
]
"""Six categories the seed questions cover, per system_design.md
Subsystem 1."""


class Option(BaseModel):
    """A selectable option on a single_select / multi_select question."""

    value: str
    label: str


class QuestionPublic(BaseModel):
    """Shape returned to the client by GET /api/questions/next."""

    id: str
    key: str
    text: str
    kind: KindLiteral
    options: list[Option] = Field(default_factory=list)
    category: CategoryLiteral
    order: int


class NextQuestionResponse(BaseModel):
    """Wrapping shape that lets the client distinguish 'more to ask'
    from 'all done'."""

    done: bool
    question: QuestionPublic | None = None
