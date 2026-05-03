"""Extended tool-card shape used by /api/me/tools, /api/tools,
/api/launches.

Per spec-delta my-tools-explore-new-tabs F-TOOL-2 / F-TOOL-6 / F-TOOL-8 /
F-TOOL-9.

Wraps `OnboardingToolCard` with `vote_score` and `is_founder_launched`
so the user-facing browse surfaces can render likes count + founder
attribution without a second roundtrip.
"""
from typing import Any

from app.models.onboarding import OnboardingToolCard


class ToolCardWithFlags(OnboardingToolCard):
    vote_score: int
    is_founder_launched: bool


def to_tool_card_with_flags(
    doc: dict[str, Any], is_founder_launched: bool
) -> ToolCardWithFlags:
    return ToolCardWithFlags(
        slug=doc["slug"],
        name=doc.get("name", ""),
        tagline=doc.get("tagline", ""),
        description=doc.get("description", ""),
        url=doc.get("url", ""),
        pricing_summary=doc.get("pricing_summary", ""),
        category=doc.get("category", ""),
        labels=doc.get("labels") or [],
        vote_score=doc.get("vote_score", 0),
        is_founder_launched=is_founder_launched,
    )
