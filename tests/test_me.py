"""F-AUTH-5: GET /api/me requires a valid JWT."""
import pytest

from tests.conftest import auth_header, signup_user


pytestmark = pytest.mark.asyncio


async def test_me_returns_user_payload_with_valid_jwt(app_client):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.get("/api/me", headers=auth_header(body["jwt"]))
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "maya@example.com"
    assert me["role_type"] == "user"
    assert me["display_name"] == "maya"
    assert "id" in me
    assert "created_at" in me
    assert "last_active_at" in me


async def test_me_returns_401_without_jwt(app_client):
    r = await app_client.get("/api/me")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


async def test_me_returns_401_with_invalid_jwt(app_client):
    r = await app_client.get(
        "/api/me", headers={"Authorization": "Bearer this-is-not-a-jwt"}
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"
