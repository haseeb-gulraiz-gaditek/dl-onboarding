"""Pydantic schema for the `profiles` collection.

Per spec-delta question-bank-and-answer-capture F-QB-4.

Note: the live profile representation is a dict (mongo doc) handled by
app/db/profiles.py. This model is mainly for type-hint clarity and
future export/serialization support; nothing in this cycle requires
strict Pydantic validation on the profile shape.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


BudgetTier = Literal["none", "indie", "sub_100_mo", "sub_1k_mo", "enterprise"]
"""Self-reported budget bracket. Captured during onboarding once the
budget question fires; populated by the future profile-aggregation
cycle."""


class Profile(BaseModel):
    """Shape stored in the `profiles` collection.

    Default values are also produced by `app/db/profiles.py`'s
    `_new_profile_doc` factory; keep the two in sync.
    """

    user_id: str
    role: str | None = None
    current_tools: list[Any] = Field(default_factory=list)
    workflows: list[Any] = Field(default_factory=list)
    tools_tried_bounced: list[Any] = Field(default_factory=list)
    counterfactual_wishes: list[Any] = Field(default_factory=list)
    budget_tier: BudgetTier | None = None
    embedding_vector_id: str | None = None
    last_recompute_at: datetime | None = None
    last_invalidated_at: datetime
    exportable: bool = True
    created_at: datetime
