"""Tests for founder-side launch endpoints (cycle: founder-launch-...).

Covers F-LAUNCH-1, F-LAUNCH-2 plus the role-gating cases.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


# ---- F-LAUNCH-1 submit ----


@pytest.mark.asyncio
async def test_founder_submit_valid_returns_201_and_pending(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(app_client, f["token"])
    assert res["status"] == 201, res["body"]
    body = res["body"]
    assert body["verification_status"] == "pending"
    assert body["product_url"] == "https://acme.io"
    assert body["approved_tool_slug"] is None
    assert body["reviewed_by"] is None


@pytest.mark.asyncio
async def test_missing_product_url_returns_field_required(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    r = await app_client.post(
        "/api/founders/launch",
        json={
            "product_url": "",
            "problem_statement": "x",
            "icp_description": "y",
        },
        headers=auth_header(f["token"]),
    )
    assert r.status_code == 400
    detail = r.json().get("detail") or r.json()
    err = detail if isinstance(detail, dict) else detail[0]
    assert err.get("error") == "field_required"
    assert err.get("field") == "product_url"


@pytest.mark.asyncio
async def test_invalid_product_url_returns_url_invalid(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], product_url="ftp://acme.io"
    )
    assert res["status"] == 400
    assert res["body"]["detail"]["error"] == "url_invalid"


@pytest.mark.asyncio
async def test_empty_problem_statement_returns_field_required(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], problem_statement="   "
    )
    assert res["status"] == 400
    assert res["body"]["detail"]["error"] == "field_required"
    assert res["body"]["detail"]["field"] == "problem_statement"


@pytest.mark.asyncio
async def test_empty_icp_description_returns_field_required(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], icp_description=""
    )
    assert res["status"] == 400
    detail = res["body"]["detail"] if "detail" in res["body"] else res["body"]
    err = detail if isinstance(detail, dict) else detail[0]
    assert err.get("field") == "icp_description"


@pytest.mark.asyncio
async def test_too_many_presence_links_returns_field_invalid(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    links = [f"https://example.com/{i}" for i in range(7)]
    res = await submit_test_launch(
        app_client, f["token"], existing_presence_links=links
    )
    assert res["status"] == 400
    detail = res["body"]["detail"] if "detail" in res["body"] else res["body"]
    err = detail if isinstance(detail, dict) else detail[0]
    assert err.get("field") == "existing_presence_links"


@pytest.mark.asyncio
async def test_user_role_cannot_submit_launch(app_client, seed_test_communities):
    body = await signup_user(app_client, "maya@example.com")
    res = await submit_test_launch(app_client, body["jwt"])
    assert res["status"] == 403
    assert res["body"]["detail"]["error"] == "role_mismatch"


@pytest.mark.asyncio
async def test_unauthenticated_cannot_submit_launch(app_client, seed_test_communities):
    r = await app_client.post(
        "/api/founders/launch",
        json={
            "product_url": "https://acme.io",
            "problem_statement": "x",
            "icp_description": "y",
        },
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


@pytest.mark.asyncio
async def test_founder_can_submit_after_rejection(app_client, seed_test_communities):
    """F-LAUNCH-1: append-only — second submission allowed."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res1 = await submit_test_launch(app_client, f["token"])
    assert res1["status"] == 201
    res2 = await submit_test_launch(
        app_client, f["token"], product_url="https://acme.io/v2"
    )
    assert res2["status"] == 201
    assert res2["body"]["id"] != res1["body"]["id"]


# ---- F-LAUNCH-2 read ----


@pytest.mark.asyncio
async def test_list_only_own_launches(app_client, seed_test_communities):
    f1 = await signup_founder_with_token(app_client, "aamir@example.com")
    f2 = await signup_founder_with_token(app_client, "tara@example.com")

    await submit_test_launch(app_client, f1["token"])
    await submit_test_launch(app_client, f2["token"], product_url="https://tara.dev")

    r1 = await app_client.get(
        "/api/founders/launches", headers=auth_header(f1["token"])
    )
    assert r1.status_code == 200
    urls = [l["product_url"] for l in r1.json()["launches"]]
    assert urls == ["https://acme.io"]

    r2 = await app_client.get(
        "/api/founders/launches", headers=auth_header(f2["token"])
    )
    urls2 = [l["product_url"] for l in r2.json()["launches"]]
    assert urls2 == ["https://tara.dev"]


@pytest.mark.asyncio
async def test_list_status_filter(app_client, seed_test_communities):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    await submit_test_launch(app_client, f["token"])

    r = await app_client.get(
        "/api/founders/launches?status=approved",
        headers=auth_header(f["token"]),
    )
    assert r.status_code == 200
    assert r.json()["launches"] == []

    r2 = await app_client.get(
        "/api/founders/launches?status=pending",
        headers=auth_header(f["token"]),
    )
    assert len(r2.json()["launches"]) == 1


@pytest.mark.asyncio
async def test_get_other_founders_launch_returns_404(app_client, seed_test_communities):
    f1 = await signup_founder_with_token(app_client, "aamir@example.com")
    f2 = await signup_founder_with_token(app_client, "tara@example.com")
    res = await submit_test_launch(app_client, f1["token"])
    launch_id = res["body"]["id"]

    r = await app_client.get(
        f"/api/founders/launches/{launch_id}",
        headers=auth_header(f2["token"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "launch_not_found"
