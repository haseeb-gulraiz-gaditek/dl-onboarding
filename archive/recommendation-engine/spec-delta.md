# Spec Delta: recommendation-engine

## ADDED

### F-REC-1 — `POST /api/recommendations` endpoint exists

A new endpoint at `POST /api/recommendations` is mounted behind `Depends(require_role("user"))`. Optional request body `{count?: int}` defaults to `3`, clamped to `1..5`.

**Given** an authenticated `role_type=user` caller with ≥3 distinct answered questions
**When** they `POST /api/recommendations` with `{"count": 5}`
**Then** the system returns `200 OK` with a `RecommendationsResponse` body (see F-REC-5).

**Founder caller** → `403 role_mismatch` (per F-AUTH-3).
**Unauthenticated** → `401 auth_required` (per F-AUTH-3).

---

### F-REC-2 — Minimum answers gate

**Given** an authenticated user with `count_distinct_answers < 3`
**When** they `POST /api/recommendations`
**Then** the system returns `400 Bad Request` with `{"error": "no_profile_yet", "min_answers": 3}`.

`MIN_ANSWERS_FOR_RECS = 3` is a module-level constant matching cycle #5's `GENERIC_MODE_MAX_ANSWERS`. The two thresholds intentionally align: the same point at which onboarding match flips to embedding-mode is the point at which the recommendation engine becomes available.

---

### F-REC-3 — Cache hit path

**Given** a user has a cached `recommendations` row where `cache_expires_at > now` AND `profile.last_invalidated_at <= recommendations.generated_at`
**When** they `POST /api/recommendations` with any valid `count`
**Then** the system returns the cached picks (truncated to `count`) with `from_cache: true` in the response.

No OpenAI call. No similarity_search call. Pure Mongo read. Latency target: <50ms.

The cache stores **up to 5 picks** regardless of the count of the call that generated it. Subsequent calls with `count=3` serve the first 3 picks in stored order; calls with `count=5` serve all stored picks.

---

### F-REC-4 — Cache miss / fresh generation path

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

### F-REC-5 — Response shape

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
  "from_cache": false
}
```

Recommendations are returned in `score`-descending order. `OnboardingToolCard` is reused (cycle #5 schema) — only user-facing tool fields, no internal state.

---

### F-REC-6 — `recommendations` collection schema

A new MongoDB collection `recommendations` stores per-user cached results.

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
  cache_expires_at: <datetime>  // = generated_at + 7 days
}
```

Unique index on `user_id`: one cached row per user. Upsert on regeneration replaces the entire document.

---

### F-REC-7 — OpenAI failure → degraded response

**Given** the cache is stale and the ranker step (F-REC-4 step 3) raises any exception (timeout, 429, 5xx, schema parse failure)
**When** the endpoint runs
**Then** the system:

1. Logs the exception with `[recommendations] ranker degraded: <reason>`.
2. Builds a fallback recommendations list from the `similarity_search` results: up to 5 picks, all with `verdict: "try"`, generic reasoning string `"Top match by profile similarity. Personalized reasoning unavailable right now."`, and `score` = the cosine score from similarity_search.
3. Caches the degraded response (so we don't keep hammering OpenAI on every retry within the cache window).
4. Returns `200 OK` with the degraded response. The response includes `from_cache: false` and a `degraded: true` flag at the top level.

The user never sees a 5xx. They see slightly worse reasoning until OpenAI recovers and the cache expires.

## MODIFIED

(None. This cycle adds new collections / endpoints / modules without modifying any prior spec.)

## REMOVED

(None.)
