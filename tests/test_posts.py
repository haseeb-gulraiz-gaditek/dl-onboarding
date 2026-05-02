"""Tests for post endpoints (cycle: communities-and-flat-comments).

Covers F-COM-3, F-COM-4, F-COM-8 (founder write block on POST /api/posts).
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


async def _create_post(client, token, **overrides):
    payload = {
        "community_slug": "marketing-ops",
        "title": "Hello world",
        "body_md": "Some content here.",
    }
    payload.update(overrides)
    return await client.post(
        "/api/posts", json=payload, headers=auth_header(token)
    )


# ---- F-COM-3 create ----


@pytest.mark.asyncio
async def test_create_post_returns_201_with_persisted_row(
    app_client, seed_test_communities
):
    """F-COM-3: valid post → 201 + persisted document."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(app_client, body["jwt"])
    assert r.status_code == 201, r.text
    post = r.json()
    assert post["title"] == "Hello world"
    assert post["community_slug"] == "marketing-ops"
    assert post["cross_posted_to"] == []
    assert post["attached_launch_id"] is None
    assert post["vote_score"] == 0
    assert post["comment_count"] == 0


@pytest.mark.asyncio
async def test_create_post_with_valid_cross_posts(app_client, seed_test_communities):
    """F-COM-3: cross_post_slugs up to 2 valid extras → 201."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client,
        body["jwt"],
        cross_post_slugs=["engineering-bench", "weekly-launches"],
    )
    assert r.status_code == 201
    assert sorted(r.json()["cross_posted_to"]) == sorted(
        ["engineering-bench", "weekly-launches"]
    )


@pytest.mark.asyncio
async def test_cross_post_too_many_returns_400(app_client, seed_test_communities):
    """F-COM-3: >2 cross_post_slugs → 400 cross_post_invalid."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client,
        body["jwt"],
        cross_post_slugs=["engineering-bench", "weekly-launches", "marketing-ops"],
    )
    # 3 entries exceeds MAX_CROSS_POSTS=2 (one of the violations triggers first).
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "cross_post_invalid"


@pytest.mark.asyncio
async def test_cross_post_includes_home_returns_400(
    app_client, seed_test_communities
):
    """F-COM-3: cross_post_slugs containing the home slug → 400."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client, body["jwt"], cross_post_slugs=["marketing-ops"]
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "cross_post_invalid"


@pytest.mark.asyncio
async def test_cross_post_duplicates_returns_400(
    app_client, seed_test_communities
):
    """F-COM-3: duplicate cross_post_slugs → 400."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client,
        body["jwt"],
        cross_post_slugs=["engineering-bench", "engineering-bench"],
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "cross_post_invalid"


@pytest.mark.asyncio
async def test_cross_post_unknown_slug_returns_400(
    app_client, seed_test_communities
):
    """F-COM-3: cross_post_slugs containing an unknown slug → 400."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client, body["jwt"], cross_post_slugs=["does-not-exist"]
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "cross_post_invalid"


@pytest.mark.asyncio
async def test_empty_title_returns_field_required(
    app_client, seed_test_communities
):
    """F-COM-3: empty title → 400 field_required(title) via validator."""
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/posts",
        json={"community_slug": "marketing-ops", "title": "", "body_md": "hi"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    detail = r.json().get("detail") or r.json()
    # The global handler returns {"error": "field_required", "field": "title"}.
    err_obj = detail if isinstance(detail, dict) else detail[0]
    assert err_obj.get("error") == "field_required"
    assert err_obj.get("field") == "title"


@pytest.mark.asyncio
async def test_unknown_community_returns_404(app_client, seed_test_communities):
    """F-COM-3: unknown community_slug → 404 community_not_found."""
    body = await signup_user(app_client, "maya@example.com")
    r = await _create_post(
        app_client, body["jwt"], community_slug="does-not-exist"
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "community_not_found"


@pytest.mark.asyncio
async def test_founder_cannot_create_post(app_client, seed_test_communities):
    """F-COM-3 + F-COM-8: founder → 403 role_mismatch."""
    body = await signup_founder(app_client, "frank@example.com")
    r = await _create_post(app_client, body["jwt"])
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"


# ---- F-COM-4 feed + detail ----


@pytest.mark.asyncio
async def test_feed_returns_newest_first(app_client, seed_test_communities):
    """F-COM-4: feed sorted by created_at DESC."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    titles = ["First", "Second", "Third"]
    for t in titles:
        r = await _create_post(app_client, token, title=t)
        assert r.status_code == 201

    feed = await app_client.get(
        "/api/communities/marketing-ops/posts", headers=auth_header(token)
    )
    assert feed.status_code == 200
    assert [p["title"] for p in feed.json()["posts"]] == ["Third", "Second", "First"]


@pytest.mark.asyncio
async def test_feed_includes_cross_posted_into_community(
    app_client, seed_test_communities
):
    """F-COM-4: posts cross-posting INTO a community appear in its feed."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    # Home = marketing-ops, cross-posted to engineering-bench.
    r = await _create_post(
        app_client, token, cross_post_slugs=["engineering-bench"]
    )
    assert r.status_code == 201

    feed_eng = await app_client.get(
        "/api/communities/engineering-bench/posts", headers=auth_header(token)
    )
    assert feed_eng.status_code == 200
    titles = [p["title"] for p in feed_eng.json()["posts"]]
    assert "Hello world" in titles


@pytest.mark.asyncio
async def test_feed_pagination_cursor(app_client, seed_test_communities):
    """F-COM-4: ?before&limit cursor pagination works."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    for i in range(5):
        r = await _create_post(app_client, token, title=f"Post {i}")
        assert r.status_code == 201

    page1 = await app_client.get(
        "/api/communities/marketing-ops/posts?limit=2",
        headers=auth_header(token),
    )
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["posts"]) == 2
    assert body1["next_before"] is not None

    page2 = await app_client.get(
        f"/api/communities/marketing-ops/posts?limit=2&before={body1['next_before']}",
        headers=auth_header(token),
    )
    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2["posts"]) == 2

    # Last page has fewer than limit → next_before should be None.
    page3 = await app_client.get(
        f"/api/communities/marketing-ops/posts?limit=10&before={body2['next_before']}",
        headers=auth_header(token),
    )
    body3 = page3.json()
    assert body3["next_before"] is None


@pytest.mark.asyncio
async def test_post_detail_includes_comments_and_user_vote(
    app_client, seed_test_communities
):
    """F-COM-4: GET /api/posts/{id} returns post + comments newest-first + user_vote."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    create = await _create_post(app_client, token)
    post_id = create.json()["id"]

    # Add 2 comments.
    for i in range(2):
        rc = await app_client.post(
            "/api/comments",
            json={"post_id": post_id, "body_md": f"Comment {i}"},
            headers=auth_header(token),
        )
        assert rc.status_code == 201

    detail = await app_client.get(
        f"/api/posts/{post_id}", headers=auth_header(token)
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["post"]["id"] == post_id
    assert body["post"]["user_vote"] == 0
    assert len(body["comments"]) == 2
    assert body["comments"][0]["body_md"] == "Comment 1"  # newest first
    assert body["comments"][1]["body_md"] == "Comment 0"


@pytest.mark.asyncio
async def test_post_detail_unknown_id_returns_404(
    app_client, seed_test_communities
):
    """F-COM-4: unknown post id → 404 post_not_found."""
    body = await signup_user(app_client, "maya@example.com")
    fake_id = "507f1f77bcf86cd799439011"
    r = await app_client.get(
        f"/api/posts/{fake_id}", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "post_not_found"
