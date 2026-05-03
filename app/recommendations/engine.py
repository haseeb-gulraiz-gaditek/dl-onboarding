"""Recommendation engine orchestrator.

Per spec-delta recommendation-engine F-REC-3, F-REC-4, F-REC-7.

Pipeline:
  1. Cache check. Hit -> return cached, truncated.
  2. Cache miss -> ensure_profile_embedding -> similarity_search top-20
     -> rank_with_llm (gpt-5) -> validate slugs against candidates ->
     upsert cache -> return.
  3. Ranker exception -> degraded fallback: similarity_search top-N
     with verdict="try" + generic reasoning. Cached so the next call
     within TTL doesn't re-hammer OpenAI.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.answers import answers_collection
from app.db.profiles import find_profile_by_user_id
from app.db.recommendations import (
    find_for_user,
    is_cache_valid,
    upsert_for_user,
)
from app.db.tools_founder_launched import find_by_slug as fl_find_by_slug
from app.db.tools_seed import find_tool_by_slug
from app.embeddings.lifecycle import ensure_profile_embedding
from app.embeddings.vector_store import TOOL_CLASS, similarity_search
from app.models.onboarding import tool_to_card
from app.models.recommendation import (
    RecommendationPick,
    RecommendationsResponse,
)
from app.recommendations.ranker import rank_with_llm


CACHE_TTL = timedelta(days=7)
SIMILARITY_TOP_K = 20
MAX_PICKS = 5
LAUNCH_TOP_K = 5  # F-PUB-6: top-5 launches by similarity, no floor


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _rank_score(rank_index: int, total: int) -> float:
    """Convert a 0-indexed rank into a 0..1 score (higher = better)."""
    if total <= 0:
        return 0.0
    return 1.0 - (rank_index / total)


async def generate_recommendations(
    user: dict[str, Any], count: int
) -> RecommendationsResponse:
    """End-to-end. Caller (endpoint) is responsible for the >=3-answers
    gate; this function assumes the user is recommendation-ready."""
    user_id = user["_id"]
    profile = await find_profile_by_user_id(user_id)

    cached = await find_for_user(user_id)
    if cached is not None and await is_cache_valid(cached, profile):
        return await _build_response(
            cached,
            count=count,
            from_cache=True,
            degraded=cached.get("degraded", False),
        )

    # Cache miss: ensure embedding, retrieve candidates, rank.
    await ensure_profile_embedding(user)
    profile = await find_profile_by_user_id(user_id)  # reload after embed

    candidates: list[dict[str, Any]] = []
    launch_candidates: list[dict[str, Any]] = []
    if profile is not None and profile.get("embedding") is not None:
        candidates = await similarity_search(
            collection_name="tools_seed",
            weaviate_class=TOOL_CLASS,
            query_vector=profile["embedding"],
            top_k=SIMILARITY_TOP_K,
            filters={"curation_status": "approved"},
        )
        # F-PUB-6: parallel similarity_search over founder-launched tools.
        # Returned in a separate `launches` slot, never commingled with
        # the organic ranking. No gpt-5 ranker call — these surface
        # by similarity score only.
        try:
            launch_candidates = await similarity_search(
                collection_name="tools_founder_launched",
                weaviate_class=TOOL_CLASS,
                query_vector=profile["embedding"],
                top_k=LAUNCH_TOP_K,
                filters={"curation_status": "approved"},
            )
        except Exception as exc:
            print(f"[recommendations] launch fan-in failed: {exc}")
            launch_candidates = []

    candidate_score: dict[str, float] = {
        c["slug"]: _rank_score(i, len(candidates))
        for i, c in enumerate(candidates)
    }

    cursor = answers_collection().find(
        {"user_id": user_id}
    ).sort("captured_at", -1).limit(10)
    recent_answers = await cursor.to_list(length=10)

    pick_dicts: list[dict[str, Any]]
    degraded = False
    try:
        if not candidates:
            raise RuntimeError("no candidates from similarity_search")
        ranker_picks = await rank_with_llm(
            profile=profile or {},
            recent_answers=recent_answers,
            candidates=candidates,
            count=MAX_PICKS,
        )
        # F-REC-4 step 4: validate slugs.
        valid_slugs = set(candidate_score.keys())
        validated = [p for p in ranker_picks if p.slug in valid_slugs]
        if not validated:
            raise RuntimeError("ranker returned no valid candidate slugs")
        pick_dicts = [
            {
                "tool_slug": p.slug,
                "verdict": p.verdict,
                "reasoning": p.reasoning,
                "score": candidate_score.get(p.slug, 0.0),
            }
            for p in validated[:MAX_PICKS]
        ]
    except Exception as exc:
        print(f"[recommendations] ranker degraded: {exc}")
        degraded = True
        pick_dicts = [
            {
                "tool_slug": c["slug"],
                "verdict": "try",
                "reasoning": (
                    "Top match by profile similarity. Personalized "
                    "reasoning unavailable right now."
                ),
                "score": candidate_score.get(c["slug"], 0.0),
            }
            for c in candidates[:MAX_PICKS]
        ]

    # F-PUB-6: project launch candidates into pick-shaped dicts.
    launch_pick_dicts: list[dict[str, Any]] = [
        {
            "tool_slug": c["slug"],
            "verdict": "try",
            "reasoning": "New launch matched against your profile.",
            "score": _rank_score(i, len(launch_candidates)),
        }
        for i, c in enumerate(launch_candidates[:LAUNCH_TOP_K])
    ]

    now = _now()
    rec_doc = {
        "user_id": user_id,
        "picks": pick_dicts,
        "launch_picks": launch_pick_dicts,
        "generated_at": now,
        "cache_expires_at": now + CACHE_TTL,
        "degraded": degraded,
    }
    await upsert_for_user(user_id, rec_doc)

    return await _build_response(
        rec_doc, count=count, from_cache=False, degraded=degraded
    )


async def _build_response(
    rec_doc: dict[str, Any], count: int, from_cache: bool, degraded: bool
) -> RecommendationsResponse:
    """Project a stored rec doc into RecommendationsResponse, hydrating
    each pick with the current tool details. Organic picks come from
    `tools_seed`; launch picks (F-PUB-6) come from
    `tools_founder_launched`. Tools that have been rejected or removed
    since the rec was cached are silently dropped."""
    picks = rec_doc.get("picks") or []
    items: list[RecommendationPick] = []
    for p in picks[:count]:
        tool_doc = await find_tool_by_slug(p["tool_slug"])
        if tool_doc is None:
            continue
        if tool_doc.get("curation_status") != "approved":
            continue
        items.append(
            RecommendationPick(
                tool=tool_to_card(tool_doc),
                verdict=p["verdict"],
                reasoning=p["reasoning"],
                score=p["score"],
            )
        )

    # F-PUB-6: hydrate launch picks from tools_founder_launched.
    launch_picks_raw = rec_doc.get("launch_picks") or []
    launch_items: list[RecommendationPick] = []
    for p in launch_picks_raw[:count]:
        tool_doc = await fl_find_by_slug(p["tool_slug"])
        if tool_doc is None:
            continue
        if tool_doc.get("curation_status") != "approved":
            continue
        launch_items.append(
            RecommendationPick(
                tool=tool_to_card(tool_doc),
                verdict=p["verdict"],
                reasoning=p["reasoning"],
                score=p["score"],
            )
        )

    return RecommendationsResponse(
        recommendations=items,
        launches=launch_items,
        generated_at=rec_doc.get("generated_at") or _now(),
        from_cache=from_cache,
        degraded=degraded,
    )
