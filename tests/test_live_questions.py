"""F-LIVE-1: live-question schema endpoints.

GET /api/onboarding/live-questions
GET /api/onboarding/live-questions/{q_index}/options?role=...
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


pytestmark = pytest.mark.asyncio


async def test_unauthenticated_returns_401_on_questions(app_client):
    r = await app_client.get("/api/onboarding/live-questions")
    assert r.status_code == 401


async def test_founder_returns_403(app_client):
    f = await signup_founder(app_client, "f@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions",
        headers=auth_header(f["jwt"]),
    )
    assert r.status_code == 403


async def test_user_gets_4_questions(app_client):
    u = await signup_user(app_client, "u@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions",
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    qs = body["questions"]
    assert len(qs) == 4
    assert [q["q_index"] for q in qs] == [1, 2, 3, 4]
    # Q1 has sub_dropdowns
    assert qs[0]["kind"] == "dropdowns_3"
    assert "job_title" in qs[0]["sub_dropdowns"]
    # Q2 multi_select with options_per_role
    assert qs[1]["kind"] == "multi_select"
    assert qs[1]["options_per_role"] is not None
    # Q4 role-agnostic single_select
    assert qs[3]["kind"] == "single_select"
    assert qs[3]["options"] is not None
    assert qs[3]["options_per_role"] is None


async def test_role_conditioned_options_for_known_role(app_client):
    u = await signup_user(app_client, "u2@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/2/options",
        params={"role": "software_engineer"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role_key_resolved"] == "software_engineer"
    values = [o["value"] for o in body["options"]]
    assert "vscode" in values
    assert "terminal" in values


async def test_role_alias_resolves_via_role_key_map(app_client):
    """data_scientist normalizes to software_engineer via ROLE_KEY_MAP."""
    u = await signup_user(app_client, "u3@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/3/options",
        params={"role": "data_scientist"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role_key_resolved"] == "software_engineer"
    assert len(body["options"]) >= 5  # has scenarios


async def test_unknown_role_falls_back(app_client):
    u = await signup_user(app_client, "u4@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/2/options",
        params={"role": "underwater_basket_weaver"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role_key_resolved"] == "other"
    values = [o["value"] for o in body["options"]]
    # FALLBACK_OPTIONS_Q2 starts with "email"
    assert "email" in values


async def test_q1_options_endpoint_400(app_client):
    """Q1 isn't role-conditioned — endpoint should refuse."""
    u = await signup_user(app_client, "u5@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/1/options",
        params={"role": "anything"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "question_not_role_conditioned"


async def test_q4_options_endpoint_400(app_client):
    """Q4 is role-agnostic — endpoint should refuse."""
    u = await signup_user(app_client, "u6@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/4/options",
        params={"role": "anything"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 400


async def test_invalid_q_index_404(app_client):
    u = await signup_user(app_client, "u7@example.com")
    r = await app_client.get(
        "/api/onboarding/live-questions/99/options",
        params={"role": "anything"},
        headers=auth_header(u["jwt"]),
    )
    assert r.status_code == 404
