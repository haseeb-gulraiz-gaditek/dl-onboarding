"""Tests for the inbox endpoints (cycle: notifications-in-app).

Covers F-NOTIF-2..6 + role-agnostic surface.
"""
import asyncio

import pytest
from bson import ObjectId

from tests.conftest import (
    auth_header,
    seed_notification,
    signup_founder,
    signup_user,
)


# ---- F-NOTIF-2: list ----


@pytest.mark.asyncio
async def test_list_returns_newest_first(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    # Seed three with deterministic order via small sleeps.
    a = await seed_notification(user_id=user_id, kind="community_reply", payload={"n": 1})
    await asyncio.sleep(0.01)
    b = await seed_notification(user_id=user_id, kind="community_reply", payload={"n": 2})
    await asyncio.sleep(0.01)
    c = await seed_notification(user_id=user_id, kind="community_reply", payload={"n": 3})

    r = await app_client.get(
        "/api/me/notifications", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    ids = [n["id"] for n in r.json()["notifications"]]
    assert ids == [str(c["_id"]), str(b["_id"]), str(a["_id"])]


@pytest.mark.asyncio
async def test_list_unread_only_filter(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(user_id=user_id, kind="community_reply", read=True)
    await seed_notification(user_id=user_id, kind="community_reply", read=False)

    r = await app_client.get(
        "/api/me/notifications?unread_only=true",
        headers=auth_header(body["jwt"]),
    )
    notes = r.json()["notifications"]
    assert len(notes) == 1
    assert notes[0]["read"] is False


@pytest.mark.asyncio
async def test_list_scoped_to_self(app_client):
    """F-NOTIF-2: other users' notifications NEVER appear."""
    a = await signup_user(app_client, "alice@example.com")
    b = await signup_user(app_client, "bob@example.com")
    a_id = ObjectId(a["user"]["id"])
    b_id = ObjectId(b["user"]["id"])

    await seed_notification(user_id=a_id, kind="community_reply", payload={"who": "alice"})
    await seed_notification(user_id=b_id, kind="community_reply", payload={"who": "bob"})

    r = await app_client.get(
        "/api/me/notifications", headers=auth_header(a["jwt"])
    )
    notes = r.json()["notifications"]
    assert len(notes) == 1
    assert notes[0]["payload"] == {"who": "alice"}


@pytest.mark.asyncio
async def test_list_empty_returns_empty_arrays(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/me/notifications", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"notifications": [], "next_before": None}


@pytest.mark.asyncio
async def test_list_response_projects_read_bool_not_timestamp(app_client):
    """F-NOTIF-2: response shape projects `read: bool`, not the timestamp."""
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(user_id=user_id, kind="community_reply", read=True)

    r = await app_client.get(
        "/api/me/notifications", headers=auth_header(body["jwt"])
    )
    note = r.json()["notifications"][0]
    assert note["read"] is True
    assert "read_at" not in note  # timestamp not exposed


@pytest.mark.asyncio
async def test_list_pagination_cursor(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    for i in range(5):
        await seed_notification(user_id=user_id, kind="community_reply", payload={"n": i})
        await asyncio.sleep(0.005)

    p1 = await app_client.get(
        "/api/me/notifications?limit=2", headers=auth_header(body["jwt"])
    )
    body1 = p1.json()
    assert len(body1["notifications"]) == 2
    assert body1["next_before"] is not None

    p2 = await app_client.get(
        f"/api/me/notifications?limit=2&before={body1['next_before']}",
        headers=auth_header(body["jwt"]),
    )
    assert len(p2.json()["notifications"]) == 2

    p3 = await app_client.get(
        f"/api/me/notifications?limit=10&before={p2.json()['next_before']}",
        headers=auth_header(body["jwt"]),
    )
    assert p3.json()["next_before"] is None


# ---- F-NOTIF-3: unread count ----


@pytest.mark.asyncio
async def test_unread_count(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(user_id=user_id, kind="community_reply", read=False)
    await seed_notification(user_id=user_id, kind="community_reply", read=False)
    await seed_notification(user_id=user_id, kind="community_reply", read=True)

    r = await app_client.get(
        "/api/me/notifications/unread-count",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    assert r.json() == {"count": 2}


@pytest.mark.asyncio
async def test_unread_count_zero(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/me/notifications/unread-count",
        headers=auth_header(body["jwt"]),
    )
    assert r.json() == {"count": 0}


# ---- F-NOTIF-4: banner ----


@pytest.mark.asyncio
async def test_banner_returns_latest_unread_concierge_nudge(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(user_id=user_id, kind="concierge_nudge", payload={"n": 1})
    await asyncio.sleep(0.01)
    await seed_notification(user_id=user_id, kind="concierge_nudge", payload={"n": 2})

    r = await app_client.get(
        "/api/me/notifications/banner", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    note = r.json()["notification"]
    assert note["payload"]["n"] == 2  # most recent


@pytest.mark.asyncio
async def test_banner_returns_null_when_none_unread(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    # All read.
    await seed_notification(user_id=user_id, kind="concierge_nudge", read=True)

    r = await app_client.get(
        "/api/me/notifications/banner", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"notification": None}


@pytest.mark.asyncio
async def test_banner_skips_other_kinds(app_client):
    """F-NOTIF-4: only concierge_nudge counts for the banner."""
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(user_id=user_id, kind="community_reply", payload={"n": "reply"})
    await seed_notification(user_id=user_id, kind="launch_approved", payload={"n": "ok"})

    r = await app_client.get(
        "/api/me/notifications/banner", headers=auth_header(body["jwt"])
    )
    assert r.json() == {"notification": None}


# ---- F-NOTIF-5: mark single ----


@pytest.mark.asyncio
async def test_mark_read_first_call_returns_updated(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    n = await seed_notification(user_id=user_id, kind="community_reply")

    r = await app_client.post(
        f"/api/me/notifications/{n['_id']}/read",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    assert r.json() == {"updated": True}


@pytest.mark.asyncio
async def test_mark_read_second_call_returns_noop(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    n = await seed_notification(user_id=user_id, kind="community_reply", read=True)

    r = await app_client.post(
        f"/api/me/notifications/{n['_id']}/read",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    assert r.json() == {"updated": False}


@pytest.mark.asyncio
async def test_mark_read_other_users_notification_returns_404(app_client):
    """F-NOTIF-5: existence-leak protection — non-owner gets 404."""
    a = await signup_user(app_client, "alice@example.com")
    b = await signup_user(app_client, "bob@example.com")
    n = await seed_notification(
        user_id=ObjectId(a["user"]["id"]), kind="community_reply"
    )

    r = await app_client.post(
        f"/api/me/notifications/{n['_id']}/read",
        headers=auth_header(b["jwt"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "notification_not_found"


@pytest.mark.asyncio
async def test_mark_read_malformed_id_returns_404(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/me/notifications/not-an-oid/read",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 404


# ---- F-NOTIF-6: read-all ----


@pytest.mark.asyncio
async def test_read_all_marks_all_unread(app_client):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    for _ in range(3):
        await seed_notification(user_id=user_id, kind="community_reply", read=False)
    await seed_notification(user_id=user_id, kind="community_reply", read=True)

    r = await app_client.post(
        "/api/me/notifications/read-all",
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    assert r.json() == {"updated": 3}

    # Subsequent call returns 0.
    r2 = await app_client.post(
        "/api/me/notifications/read-all",
        headers=auth_header(body["jwt"]),
    )
    assert r2.json() == {"updated": 0}


# ---- Inbox role-agnostic ----


@pytest.mark.asyncio
async def test_inbox_role_agnostic_for_founder(app_client):
    """A founder reading /api/me/notifications sees their launch_*
    rows; the same endpoint works for both roles."""
    body = await signup_founder(app_client, "frank@example.com")
    user_id = ObjectId(body["user"]["id"])
    await seed_notification(
        user_id=user_id, kind="launch_approved", payload={"x": 1}
    )

    r = await app_client.get(
        "/api/me/notifications", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    notes = r.json()["notifications"]
    assert len(notes) == 1
    assert notes[0]["kind"] == "launch_approved"
