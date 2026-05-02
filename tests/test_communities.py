"""Tests for community endpoints (cycle: communities-and-flat-comments).

Covers F-COM-1, F-COM-2, F-COM-8 (founder write block on join/leave).
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


@pytest.mark.asyncio
async def test_list_communities_sorted_by_name(app_client, seed_test_communities):
    """F-COM-1: GET /api/communities sorted by name ASC."""
    body = await signup_user(app_client, "alice@example.com")
    r = await app_client.get(
        "/api/communities", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    names = [c["name"] for c in r.json()["communities"]]
    assert names == sorted(names)
    assert len(names) == 3


@pytest.mark.asyncio
async def test_list_communities_open_to_founder(app_client, seed_test_communities):
    """F-COM-1: founder CAN read the community list (no role gate on reads)."""
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.get(
        "/api/communities", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_community_unknown_slug_returns_404(app_client, seed_test_communities):
    """F-COM-1: unknown slug → 404 community_not_found."""
    body = await signup_user(app_client, "alice@example.com")
    r = await app_client.get(
        "/api/communities/does-not-exist",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "community_not_found"


@pytest.mark.asyncio
async def test_get_community_is_member_flag(app_client, seed_test_communities):
    """F-COM-1: is_member reflects the requesting user's membership."""
    body = await signup_user(app_client, "alice@example.com")
    token = body["jwt"]

    r = await app_client.get(
        "/api/communities/marketing-ops",
        headers=auth_header(token),
    )
    assert r.status_code == 200
    assert r.json()["is_member"] is False

    join = await app_client.post(
        "/api/communities/marketing-ops/join",
        headers=auth_header(token),
    )
    assert join.status_code == 200

    r2 = await app_client.get(
        "/api/communities/marketing-ops",
        headers=auth_header(token),
    )
    assert r2.json()["is_member"] is True


@pytest.mark.asyncio
async def test_join_is_idempotent_and_member_count_correct(app_client, seed_test_communities):
    """F-COM-2: second join is a no-op; member_count not double-counted."""
    body = await signup_user(app_client, "alice@example.com")
    token = body["jwt"]

    r1 = await app_client.post(
        "/api/communities/marketing-ops/join", headers=auth_header(token)
    )
    assert r1.status_code == 200
    assert r1.json()["joined"] is True

    r2 = await app_client.post(
        "/api/communities/marketing-ops/join", headers=auth_header(token)
    )
    assert r2.status_code == 200
    assert r2.json()["joined"] is False
    assert r2.json()["is_member"] is True

    detail = await app_client.get(
        "/api/communities/marketing-ops", headers=auth_header(token)
    )
    assert detail.json()["community"]["member_count"] == 1


@pytest.mark.asyncio
async def test_leave_is_idempotent(app_client, seed_test_communities):
    """F-COM-2: leave when not a member → left=false; member_count floors at 0."""
    body = await signup_user(app_client, "alice@example.com")
    token = body["jwt"]

    r = await app_client.post(
        "/api/communities/marketing-ops/leave", headers=auth_header(token)
    )
    assert r.status_code == 200
    assert r.json()["left"] is False
    assert r.json()["is_member"] is False

    # Sanity: count didn't go negative.
    detail = await app_client.get(
        "/api/communities/marketing-ops", headers=auth_header(token)
    )
    assert detail.json()["community"]["member_count"] == 0


@pytest.mark.asyncio
async def test_join_then_leave_decrements_count(app_client, seed_test_communities):
    """F-COM-2: join + leave round-trips member_count to 0."""
    body = await signup_user(app_client, "alice@example.com")
    token = body["jwt"]

    await app_client.post(
        "/api/communities/marketing-ops/join", headers=auth_header(token)
    )
    await app_client.post(
        "/api/communities/marketing-ops/leave", headers=auth_header(token)
    )

    detail = await app_client.get(
        "/api/communities/marketing-ops", headers=auth_header(token)
    )
    assert detail.json()["community"]["member_count"] == 0
    assert detail.json()["is_member"] is False


@pytest.mark.asyncio
async def test_founder_cannot_join_or_leave(app_client, seed_test_communities):
    """F-COM-2 + F-COM-8: founders blocked from join AND leave."""
    body = await signup_founder(app_client, "frank@example.com")
    token = body["jwt"]

    r1 = await app_client.post(
        "/api/communities/marketing-ops/join", headers=auth_header(token)
    )
    assert r1.status_code == 403
    assert r1.json()["detail"]["error"] == "role_mismatch"

    r2 = await app_client.post(
        "/api/communities/marketing-ops/leave", headers=auth_header(token)
    )
    assert r2.status_code == 403
    assert r2.json()["detail"]["error"] == "role_mismatch"
