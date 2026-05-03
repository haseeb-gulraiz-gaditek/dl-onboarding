"""Tests for /api/launches (cycle: my-tools-explore-new-tabs).

Covers F-TOOL-9 — joined-community filter + ?all=true escape hatch.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


async def _seed_approved_launch(app_client, admin_token, target_slugs):
    """Helper: submit + approve a launch in one go."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=target_slugs
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    return launch_id


# ---- F-TOOL-9 ----


@pytest.mark.asyncio
async def test_default_filter_returns_only_joined_community_launches(
    app_client, seed_test_communities, admin_token
):
    await _seed_approved_launch(
        app_client, admin_token, ["marketing-ops"]
    )

    body = await signup_user(app_client, "maya@example.com")
    # Maya joins marketing-ops.
    await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(body["jwt"]),
    )

    r = await app_client.get(
        "/api/launches", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    launches = r.json()["launches"]
    assert len(launches) == 1
    assert launches[0]["tool"]["slug"] == "acme-io"
    assert launches[0]["in_my_communities"] == ["marketing-ops"]


@pytest.mark.asyncio
async def test_user_with_no_memberships_gets_empty_default(
    app_client, seed_test_communities, admin_token
):
    """F-TOOL-9: zero memberships → empty list on default."""
    await _seed_approved_launch(
        app_client, admin_token, ["marketing-ops"]
    )

    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/launches", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json()["launches"] == []


@pytest.mark.asyncio
async def test_all_query_returns_all_approved_launches(
    app_client, seed_test_communities, admin_token
):
    """F-TOOL-9: ?all=true bypasses the joined-community filter."""
    await _seed_approved_launch(
        app_client, admin_token, ["marketing-ops"]
    )

    body = await signup_user(app_client, "maya@example.com")
    # No membership.
    r = await app_client.get(
        "/api/launches?all=true", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    launches = r.json()["launches"]
    assert len(launches) == 1
    # in_my_communities is empty since user joined nothing.
    assert launches[0]["in_my_communities"] == []


@pytest.mark.asyncio
async def test_in_my_communities_intersection(
    app_client, seed_test_communities, admin_token
):
    """F-TOOL-9: in_my_communities reflects intersection of launch's
    target_community_slugs and user's memberships."""
    await _seed_approved_launch(
        app_client,
        admin_token,
        ["marketing-ops", "engineering-bench"],
    )

    body = await signup_user(app_client, "maya@example.com")
    # Maya only joins one of the two.
    await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(body["jwt"]),
    )

    r = await app_client.get(
        "/api/launches", headers=auth_header(body["jwt"])
    )
    launches = r.json()["launches"]
    assert len(launches) == 1
    assert launches[0]["in_my_communities"] == ["marketing-ops"]


@pytest.mark.asyncio
async def test_response_includes_launch_meta(
    app_client, seed_test_communities, admin_token
):
    """F-TOOL-9: each item carries founder_display_name + problem_statement."""
    await _seed_approved_launch(
        app_client, admin_token, ["marketing-ops"]
    )

    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(body["jwt"]),
    )

    r = await app_client.get(
        "/api/launches", headers=auth_header(body["jwt"])
    )
    item = r.json()["launches"][0]
    assert item["launch_meta"]["founder_display_name"] == "aamir"
    assert "Marketers waste 3 hours" in item["launch_meta"]["problem_statement"]


@pytest.mark.asyncio
async def test_founder_cannot_browse_launches(
    app_client, seed_test_communities
):
    body = await signup_founder(app_client, "frank2@example.com")
    r = await app_client.get(
        "/api/launches", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
