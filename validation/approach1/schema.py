"""Feature schema for Approach 1.

Six dimensions per validation/approaches.md. Both tools and users get a
record in the same shape, so the scorer can compare them directly.

Industry / paradigm / task_shape / setup_tolerance are CLOSED vocabularies
(enums) — the LLM tagger is told to pick from these lists. role_fit and
capabilities are OPEN (free-form short strings) so the model can describe
nuance the enums miss.
"""
from typing import Literal

# ---- Closed vocabularies (enums) ----

INDUSTRIES = [
    "software_tech",
    "finance_accounting",
    "healthcare",
    "legal",
    "education",
    "marketing_advertising",
    "sales",
    "consulting",
    "design_creative",
    "operations",
    "hr",
    "government",
    "non_profit",
    "manufacturing",
    "real_estate",
    "media_content",
    "retail_ecomm",
    "generic",  # broadly applicable, no industry skew
]

# Coarse-grained shapes a "big task" can take. A tool can serve more
# than one (a meeting tool is short-cycle + capture + async-handoff).
TASK_SHAPES = [
    "long_cycle",       # multi-day/week deliverables
    "short_cycle",      # done-in-a-session
    "multi_stage",      # has explicit stages with sign-off
    "reactive",         # responds to incoming pings/events
    "producer",         # creates new artifacts
    "reviewer",         # critiques/approves others' work
    "capture",          # records info passively (meetings, notes)
    "async_handoff",    # bridges across people/tools
    "deep_work",        # demands sustained focus
    "high_throughput",  # batches many similar items
]

# How the tool fits into the day. excluded_paradigms is the negation —
# "do NOT recommend this if user is X."
PARADIGMS = [
    "in_flow",          # tool sits inside the work surface (IDE plugin etc)
    "ambient",          # runs in background, no active engagement
    "async",            # used between sessions, not during work
    "morning_deep",     # fits AM deep-work blocks
    "afternoon_coord",  # fits PM coordination/communication
    "reactive",         # for handling interrupts
    "ai_mature",        # assumes user already trusts AI workflows
    "ai_naive",         # ok for first-time AI users
    "offline_capable",  # works without connectivity
]

SETUP_TOLERANCE = ["under_2min", "around_10min", "willing_to_customize"]

MATURITY = ["low", "medium", "high"]  # how AI-mature user must be

SetupTolerance = Literal["under_2min", "around_10min", "willing_to_customize"]
Maturity = Literal["low", "medium", "high"]
