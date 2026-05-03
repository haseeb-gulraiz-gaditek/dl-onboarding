"""Tests for the community_reply trigger inside POST /api/comments.

Per spec-delta notifications-in-app F-NOTIF-7 / F-COM-5 MODIFIED.
"""
import pytest

from tests.conftest import auth_header, signup_user


async def _create_post(client, token):
    return await client.post(
        "/api/posts",
        json={
            "community_slug": "marketing-ops",
            "title": "Looking for a Notion plugin",
            "body_md": "Anyone use one that auto-summarizes meeting notes?",
        },
        headers=auth_header(token),
    )


@pytest.mark.asyncio
async def test_comment_on_others_post_writes_community_reply_notification(
    app_client, seed_test_communities
):
    """F-NOTIF-7: comment on someone else's post fires the trigger."""
    from bson import ObjectId
    from app.db.notifications import notifications_collection

    sam = await signup_user(app_client, "sam@example.com")
    sam_id = ObjectId(sam["user"]["id"])
    post_resp = await _create_post(app_client, sam["jwt"])
    post_id = post_resp.json()["id"]

    maya = await signup_user(app_client, "maya@example.com")
    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": "Try Reflect AI."},
        headers=auth_header(maya["jwt"]),
    )
    assert rc.status_code == 201

    # Notification went to the post author (Sam), payload references the comment.
    notes = await notifications_collection().find(
        {"user_id": sam_id, "kind": "community_reply"}
    ).to_list(length=None)
    assert len(notes) == 1
    payload = notes[0]["payload"]
    assert payload["post_id"] == post_id
    assert payload["comment_id"] == rc.json()["comment"]["id"]
    assert payload["commenter_display_name"] == "maya"


@pytest.mark.asyncio
async def test_self_reply_does_not_create_notification(
    app_client, seed_test_communities
):
    """F-NOTIF-7: commenting on your own post is a no-op."""
    from bson import ObjectId
    from app.db.notifications import notifications_collection

    sam = await signup_user(app_client, "sam@example.com")
    sam_id = ObjectId(sam["user"]["id"])
    post_resp = await _create_post(app_client, sam["jwt"])
    post_id = post_resp.json()["id"]

    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": "Update: I went with Reflect AI."},
        headers=auth_header(sam["jwt"]),
    )
    assert rc.status_code == 201

    notes = await notifications_collection().find(
        {"user_id": sam_id, "kind": "community_reply"}
    ).to_list(length=None)
    assert notes == []  # no self-notification


@pytest.mark.asyncio
async def test_notification_failure_does_not_abort_comment(
    app_client, seed_test_communities, monkeypatch
):
    """F-NOTIF-7: trigger is best-effort; an exception in the
    notification write does NOT abort the comment write."""
    sam = await signup_user(app_client, "sam@example.com")
    post_resp = await _create_post(app_client, sam["jwt"])
    post_id = post_resp.json()["id"]

    # Patch insert_notification at the binding inside app.api.comments.
    async def _boom(*args, **kwargs):
        raise RuntimeError("simulated mongo blip")

    monkeypatch.setattr(
        "app.api.comments.insert_notification", _boom
    )

    maya = await signup_user(app_client, "maya@example.com")
    rc = await app_client.post(
        "/api/comments",
        json={"post_id": post_id, "body_md": "Trying it out."},
        headers=auth_header(maya["jwt"]),
    )
    assert rc.status_code == 201, rc.text  # comment write succeeded
