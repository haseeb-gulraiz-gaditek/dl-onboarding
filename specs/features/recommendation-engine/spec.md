# Feature: Recommendation Engine

> **Cycle of origin:** `recommendation-engine` (archived; see `archive/recommendation-engine/`)
> **Last reviewed:** 2026-05-02
> **Constitution touchpoints:** `principles.md` (*"Recommend honestly, including skip-this"* — `verdict` field surfaces try/skip per pick; *"Tapping IS the ritual"* — endpoint fires after onboarding completes; *"Anti-spam is structural, not enforced"* — founder accounts are structurally barred).
> **Builds on:** `auth-role-split` (`require_role`), `question-bank-and-answer-capture` (answers, profiles, `last_invalidated_at`), `catalog-seed-and-curation` (tools_seed), `weaviate-pipeline` (`ensure_profile_embedding`, `similarity_search`), `fast-onboarding-match-and-graph` (`count_distinct_answers`).

> **Companion-vs-replacement note:** `POST /api/onboarding/match` (cycle #5) is the *fast* per-tap companion — no LLM, no caching, just role-bucket or similarity search. `POST /api/recommendations` (this cycle) is the *slow* end-of-onboarding ranker — calls GPT-5 to write personalized reasoning per pick, caches for 7 days, surfaces `verdict: "skip"` when a candidate is a poor fit. Both endpoints coexist; they serve different moments in the user's journey.

---

## Intent

Maya finishes onboarding (or returns a week later). She wants Mesh to think about her workflow and tell her — in her words — which 3-5 tools are actually worth her time. Not "here are tools tagged `marketing`," but "you mentioned the Tuesday Notion → Linear copy-paste pain; Cursor's repo-wide refactor commands directly remove that grunt work."

A single endpoint, `POST /api/recommendations`, behind `require_role("user")`. Optional `{count}` body, defaults 3, clamped 1..5. Pipeline:

1. **Gate**: user must have ≥3 distinct answered questions (matches cycle #5's `GENERIC_MODE_MAX_ANSWERS` — same threshold at which match flips to embedding mode).
2. **Cache check** (Mongo only, ~10ms): if `cache_expires_at > now` AND `profile.last_invalidated_at <= rec.generated_at`, return cached picks truncated to `count`.
3. **Cache miss**: `ensure_profile_embedding` → `similarity_search` (top-20 candidates, `curation_status=approved`) → `rank_with_llm` (GPT-5 via `beta.chat.completions.parse` with Pydantic structured output) → drop hallucinated slugs → upsert cache → return.
4. **Degraded path**: any ranker exception caught; fall back to similarity_search results with `verdict="try"` and a generic reasoning string. Still cached so we don't re-hammer OpenAI on every retry within the cache window. Response includes `degraded: true`.

Cache TTL: 7 days. Cache invalidation: TTL elapsed OR profile mutated since last gen (cycle #2's `last_invalidated_at` contract). Founders blocked at the route boundary; unauthenticated → 401.

## Surface

- **HTTP:** `POST /api/recommendations` — body `{count?: int}` (default 3, clamped 1..5).
- **Response model:** `RecommendationsResponse` with `recommendations: list[RecommendationPick]`, `generated_at`, `from_cache`, `degraded`. Each `RecommendationPick` has `tool: OnboardingToolCard`, `verdict ∈ {"try", "skip"}`, `reasoning: str`, `score: float`.
- **OpenAI structured output:** `RankerOutput { picks: list[RankerPick] }`, where `RankerPick { slug, verdict, reasoning }`. Slugs are validated server-side against the candidate set to drop hallucinations.
- **Internal modules:**
  - `app/recommendations/engine.py` — `generate_recommendations(user, count)` orchestrator.
  - `app/recommendations/ranker.py` — `rank_with_llm(profile, recent_answers, candidates, count)` GPT-5 call.
  - `app/db/recommendations.py` — `recommendations_collection`, `find_for_user`, `upsert_for_user`, `is_cache_valid`.
- **MongoDB collection:** `recommendations` (one row per user, unique on `user_id`).

---

## F-REC-1 — `POST /api/recommendations` endpoint exists

A new endpoint at `POST /api/recommendations` is mounted behind `Depends(require_role("user"))`. Optional request body `{count?: int}` defaults to `3`, clamped to `1..5`.

**Given** an authenticated `role_type=user` caller with ≥3 distinct answered questions
**When** they `POST /api/recommendations` with `{"count": 5}`
**Then** the system returns `200 OK` with a `RecommendationsResponse` body (see F-REC-5).

**Founder caller** → `403 role_mismatch` (per F-AUTH-3).
**Unauthenticated** → `401 auth_required` (per F-AUTH-3).

---

## F-REC-2 — Minimum answers gate

**Given** an authenticated user with `count_distinct_answers < 3`
**When** they `POST /api/recommendations`
**Then** the system returns `400 Bad Request` with `{"error": "no_profile_yet", "min_answers": 3}`.

`MIN_ANSWERS_FOR_RECS = 3` is a module-level constant matching cycle #5's `GENERIC_MODE_MAX_ANSWERS`. The two thresholds intentionally align: the same point at which onboarding match flips to embedding-mode is the point at which the recommendation engine becomes available.

---

## F-REC-3 — Cache hit path

**Given** a user has a cached `recommendations` row where `cache_expires_at > now` AND `profile.last_invalidated_at <= recommendations.generated_at`
**When** they `POST /api/recommendations` with any valid `count`
**Then** the system returns the cached picks (truncated to `count`) with `from_cache: true` in the response.

No OpenAI call. No similarity_search call. Pure Mongo read. Latency target: <50ms.

The cache stores **up to 5 picks** regardless of the count of the call that generated it. Subsequent calls with `count=3` serve the first 3 picks in stored order; calls with `count=5` serve all stored picks.

---

## F-REC-4 — Cache miss / fresh generation path

**Given** the cache is missing OR expired OR profile has been invalidated since the cached `generated_at`
**When** the endpoint runs
**Then** the system:

1. Calls `ensure_profile_embedding(user)` — regenerates the profile vector if cycle #2's `last_invalidated_at` is newer than `last_recompute_at`.
2. Calls `similarity_search(collection_name="tools_seed", weaviate_class="ToolEmbedding", query_vector=<embedding>, top_k=20, filters={"curation_status": "approved"})` — returns up to 20 candidates ranked by cosine.
3. Calls the OpenAI `gpt-5` ranker via `beta.chat.completions.parse` with a structured-output schema. Input: profile (role + last 10 answers) + the 20 candidates' (slug, name, tagline, description, category, labels). Output: a list of up to 5 `RankerPick` objects, each with `slug`, `verdict ∈ {"try", "skip"}`, `reasoning` (1–3 sentences).
4. **Validates each picked slug** is present in the input candidate set. Drops any hallucinated slugs.
5. Computes a cosine `score` for each surviving pick by re-looking-up the candidate's position in the similarity_search result (or 0.0 if it's somehow missing).
6. Upserts the `recommendations` row for `user_id`: `{picks, generated_at: now, cache_expires_at: now + 7 days}`.
7. Returns the picks (truncated to `count`) with `from_cache: false`.

---

## F-REC-5 — Response shape

```json
{
  "recommendations": [
    {
      "tool": {
        "slug": "cursor",
        "name": "Cursor",
        "tagline": "AI-first code editor.",
        "description": "...",
        "url": "...",
        "pricing_summary": "...",
        "category": "engineering",
        "labels": ["all_time_best"]
      },
      "verdict": "try",
      "reasoning": "Given your Tuesday Notion → Linear copy-paste pain, Cursor's repo-wide refactor commands directly remove the kind of grunt work you flagged.",
      "score": 0.87
    },
    {
      "tool": { ... },
      "verdict": "skip",
      "reasoning": "Hyped this month, but doesn't actually overlap with what you said you do — skip until you start working on something it solves.",
      "score": 0.61
    }
    // ...up to `count` items
  ],
  "generated_at": "2026-05-02T12:34:56Z",
  "from_cache": false,
  "degraded": false
}
```

Recommendations are returned in `score`-descending order. `OnboardingToolCard` is reused (cycle #5 schema) — only user-facing tool fields, no internal state.

---

## F-REC-6 — `recommendations` collection schema

A MongoDB collection `recommendations` stores per-user cached results.

```
{
  user_id: <ObjectId, unique>,
  picks: [
    {
      tool_slug: <string>,
      verdict: "try" | "skip",
      reasoning: <string>,
      score: <float>
    },
    ... up to 5 picks
  ],
  generated_at: <datetime>,
  cache_expires_at: <datetime>,  // = generated_at + 7 days
  degraded: <bool>
}
```

Unique index on `user_id`: one cached row per user. Upsert on regeneration replaces the entire document.

---

## F-REC-7 — OpenAI failure → degraded response

**Given** the cache is stale and the ranker step (F-REC-4 step 3) raises any exception (timeout, 429, 5xx, schema parse failure)
**When** the endpoint runs
**Then** the system:

1. Logs the exception with `[recommendations] ranker degraded: <reason>`.
2. Builds a fallback recommendations list from the `similarity_search` results: up to 5 picks, all with `verdict: "try"`, generic reasoning string `"Top match by profile similarity. Personalized reasoning unavailable right now."`, and `score` = the cosine score from similarity_search.
3. Caches the degraded response (so we don't keep hammering OpenAI on every retry within the cache window).
4. Returns `200 OK` with the degraded response. The response includes `from_cache: false` and a `degraded: true` flag at the top level.

The user never sees a 5xx. They see slightly worse reasoning until OpenAI recovers and the cache expires.
