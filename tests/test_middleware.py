"""F-AUTH-3: role-aware middleware contract."""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


pytestmark = pytest.mark.asyncio


async def test_middleware_accepts_matching_role(app_client):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.get("/api/me/user-only", headers=auth_header(body["jwt"]))
    assert r.status_code == 200
    assert r.json()["role_type"] == "user"


async def test_middleware_rejects_mismatched_role_with_403(app_client):
    # Sign up as a founder, hit the user-only endpoint.
    body = await signup_founder(app_client, "aamir@example.com")

    r = await app_client.get("/api/me/user-only", headers=auth_header(body["jwt"]))
    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["error"] == "role_mismatch"
    assert detail["required"] == "user"
    assert detail["actual"] == "founder"


async def test_middleware_rejects_unauthenticated_with_401(app_client):
    r = await app_client.get("/api/me/user-only")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


async def test_middleware_symmetric_for_founder_only(app_client):
    user_body = await signup_user(app_client, "maya@example.com")
    founder_body = await signup_founder(app_client, "aamir@example.com")

    # Founder hits founder-only -> 200.
    r1 = await app_client.get(
        "/api/me/founder-only", headers=auth_header(founder_body["jwt"])
    )
    assert r1.status_code == 200
    assert r1.json()["role_type"] == "founder"

    # User hits founder-only -> 403.
    r2 = await app_client.get(
        "/api/me/founder-only", headers=auth_header(user_body["jwt"])
    )
    assert r2.status_code == 403
    assert r2.json()["detail"]["required"] == "founder"
    assert r2.json()["detail"]["actual"] == "user"
