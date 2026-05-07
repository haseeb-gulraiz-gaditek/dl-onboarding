# Proposal: live-narrowing-onboarding

> Source: `backlog:15` (priority: high). Pre-filled from the backlog body and the
> 8-tension reconciliation conversation logged 2026-05-06. All sections marked
> `[REVIEW]` rather than `[REQUIRED]` — content is locked, just confirm.

## Problem

The current onboarding ships ~12 free-text + multi-select questions, persists
each answer to Mongo, and on completion fires `POST /api/onboarding/match` which
runs a 2-mode dispatch (generic <3 questions, embedding ≥3) against a single
catalog (`tools_seed`). It works, but the user only sees recommendations *after*
they finish — there's no feedback loop showing "Mesh is learning you." For a
positioning that sells "the AI agent that maps your context graph," that's a
silent first impression.

We have algorithm research locked in `validation/onboarding-v1-locked.md` for a
**live-narrowing flow**: 4 questions, hybrid search after each answer, ranked
list of tools shrinking 20 → 15 → 10 → 6 in real time, with score-band labels
("general / relevant / niche") replacing pre-clustering. The validation harness
exists (`validation/approach1/`) as a no-embedding baseline.

## Solution

Add a **second**, parallel onboarding flow at `/onboarding/live` that ships the
locked 4-question schema + a single new endpoint
`POST /api/recommendations/live-step`. Per tap: persist the answer (existing
collection), re-embed the accumulated profile, run a Weaviate hybrid query
(alpha schedule by question index), return top-K + 1 wildcard with score-band
layer labels.

**Deliberately keeps both flows.** The old onboarding stays at `/onboarding`
(unchanged); the new one ships at `/onboarding/live` behind a feature flag. Old
question seed stays in `app/seed/questions.json`; new questions live in
`app/onboarding/live_questions.py` as a code constant (NOT a seed file). This
avoids breaking `fast-onboarding-match-and-graph`'s reliance on
`role.primary_function` and lets us A/B test by completion + adoption rate.

**Persistence model is uniform.** Every tap persists both the answer
(existing `answers` collection) and the recomputed profile vector (existing
`profiles` collection via `ensure_profile_embedding`). If a user abandons at
Q2, their profile reflects 2 questions and `/home` shows the cached top-15 —
no "ephemeral throwaway vectors" complexity.

**No Weaviate schema change.** The existing `ToolEmbedding` class has `slug`,
`category`, `labels` indexed; that's enough for BM25 keyword matching at
hybrid-low alpha. Vectors carry the semantic load. If results feel weak after
live testing, a follow-up cycle can extend the schema.

**Dev resilience.** The 8-tension call surfaced that this dev box's network
silently blocks Weaviate's gRPC subdomain (REST works, gRPC is firewalled).
This cycle adds a `WEAVIATE_USE_GRPC` env flag that, when false, configures the
Python client to skip gRPC entirely and use REST-only — slower per query but
unblocks dev on any network. Production stays on gRPC.

## Scope

**In:**
- `app/onboarding/live_questions.py` — the locked 4-question schema (Q1
  dropdowns, Q2 chips, Q3 single-select scenarios, Q4 friction). Hand-curated
  role-conditioned option tables for ~12 roles + a generic fallback. No LLM
  long-tail in V1.
- New `LiveQuestion` Pydantic model — separate from the existing `Question`
  model in `question-bank-and-answer-capture`.
- `app/recommendations/live_engine.py` — `live_match(user, q_index)`:
  builds profile_text from accumulated answers, calls
  `ensure_profile_embedding`, runs Weaviate hybrid with alpha-schedule
  `[0.3, 0.5, 0.7, 0.8]` and K-schedule `[20, 15, 10, 6]`, applies score-band
  layer labels (general s≥0.55, relevant s≥0.65, niche s≥0.75), returns top-K
  + 1 wildcard.
- `POST /api/recommendations/live-step` — request `{q_index, answer_value}`,
  response `{step, top:[{slug,name,score,layer,reasoning_hook}], count_kept}`.
  Persists both the answer and the regenerated profile vector before returning.
- `app/embeddings/vector_store.py` — extend `_get_weaviate_client()` to honour
  `WEAVIATE_USE_GRPC=false` (default true). When false, configure the v4
  client with HTTP-only options (no gRPC connection attempt).
- `app/embeddings/vector_store.py` — new `hybrid_search()` helper that wraps
  Weaviate v4's `collection.query.hybrid(query=..., vector=..., alpha=...,
  limit=..., filters=...)`.
- `frontend/src/app/onboarding/live/page.tsx` — animated narrowing list,
  layer chips, per-question persistence indicators, "saved so far →" link
  back to /home if user bails mid-flow.
- Feature flag: `MESH_ONBOARDING_VARIANT={"classic","live"}` env, defaulting
  to `classic`. Frontend reads it from `/api/me` on mount and routes to the
  matching onboarding page.
- Persona walkthrough validation as a smoke test (re-run `validation/approach1/`
  three personas through the new pipeline; record results in
  `validation/approach1/results-live.md`).

**Out (deferred V1.5+):**
- Replacing `/api/onboarding/match` (the old endpoint stays — old flow
  unchanged).
- LLM long-tail option generation for unrecognized roles (V1 falls back to a
  generic ~12-tool option set).
- Weaviate schema extension to add `name`/`tagline`/`description` text
  properties for richer BM25 (a follow-up cycle if hybrid feels weak).
- Threshold auto-tuning. Score-band thresholds are single module-level
  constants; tuning is a one-line edit. No A/B framework yet.
- Replacing the post-onboarding `recommendation-engine` (cycle #6) — that
  still runs after Q4 completes against the same persisted profile vector.

## Risks

- **Weaviate gRPC unreachable from dev.** Mitigated by the
  `WEAVIATE_USE_GRPC=false` flag. Slower per query (REST hybrid is ~3x slower
  than gRPC) but functional. Production stays gRPC.
- **Latency target slippage.** OpenAI embed is 250–400ms from the user's region.
  Per-tap pipeline target is now <800ms (relaxed from 200ms in the backlog) with
  an "Updating…" UI placeholder during embed. If embed is the bottleneck V1.5
  may move it to a background task and stream the rank update.
- **Role-conditioned option tables drift from reality.** The 12 hand-curated
  role → tool lists are product judgement, not data-backed. Document in the
  module that they're tunable; expect to revise after watching real users.
- **Score-band thresholds (0.55 / 0.65 / 0.75) are gut-feel.** Locked as
  module constants for V1. If layer labels look noisy in the persona
  walkthrough, tune within the cycle.
- **Both onboarding flows live = double maintenance until classic is sunset.**
  Accepted; the A/B is the point. Sunset gate is documented as ≥70% recall@10
  vs founder-graded gold ranks before promoting `live` to default.
- **Hybrid search over the minimal `ToolEmbedding` schema may underperform.**
  V1 BM25 only matches against `slug`, `category`, `labels`. If keyword side is
  effectively useless, fall back to alpha=1.0 (pure vector) for that step and
  log it. Schema extension is a separate cycle.
