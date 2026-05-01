"""F-EMB-2, F-EMB-3, F-EMB-6: embedding lifecycle helpers."""
import asyncio
from datetime import datetime, timezone

import pytest
from bson import ObjectId

from app.db.profiles import profiles_collection
from app.db.tools_seed import find_tool_by_slug, tools_seed_collection
from app.embeddings.lifecycle import (
    clear_tool_embedding,
    ensure_profile_embedding,
    ensure_tool_embedding,
)
from tests.conftest import (
    auth_header,
    signed_up_user_with_profile,
    signup_founder,
    signup_user,
)


pytestmark = pytest.mark.asyncio


# ---- F-EMB-2: tool embeddings ----

async def test_ensure_tool_embedding_populates_embedding(
    app_client, seed_test_catalog
):
    pre = await find_tool_by_slug("test-tool-approved")
    assert pre["embedding"] is None

    did_embed = await ensure_tool_embedding("test-tool-approved")
    assert did_embed is True

    post = await find_tool_by_slug("test-tool-approved")
    assert post["embedding"] is not None
    assert isinstance(post["embedding"], list)
    assert len(post["embedding"]) == 1536


async def test_ensure_tool_embedding_idempotent_when_already_embedded(
    app_client, seed_test_catalog
):
    await ensure_tool_embedding("test-tool-approved")
    pre = await find_tool_by_slug("test-tool-approved")
    pre_vec = pre["embedding"]

    did_embed = await ensure_tool_embedding("test-tool-approved")
    assert did_embed is False

    post = await find_tool_by_slug("test-tool-approved")
    assert post["embedding"] == pre_vec  # unchanged


async def test_ensure_tool_embedding_no_op_on_missing_slug(
    app_client, seed_test_catalog
):
    did_embed = await ensure_tool_embedding("does-not-exist")
    assert did_embed is False


async def test_admin_approve_triggers_embedding(
    app_client, seed_test_catalog, admin_token
):
    pre = await find_tool_by_slug("test-tool-pending")
    assert pre["embedding"] is None

    r = await app_client.post(
        "/admin/catalog/test-tool-pending/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["embedding"] is not None
    assert len(body["embedding"]) == 1536


async def test_admin_approve_succeeds_even_if_openai_fails(
    app_client, seed_test_catalog, admin_token, monkeypatch
):
    async def _failing_embed(text: str) -> list[float]:
        raise RuntimeError("OpenAI is down")

    monkeypatch.setattr("app.embeddings.lifecycle.embed_text", _failing_embed)

    r = await app_client.post(
        "/admin/catalog/test-tool-pending/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["curation_status"] == "approved"
    # Embedding stayed null due to the failure.
    assert body["embedding"] is None


# ---- F-EMB-3: profile embeddings ----

async def test_ensure_profile_embedding_populates_fresh_profile(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    qid = info["first"]["question"]["id"]

    # Answer one question so there's something to embed.
    await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "designer"},
        headers=auth_header(info["token"]),
    )

    # Fetch the user dict shape ensure_profile_embedding expects.
    from app.db.users import find_user_by_id

    user = await find_user_by_id(info["user"]["id"])
    did_embed = await ensure_profile_embedding(user)
    assert did_embed is True

    profile = await profiles_collection().find_one({"user_id": user["_id"]})
    assert profile["embedding"] is not None
    assert profile["last_recompute_at"] is not None


async def test_ensure_profile_embedding_no_op_on_fresh_embedding(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    qid = info["first"]["question"]["id"]
    await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "designer"},
        headers=auth_header(info["token"]),
    )
    from app.db.users import find_user_by_id

    user = await find_user_by_id(info["user"]["id"])
    await ensure_profile_embedding(user)

    pre = await profiles_collection().find_one({"user_id": user["_id"]})
    pre_recompute = pre["last_recompute_at"]

    # Re-call: no-op because last_recompute_at >= last_invalidated_at.
    did_embed = await ensure_profile_embedding(user)
    assert did_embed is False

    post = await profiles_collection().find_one({"user_id": user["_id"]})
    assert post["last_recompute_at"] == pre_recompute  # unchanged


async def test_ensure_profile_embedding_regenerates_when_invalidated(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    qid = info["first"]["question"]["id"]
    await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "designer"},
        headers=auth_header(info["token"]),
    )
    from app.db.users import find_user_by_id

    user = await find_user_by_id(info["user"]["id"])
    await ensure_profile_embedding(user)

    pre = await profiles_collection().find_one({"user_id": user["_id"]})
    pre_recompute = pre["last_recompute_at"]

    # Force the freshness check to fail by making last_recompute_at
    # stale (in the past). This is more deterministic than bumping
    # last_invalidated_at into the future, since the regenerated
    # last_recompute_at = now() may not be > a future timestamp.
    from datetime import timedelta

    stale = pre_recompute - timedelta(hours=1)
    await profiles_collection().update_one(
        {"user_id": user["_id"]},
        {"$set": {"last_recompute_at": stale}},
    )

    did_embed = await ensure_profile_embedding(user)
    assert did_embed is True

    post = await profiles_collection().find_one({"user_id": user["_id"]})
    assert post["last_recompute_at"] > stale


async def test_ensure_profile_embedding_refuses_founder(app_client):
    body = await signup_founder(app_client, "aamir@example.com")
    from app.db.users import find_user_by_id

    user = await find_user_by_id(body["user"]["id"])

    with pytest.raises(ValueError, match="founders have no profile"):
        await ensure_profile_embedding(user)


# ---- F-EMB-6: reject clears the embedding ----

async def test_reject_clears_embedding(
    app_client, seed_test_catalog, admin_token
):
    # First approve to populate the embedding.
    await app_client.post(
        "/admin/catalog/test-tool-pending/approve",
        headers=auth_header(admin_token["token"]),
    )
    pre = await find_tool_by_slug("test-tool-pending")
    assert pre["embedding"] is not None

    # Reject -- should clear the embedding.
    r = await app_client.post(
        "/admin/catalog/test-tool-pending/reject",
        json={"comment": "Stale URL"},
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["curation_status"] == "rejected"
    assert body["embedding"] is None

    post = await find_tool_by_slug("test-tool-pending")
    assert post["embedding"] is None


async def test_re_approve_after_reject_re_embeds(
    app_client, seed_test_catalog, admin_token
):
    # The fixture has test-tool-rejected with curation_status=rejected
    # and embedding=None. Re-approve and confirm embedding comes back.
    r = await app_client.post(
        "/admin/catalog/test-tool-rejected/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["curation_status"] == "approved"
    assert body["embedding"] is not None
    assert len(body["embedding"]) == 1536
