"""Pydantic schemas for the `tools_seed` collection.

Per spec-delta catalog-seed-and-curation F-CAT-1, F-CAT-5.
"""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


Category = Literal[
    "productivity",
    "writing",
    "design",
    "engineering",
    "research_browsing",
    "meetings",
    "marketing",
    "sales",
    "analytics_data",
    "finance",
    "education",
    "creative_video",
    "automation_agents",
]
"""Closed enum of 13 categories. Matches the catalog research prompt."""


Label = Literal["new", "all_time_best", "gaining_traction"]
"""Hype/recency labels. A tool may carry multiple. Orthogonal to category."""


CurationStatus = Literal["pending", "approved", "rejected"]
"""V1 admin-curation states. Cycle #4 will only embed approved tools."""


Source = Literal["manual", "taaft", "producthunt", "futuretools", "founder_launch"]
"""Where the tool entry came from. `founder_launch` rows MUST live in
the separate `tools_founder_launched` collection (cycle #8); they are
explicitly NOT permitted in `tools_seed`."""


class ToolPublic(BaseModel):
    """Shape returned by admin endpoints."""

    slug: str
    name: str
    tagline: str
    description: str
    url: str
    pricing_summary: str
    category: Category
    labels: list[Label]
    curation_status: CurationStatus
    rejection_comment: str | None = None
    source: Source
    embedding_vector_id: str | None = None
    created_at: datetime
    last_reviewed_at: datetime | None = None
    reviewed_by: str | None = None


class ToolReject(BaseModel):
    """Request body for POST /admin/catalog/{slug}/reject."""

    comment: Annotated[str, Field(min_length=1)]


def to_public(doc: dict) -> ToolPublic:
    """Project a stored tools_seed document into the client-safe shape."""
    return ToolPublic(
        slug=doc["slug"],
        name=doc["name"],
        tagline=doc["tagline"],
        description=doc["description"],
        url=doc["url"],
        pricing_summary=doc["pricing_summary"],
        category=doc["category"],
        labels=doc.get("labels", []),
        curation_status=doc["curation_status"],
        rejection_comment=doc.get("rejection_comment"),
        source=doc.get("source", "manual"),
        embedding_vector_id=doc.get("embedding_vector_id"),
        created_at=doc["created_at"],
        last_reviewed_at=doc.get("last_reviewed_at"),
        reviewed_by=doc.get("reviewed_by"),
    )
