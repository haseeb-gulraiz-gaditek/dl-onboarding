"""Pydantic shapes for the onboarding match endpoint.

Per spec-delta fast-onboarding-match-and-graph F-MATCH-5.

OnboardingToolCard is a deliberate subset of ToolPublic: only the
fields the user-facing onboarding UI needs. Internal fields
(curation_status, embedding, source, created_at, last_reviewed_at,
reviewed_by, rejection_comment) are excluded from the API response.
"""
from typing import Literal

from pydantic import BaseModel

from app.models.tool import Category, Label


class OnboardingToolCard(BaseModel):
    """The public shape of a single tool in a match response."""

    slug: str
    name: str
    tagline: str
    description: str
    url: str
    pricing_summary: str
    category: Category
    labels: list[Label]


MatchMode = Literal["generic", "embedding"]


class MatchResponse(BaseModel):
    """Wrapping shape for POST /api/onboarding/match."""

    mode: MatchMode
    tools: list[OnboardingToolCard]


def tool_to_card(doc: dict) -> OnboardingToolCard:
    """Project a tools_seed document into the user-facing card shape."""
    return OnboardingToolCard(
        slug=doc["slug"],
        name=doc["name"],
        tagline=doc["tagline"],
        description=doc["description"],
        url=doc["url"],
        pricing_summary=doc["pricing_summary"],
        category=doc["category"],
        labels=doc.get("labels") or [],
    )
