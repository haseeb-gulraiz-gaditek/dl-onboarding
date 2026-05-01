"""F-MATCH-1..6: POST /api/onboarding/match."""
import json
from pathlib import Path

import pytest
from bson import ObjectId

from app.db.profiles import profiles_collection
from app.db.users import find_user_by_id
from app.onboarding.role_map import ROLE_TO_CATEGORIES
from tests.conftest import (
    auth_header,
    insert_dummy_answers,
    insert_role_answer,
    signed_up_user_with_profile,
    signup_founder,
    signup_user,
)


pytestmark = pytest.mark.asyncio


# ---- F-MATCH-1: auth boundary ----

async def test_unauthenticated_returns_401(app_client):
    r = await app_client.post("/api/onboarding/match")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"


async def test_founder_returns_403(app_client):
    body = await signup_founder(app_client, "aamir@example.com")
    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"


# ---- F-MATCH-2: mode dispatch by answered_count ----

async def test_zero_answers_uses_generic_mode(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json()["mode"] == "generic"


async def test_two_answers_uses_generic_mode(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    user_id = body["user"]["id"]
    await insert_dummy_answers(user_id, 2)

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.json()["mode"] == "generic"


async def test_three_answers_flips_to_embedding_mode(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    user_id = body["user"]["id"]
    await insert_dummy_answers(user_id, 3)

    # We need a profile to exist for ensure_profile_embedding to succeed.
    # Hit /api/questions/next once to lazy-create one.
    user = await find_user_by_id(user_id)
    from app.db.profiles import get_or_create_profile

    await get_or_create_profile(user)

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json()["mode"] == "embedding"


async def test_five_answers_uses_embedding_mode(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    user_id = body["user"]["id"]
    await insert_dummy_answers(user_id, 5)
    user = await find_user_by_id(user_id)
    from app.db.profiles import get_or_create_profile

    await get_or_create_profile(user)

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.json()["mode"] == "embedding"


# ---- F-MATCH-3: generic mode ----

async def test_generic_mode_role_bucket_returns_mapped_categories(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    await insert_role_answer(body["user"]["id"], "marketing_ops")

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.json()["mode"] == "generic"
    tools = r.json()["tools"]
    assert len(tools) == 5
    # marketing_ops -> [marketing, analytics_data, writing]; only
    # marketing exists in the seed_minimal_catalog.
    for tool in tools:
        assert tool["category"] == "marketing"
    # Alphabetical.
    slugs = [t["slug"] for t in tools]
    assert slugs == sorted(slugs)


async def test_generic_mode_no_role_returns_catalog_wide(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")
    # No role answer.

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    tools = r.json()["tools"]
    assert len(tools) == 5
    slugs = [t["slug"] for t in tools]
    # Catalog has 8 tools; alphabetical top-5.
    assert slugs == ["convertkit", "figma", "hubspot", "klaviyo", "mailchimp"]


async def test_generic_mode_role_bucket_under_top_k_falls_back(
    app_client, seed_minimal_catalog, seed_role_question
):
    """role=design has only 2 tools in the bucket -- falls back to
    catalog-wide all_time_best."""
    body = await signup_user(app_client, "maya@example.com")
    await insert_role_answer(body["user"]["id"], "design")

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    tools = r.json()["tools"]
    assert len(tools) == 5
    slugs = [t["slug"] for t in tools]
    # Same alphabetical top-5 as the no-role case (catalog-wide
    # fallback).
    assert slugs == ["convertkit", "figma", "hubspot", "klaviyo", "mailchimp"]


# ---- F-MATCH-4: embedding mode ----

async def test_embedding_mode_calls_ensure_profile_embedding(
    app_client, seed_minimal_catalog, seed_role_question
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    user_id = info["user"]["id"]
    await insert_dummy_answers(user_id, 3)

    # Profile exists (created by signed_up_user_with_profile fixture)
    # but has no embedding yet.
    pre = await profiles_collection().find_one(
        {"user_id": ObjectId(user_id)}
    )
    assert pre["embedding"] is None

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(info["token"])
    )
    assert r.status_code == 200
    assert r.json()["mode"] == "embedding"

    # Profile embedding now populated by ensure_profile_embedding.
    post = await profiles_collection().find_one(
        {"user_id": ObjectId(user_id)}
    )
    assert post["embedding"] is not None


async def test_embedding_mode_with_no_embedded_tools_returns_empty_list(
    app_client, seed_role_question
):
    """No tools have embeddings yet -- the cosine fallback returns []."""
    body = await signup_user(app_client, "maya@example.com")
    user_id = body["user"]["id"]
    await insert_dummy_answers(user_id, 3)
    user = await find_user_by_id(user_id)
    from app.db.profiles import get_or_create_profile

    await get_or_create_profile(user)

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    body_json = r.json()
    assert body_json["mode"] == "embedding"
    assert body_json["tools"] == []


async def test_openai_failure_falls_back_to_generic(
    app_client, seed_minimal_catalog, seed_role_question, monkeypatch
):
    body = await signup_user(app_client, "maya@example.com")
    user_id = body["user"]["id"]
    await insert_dummy_answers(user_id, 3)
    user = await find_user_by_id(user_id)
    from app.db.profiles import get_or_create_profile

    await get_or_create_profile(user)

    async def _failing_embed(text: str) -> list[float]:
        raise RuntimeError("OpenAI is down")

    monkeypatch.setattr("app.embeddings.lifecycle.embed_text", _failing_embed)

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    # Fell back to generic.
    assert r.json()["mode"] == "generic"
    assert len(r.json()["tools"]) > 0


# ---- F-MATCH-5: response shape ----

async def test_response_shape_matches_contract(
    app_client, seed_minimal_catalog, seed_role_question
):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.post(
        "/api/onboarding/match", headers=auth_header(body["jwt"])
    )
    payload = r.json()
    assert set(payload.keys()) == {"mode", "tools"}
    assert payload["mode"] in {"generic", "embedding"}
    for tool in payload["tools"]:
        assert set(tool.keys()) == {
            "slug", "name", "tagline", "description", "url",
            "pricing_summary", "category", "labels",
        }


# ---- F-MATCH-6: ROLE_TO_CATEGORIES audit ----

async def test_role_to_categories_keys_match_seed_options():
    """ROLE_TO_CATEGORIES keys must exactly match the option values
    of the role.primary_function seed question. Drift here means a
    role added to the seed is silently unmapped (and falls through
    to catalog-wide), or vice versa."""
    seed_path = Path("/home/haseeb/dl-onboarding/app/seed/questions.json")
    entries = json.loads(seed_path.read_text(encoding="utf-8"))
    role_q = next(e for e in entries if e["key"] == "role.primary_function")
    seed_values = {opt["value"] for opt in role_q["options"]}
    map_keys = set(ROLE_TO_CATEGORIES.keys())

    assert seed_values == map_keys, (
        f"ROLE_TO_CATEGORIES keys drifted from seed options.\n"
        f"In seed but not map: {sorted(seed_values - map_keys)}\n"
        f"In map but not seed: {sorted(map_keys - seed_values)}"
    )
