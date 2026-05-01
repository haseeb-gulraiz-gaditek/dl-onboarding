# Proposal: fast-onboarding-match-and-graph

> **Slug-vs-implementation note:** the slug includes "graph" because the original system_design called for a live force-directed graph in the React onboarding screen. **This cycle ships the API only** — the React frontend that renders a graph is the user's separate Claude Design parallel track. The slug stays for backlog traceability; "graph" here refers to the *data structure* the API exposes (top-K tools with category/label metadata) that a frontend can render as a graph.

## Problem

Maya (the layperson persona) opens `/onboarding`, taps her way through the question bank, and expects to see a tool cloud refining in real time — *"this is what Mesh thinks fits you so far."* That's the constitutional *"Tapping IS the ritual"* tenet made visible: every tap should change what she sees on screen.

We have the data layer (cycles #1–#4) but no endpoint that returns "top tools given the user's current onboarding state." Cycle #6's recommendation engine will be the **slow, smart, LLM-ranked** endpoint that fires once at end-of-onboarding and weekly thereafter. This cycle delivers the **fast, dumb, search-only** companion: every tap re-fires it, every response is sub-second, no LLM in the loop, results are personalized by the data we have so far.

## Solution

A single endpoint, `POST /api/onboarding/match`, behind `Depends(require_role("user"))`. Two execution modes selected automatically by how many answers the user has so far:

- **Generic mode (`answered_count < 3`):** look up the user's role answer (if they've answered the role question), map it to a closed list of relevant categories (`ROLE_TO_CATEGORIES` constant), filter `tools_seed` by those categories + `curation_status=approved` + `labels` containing `"all_time_best"`, return up to 5 tools alphabetical by name. If the role answer is absent, return up to 5 from the catalog-wide `all_time_best` set. **No OpenAI call.** Latency target: <50ms.
- **Embedding mode (`answered_count >= 3`):** call `ensure_profile_embedding(user)` (regenerates the embedding if stale, ~500ms via OpenAI when needed), then call cycle #4's `similarity_search` with `weaviate_class=ToolEmbedding` and `top_k=5`. Return whatever Weaviate ranks at the top. **No filter relaxation** — if the user's profile is too niche to find 5 strong matches, that's signal, not failure.

Response shape: `{mode: "generic" | "embedding", tools: [{slug, name, tagline, description, url, pricing_summary, category, labels}, ...]}`. Up to 5 tools, ranked.

Frontend (out of scope here) calls this endpoint after every `POST /api/answers`. The frontend decides how to render — could be a graph, could be a list, could be cards.

## Scope

**In:**
- `POST /api/onboarding/match` endpoint behind `require_role("user")`
- `app/onboarding/role_map.py` — closed-list `ROLE_TO_CATEGORIES` mapping each `role.primary_function` enum value to a list of relevant categories
- Mode-selection logic: count user's answers, pick generic vs embedding
- Generic-mode implementation: read role answer, apply category filter, query Mongo, return alphabetical top-5
- Embedding-mode implementation: `ensure_profile_embedding` + `similarity_search`
- `MatchResponse` Pydantic model (mode discriminator + tool list)
- Tests covering both modes, both happy-path and edge cases
- Conftest helpers for "signed-up user with N answers"

**Out:**
- Frontend (React graph component) — your Claude Design track
- Caller-supplied filters in the request body — V1.5+ once a frontend has a "refine" UX
- LLM-ranked starter recs at end-of-onboarding — owned by cycle #6
- Community auto-suggestions at end-of-onboarding — owned by cycle #7
- Tool-to-tool relationship edges (integration / replacement signals) — schema doesn't have this data; deferred until tools start carrying it
- Latency optimization (sub-200ms target from the original backlog dropped per user call; "slow is fine for MVP")
- Caching of generic-mode results — V1.5+

## Alternatives Considered

1. **Single mode using Weaviate from question 1** — rejected per user call. The first 3 answers don't carry enough signal to produce useful embedding-based matches; generic role-bucket ranking is faster, deterministic, and demoably good enough.
2. **Filter relaxation when search returns <5** — rejected per user call. Returning fewer tools when the user's profile is genuinely niche is honest signal; padding with unrelated tools to hit a "5-minimum" feels like vendor-spam.
3. **`MERGE-mode` (mix generic + embedding 50/50)** — rejected. Two modes are sharper to reason about and test; mixing creates blend-ratio tuning that's not worth V1.
4. **Caller-supplied filters in request body** — deferred. Adds API surface area before we have a frontend that uses it. Easier to add later than to remove.

## Risks

1. **The 3-answer threshold is arbitrary** — chosen because the user previously said "first 3 questions" generic. May want to tune to 4 or 5 once we have real cohort data. Mitigation: threshold is a single constant (`GENERIC_MODE_MAX_ANSWERS = 3`); easy to amend.
2. **Embedding-mode latency hits ~600ms on every tap from Q3 onward** — slow, but per user call ("slow is fine for MVP"). Mitigation: profile embeddings are cached after first regeneration; subsequent taps are ~100ms (Weaviate only). The slow tap is the one *triggering* a re-embed; the next 5–10 taps reuse the cached embedding until the next answer invalidates it.
3. **Role-to-categories mapping is a product judgement that may be wrong.** Mitigation: it's a single dict in code, editable without a schema change. Future cycle can replace with a learned mapping.
4. **Founder accounts hit this endpoint** — `require_role("user")` returns 403. Surfaces a frontend bug if a founder is shown the onboarding screen, but no data leak.
5. **`ensure_profile_embedding` failure (OpenAI down)** — would fail the match call. Mitigation: catch the exception and fall back to generic mode for this request. Logs a warning but the user still sees tools. Same graceful-degradation pattern as cycle #3's approve handler.

## Rollback

- Drop `app/api/onboarding.py` and `app/onboarding/role_map.py`.
- Unmount the router in `app/main.py`.
- Revert this cycle's commits.

No downstream cycle depends on this endpoint yet. Rollback cost is bounded.
