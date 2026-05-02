"""Tests for vote endpoint (cycle: communities-and-flat-comments).

Covers F-COM-6 (insert/toggle/flip), F-COM-7 (tool voting hooks
tools_seed.vote_score), F-COM-8 (founder write block).
"""
import pytest

from tests.conftest import (
    auth_header,
    seed_test_catalog,  # noqa: F401  -- imported indirectly by fixture
    signup_founder,
    signup_user,
)


async def _create_post(client, token):
    return await client.post(
        "/api/posts",
        json={
            "community_slug": "marketing-ops",
            "title": "post for voting",
            "body_md": "x",
        },
        headers=auth_header(token),
    )


# ---- F-COM-6 three-way semantics on posts ----


@pytest.mark.asyncio
async def test_first_vote_inserts_and_bumps_score(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]
    post = (await _create_post(app_client, token)).json()

    r = await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": 1},
        headers=auth_header(token),
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"voted": True, "current_direction": 1}

    detail = await app_client.get(
        f"/api/posts/{post['id']}", headers=auth_header(token)
    )
    assert detail.json()["post"]["vote_score"] == 1
    assert detail.json()["post"]["user_vote"] == 1


@pytest.mark.asyncio
async def test_revote_same_direction_toggles_off(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]
    post = (await _create_post(app_client, token)).json()

    await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": 1},
        headers=auth_header(token),
    )
    r = await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": 1},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    assert r.json() == {"voted": False, "current_direction": 0}

    detail = await app_client.get(
        f"/api/posts/{post['id']}", headers=auth_header(token)
    )
    assert detail.json()["post"]["vote_score"] == 0
    assert detail.json()["post"]["user_vote"] == 0


@pytest.mark.asyncio
async def test_revote_opposite_direction_flips_by_two(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]
    post = (await _create_post(app_client, token)).json()

    await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": 1},
        headers=auth_header(token),
    )
    r = await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": -1},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    assert r.json() == {"voted": True, "current_direction": -1}

    detail = await app_client.get(
        f"/api/posts/{post['id']}", headers=auth_header(token)
    )
    assert detail.json()["post"]["vote_score"] == -1


# ---- F-COM-6 invalid input ----


@pytest.mark.asyncio
async def test_invalid_target_id_returns_400(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    fake_oid = "507f1f77bcf86cd799439011"
    r = await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": fake_oid, "direction": 1},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "target_invalid"


@pytest.mark.asyncio
async def test_invalid_target_type_returns_400(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/votes",
        json={"target_type": "asteroid", "target_id": "507f1f77bcf86cd799439011", "direction": 1},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    assert r.json().get("detail", {}).get("error") == "target_invalid" or \
           (r.json().get("error") == "target_invalid")


# ---- F-COM-6 founder block ----


@pytest.mark.asyncio
async def test_founder_cannot_vote(app_client, seed_test_communities):
    user_body = await signup_user(app_client, "maya@example.com")
    post = (await _create_post(app_client, user_body["jwt"])).json()

    fb = await signup_founder(app_client, "frank@example.com")
    r = await app_client.post(
        "/api/votes",
        json={"target_type": "post", "target_id": post["id"], "direction": 1},
        headers=auth_header(fb["jwt"]),
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"


# ---- F-COM-7 tool voting ----


@pytest.mark.asyncio
async def test_tool_vote_updates_tools_seed_vote_score(
    app_client, seed_test_communities, seed_test_catalog
):
    """F-COM-7: voting on a tool bumps tools_seed.vote_score; toggle
    and flip work for tools too."""
    from app.db.tools_seed import tools_seed_collection

    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    tool = await tools_seed_collection().find_one({"slug": "test-tool-approved"})
    assert tool is not None
    tool_id_str = str(tool["_id"])

    # Insert.
    r1 = await app_client.post(
        "/api/votes",
        json={"target_type": "tool", "target_id": tool_id_str, "direction": 1},
        headers=auth_header(token),
    )
    assert r1.status_code == 200
    assert r1.json() == {"voted": True, "current_direction": 1}

    fresh = await tools_seed_collection().find_one({"_id": tool["_id"]})
    assert fresh.get("vote_score") == 1

    # Flip to -1 → swing of 2.
    r2 = await app_client.post(
        "/api/votes",
        json={"target_type": "tool", "target_id": tool_id_str, "direction": -1},
        headers=auth_header(token),
    )
    assert r2.status_code == 200
    fresh = await tools_seed_collection().find_one({"_id": tool["_id"]})
    assert fresh["vote_score"] == -1

    # Toggle off → back to 0.
    r3 = await app_client.post(
        "/api/votes",
        json={"target_type": "tool", "target_id": tool_id_str, "direction": -1},
        headers=auth_header(token),
    )
    assert r3.status_code == 200
    assert r3.json() == {"voted": False, "current_direction": 0}
    fresh = await tools_seed_collection().find_one({"_id": tool["_id"]})
    assert fresh["vote_score"] == 0


# ---- F-COM-6 voting on comments ----


@pytest.mark.asyncio
async def test_comment_vote_updates_comment_score(
    app_client, seed_test_communities
):
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]
    post = (await _create_post(app_client, token)).json()

    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post["id"], "body_md": "vote on me"},
        headers=auth_header(token),
    )
    comment_id = rc.json()["comment"]["id"]

    r = await app_client.post(
        "/api/votes",
        json={"target_type": "comment", "target_id": comment_id, "direction": 1},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    assert r.json() == {"voted": True, "current_direction": 1}

    detail = await app_client.get(
        f"/api/posts/{post['id']}", headers=auth_header(token)
    )
    target_comment = next(c for c in detail.json()["comments"] if c["id"] == comment_id)
    assert target_comment["vote_score"] == 1
    assert target_comment["user_vote"] == 1
