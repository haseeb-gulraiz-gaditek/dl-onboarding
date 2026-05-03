"""Tests for /api/me/tools (cycle: my-tools-explore-new-tabs).

Covers F-TOOL-1, F-TOOL-3, F-TOOL-4, F-TOOL-5, F-TOOL-6.
"""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


# ---- F-TOOL-3 explicit save ----


@pytest.mark.asyncio
async def test_save_tool_creates_row_with_explicit_source(
    app_client, seed_test_catalog
):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved", "status": "saved"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200, r.text
    row = r.json()
    assert row["source"] == "explicit_save"
    assert row["status"] == "saved"
    assert row["tool"]["slug"] == "test-tool-approved"
    assert row["tool"]["is_founder_launched"] is False


@pytest.mark.asyncio
async def test_save_unknown_slug_returns_404(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "does-not-exist"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_found"


@pytest.mark.asyncio
async def test_founder_cannot_save(app_client, seed_test_catalog):
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_save_promotes_existing_auto_row(
    app_client, seed_test_catalog
):
    """F-TOOL-3 + F-TOOL-7 interplay: auto-populated row gets promoted to
    explicit_save when the user hits POST /api/me/tools."""
    from app.db.user_tools import upsert_auto_from_profile
    from app.db.tools_seed import find_tool_by_slug
    from bson import ObjectId

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    tool = await find_tool_by_slug("test-tool-approved")
    await upsert_auto_from_profile(user_id, tool["_id"])

    r = await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved", "status": "using"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    row = r.json()
    assert row["source"] == "explicit_save"
    assert row["status"] == "using"


# ---- F-TOOL-4 delete ----


@pytest.mark.asyncio
async def test_delete_existing_returns_true(app_client, seed_test_catalog):
    from app.db.tools_seed import find_tool_by_slug

    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved"},
        headers=auth_header(body["jwt"]),
    )
    tool = await find_tool_by_slug("test-tool-approved")

    r = await app_client.delete(
        f"/api/me/tools/{tool['_id']}", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"deleted": True}


@pytest.mark.asyncio
async def test_delete_missing_returns_false(app_client):
    body = await signup_user(app_client, "maya@example.com")
    fake = "507f1f77bcf86cd799439011"
    r = await app_client.delete(
        f"/api/me/tools/{fake}", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"deleted": False}


# ---- F-TOOL-5 patch status ----


@pytest.mark.asyncio
async def test_patch_status_updates_and_preserves_source(
    app_client, seed_test_catalog
):
    from app.db.tools_seed import find_tool_by_slug

    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved", "status": "saved"},
        headers=auth_header(body["jwt"]),
    )
    tool = await find_tool_by_slug("test-tool-approved")

    r = await app_client.patch(
        f"/api/me/tools/{tool['_id']}",
        json={"status": "using"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200
    row = r.json()
    assert row["status"] == "using"
    assert row["source"] == "explicit_save"  # preserved


@pytest.mark.asyncio
async def test_patch_missing_row_returns_404(app_client, seed_test_catalog):
    from app.db.tools_seed import find_tool_by_slug

    body = await signup_user(app_client, "maya@example.com")
    tool = await find_tool_by_slug("test-tool-approved")
    r = await app_client.patch(
        f"/api/me/tools/{tool['_id']}",
        json={"status": "using"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "tool_not_in_mine"


# ---- F-TOOL-6 list ----


@pytest.mark.asyncio
async def test_list_returns_tools_in_last_updated_desc(
    app_client, seed_test_catalog
):
    body = await signup_user(app_client, "maya@example.com")
    # Save approved first, then re-bookmark a different one (which is more recent).
    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved"},
        headers=auth_header(body["jwt"]),
    )
    # test-tool-rejected has curation_status="rejected" so we can't save it.
    # Save the same tool again which bumps last_updated_at — order shouldn't change.
    r = await app_client.get(
        "/api/me/tools", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert len(r.json()["tools"]) == 1


@pytest.mark.asyncio
async def test_list_status_filter(app_client, seed_test_catalog):
    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved", "status": "saved"},
        headers=auth_header(body["jwt"]),
    )
    r1 = await app_client.get(
        "/api/me/tools?status=saved", headers=auth_header(body["jwt"])
    )
    assert len(r1.json()["tools"]) == 1
    r2 = await app_client.get(
        "/api/me/tools?status=using", headers=auth_header(body["jwt"])
    )
    assert r2.json()["tools"] == []


@pytest.mark.asyncio
async def test_list_drops_orphaned_rows(app_client, seed_test_catalog):
    """F-TOOL-6: row whose tool was rejected/deleted is silently dropped."""
    from app.db.tools_seed import find_tool_by_slug, tools_seed_collection

    body = await signup_user(app_client, "maya@example.com")
    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved"},
        headers=auth_header(body["jwt"]),
    )
    tool = await find_tool_by_slug("test-tool-approved")
    # Flip curation_status to rejected.
    await tools_seed_collection().update_one(
        {"_id": tool["_id"]}, {"$set": {"curation_status": "rejected"}}
    )

    r = await app_client.get(
        "/api/me/tools", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json()["tools"] == []  # silently dropped
