"""Role -> categories mapping for the generic-mode onboarding match.

Per spec-delta fast-onboarding-match-and-graph F-MATCH-6.

The keys MUST exactly match the `value` field of every option in the
`role.primary_function` seed question (`app/seed/questions.json`).
A test in `tests/test_onboarding_match.py` audits this invariant.

This map is product judgement subject to refinement. It lives as a
plain dict in code so updates are a one-line change without a schema
migration.
"""
from app.models.tool import Category


ROLE_TO_CATEGORIES: dict[str, list[Category]] = {
    "marketing_ops": ["marketing", "analytics_data", "writing"],
    "product_management": ["productivity", "analytics_data", "research_browsing"],
    "design": ["design", "creative_video"],
    "content": ["writing", "creative_video"],
    "engineering": ["engineering", "research_browsing"],
    "operations": ["productivity", "automation_agents", "analytics_data"],
    "customer_success": ["productivity", "writing", "meetings"],
    "sales": ["sales", "writing"],
    "founder_non_ai": ["productivity", "marketing", "writing"],
    "freelance_consulting": ["productivity", "writing", "design"],
    "student_research": ["education", "research_browsing", "writing"],
    "other": [],
}


def categories_for_role(role: str | None) -> list[Category]:
    """Return the mapped categories for a role, or [] if the role is
    unknown or None. Unknown values silently fall back to the catalog-
    wide path in F-MATCH-3."""
    if not role:
        return []
    return ROLE_TO_CATEGORIES.get(role, [])
