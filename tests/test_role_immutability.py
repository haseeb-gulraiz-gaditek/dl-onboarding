"""F-AUTH-4: role_type is non-transferable at the data layer.

The strongest end-to-end test of this contract is: there is no API
path that mutates role_type. We exercise this by:

  1. Confirming the only API that accepts role_question_answer
     (signup) returns 409 on duplicate email rather than mutating
     the existing row.
  2. Confirming there is no PATCH /api/me, /api/users/:id, or
     similar route that could accept a role_type field.
"""
import pytest

from tests.conftest import auth_header


pytestmark = pytest.mark.asyncio


async def test_role_is_immutable_via_repeat_signup(app_client):
    # Sign up as user.
    r1 = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "maya@example.com",
            "password": "password123",
            "role_question_answer": "finding_tools",
        },
    )
    assert r1.status_code == 200
    assert r1.json()["user"]["role_type"] == "user"

    # Attempt to "re-signup" with same email but the founder answer.
    r2 = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "maya@example.com",
            "password": "password123",
            "role_question_answer": "launching_product",
        },
    )
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"] == "email_already_registered"

    # Login and confirm role_type is still "user".
    r3 = await app_client.post(
        "/api/auth/login",
        json={"email": "maya@example.com", "password": "password123"},
    )
    assert r3.status_code == 200
    assert r3.json()["user"]["role_type"] == "user"

    # And /api/me also shows user.
    me = await app_client.get(
        "/api/me", headers=auth_header(r3.json()["jwt"])
    )
    assert me.status_code == 200
    assert me.json()["role_type"] == "user"


async def test_no_api_path_accepts_role_type_write(app_client):
    """Audit test -- there must be no endpoint that writes role_type.

    We probe a few obvious candidates and confirm they don't exist
    (404) or refuse role_type (4xx). If a future cycle ever adds
    such a path, this test fails and forces a constitutional
    review against the principle "Never let founder accounts post
    in user communities".
    """
    # Sign up so we have a valid token to probe with.
    signup = await app_client.post(
        "/api/auth/signup",
        json={
            "email": "maya@example.com",
            "password": "password123",
            "role_question_answer": "finding_tools",
        },
    )
    token = signup.json()["jwt"]
    headers = auth_header(token)

    # PATCH /api/me — must not exist.
    r = await app_client.patch("/api/me", headers=headers, json={"role_type": "founder"})
    assert r.status_code in (404, 405), (
        "PATCH /api/me exists and accepted a role_type write -- "
        "F-AUTH-4 regression: see specs/constitution/principles.md"
    )

    # PUT /api/me — must not exist.
    r = await app_client.put("/api/me", headers=headers, json={"role_type": "founder"})
    assert r.status_code in (404, 405)

    # POST /api/me — must not exist.
    r = await app_client.post("/api/me", headers=headers, json={"role_type": "founder"})
    assert r.status_code in (404, 405)
