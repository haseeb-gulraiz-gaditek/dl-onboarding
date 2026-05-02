"""Tests for comment endpoint (cycle: communities-and-flat-comments).

Covers F-COM-5, F-COM-8 (founder write block on POST /api/comments).
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


async def _create_post(client, token):
    return await client.post(
        "/api/posts",
        json={
            "community_slug": "marketing-ops",
            "title": "Some post",
            "body_md": "Body",
        },
        headers=auth_header(token),
    )


@pytest.mark.asyncio
async def test_create_comment_increments_post_count_and_last_activity(
    app_client, seed_test_communities
):
    """F-COM-5: comment_count++ and last_activity_at bumped."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    post_resp = await _create_post(app_client, token)
    post_id = post_resp.json()["id"]
    initial_activity = post_resp.json()["last_activity_at"]

    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": "First comment"},
        headers=auth_header(token),
    )
    assert rc.status_code == 201, rc.text
    assert rc.json()["comment"]["body_md"] == "First comment"

    # Verify count and last_activity_at on the post detail.
    detail = await app_client.get(
        f"/api/posts/{post_id}", headers=auth_header(token)
    )
    assert detail.json()["post"]["comment_count"] == 1
    assert detail.json()["post"]["last_activity_at"] >= initial_activity


@pytest.mark.asyncio
async def test_parent_comment_id_is_silently_ignored(
    app_client, seed_test_communities
):
    """F-COM-5: clients sending parent_comment_id cannot create threading;
    schema doesn't accept it, but Pydantic by default ignores extra
    fields → comment is created flat."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]

    post_resp = await _create_post(app_client, token)
    post_id = post_resp.json()["id"]

    rc = await app_client.post(
        "/api/comments",
        json={
            "post_id": post_id,
            "body_md": "Reply attempt",
            "parent_comment_id": "507f1f77bcf86cd799439011",
        },
        headers=auth_header(token),
    )
    assert rc.status_code == 201, rc.text

    # Verify the stored doc has parent_comment_id = None.
    from app.db.comments import comments_collection
    from bson import ObjectId
    stored = await comments_collection().find_one(
        {"_id": ObjectId(rc.json()["comment"]["id"])}
    )
    assert stored is not None
    assert stored["parent_comment_id"] is None


@pytest.mark.asyncio
async def test_empty_body_returns_field_required(
    app_client, seed_test_communities
):
    """F-COM-5: empty body_md → 400 field_required(body_md)."""
    body = await signup_user(app_client, "maya@example.com")
    token = body["jwt"]
    post_resp = await _create_post(app_client, token)
    post_id = post_resp.json()["id"]

    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": ""},
        headers=auth_header(token),
    )
    assert rc.status_code == 400
    detail = rc.json().get("detail") or rc.json()
    err_obj = detail if isinstance(detail, dict) else detail[0]
    assert err_obj.get("error") == "field_required"
    assert err_obj.get("field") == "body_md"


@pytest.mark.asyncio
async def test_unknown_post_id_returns_404(app_client, seed_test_communities):
    """F-COM-5: unknown post_id → 404 post_not_found."""
    body = await signup_user(app_client, "maya@example.com")
    fake_id = "507f1f77bcf86cd799439011"
    rc = await app_client.post(
        "/api/comments",
        json={"post_id": fake_id, "body_md": "anything"},
        headers=auth_header(body["jwt"]),
    )
    assert rc.status_code == 404
    assert rc.json()["detail"]["error"] == "post_not_found"


@pytest.mark.asyncio
async def test_founder_cannot_comment(app_client, seed_test_communities):
    """F-COM-5 + F-COM-8: founder → 403 role_mismatch."""
    user_body = await signup_user(app_client, "maya@example.com")
    post_resp = await _create_post(app_client, user_body["jwt"])
    post_id = post_resp.json()["id"]

    fb = await signup_founder(app_client, "frank@example.com")
    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": "I am a founder!"},
        headers=auth_header(fb["jwt"]),
    )
    assert rc.status_code == 403
    assert rc.json()["detail"]["error"] == "role_mismatch"
