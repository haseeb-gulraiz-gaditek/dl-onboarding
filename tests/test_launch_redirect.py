"""Tests for click-tracking redirect (cycle: launch-publish-...).

Covers F-PUB-3.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder_with_token,
    submit_test_launch,
)


@pytest.mark.asyncio
async def test_redirect_with_valid_user_hash_logs_engagement_and_302s(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-3: valid u → engagement row gets user_id; 302 to product_url."""
    from bson import ObjectId
    from app.db.engagements import engagements_collection
    from app.launches.redirect import make_user_hash
    from tests.conftest import signup_user

    user = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(user["user"]["id"])
    u_hash = make_user_hash(user_id)

    # Approved launch needed first.
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    r = await app_client.get(
        f"/r/{launch_id}?u={u_hash}&s=concierge_nudge",
        follow_redirects=False,
    )
    assert r.status_code == 302, r.text
    assert r.headers["location"] == "https://acme.io"

    docs = await engagements_collection().find(
        {"launch_id": ObjectId(launch_id), "action": "click"}
    ).to_list(length=None)
    assert len(docs) == 1
    assert docs[0]["user_id"] == user_id
    assert docs[0]["surface"] == "concierge_nudge"


@pytest.mark.asyncio
async def test_redirect_without_hash_logs_anonymous_click(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-3: missing/invalid u → engagement row with user_id=null."""
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

    r = await app_client.get(f"/r/{launch_id}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://acme.io"

    docs = await engagements_collection().find(
        {"launch_id": ObjectId(launch_id)}
    ).to_list(length=None)
    click_docs = [d for d in docs if d["action"] == "click"]
    assert len(click_docs) == 1
    assert click_docs[0]["user_id"] is None


@pytest.mark.asyncio
async def test_redirect_unknown_launch_returns_404(app_client):
    """F-PUB-3: unknown launch_id → 404 launch_not_found."""
    fake = "507f1f77bcf86cd799439011"
    r = await app_client.get(f"/r/{fake}", follow_redirects=False)
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "launch_not_found"
