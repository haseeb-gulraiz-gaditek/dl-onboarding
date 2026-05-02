"""Tests for the recommendation engine launch fan-in.

Covers F-PUB-6 (MODIFIED F-REC-5/6): RecommendationsResponse.launches
slot, threshold-gated by similarity, structurally separate from
organic recommendations.
"""
import pytest

from tests.conftest import (
    auth_header,
    prepare_user_for_recs,
    seed_recs_catalog,  # noqa: F401  -- imported indirectly
    signup_founder_with_token,
    submit_test_launch,
)


@pytest.mark.asyncio
async def test_response_includes_launches_field(
    app_client, seed_recs_catalog
):
    """F-PUB-6: response always includes `launches` key, even when empty."""
    prep = await prepare_user_for_recs(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert "launches" in body
    assert body["launches"] == []  # No approved launches in this fixture


@pytest.mark.asyncio
async def test_approved_launch_appears_in_launches_slot(
    app_client, seed_recs_catalog, seed_test_communities, admin_token
):
    """F-PUB-6: approved launch with matching profile shows in launches[]."""
    # Submit + approve a launch.
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    # Now a user fetches recs.
    prep = await prepare_user_for_recs(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 5},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["launches"]) >= 1
    launch_slugs = [p["tool"]["slug"] for p in body["launches"]]
    assert "acme-io" in launch_slugs

    # Constitutional: never commingled with organic recs.
    organic_slugs = [p["tool"]["slug"] for p in body["recommendations"]]
    assert "acme-io" not in organic_slugs

    # Each launch pick is marked is_founder_launched (via the model).
    for pick in body["launches"]:
        # OnboardingToolCard doesn't carry is_founder_launched, but the
        # slug resolves only in tools_founder_launched, so by virtue of
        # being in this slot it IS founder-launched. Sanity: verdict + score.
        assert pick["verdict"] == "try"
        assert "matched against your profile" in pick["reasoning"]


@pytest.mark.asyncio
async def test_cache_hit_serves_both_arrays(
    app_client, seed_recs_catalog, seed_test_communities, admin_token
):
    """F-PUB-6 + cache: second call serves both arrays from cache."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    prep = await prepare_user_for_recs(app_client, "maya@example.com")
    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200
    assert r1.json()["from_cache"] is False
    launch_count_1 = len(r1.json()["launches"])

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is True
    assert len(r2.json()["launches"]) == launch_count_1
