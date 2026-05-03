"""Tests for GET /api/me/communities (cycle: frontend-core).

Per spec-delta F-FE-2.
"""
import asyncio

import pytest

from tests.conftest import auth_header, signup_founder, signup_user


@pytest.mark.asyncio
async def test_returns_joined_communities_newest_first(
    app_client, seed_test_communities
):
    """F-FE-2: list scoped to requesting user, joined_at DESC."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    # Join two communities with a small delay so joined_at is distinct.
    await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(token),
    )
    await asyncio.sleep(0.01)
    await app_client.post(
        "/api/communities/weekly-launches/join",
        headers=auth_header(token),
    )

    r = await app_client.get(
        "/api/me/communities", headers=auth_header(token)
    )
    assert r.status_code == 200
    body_json = r.json()
    slugs = [c["slug"] for c in body_json["communities"]]
    # Newest-first: weekly-launches (joined later) before marketing-ops.
    assert slugs == ["weekly-launches", "marketing-ops"]
    # Each entry includes joined_at + the CommunityCard fields.
    for entry in body_json["communities"]:
        assert "joined_at" in entry
        assert "name" in entry
        assert "slug" in entry
        assert "category" in entry
        assert "member_count" in entry


@pytest.mark.asyncio
async def test_user_with_no_memberships_returns_empty(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "alone@example.com")
    r = await app_client.get(
        "/api/me/communities", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"communities": []}


@pytest.mark.asyncio
async def test_founder_caller_returns_403(app_client):
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.get(
        "/api/me/communities", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(app_client):
    r = await app_client.get("/api/me/communities")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


@pytest.mark.asyncio
async def test_inactive_communities_silently_dropped(
    app_client, seed_test_communities
):
    """If a community is deactivated after the user joined, it's
    dropped from the response (no orphan rows surfaced)."""
    from app.db.communities import communities_collection

    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(body["jwt"]),
    )

    # Deactivate the community.
    await communities_collection().update_one(
        {"slug": "marketing-ops"}, {"$set": {"is_active": False}}
    )

    r = await app_client.get(
        "/api/me/communities", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json()["communities"] == []
