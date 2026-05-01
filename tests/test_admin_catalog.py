"""F-CAT-5: admin catalog endpoints."""
import pytest

from tests.conftest import auth_header


pytestmark = pytest.mark.asyncio


async def test_list_returns_all_by_default(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.get(
        "/admin/catalog", headers=auth_header(admin_token["token"])
    )
    assert r.status_code == 200
    payload = r.json()
    assert len(payload) == 3
    slugs = {t["slug"] for t in payload}
    assert slugs == {
        "test-tool-pending", "test-tool-approved", "test-tool-rejected"
    }


async def test_list_filters_by_status(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.get(
        "/admin/catalog?status=pending",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    payload = r.json()
    assert len(payload) == 1
    assert payload[0]["slug"] == "test-tool-pending"


async def test_list_with_invalid_status_returns_400(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.get(
        "/admin/catalog?status=blah",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "status_invalid"


async def test_get_one_returns_entry(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.get(
        "/admin/catalog/test-tool-pending",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    assert r.json()["slug"] == "test-tool-pending"


async def test_get_one_returns_404_on_unknown_slug(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.get(
        "/admin/catalog/does-not-exist",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_found"


async def test_approve_sets_status_and_reviewer_clears_rejection_comment(
    app_client, seed_test_catalog, admin_token
):
    # Start with a rejected entry that has a rejection_comment.
    r = await app_client.post(
        "/admin/catalog/test-tool-rejected/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["curation_status"] == "approved"
    assert payload["reviewed_by"] == "admin@example.com"
    assert payload["last_reviewed_at"] is not None
    assert payload["rejection_comment"] is None  # cleared


async def test_reject_with_comment_sets_fields(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.post(
        "/admin/catalog/test-tool-pending/reject",
        json={"comment": "Stale URL"},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["curation_status"] == "rejected"
    assert payload["rejection_comment"] == "Stale URL"
    assert payload["reviewed_by"] == "admin@example.com"


async def test_reject_with_missing_comment_returns_field_required(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.post(
        "/admin/catalog/test-tool-pending/reject",
        json={},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error"] == "field_required"
    assert body["field"] == "comment"


async def test_reject_with_empty_string_comment_returns_field_required(
    app_client, seed_test_catalog, admin_token
):
    """Pydantic min_length=1 catches empty string at the schema layer
    -> RequestValidationError -> field_required."""
    r = await app_client.post(
        "/admin/catalog/test-tool-pending/reject",
        json={"comment": ""},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error"] == "field_required"
    assert body["field"] == "comment"


async def test_reject_with_whitespace_only_comment_returns_comment_invalid(
    app_client, seed_test_catalog, admin_token
):
    """Pydantic accepts non-empty strings; the handler rejects whitespace-
    only via an explicit strip+check -> 400 comment_invalid."""
    r = await app_client.post(
        "/admin/catalog/test-tool-pending/reject",
        json={"comment": "    "},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "comment_invalid"


async def test_approve_unknown_slug_returns_404(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.post(
        "/admin/catalog/does-not-exist/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_found"


async def test_reject_unknown_slug_returns_404(
    app_client, seed_test_catalog, admin_token
):
    r = await app_client.post(
        "/admin/catalog/does-not-exist/reject",
        json={"comment": "n/a"},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_found"
