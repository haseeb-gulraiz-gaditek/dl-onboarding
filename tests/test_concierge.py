"""Tests for concierge respond endpoint (cycle: launch-publish-...).

Covers F-PUB-5.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


@pytest.mark.asyncio
async def test_tell_me_more_returns_redirect_url_and_logs_engagement(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-5: tell_me_more → engagement row + redirect_url with hash."""
    from bson import ObjectId
    from app.db.engagements import engagements_collection
    from app.launches.redirect import make_user_hash

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
    user_id = ObjectId(user["user"]["id"])

    r = await app_client.post(
        "/api/concierge/respond",
        json={"launch_id": launch_id, "action": "tell_me_more"},
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is True
    assert body["redirect_url"] is not None
    assert make_user_hash(user_id) in body["redirect_url"]
    assert "concierge_nudge" in body["redirect_url"]

    docs = await engagements_collection().find(
        {"launch_id": ObjectId(launch_id), "action": "tell_me_more"}
    ).to_list(length=None)
    assert len(docs) == 1
    assert docs[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_skip_returns_null_redirect_and_logs_engagement(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-5: skip → engagement row + redirect_url=null."""
    from bson import ObjectId
    from app.db.engagements import engagements_collection

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
    r = await app_client.post(
        "/api/concierge/respond",
        json={"launch_id": launch_id, "action": "skip"},
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is True
    assert body["redirect_url"] is None

    docs = await engagements_collection().find(
        {"launch_id": ObjectId(launch_id), "action": "skip"}
    ).to_list(length=None)
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_founder_cannot_respond(
    app_client, seed_test_communities, admin_token
):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    fb = await signup_founder(app_client, "frank@example.com")
    r = await app_client.post(
        "/api/concierge/respond",
        json={"launch_id": launch_id, "action": "tell_me_more"},
        headers=auth_header(fb["jwt"]),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unknown_launch_returns_404(app_client):
    user = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/concierge/respond",
        json={"launch_id": "507f1f77bcf86cd799439011", "action": "skip"},
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "launch_not_found"
