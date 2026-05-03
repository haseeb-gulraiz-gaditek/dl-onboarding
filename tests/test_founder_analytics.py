"""Tests for the analytics aggregation helpers (cycle: founder-dashboard...).

Covers F-DASH-1 (each helper) + F-DASH-4 (empty results).
"""
import pytest
from bson import ObjectId

from tests.conftest import seed_engagement


# ---- F-DASH-4 empty cases ----


@pytest.mark.asyncio
async def test_helpers_return_zero_on_no_engagements(app_client):
    """F-DASH-4: every helper returns its zero on empty result."""
    from app.founders.analytics import (
        clicks_by_community,
        clicks_by_surface,
        matched_count,
        nudge_response_counts,
        total_clicks,
    )

    fake_launch = ObjectId()
    assert await matched_count(fake_launch) == 0
    assert await nudge_response_counts(fake_launch) == {"tell_me_more": 0, "skip": 0}
    assert await total_clicks(fake_launch) == 0
    assert await clicks_by_community(fake_launch) == {}
    assert await clicks_by_surface(fake_launch) == {}


# ---- F-DASH-1: matched_count ----


@pytest.mark.asyncio
async def test_matched_count_is_distinct_users(app_client):
    """matched_count counts distinct users with concierge_nudge VIEW."""
    from app.founders.analytics import matched_count

    launch_id = ObjectId()
    u1 = ObjectId()
    u2 = ObjectId()
    # Two distinct users get nudged (one twice — only counted once).
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="view", user_id=u1)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="view", user_id=u1)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="view", user_id=u2)
    # An unrelated row on a different surface — should NOT count.
    await seed_engagement(launch_id=launch_id, surface="community_post", action="view", user_id=u1)

    assert await matched_count(launch_id) == 2


# ---- F-DASH-1: nudge_response_counts ----


@pytest.mark.asyncio
async def test_nudge_response_counts_returns_distinct_users(app_client):
    """nudge_response_counts groups distinct users by action."""
    from app.founders.analytics import nudge_response_counts

    launch_id = ObjectId()
    u1, u2, u3 = ObjectId(), ObjectId(), ObjectId()
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="tell_me_more", user_id=u1)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="skip", user_id=u2)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="skip", user_id=u3)
    # Same user double-skip — counted once.
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="skip", user_id=u3)

    counts = await nudge_response_counts(launch_id)
    assert counts == {"tell_me_more": 1, "skip": 2}


# ---- F-DASH-1: total_clicks ----


@pytest.mark.asyncio
async def test_total_clicks_counts_all_click_actions(app_client):
    from app.founders.analytics import total_clicks

    launch_id = ObjectId()
    await seed_engagement(launch_id=launch_id, surface="community_post", action="click")
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="click")
    await seed_engagement(launch_id=launch_id, surface="redirect", action="click", user_id=ObjectId())
    # Non-click action — should NOT count.
    await seed_engagement(launch_id=launch_id, surface="community_post", action="view")

    assert await total_clicks(launch_id) == 3


# ---- F-DASH-1: clicks_by_community ----


@pytest.mark.asyncio
async def test_clicks_by_community_groups_correctly(app_client):
    from app.founders.analytics import clicks_by_community

    launch_id = ObjectId()
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "marketing-ops"},
    )
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "marketing-ops"},
    )
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "weekly-launches"},
    )
    # A non-community surface click — should NOT appear.
    await seed_engagement(
        launch_id=launch_id, surface="concierge_nudge", action="click",
    )

    result = await clicks_by_community(launch_id)
    assert result == {"marketing-ops": 2, "weekly-launches": 1}


# ---- F-DASH-1: clicks_by_surface ----


@pytest.mark.asyncio
async def test_clicks_by_surface_groups_across_surfaces(app_client):
    from app.founders.analytics import clicks_by_surface

    launch_id = ObjectId()
    await seed_engagement(launch_id=launch_id, surface="community_post", action="click")
    await seed_engagement(launch_id=launch_id, surface="community_post", action="click")
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="click")
    await seed_engagement(launch_id=launch_id, surface="redirect", action="click")

    result = await clicks_by_surface(launch_id)
    assert result == {"community_post": 2, "concierge_nudge": 1, "redirect": 1}
