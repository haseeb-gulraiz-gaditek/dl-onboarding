"""F-LIVE-2 / F-LIVE-5 / F-LIVE-6: live-narrowing engine pipeline.

Heavy use of monkey-patching for OpenAI + Weaviate so tests run in
the mongomock-motor environment without external services.
"""
from typing import Any
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.recommendations.live_engine import (
    ALPHA_SCHEDULE,
    K_SCHEDULE,
    LAYER_BANDS,
    layer_for,
    live_match,
    profile_text_from_live_answers,
)


pytestmark = pytest.mark.asyncio


# ---- F-LIVE-5: layer_for() boundaries ----

def test_layer_for_below_floor_is_none():
    assert layer_for(0.0) is None
    assert layer_for(0.54) is None
    assert layer_for(0.5499) is None


def test_layer_for_general_band():
    assert layer_for(0.55) == "general"
    assert layer_for(0.60) == "general"
    assert layer_for(0.6499) == "general"


def test_layer_for_relevant_band():
    assert layer_for(0.65) == "relevant"
    assert layer_for(0.70) == "relevant"
    assert layer_for(0.7499) == "relevant"


def test_layer_for_niche_band():
    assert layer_for(0.75) == "niche"
    assert layer_for(0.99) == "niche"


def test_layer_bands_constants_consistent():
    assert LAYER_BANDS["niche"] > LAYER_BANDS["relevant"] > LAYER_BANDS["general"]


# ---- profile_text_from_live_answers() ----

def test_profile_text_empty():
    assert profile_text_from_live_answers({}) == "I'm new to this."


def test_profile_text_q1_only():
    text = profile_text_from_live_answers({
        1: {"job_title": "software_engineer", "level": "senior", "industry": "software_tech"},
    })
    assert "software engineer" in text.lower()
    assert "senior" in text.lower()
    assert "software tech" in text.lower()


def test_profile_text_grows_with_each_q():
    answers = {
        1: {"job_title": "doctor", "level": "senior", "industry": "healthcare"},
        2: {"selected_values": ["epic", "uptodate"]},
        4: {"selected_value": "copy_paste"},
    }
    text = profile_text_from_live_answers(answers)
    assert "doctor" in text.lower()
    assert "epic" in text.lower()
    assert "copy" in text.lower() or "paste" in text.lower()


# ---- ALPHA_SCHEDULE / K_SCHEDULE constants ----

def test_alpha_schedule_has_4_entries_increasing():
    assert len(ALPHA_SCHEDULE) == 4
    assert ALPHA_SCHEDULE == sorted(ALPHA_SCHEDULE)
    assert all(0.0 <= a <= 1.0 for a in ALPHA_SCHEDULE)


def test_k_schedule_shrinks():
    assert K_SCHEDULE == [20, 15, 10, 6]


# ---- live_match() — uses mongomock + monkey-patched embed/hybrid ----

async def _fake_embed_text(_text: str) -> list[float]:
    return [0.1] * 1536


async def test_live_match_uses_alpha_and_k_for_step(
    monkeypatch, app_client,
):
    """Smoke: live_match calls hybrid_search with alpha=ALPHA_SCHEDULE[q-1]
    and limit=K_SCHEDULE[q-1]+1, persists profile vector via
    ensure_profile_embedding."""
    from tests.conftest import signup_user, signed_up_user_with_profile

    u = await signed_up_user_with_profile(app_client, "lm1@example.com")

    # Stub OpenAI embed everywhere it's bound.
    monkeypatch.setattr(
        "app.embeddings.openai.embed_text", _fake_embed_text, raising=True,
    )
    monkeypatch.setattr(
        "app.embeddings.lifecycle.embed_text", _fake_embed_text, raising=True,
    )

    # Stub hybrid_search to record the args + return canned (slug, score) pairs.
    captured: dict[str, Any] = {}

    async def fake_hybrid(*, weaviate_class, query, vector, alpha, limit, filters):
        captured["alpha"] = alpha
        captured["limit"] = limit
        captured["filters"] = filters
        return [
            ({"slug": "fake-tool"}, 0.81),
            ({"slug": "fake-tool-2"}, 0.69),
        ]

    monkeypatch.setattr(
        "app.recommendations.live_engine.hybrid_search", fake_hybrid, raising=True,
    )
    # Stub Weaviate publish_profile (write side) — not needed in this
    # path since ensure_profile_embedding's vs_publish is best-effort.

    # Seed two tools_seed entries so hydrate succeeds.
    from app.db.tools_seed import tools_seed_collection
    await tools_seed_collection().insert_many([
        {"slug": "fake-tool", "name": "Fake Tool", "tagline": "A", "category": "productivity", "curation_status": "approved"},
        {"slug": "fake-tool-2", "name": "Fake Tool 2", "tagline": "B", "category": "productivity", "curation_status": "approved"},
    ])

    # Look up the persisted user dict to pass to live_match.
    from app.db.users import find_user_by_id
    user_doc = await find_user_by_id(ObjectId(u["user"]["id"]))

    result = await live_match(
        user=user_doc,
        q_index=2,
        live_answers={
            1: {"job_title": "software_engineer", "level": "mid", "industry": "software_tech"},
            2: {"selected_values": ["vscode", "github"]},
        },
    )

    assert captured["alpha"] == 0.5
    assert captured["limit"] == 16  # K_SCHEDULE[1]=15 + 1 wildcard
    assert captured["filters"] == {"curation_status": "approved"}
    assert result.step == 2
    assert len(result.top) == 2
    assert result.top[0]["slug"] == "fake-tool"
    assert result.top[0]["score"] == 0.81
    assert result.top[0]["layer"] == "niche"
    assert result.top[1]["layer"] == "relevant"


async def test_live_match_degrades_when_hybrid_returns_empty(
    monkeypatch, app_client,
):
    """When hybrid_search returns [], live_match falls back to
    similarity_search and sets degraded=True."""
    from tests.conftest import signed_up_user_with_profile

    u = await signed_up_user_with_profile(app_client, "lm2@example.com")

    monkeypatch.setattr(
        "app.embeddings.openai.embed_text", _fake_embed_text, raising=True,
    )
    monkeypatch.setattr(
        "app.embeddings.lifecycle.embed_text", _fake_embed_text, raising=True,
    )

    async def empty_hybrid(**_kw):
        return []

    monkeypatch.setattr(
        "app.recommendations.live_engine.hybrid_search", empty_hybrid, raising=True,
    )

    from app.db.tools_seed import tools_seed_collection
    await tools_seed_collection().insert_many([
        {"slug": "x", "name": "X", "tagline": "x", "category": "productivity", "curation_status": "approved", "embedding": [0.1] * 1536},
        {"slug": "y", "name": "Y", "tagline": "y", "category": "productivity", "curation_status": "approved", "embedding": [0.1] * 1536},
    ])

    from app.db.users import find_user_by_id
    user_doc = await find_user_by_id(ObjectId(u["user"]["id"]))

    result = await live_match(
        user=user_doc,
        q_index=1,
        live_answers={
            1: {"job_title": "software_engineer", "level": "mid", "industry": "software_tech"},
        },
    )
    assert result.degraded is True
    assert len(result.top) >= 1
