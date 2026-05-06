"""Live-narrowing recommendation engine for cycle #15.

Per spec-delta `live-narrowing-onboarding` F-LIVE-2 / F-LIVE-3 /
F-LIVE-5 / F-LIVE-6.

The classic post-onboarding engine (`app/recommendations/engine.py`)
stays unchanged — it still serves /api/recommendations after Q4
finishes. This module is the per-tap surface used during the live
flow.
"""
from __future__ import annotations

from typing import Any

from app.db.mongo import get_db
from app.embeddings.lifecycle import ensure_profile_embedding
from app.embeddings.vector_store import (
    TOOL_CLASS,
    hybrid_search,
    similarity_search,
)
from app.onboarding.live_questions import LIVE_QUESTIONS, role_key_for


# ---- Schedules ----

ALPHA_SCHEDULE: list[float] = [0.3, 0.5, 0.7, 0.8]   # BM25 → vector lean by question
K_SCHEDULE: list[int] = [20, 15, 10, 6]              # UI-shrink budget


# ---- Score-band layers (F-LIVE-5) ----

LAYER_BANDS: dict[str, float] = {
    "niche": 0.75,
    "relevant": 0.65,
    "general": 0.55,
}


def layer_for(score: float) -> str | None:
    """Return the highest band a score qualifies for, or None when
    below the floor (excluded from `top`)."""
    if score >= LAYER_BANDS["niche"]:
        return "niche"
    if score >= LAYER_BANDS["relevant"]:
        return "relevant"
    if score >= LAYER_BANDS["general"]:
        return "general"
    return None


# ---- profile_text builder ----

def _humanize_q1(answer_value: dict[str, Any]) -> str:
    job = answer_value.get("job_title", "")
    level = answer_value.get("level", "")
    industry = answer_value.get("industry", "")
    parts = []
    if level:
        parts.append(level.replace("_", " "))
    if job:
        parts.append(job.replace("_", " "))
    base = " ".join(parts).strip() or "professional"
    if industry:
        base += f" in {industry.replace('_', ' ')}"
    return f"I'm a {base}."


def _humanize_q2(answer_value: dict[str, Any]) -> str:
    selected = answer_value.get("selected_values") or []
    if not selected:
        return ""
    nice = ", ".join(s.replace("_", " ") for s in selected)
    return f"On a typical day I have these tools open: {nice}."


def _humanize_q3(answer_value: dict[str, Any], q3_label_lookup: dict[str, str]) -> str:
    sel = answer_value.get("selected_value", "")
    if not sel:
        return ""
    label = q3_label_lookup.get(sel, sel.replace("_", " "))
    return f"A 'big task' I actually finish at work: {label}"


def _humanize_q4(answer_value: dict[str, Any], q4_label_lookup: dict[str, str]) -> str:
    sel = answer_value.get("selected_value", "")
    if not sel:
        return ""
    label = q4_label_lookup.get(sel, sel.replace("_", " "))
    return f"What slows me down most: {label}"


def profile_text_from_live_answers(
    live_answers: dict[int, dict[str, Any]],
) -> str:
    """Build a structured paragraph from accumulated Q1..Q4 answers.

    `live_answers` maps q_index → answer_value dict (from POSTed
    requests). Missing Q's are skipped — the paragraph grows as the
    user advances.
    """
    # Lookup tables for human-readable labels.
    q3_labels: dict[str, str] = {}
    q4_labels: dict[str, str] = {}
    for q in LIVE_QUESTIONS:
        if q.q_index == 3 and q.options_per_role:
            for opts in q.options_per_role.values():
                for o in opts:
                    q3_labels[o.value] = o.label
            for o in (q.fallback_options or []):
                q3_labels[o.value] = o.label
        if q.q_index == 4 and q.options:
            for o in q.options:
                q4_labels[o.value] = o.label

    parts: list[str] = []
    if 1 in live_answers:
        parts.append(_humanize_q1(live_answers[1]))
    if 2 in live_answers:
        s = _humanize_q2(live_answers[2])
        if s:
            parts.append(s)
    if 3 in live_answers:
        s = _humanize_q3(live_answers[3], q3_labels)
        if s:
            parts.append(s)
    if 4 in live_answers:
        s = _humanize_q4(live_answers[4], q4_labels)
        if s:
            parts.append(s)
    return " ".join(parts).strip() or "I'm new to this."


# ---- Main pipeline ----

class LiveMatchResult:
    """Return value of `live_match()`. Plain class (not Pydantic) so
    the API layer can shape the response with full control."""

    def __init__(
        self,
        *,
        step: int,
        top: list[dict[str, Any]],
        wildcard: dict[str, Any] | None,
        count_kept: int,
        degraded: bool,
    ) -> None:
        self.step = step
        self.top = top
        self.wildcard = wildcard
        self.count_kept = count_kept
        self.degraded = degraded


async def _hydrate_tools(slugs: list[str]) -> dict[str, dict[str, Any]]:
    """Pull full tool docs by slug from `tools_seed` (organic catalog)."""
    if not slugs:
        return {}
    coll = get_db()["tools_seed"]
    docs = await coll.find({"slug": {"$in": slugs}}).to_list(length=len(slugs) + 5)
    return {d["slug"]: d for d in docs}


def _reasoning_hook_for(layer: str | None, q_index: int) -> str:
    """One-line reasoning copy keyed by layer + step. Generic per V1."""
    if layer is None:
        return "from outside the top band — concierge surprise"
    if q_index == 1:
        return f"matches your role / industry ({layer})"
    if q_index == 2:
        return f"fits your daily-open stack ({layer})"
    if q_index == 3:
        return f"helps with the task you actually finish ({layer})"
    if q_index == 4:
        return f"attacks the friction you flagged ({layer})"
    return layer


async def live_match(
    *,
    user: dict[str, Any],
    q_index: int,
    live_answers: dict[int, dict[str, Any]],
) -> LiveMatchResult:
    """F-LIVE-2 pipeline: build profile_text, re-embed, hybrid search,
    layer-label, wildcard-pick, hydrate.

    Caller is responsible for persisting the latest answer to the
    `answers` collection BEFORE calling this. We just read the
    accumulated map.
    """
    profile_text = profile_text_from_live_answers(live_answers)

    # Force-recompute the profile vector each tap (per F-LIVE-4).
    await ensure_profile_embedding(user, force_recompute=True, override_text=profile_text)

    # Re-fetch profile to read the freshly-stored vector.
    profiles = get_db()["profiles"]
    profile_doc = await profiles.find_one({"user_id": user["_id"]})
    vector: list[float] = (profile_doc or {}).get("embedding") or []

    alpha = ALPHA_SCHEDULE[q_index - 1]
    k = K_SCHEDULE[q_index - 1]
    # Over-fetch generously so we still hit `k + wildcard` after
    # filtering out household-name tools (label `all_time_best`).
    # Worst case ~30% of the over-fetch is filtered; +12 buffer is plenty.
    overfetch_limit = k + 12

    degraded = False
    pairs: list[tuple[dict[str, Any], float]] = []

    if vector:
        pairs = await hybrid_search(
            weaviate_class=TOOL_CLASS,
            query=profile_text,
            vector=vector,
            alpha=alpha,
            limit=overfetch_limit,
            filters={"curation_status": "approved"},
        )

    # Hybrid empty → fall back to similarity_search (covers Weaviate
    # down OR mongomock test env).
    if not pairs:
        degraded = True
        # similarity_search hydrates against tools_seed for us.
        docs = await similarity_search(
            collection_name="tools_seed",
            weaviate_class=TOOL_CLASS,
            query_vector=vector or [0.0] * 1536,
            top_k=overfetch_limit,
            filters={"curation_status": "approved"},
        )
        # Synthesize scores: descending decimals so the ranking from
        # similarity_search is preserved with synthetic scores in the
        # general band. Real scores are unavailable in fallback mode.
        pairs = [
            ({"slug": d.get("slug")}, max(0.55, 0.85 - i * 0.02))
            for i, d in enumerate(docs)
        ]

    # Hydrate full tool docs by slug.
    slugs = [p[0].get("slug") for p in pairs if p[0].get("slug")]
    tools_by_slug = await _hydrate_tools([s for s in slugs if isinstance(s, str)])

    enriched: list[tuple[dict[str, Any], float]] = []
    for props, score in pairs:
        slug = props.get("slug")
        if not isinstance(slug, str):
            continue
        tool = tools_by_slug.get(slug)
        if tool is None:
            continue
        # Filter out household-name tools — `all_time_best` is the
        # catalog label for "everyone-already-knows-this." The live
        # flow's job is to surface lesser-known fits, not re-recommend
        # ChatGPT / Notion / Slack to people who already use them.
        labels = tool.get("labels") or []
        if "all_time_best" in labels:
            continue
        enriched.append((tool, score))

    # Top-K, then wildcard. Tools below the general band ARE allowed
    # in `top` for V1 (the layer label is informational; we don't drop
    # below-band hits since the score-band thresholds are gut-feel and
    # niche profiles need to see *something*).
    top_pairs = enriched[:k]
    wildcard_pair = enriched[k] if len(enriched) > k else None

    top_payload: list[dict[str, Any]] = []
    for tool, score in top_pairs:
        layer = layer_for(score)
        top_payload.append({
            "slug": tool.get("slug"),
            "name": tool.get("name"),
            "tagline": tool.get("tagline"),
            "category": tool.get("category"),
            "score": round(float(score), 4),
            "layer": layer,
            "reasoning_hook": _reasoning_hook_for(layer, q_index),
        })

    wildcard_payload: dict[str, Any] | None = None
    if wildcard_pair is not None:
        tool, score = wildcard_pair
        wildcard_payload = {
            "slug": tool.get("slug"),
            "name": tool.get("name"),
            "tagline": tool.get("tagline"),
            "category": tool.get("category"),
            "score": round(float(score), 4),
            "layer": layer_for(score),
            "reasoning_hook": _reasoning_hook_for(None, q_index),
        }

    return LiveMatchResult(
        step=q_index,
        top=top_payload,
        wildcard=wildcard_payload,
        count_kept=len(top_payload),
        degraded=degraded,
    )
