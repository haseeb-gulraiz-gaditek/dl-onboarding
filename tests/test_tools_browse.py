"""Tests for /api/tools (cycle: my-tools-explore-new-tabs).

Covers F-TOOL-8 — alphabetical browse with filters + cursor pagination.
Reads tools_seed only.
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


@pytest.mark.asyncio
async def test_default_browse_returns_approved_alphabetical(
    app_client, seed_test_catalog
):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    tools = r.json()["tools"]
    # Only test-tool-approved is approved in seed_test_catalog.
    assert len(tools) == 1
    assert tools[0]["slug"] == "test-tool-approved"
    assert tools[0]["is_founder_launched"] is False


@pytest.mark.asyncio
async def test_category_filter(app_client, seed_minimal_catalog):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools?category=marketing", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    tools = r.json()["tools"]
    assert all(t["category"] == "marketing" for t in tools)


@pytest.mark.asyncio
async def test_label_filter(app_client, seed_minimal_catalog):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools?label=all_time_best", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    tools = r.json()["tools"]
    assert len(tools) > 0
    for t in tools:
        assert "all_time_best" in t["labels"]


@pytest.mark.asyncio
async def test_q_substring_matches_name(app_client, seed_minimal_catalog):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools?q=Notion", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    slugs = [t["slug"] for t in r.json()["tools"]]
    assert "notion" in slugs


@pytest.mark.asyncio
async def test_cursor_pagination(app_client, seed_minimal_catalog):
    body = await signup_user(app_client, "maya@example.com")
    p1 = await app_client.get(
        "/api/tools?limit=2", headers=auth_header(body["jwt"])
    )
    assert p1.status_code == 200
    body1 = p1.json()
    assert len(body1["tools"]) == 2
    assert body1["next_before"] is not None

    p2 = await app_client.get(
        f"/api/tools?limit=2&before={body1['next_before']}",
        headers=auth_header(body["jwt"]),
    )
    assert p2.status_code == 200
    # Second page tools come after page-1 tools alphabetically.
    p1_names = [t["name"] for t in body1["tools"]]
    p2_names = [t["name"] for t in p2.json()["tools"]]
    if p2_names:
        assert all(n > p1_names[-1] for n in p2_names)


@pytest.mark.asyncio
async def test_pending_and_rejected_excluded(app_client, seed_test_catalog):
    """F-TOOL-8: only curation_status=approved entries appear."""
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools", headers=auth_header(body["jwt"])
    )
    slugs = [t["slug"] for t in r.json()["tools"]]
    assert "test-tool-pending" not in slugs
    assert "test-tool-rejected" not in slugs


@pytest.mark.asyncio
async def test_founder_launched_not_in_browse(
    app_client, seed_test_communities, admin_token
):
    """F-TOOL-8: tools_founder_launched entries NEVER appear (constitutional
    storage separation)."""
    from tests.conftest import signup_founder_with_token, submit_test_launch

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools", headers=auth_header(body["jwt"])
    )
    slugs = [t["slug"] for t in r.json()["tools"]]
    assert "acme-io" not in slugs


@pytest.mark.asyncio
async def test_founder_cannot_browse(app_client, seed_test_catalog):
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.get(
        "/api/tools", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
