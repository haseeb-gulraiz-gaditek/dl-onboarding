"""Tests for admin-side launch verification (cycle: founder-launch-...).

Covers F-LAUNCH-3, F-LAUNCH-4, F-LAUNCH-5, F-LAUNCH-7, F-LAUNCH-8.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


# ---- F-LAUNCH-3 queue + detail ----


@pytest.mark.asyncio
async def test_admin_queue_defaults_to_pending(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    await submit_test_launch(app_client, f["token"])

    r = await app_client.get(
        "/admin/launches", headers=auth_header(admin_token["token"])
    )
    assert r.status_code == 200
    cards = r.json()["launches"]
    assert len(cards) == 1
    assert cards[0]["verification_status"] == "pending"
    assert cards[0]["founder_email"] == "aamir@example.com"


@pytest.mark.asyncio
async def test_admin_queue_status_filter(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    await submit_test_launch(app_client, f["token"])

    r = await app_client.get(
        "/admin/launches?status=approved",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    assert r.json()["launches"] == []


@pytest.mark.asyncio
async def test_admin_detail_includes_founder_email(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r = await app_client.get(
        f"/admin/launches/{launch_id}",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["founder_email"] == "aamir@example.com"
    assert body["icp_description"]


@pytest.mark.asyncio
async def test_non_admin_cannot_access_queue(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/admin/launches", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
    # cycle #3's existing error shape; F-LAUNCH-3 reuses require_admin().
    assert r.json()["detail"]["error"] == "admin_only"


# ---- F-LAUNCH-4 approve ----


@pytest.mark.asyncio
async def test_approve_creates_founder_launched_tool(app_client, admin_token):
    """F-LAUNCH-4: approve creates tools_founder_launched row with the
    derived slug, is_founder_launched=True, launched_via_id."""
    from app.db.tools_founder_launched import find_by_slug
    from bson import ObjectId

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["verification_status"] == "approved"
    assert body["approved_tool_slug"] == "acme-io"
    assert body["reviewed_by"] == admin_token["email"]

    tool = await find_by_slug("acme-io")
    assert tool is not None
    assert tool["is_founder_launched"] is True
    assert tool["launched_via_id"] == ObjectId(launch_id)
    assert tool["source"] == "founder_launch"
    assert tool["curation_status"] == "approved"


@pytest.mark.asyncio
async def test_approve_writes_notification(app_client, admin_token):
    """F-LAUNCH-4 + F-LAUNCH-8: launch_approved notification written."""
    from app.db.notifications import notifications_collection

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    note = await notifications_collection().find_one(
        {"user_id": f["user_id"], "kind": "launch_approved"}
    )
    assert note is not None
    assert note["payload"]["launch_id"] == launch_id
    assert note["payload"]["tool_slug"] == "acme-io"


@pytest.mark.asyncio
async def test_re_approving_returns_409(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r1 = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r1.status_code == 200
    r2 = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"] == "launch_already_resolved"


@pytest.mark.asyncio
async def test_approving_rejected_returns_409(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    rj = await app_client.post(
        f"/admin/launches/{launch_id}/reject",
        json={"comment": "Not a fit."},
        headers=auth_header(admin_token["token"]),
    )
    assert rj.status_code == 200

    rap = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert rap.status_code == 409


# ---- F-LAUNCH-5 reject ----


@pytest.mark.asyncio
async def test_reject_without_comment_returns_400(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r = await app_client.post(
        f"/admin/launches/{launch_id}/reject",
        json={},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 400
    detail = r.json().get("detail") or r.json()
    err = detail if isinstance(detail, dict) else detail[0]
    assert err.get("error") == "field_required"
    assert err.get("field") == "comment"


@pytest.mark.asyncio
async def test_reject_stores_comment_and_writes_notification(
    app_client, admin_token
):
    from app.db.notifications import notifications_collection

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r = await app_client.post(
        f"/admin/launches/{launch_id}/reject",
        json={"comment": "Too early-stage; resubmit when you have signups."},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verification_status"] == "rejected"
    assert "early-stage" in body["rejection_comment"]

    note = await notifications_collection().find_one(
        {"user_id": f["user_id"], "kind": "launch_rejected"}
    )
    assert note is not None
    assert "early-stage" in note["payload"]["comment"]


@pytest.mark.asyncio
async def test_re_rejecting_returns_409(app_client, admin_token):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = res["body"]["id"]

    r1 = await app_client.post(
        f"/admin/launches/{launch_id}/reject",
        json={"comment": "x"},
        headers=auth_header(admin_token["token"]),
    )
    assert r1.status_code == 200
    r2 = await app_client.post(
        f"/admin/launches/{launch_id}/reject",
        json={"comment": "y"},
        headers=auth_header(admin_token["token"]),
    )
    assert r2.status_code == 409


# ---- F-LAUNCH-7 collection seal ----


@pytest.mark.asyncio
async def test_tools_founder_launched_refuses_wrong_source(app_client):
    from app.db.tools_founder_launched import insert as insert_fl_tool

    with pytest.raises(ValueError):
        await insert_fl_tool({"slug": "evil", "source": "manual"})
