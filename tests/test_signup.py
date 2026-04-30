"""F-AUTH-1: signup happy paths and error contracts.

Covers 6 spec-delta scenarios: 2 happy paths (one per role question
answer), and 4 error paths (duplicate email, invalid role answer,
weak password, malformed email).
"""
import pytest


pytestmark = pytest.mark.asyncio


async def test_signup_finding_tools_creates_user_role(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "maya@example.com",
            "password": "password123",
            "role_question_answer": "finding_tools",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role_type"] == "user"
    assert body["user"]["email"] == "maya@example.com"
    assert body["user"]["display_name"] == "maya"
    assert body["jwt"]


async def test_signup_launching_product_creates_founder_role(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "aamir@example.com",
            "password": "password123",
            "role_question_answer": "launching_product",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role_type"] == "founder"
    assert body["jwt"]


async def test_signup_duplicate_email_returns_409(app_client):
    payload = {
        "email": "x@example.com",
        "password": "password123",
        "role_question_answer": "finding_tools",
    }
    r1 = await app_client.post("/api/auth/signup", json=payload)
    assert r1.status_code == 200

    r2 = await app_client.post("/api/auth/signup", json=payload)
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"] == "email_already_registered"


async def test_signup_invalid_role_question_answer_returns_400(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "x@example.com",
            "password": "password123",
            "role_question_answer": "neither_of_the_above",
        },
    )
    assert r.status_code == 400
    assert r.json()["error"] == "role_question_required"


async def test_signup_missing_role_question_answer_returns_400(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "role_question_required"


async def test_signup_weak_password_returns_400(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "x@example.com",
            "password": "short",
            "role_question_answer": "finding_tools",
        },
    )
    assert r.status_code == 400
    assert r.json()["error"] == "password_too_short"


async def test_signup_malformed_email_returns_400(app_client):
    r = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "not-an-email",
            "password": "password123",
            "role_question_answer": "finding_tools",
        },
    )
    assert r.status_code == 400
    assert r.json()["error"] == "email_invalid"
