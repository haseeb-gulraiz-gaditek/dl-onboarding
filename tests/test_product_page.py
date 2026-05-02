"""Tests for canonical product page (cycle: launch-publish-...).

Covers F-PUB-4.
"""
import pytest

from tests.conftest import (
    auth_header,
    seed_test_catalog,  # noqa: F401  -- imported indirectly via fixture
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


@pytest.mark.asyncio
async def test_get_seed_tool_returns_card_with_no_launch(
    app_client, seed_test_catalog
):
    """F-PUB-4: tools_seed entry → is_founder_launched=false, launch=null."""
    user = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools/test-tool-approved",
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tool"]["slug"] == "test-tool-approved"
    assert body["tool"]["is_founder_launched"] is False
    assert body["launch"] is None


@pytest.mark.asyncio
async def test_get_founder_launched_tool_returns_launch_meta(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-4: tools_founder_launched entry → launch metadata
    populated."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    user = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools/acme-io",
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tool"]["slug"] == "acme-io"
    assert body["tool"]["is_founder_launched"] is True
    assert body["launch"] is not None
    assert body["launch"]["founder_email"] == "aamir@example.com"
    assert "Marketers" in body["launch"]["problem_statement"]


@pytest.mark.asyncio
async def test_get_unknown_slug_returns_404(app_client):
    user = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/tools/does-not-exist", headers=auth_header(user["jwt"])
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_found"
