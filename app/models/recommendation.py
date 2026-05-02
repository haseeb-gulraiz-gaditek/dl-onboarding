"""Pydantic shapes for the recommendations endpoint + ranker.

Per spec-delta recommendation-engine F-REC-5.

Two pairs of models:
  - Public response shapes (RecommendationPick, RecommendationsResponse)
  - OpenAI structured-output shapes (RankerPick, RankerOutput) used
    by app/recommendations/ranker.py to enforce JSON output strictly
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.onboarding import OnboardingToolCard


Verdict = Literal["try", "skip"]
"""Per-rec verdict surfaces the constitutional principle 'Recommend
honestly, including skip-this'. Frontend renders skip-tagged recs
visually different (e.g., greyed out with the reasoning shown as
the rationale)."""


class RecommendationPick(BaseModel):
    """A single tool recommendation as returned to the client."""

    tool: OnboardingToolCard
    verdict: Verdict
    reasoning: str
    score: float


class RecommendationsResponse(BaseModel):
    """Response body for POST /api/recommendations.

    Per F-REC-5 MODIFIED by cycle #9: gains a `launches` field for
    threshold-gated founder-launched picks (see F-PUB-6). The two
    arrays are NEVER commingled — organic recommendations are
    ranked by gpt-5; launches are surfaced by similarity score
    only, never moving the organic ranking signal.
    """

    recommendations: list[RecommendationPick]
    launches: list[RecommendationPick] = []
    generated_at: datetime
    from_cache: bool
    degraded: bool = False


# ---- OpenAI structured-output models ----

class RankerPick(BaseModel):
    """One pick the LLM ranker makes. Validated server-side: any slug
    not in the candidate set is dropped."""

    slug: str
    verdict: Verdict
    reasoning: str


class RankerOutput(BaseModel):
    """Top-level structured output the ranker prompt asks GPT-5 to
    produce. Forces a list of picks with no other extraneous fields."""

    picks: list[RankerPick]
