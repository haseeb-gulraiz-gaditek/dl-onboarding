"""Pydantic shapes for the canonical product page.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-4.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProductCard(BaseModel):
    slug: str
    name: str
    tagline: str
    description: str
    url: str
    pricing_summary: str
    category: str
    labels: list[str]
    vote_score: int
    is_founder_launched: bool


class LaunchMeta(BaseModel):
    founder_email: str
    founder_display_name: str
    problem_statement: str
    icp_description: str
    approved_at: datetime | None


class ProductPageResponse(BaseModel):
    tool: ProductCard
    launch: LaunchMeta | None


def to_product_card(doc: dict[str, Any], is_founder_launched: bool) -> ProductCard:
    return ProductCard(
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
