"""F-AUTH-2: login happy path and credential errors.

The wrong-password and unknown-email cases must return the SAME
error message so account existence is not leaked.
"""
import pytest

from tests.conftest import auth_header, signup_user


pytestmark = pytest.mark.asyncio


async def test_login_happy_path_returns_jwt_and_touches_last_active(app_client):
    await signup_user(app_client, "maya@example.com", "password123")

    r = await app_client.post(
        "/api/auth/login",
        json={"email": "maya@example.com", "password": "password123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["jwt"]
    assert body["user"]["role_type"] == "user"

    # The returned JWT works on /api/me.
    me = await app_client.get("/api/me", headers=auth_header(body["jwt"]))
    assert me.status_code == 200
    assert me.json()["email"] == "maya@example.com"


async def test_login_wrong_password_returns_invalid_credentials(app_client):
    await signup_user(app_client, "maya@example.com", "password123")

    r = await app_client.post(
        "/api/auth/login",
        json={"email": "maya@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "invalid_credentials"


async def test_login_unknown_email_returns_same_invalid_credentials(app_client):
    # No signup -- the email simply doesn't exist.
    r = await app_client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert r.status_code == 401
    # Must be the SAME error code as wrong-password to avoid
    # leaking account existence.
    assert r.json()["detail"]["error"] == "invalid_credentials"
