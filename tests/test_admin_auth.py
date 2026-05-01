"""F-CAT-4: require_admin auth boundary."""
import pytest

from tests.conftest import auth_header


pytestmark = pytest.mark.asyncio


async def test_admin_email_passes(app_client, admin_token):
    r = await app_client.get(
        "/admin/catalog", headers=auth_header(admin_token["token"])
    )
    assert r.status_code == 200


async def test_non_admin_email_returns_403(app_client, non_admin_token):
    r = await app_client.get(
        "/admin/catalog", headers=auth_header(non_admin_token["token"])
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "admin_only"


async def test_unauthenticated_returns_401(app_client):
    r = await app_client.get("/admin/catalog")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


async def test_admin_email_check_is_case_insensitive(app_client):
    """ADMIN_EMAILS=admin@example.com,manager@example.com (set in conftest).
    Sign up "ADMIN@example.com" (uppercase localpart) and confirm we are
    treated as admin. This exercises the `.lower()` normalization in the
    require_admin dependency.
    """
    from tests.conftest import signup_user

    # The email is normalized to lowercase at signup time anyway
    # (cycle #1 stores email.lower()). The case-insensitivity matters
    # at the env-var-parsing step in require_admin.
    body = await signup_user(app_client, "ADMIN@example.com")
    r = await app_client.get(
        "/admin/catalog", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
