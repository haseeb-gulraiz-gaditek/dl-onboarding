"""F-LIVE-2: POST /api/recommendations/live-step.

Auth gate (founder 403, unauth 401), persistence (live_answers row +
profile vector), pipeline failure surfaces 503.
"""
from typing import Any

import pytest

from tests.conftest import auth_header, signed_up_user_with_profile, signup_founder


pytestmark = pytest.mark.asyncio


async def _fake_embed_text(_text: str) -> list[float]:
    return [0.05] * 1536


@pytest.fixture(autouse=True)
def stub_embed(monkeypatch):
    """All tests in this module bypass OpenAI."""
    monkeypatch.setattr(
        "app.embeddings.openai.embed_text", _fake_embed_text, raising=True,
    )
    monkeypatch.setattr(
        "app.embeddings.lifecycle.embed_text", _fake_embed_text, raising=True,
    )
    yield


@pytest.fixture
def stub_hybrid_returns_two(monkeypatch):
    async def fake_hybrid(**_kw):
        return [
            ({"slug": "a"}, 0.81),
            ({"slug": "b"}, 0.66),
        ]
    monkeypatch.setattr(
        "app.recommendations.live_engine.hybrid_search", fake_hybrid, raising=True,
    )
    yield


@pytest.fixture
async def seed_two_tools():
    from app.db.tools_seed import tools_seed_collection
    await tools_seed_collection().insert_many([
        {"slug": "a", "name": "A", "tagline": "a", "category": "productivity", "curation_status": "approved"},
        {"slug": "b", "name": "B", "tagline": "b", "category": "productivity", "curation_status": "approved"},
    ])
    yield


# ---- Auth boundaries ----

async def test_unauthenticated_401(app_client):
    r = await app_client.post(
        "/api/recommendations/live-step",
        json={"q_index": 1, "answer_value": {"job_title": "x", "level": "y", "industry": "z"}},
    )
    assert r.status_code == 401


async def test_founder_403(app_client):
    f = await signup_founder(app_client, "f@example.com")
    r = await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(f["jwt"]),
        json={"q_index": 1, "answer_value": {"job_title": "x", "level": "y", "industry": "z"}},
    )
    assert r.status_code == 403


# ---- Happy path ----

async def test_live_step_q1_returns_top_with_scores(
    app_client, stub_hybrid_returns_two, seed_two_tools,
):
    u = await signed_up_user_with_profile(app_client, "u@example.com")
    r = await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(u["token"]),
        json={
            "q_index": 1,
            "answer_value": {
                "job_title": "software_engineer",
                "level": "senior",
                "industry": "software_tech",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["step"] == 1
    assert body["count_kept"] == 2
    assert body["top"][0]["slug"] == "a"
    assert body["top"][0]["score"] == 0.81
    assert body["top"][0]["layer"] == "niche"
    assert body["top"][1]["layer"] == "relevant"
    assert body["wildcard"] is None  # only 2 results, no overflow


async def test_live_step_persists_live_answer(
    app_client, stub_hybrid_returns_two, seed_two_tools,
):
    u = await signed_up_user_with_profile(app_client, "u2@example.com")
    await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(u["token"]),
        json={
            "q_index": 2,
            "answer_value": {"selected_values": ["vscode", "github"]},
        },
    )

    from app.db.live_answers import live_answers_collection
    rows = await live_answers_collection().find({}).to_list(length=10)
    assert len(rows) == 1
    assert rows[0]["q_index"] == 2
    assert rows[0]["value"]["selected_values"] == ["vscode", "github"]


async def test_live_step_overwrites_same_q_index(
    app_client, stub_hybrid_returns_two, seed_two_tools,
):
    """Re-answering Q1 upserts (one row per (user, q_index))."""
    u = await signed_up_user_with_profile(app_client, "u3@example.com")
    for level in ("junior", "senior"):
        await app_client.post(
            "/api/recommendations/live-step",
            headers=auth_header(u["token"]),
            json={
                "q_index": 1,
                "answer_value": {
                    "job_title": "software_engineer",
                    "level": level,
                    "industry": "software_tech",
                },
            },
        )
    from app.db.live_answers import live_answers_collection
    rows = await live_answers_collection().find({}).to_list(length=10)
    assert len(rows) == 1
    assert rows[0]["value"]["level"] == "senior"  # overwritten


async def test_live_step_pipeline_failure_503(app_client, monkeypatch):
    """If live_match raises, surface 503 (answer is still persisted)."""
    u = await signed_up_user_with_profile(app_client, "u4@example.com")

    async def boom(**_kw):
        raise RuntimeError("openai down")

    monkeypatch.setattr(
        "app.api.recommendations.live_match", boom, raising=True,
    )
    r = await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(u["token"]),
        json={
            "q_index": 1,
            "answer_value": {"job_title": "x", "level": "y", "industry": "z"},
        },
    )
    assert r.status_code == 503
    assert r.json()["detail"]["error"] == "live_step_unavailable"

    # Answer still persisted despite the failure.
    from app.db.live_answers import live_answers_collection
    rows = await live_answers_collection().find({}).to_list(length=5)
    assert len(rows) == 1


async def test_live_step_returns_degraded_flag_on_hybrid_empty(
    app_client, monkeypatch, seed_two_tools,
):
    """When hybrid returns empty, response includes degraded:true."""
    u = await signed_up_user_with_profile(app_client, "u5@example.com")

    async def empty_hybrid(**_kw):
        return []

    monkeypatch.setattr(
        "app.recommendations.live_engine.hybrid_search", empty_hybrid, raising=True,
    )

    # Seed one tool with embedding so similarity_search fallback finds something.
    from app.db.tools_seed import tools_seed_collection
    await tools_seed_collection().update_one(
        {"slug": "a"},
        {"$set": {"embedding": [0.05] * 1536}},
    )

    r = await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(u["token"]),
        json={
            "q_index": 1,
            "answer_value": {
                "job_title": "software_engineer",
                "level": "senior",
                "industry": "software_tech",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["degraded"] is True


# ---- Validation ----

async def test_invalid_q_index_400_or_422(app_client):
    u = await signed_up_user_with_profile(app_client, "u6@example.com")
    r = await app_client.post(
        "/api/recommendations/live-step",
        headers=auth_header(u["token"]),
        json={"q_index": 99, "answer_value": {}},
    )
    # FastAPI's validation handler returns 400 in this app (custom
    # exception handler in app/main.py); pydantic-default would be 422.
    assert r.status_code in (400, 422)
