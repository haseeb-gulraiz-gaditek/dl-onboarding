"""Tests for /api/founders/dashboard + /api/founders/launches/{id}/analytics.

Covers F-DASH-2, F-DASH-3, plus the constitutional anonymization audit.
"""
import json

import pytest

from tests.conftest import (
    auth_header,
    seed_engagement,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


_FORBIDDEN_KEYS = {
    "user_id", "email", "display_name", "name", "founder_user_id",
}


def _scan_for_user_fields(payload, path: str = "$") -> list[str]:
    """Return a list of dotted-paths where forbidden user-identity
    keys appear anywhere in the JSON payload. Used by the
    anonymization audit (F-DASH-2 + F-DASH-3 constitutional check)."""
    hits: list[str] = []
    if isinstance(payload, dict):
        for k, v in payload.items():
            here = f"{path}.{k}"
            if k in _FORBIDDEN_KEYS:
                hits.append(here)
            hits.extend(_scan_for_user_fields(v, here))
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            hits.extend(_scan_for_user_fields(item, f"{path}[{i}]"))
    return hits


# ---- F-DASH-2: dashboard ----


@pytest.mark.asyncio
async def test_dashboard_returns_only_own_launches(
    app_client, seed_test_communities
):
    """F-DASH-2: dashboard scoped to the requesting founder."""
    f1 = await signup_founder_with_token(app_client, "aamir@example.com")
    f2 = await signup_founder_with_token(app_client, "tara@example.com")
    await submit_test_launch(app_client, f1["token"])
    await submit_test_launch(
        app_client, f2["token"], product_url="https://tara.dev"
    )

    r = await app_client.get(
        "/api/founders/dashboard", headers=auth_header(f1["token"])
    )
    assert r.status_code == 200
    body = r.json()
    urls = [card["product_url"] for card in body["dashboard"]]
    assert urls == ["https://acme.io"]


@pytest.mark.asyncio
async def test_dashboard_pending_launches_show_zero_metrics(
    app_client, seed_test_communities
):
    """F-DASH-2: pending launches appear with all-zero metrics."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    await submit_test_launch(app_client, f["token"])

    r = await app_client.get(
        "/api/founders/dashboard", headers=auth_header(f["token"])
    )
    card = r.json()["dashboard"][0]
    assert card["verification_status"] == "pending"
    assert card["matched_count"] == 0
    assert card["tell_me_more_count"] == 0
    assert card["skip_count"] == 0
    assert card["total_clicks"] == 0


@pytest.mark.asyncio
async def test_dashboard_summary_counts_match_engagements(
    app_client, seed_test_communities, admin_token
):
    """F-DASH-2: summary metrics reflect actual engagement rows."""
    from bson import ObjectId

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = ObjectId(res["body"]["id"])

    # Approve so it's "approved" status.
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    # Seed engagement events.
    u1, u2, u3 = ObjectId(), ObjectId(), ObjectId()
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="view", user_id=u1)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="view", user_id=u2)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="tell_me_more", user_id=u1)
    await seed_engagement(launch_id=launch_id, surface="concierge_nudge", action="skip", user_id=u2)
    await seed_engagement(launch_id=launch_id, surface="community_post", action="click")
    await seed_engagement(launch_id=launch_id, surface="redirect", action="click")

    r = await app_client.get(
        "/api/founders/dashboard", headers=auth_header(f["token"])
    )
    card = r.json()["dashboard"][0]
    # Note: the publish_launch orchestrator already wrote some
    # engagement rows during /approve (e.g., one per community
    # fan-out + nudge views for matched profiles). Use >= where
    # the orchestrator could have padded.
    assert card["matched_count"] >= 2
    assert card["tell_me_more_count"] == 1
    assert card["skip_count"] == 1
    assert card["total_clicks"] >= 2


@pytest.mark.asyncio
async def test_dashboard_user_role_returns_403(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/founders/dashboard", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"


@pytest.mark.asyncio
async def test_dashboard_unauthenticated_returns_401(app_client):
    r = await app_client.get("/api/founders/dashboard")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


# ---- F-DASH-3: per-launch analytics ----


@pytest.mark.asyncio
async def test_owner_gets_analytics_with_breakdowns(
    app_client, seed_test_communities, admin_token
):
    """F-DASH-3: owner sees clicks_by_community + clicks_by_surface."""
    from bson import ObjectId

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"],
        target_community_slugs=["marketing-ops", "weekly-launches"],
    )
    launch_id = ObjectId(res["body"]["id"])
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    # Seed click engagements with metadata.
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "marketing-ops"},
    )
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "marketing-ops"},
    )
    await seed_engagement(
        launch_id=launch_id, surface="community_post", action="click",
        metadata={"community_slug": "weekly-launches"},
    )
    await seed_engagement(
        launch_id=launch_id, surface="concierge_nudge", action="click",
    )

    r = await app_client.get(
        f"/api/founders/launches/{launch_id}/analytics",
        headers=auth_header(f["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["clicks_by_community"]["marketing-ops"] == 2
    assert body["clicks_by_community"]["weekly-launches"] == 1
    assert body["clicks_by_surface"]["community_post"] == 3
    assert body["clicks_by_surface"]["concierge_nudge"] == 1


@pytest.mark.asyncio
async def test_non_owner_founder_gets_404(
    app_client, seed_test_communities
):
    """F-DASH-3: existence-leak protection — different founder → 404."""
    f1 = await signup_founder_with_token(app_client, "aamir@example.com")
    f2 = await signup_founder_with_token(app_client, "tara@example.com")
    res = await submit_test_launch(app_client, f1["token"])

    r = await app_client.get(
        f"/api/founders/launches/{res['body']['id']}/analytics",
        headers=auth_header(f2["token"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "launch_not_found"


@pytest.mark.asyncio
async def test_unknown_launch_id_returns_404(app_client):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    fake = "507f1f77bcf86cd799439011"
    r = await app_client.get(
        f"/api/founders/launches/{fake}/analytics",
        headers=auth_header(f["token"]),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_malformed_launch_id_returns_404(app_client):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    r = await app_client.get(
        "/api/founders/launches/not-an-oid/analytics",
        headers=auth_header(f["token"]),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_user_caller_returns_403(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    user = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        f"/api/founders/launches/{res['body']['id']}/analytics",
        headers=auth_header(user["jwt"]),
    )
    assert r.status_code == 403


# ---- Constitutional anonymization audit ----


@pytest.mark.asyncio
async def test_dashboard_response_contains_no_user_identifying_fields(
    app_client, seed_test_communities, admin_token
):
    """Constitutional: dashboard response has zero user-identity fields."""
    from bson import ObjectId

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = ObjectId(res["body"]["id"])
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    # Seed a real-looking nudge so any leak would surface.
    await seed_engagement(
        launch_id=launch_id, surface="concierge_nudge", action="view",
        user_id=ObjectId(),
    )

    r = await app_client.get(
        "/api/founders/dashboard", headers=auth_header(f["token"])
    )
    payload = r.json()
    leaks = _scan_for_user_fields(payload)
    assert leaks == [], f"User-identifying fields leaked at: {leaks}"


@pytest.mark.asyncio
async def test_analytics_response_contains_no_user_identifying_fields(
    app_client, seed_test_communities, admin_token
):
    """Constitutional: analytics response has zero user-identity fields."""
    from bson import ObjectId

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    launch_id = ObjectId(res["body"]["id"])
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    await seed_engagement(
        launch_id=launch_id, surface="concierge_nudge", action="tell_me_more",
        user_id=ObjectId(),
    )

    r = await app_client.get(
        f"/api/founders/launches/{launch_id}/analytics",
        headers=auth_header(f["token"]),
    )
    payload = r.json()
    leaks = _scan_for_user_fields(payload)
    assert leaks == [], f"User-identifying fields leaked at: {leaks}"
