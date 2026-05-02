"""Tests for the recommendation engine (cycle: recommendation-engine).

Covers F-REC-1..7 from the spec-delta:
  - F-REC-1: endpoint exists, role-gated
  - F-REC-2: minimum-answers gate
  - F-REC-3: cache hit path
  - F-REC-4: cache miss / fresh generation
  - F-REC-5: response shape + count clamping
  - F-REC-6: collection schema (unique on user_id)
  - F-REC-7: ranker failure → degraded response

The mock_openai_chat autouse fixture in conftest.py replaces
`rank_with_llm` with a deterministic stub. Tests that need a
failing or hallucinating ranker override locally.
"""
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import (
    auth_header,
    insert_dummy_answers,
    prepare_user_for_recs,
    signup_founder,
    signup_user,
)


# ---- F-REC-1: role gating ----


@pytest.mark.asyncio
async def test_founder_cannot_call_recommendations(app_client, seed_recs_catalog):
    """F-REC-1: founder gets 403 role_mismatch."""
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["error"] == "role_mismatch"


@pytest.mark.asyncio
async def test_unauthenticated_cannot_call_recommendations(app_client):
    """F-REC-1: missing token → 401 auth_required."""
    r = await app_client.post("/api/recommendations", json={"count": 3})
    assert r.status_code == 401, r.text
    assert r.json()["detail"]["error"] == "auth_required"


# ---- F-REC-2: min-answers gate ----


@pytest.mark.asyncio
async def test_zero_answers_returns_no_profile_yet(app_client, seed_recs_catalog):
    """F-REC-2: brand-new user with 0 answers → 400 no_profile_yet."""
    body = await signup_user(app_client, "newbie@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert detail["error"] == "no_profile_yet"
    assert detail["min_answers"] == 3


@pytest.mark.asyncio
async def test_two_answers_returns_no_profile_yet(app_client, seed_recs_catalog):
    """F-REC-2: 2 answers (below threshold) → 400 no_profile_yet."""
    body = await signup_user(app_client, "two@example.com")
    from bson import ObjectId
    user_id = ObjectId(body["user"]["id"])
    await insert_dummy_answers(user_id, 2)

    r = await app_client.post(
        "/api/recommendations",
        json={},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "no_profile_yet"


@pytest.mark.asyncio
async def test_three_answers_returns_recommendations(app_client, seed_recs_catalog):
    """F-REC-2: exactly 3 answers crosses the threshold and serves recs."""
    prep = await prepare_user_for_recs(app_client, "three@example.com", n_answers=3)
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["recommendations"]) == 3
    assert body["from_cache"] is False


# ---- F-REC-3: cache hit ----


@pytest.mark.asyncio
async def test_second_call_is_cache_hit(app_client, seed_recs_catalog):
    """F-REC-3: back-to-back calls — second returns from_cache=true."""
    prep = await prepare_user_for_recs(app_client, "cache@example.com")

    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200
    assert r1.json()["from_cache"] is False

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is True


@pytest.mark.asyncio
async def test_cache_hit_does_not_call_ranker(app_client, seed_recs_catalog, monkeypatch):
    """F-REC-3: when the cache is warm, the ranker is NOT invoked."""
    prep = await prepare_user_for_recs(app_client, "noranker@example.com")

    # Warm the cache.
    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200

    # Replace the ranker with a tripwire that fails the test if called.
    call_count = {"n": 0}

    async def _tripwire(*args, **kwargs):
        call_count["n"] += 1
        raise AssertionError("ranker called on cache-hit path")

    monkeypatch.setattr(
        "app.recommendations.engine.rank_with_llm", _tripwire
    )

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is True
    assert call_count["n"] == 0


@pytest.mark.asyncio
async def test_cache_hit_truncates_to_count(app_client, seed_recs_catalog):
    """F-REC-3: cache stores up to 5 picks; subsequent calls truncate."""
    prep = await prepare_user_for_recs(app_client, "trunc@example.com")

    # First call with count=5 to fill the cache.
    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 5},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200
    assert len(r1.json()["recommendations"]) == 5

    # Second call with count=2 should serve only 2 from the same cache.
    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 2},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["from_cache"] is True
    assert len(body["recommendations"]) == 2


# ---- F-REC-4: cache miss / regenerate ----


@pytest.mark.asyncio
async def test_profile_invalidation_busts_cache(app_client, seed_recs_catalog):
    """F-REC-4: bumping last_invalidated_at past generated_at forces regen."""
    from app.db.profiles import profiles_collection

    prep = await prepare_user_for_recs(app_client, "bust@example.com")

    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200
    assert r1.json()["from_cache"] is False

    # Push last_invalidated_at into the future so it beats generated_at.
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    await profiles_collection().update_one(
        {"user_id": prep["user_id"]},
        {"$set": {"last_invalidated_at": future}},
    )

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is False


@pytest.mark.asyncio
async def test_expired_ttl_busts_cache(app_client, seed_recs_catalog):
    """F-REC-4: cache_expires_at in the past → cache miss, regenerate."""
    from app.db.recommendations import recommendations_collection

    prep = await prepare_user_for_recs(app_client, "ttl@example.com")

    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200

    # Force expiration into the past.
    past = datetime.now(timezone.utc) - timedelta(days=1)
    await recommendations_collection().update_one(
        {"user_id": prep["user_id"]},
        {"$set": {"cache_expires_at": past}},
    )

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is False


@pytest.mark.asyncio
async def test_hallucinated_slug_is_dropped(app_client, seed_recs_catalog, monkeypatch):
    """F-REC-4 step 4: ranker returning a slug not in candidates is dropped."""
    from app.models.recommendation import RankerPick

    async def _hallucinate(profile, recent_answers, candidates, count):
        # First two are real candidates, third is fake.
        real = candidates[:2]
        return [
            RankerPick(slug=real[0]["slug"], verdict="try", reasoning="real-1"),
            RankerPick(slug=real[1]["slug"], verdict="skip", reasoning="real-2"),
            RankerPick(slug="not-a-real-tool", verdict="try", reasoning="ghost"),
        ]

    monkeypatch.setattr(
        "app.recommendations.engine.rank_with_llm", _hallucinate
    )

    prep = await prepare_user_for_recs(app_client, "ghost@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 5},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    slugs = [p["tool"]["slug"] for p in body["recommendations"]]
    assert "not-a-real-tool" not in slugs
    assert len(body["recommendations"]) == 2


# ---- F-REC-5: response shape + count clamping ----


@pytest.mark.asyncio
async def test_response_shape_matches_contract(app_client, seed_recs_catalog):
    """F-REC-5: every required field present, types correct."""
    prep = await prepare_user_for_recs(app_client, "shape@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert "recommendations" in body
    assert "generated_at" in body
    assert "from_cache" in body
    assert "degraded" in body
    assert isinstance(body["from_cache"], bool)
    assert isinstance(body["degraded"], bool)
    for pick in body["recommendations"]:
        assert "tool" in pick
        assert "verdict" in pick
        assert "reasoning" in pick
        assert "score" in pick
        assert pick["verdict"] in ("try", "skip")
        # Tool card fields (cycle #5 OnboardingToolCard).
        for k in ("slug", "name", "tagline", "description", "url", "category"):
            assert k in pick["tool"]


@pytest.mark.asyncio
async def test_count_param_returns_exact_count(app_client, seed_recs_catalog):
    """F-REC-5: count=1, 3, 5 each return that many picks (catalog has 6)."""
    for desired in (1, 3, 5):
        prep = await prepare_user_for_recs(
            app_client, f"count{desired}@example.com"
        )
        r = await app_client.post(
            "/api/recommendations",
            json={"count": desired},
            headers=auth_header(prep["token"]),
        )
        assert r.status_code == 200, r.text
        assert len(r.json()["recommendations"]) == desired


@pytest.mark.asyncio
async def test_count_zero_uses_default(app_client, seed_recs_catalog):
    """F-REC-5: count=0 falls back to the default of 3."""
    prep = await prepare_user_for_recs(app_client, "zero@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 0},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    assert len(r.json()["recommendations"]) == 3


@pytest.mark.asyncio
async def test_count_too_high_clamps_to_five(app_client, seed_recs_catalog):
    """F-REC-5: count=10 clamps to 5 (the MAX_COUNT)."""
    prep = await prepare_user_for_recs(app_client, "high@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 10},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200
    assert len(r.json()["recommendations"]) == 5


# ---- F-REC-6: collection schema ----


@pytest.mark.asyncio
async def test_recommendations_collection_unique_on_user_id(app_client, seed_recs_catalog):
    """F-REC-6: two regenerations for the same user produce ONE row."""
    from app.db.recommendations import recommendations_collection

    prep = await prepare_user_for_recs(app_client, "uniq@example.com")

    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200

    # Force regeneration via TTL bust.
    past = datetime.now(timezone.utc) - timedelta(days=1)
    await recommendations_collection().update_one(
        {"user_id": prep["user_id"]},
        {"$set": {"cache_expires_at": past}},
    )
    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200

    count = await recommendations_collection().count_documents(
        {"user_id": prep["user_id"]}
    )
    assert count == 1


# ---- F-REC-7: degraded path ----


@pytest.mark.asyncio
async def test_ranker_failure_degrades_gracefully(app_client, seed_recs_catalog, monkeypatch):
    """F-REC-7: ranker raising → 200 with degraded=true and verdict=try."""

    async def _boom(profile, recent_answers, candidates, count):
        raise RuntimeError("simulated OpenAI 500")

    monkeypatch.setattr(
        "app.recommendations.engine.rank_with_llm", _boom
    )

    prep = await prepare_user_for_recs(app_client, "boom@example.com")
    r = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["degraded"] is True
    assert body["from_cache"] is False
    assert len(body["recommendations"]) == 3
    for pick in body["recommendations"]:
        assert pick["verdict"] == "try"
        assert "Personalized reasoning unavailable" in pick["reasoning"]


@pytest.mark.asyncio
async def test_degraded_response_is_cached(app_client, seed_recs_catalog, monkeypatch):
    """F-REC-7 step 3: degraded responses are cached to avoid re-hammering."""

    call_count = {"n": 0}

    async def _boom(profile, recent_answers, candidates, count):
        call_count["n"] += 1
        raise RuntimeError("simulated OpenAI 500")

    monkeypatch.setattr(
        "app.recommendations.engine.rank_with_llm", _boom
    )

    prep = await prepare_user_for_recs(app_client, "cache-boom@example.com")

    r1 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r1.status_code == 200
    assert r1.json()["degraded"] is True
    assert call_count["n"] == 1

    r2 = await app_client.post(
        "/api/recommendations",
        json={"count": 3},
        headers=auth_header(prep["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["from_cache"] is True
    # Ranker not called again because of cache.
    assert call_count["n"] == 1
