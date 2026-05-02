# Feature: Fast Onboarding Match

> **Cycle of origin:** `fast-onboarding-match-and-graph` (archived; see `archive/fast-onboarding-match-and-graph/`)
> **Last reviewed:** 2026-05-02
> **Constitution touchpoints:** `principles.md` (*"Tapping IS the ritual"* — every tap re-fires this endpoint to refresh what the user sees; *"Anti-spam is structural, not enforced"* — founder accounts can never call this endpoint).
> **Builds on:** `auth-role-split` (require_role), `question-bank-and-answer-capture` (answers, profiles), `catalog-seed-and-curation` (tools_seed), `weaviate-pipeline` (ensure_profile_embedding, similarity_search).

> **Slug-vs-implementation note:** the slug includes "-and-graph" because the original system_design called for a live React force-directed graph in onboarding. This feature ships the **API only** — the React component is a separate Claude Design track. "graph" here refers to the *data structure* the API exposes (top-K tools with category/label metadata) that a frontend can render however it wants.

---

## Intent

Maya the layperson opens onboarding, taps her way through the question bank, and expects to see her tool cloud refining in real time — *"this is what Mesh thinks fits you so far."* Cycle #6 will deliver the slow, smart, LLM-ranked endpoint that fires once at end-of-onboarding and weekly thereafter. This feature delivers the **fast, search-only companion** that fires after every tap: cheap, sub-second after warmup, no LLM in the loop.

A single endpoint, `POST /api/onboarding/match`, behind `require_role("user")`. Two modes auto-selected:

- **Generic mode** for the first 3 questions: maps the user's role answer to a closed list of relevant categories, returns the alphabetical top-5 of approved `all_time_best` tools in those categories. Catalog-wide fallback if the role-bucket has fewer than 5. **No OpenAI call**, ~50ms.
- **Embedding mode** from question 4 onward: calls cycle #4's `ensure_profile_embedding` (which lazily regenerates the OpenAI embedding when the profile has been mutated since last regen) and runs `similarity_search` against the `ToolEmbedding` Weaviate class. ~600ms when re-embedding, ~100ms when cached.

Founder accounts are structurally barred (`require_role("user")`); unauthenticated requests get 401. Embedding-mode failures (OpenAI down, Weaviate unreachable) gracefully fall back to generic mode so the user still sees tools.

## Surface

- **HTTP:** `POST /api/onboarding/match` — empty request body in V1; caller-supplied filters deferred to V1.5+.
- **Internal helpers (callable from future cycles):** `count_distinct_answers(user_id)`, `latest_role_for_user(user_id)`, `generic_match(user)`, `embedding_match(user)`, `ROLE_TO_CATEGORIES`, `categories_for_role(role)`.

---

## F-MATCH-1 — Endpoint exists behind require_role("user")

**Given** an authenticated `role_type=user` caller
**When** they `POST /api/onboarding/match`
**Then** the system returns `200 OK` with a JSON body matching `MatchResponse` (see F-MATCH-5).

- Founder caller → `403 role_mismatch` (per F-AUTH-3).
- Unauthenticated → `401 auth_required` (per F-AUTH-3).

---

## F-MATCH-2 — Mode dispatch by `answered_count`

The endpoint counts the number of DISTINCT `question_id`s the user has at least one answer for:

```
answered_count = |{ a.question_id : a.user_id == current_user._id }|
```

- `answered_count < GENERIC_MODE_MAX_ANSWERS` (3) → **generic mode** (F-MATCH-3).
- `answered_count >= GENERIC_MODE_MAX_ANSWERS` → **embedding mode** (F-MATCH-4).

The threshold is a single module-level constant in `app/onboarding/match.py`. Tuning is a one-line change. `re-answering` the same question doesn't double-count (cycle #2's `answers` is append-only by design; the distinct-question_id semantics filter the dupes).

---

## F-MATCH-3 — Generic mode

**Given** the user is in generic mode
**When** the endpoint runs
**Then** the system:

1. Reads the user's most-recent answer to the question with `key="role.primary_function"`. Returns `None` if absent.
2. If role is set: looks up `ROLE_TO_CATEGORIES[role]` to get a list of category strings. Empty list (e.g., role is `"other"`) OR `None` role → falls through to catalog-wide path.
3. Queries `tools_seed` for documents matching:
   ```
   { curation_status: "approved", category: {$in: <mapped categories>}, labels: "all_time_best" }
   ```
   Sorted alphabetical by `name`, limited to 5.
4. If <5 returned (or role mapping was empty), runs the catalog-wide fallback:
   ```
   { curation_status: "approved", labels: "all_time_best" }
   ```
   Sorted alphabetical by `name`, limited to 5.
5. Returns those tools in `MatchResponse(mode="generic", tools=[...])`.

No OpenAI call. No Weaviate call. Mongo-only. Latency target: <50ms.

---

## F-MATCH-4 — Embedding mode

**Given** the user is in embedding mode (`answered_count >= 3`)
**When** the endpoint runs
**Then** the system:

1. Calls `ensure_profile_embedding(user)`. If the cached embedding is fresh, this is a no-op. If stale or missing, it calls OpenAI to regenerate (~500ms).
2. Loads the user's profile to read `embedding`.
3. Calls `similarity_search(collection_name="tools_seed", weaviate_class="ToolEmbedding", query_vector=<embedding>, top_k=5, filters={"curation_status": "approved"})`. The cycle-#4 helper handles Weaviate query + Mongo re-fetch + degraded-cosine fallback.
4. Returns those tools in `MatchResponse(mode="embedding", tools=[...])`. **No filter relaxation** if fewer than 5 results — niche profiles return what they return; honest signal, not failure.

**Graceful degradation:** if any step raises (OpenAI down, Weaviate unreachable, profile missing), the endpoint logs the exception and falls back to F-MATCH-3 generic mode. The response `mode` field is `"generic"` in this fallback case.

If `similarity_search` returns 0 documents (empty catalog or no embedded tools), the response is `MatchResponse(mode="embedding", tools=[])`. Empty list is honest signal, not an error.

---

## F-MATCH-5 — Response shape

```json
{
  "mode": "generic" | "embedding",
  "tools": [
    {
      "slug": "chatgpt",
      "name": "ChatGPT",
      "tagline": "OpenAI's general-purpose conversational assistant.",
      "description": "Chat-based interface to ...",
      "url": "https://chat.openai.com",
      "pricing_summary": "Free + $20/mo Plus + ...",
      "category": "productivity",
      "labels": ["all_time_best"]
    },
    ...up to 5 entries
  ]
}
```

`tools[]` is ranked: in generic mode, alphabetical by `name`; in embedding mode, by Weaviate cosine descending.

`OnboardingToolCard` is a deliberate subset of `ToolPublic`: only the user-facing fields. Internal fields (`curation_status`, `embedding`, `source`, `created_at`, `last_reviewed_at`, `reviewed_by`, `rejection_comment`) are NEVER in this response.

---

## F-MATCH-6 — `ROLE_TO_CATEGORIES` mapping

A closed-list dict in `app/onboarding/role_map.py` mapping each `role.primary_function` enum value to a list of `Category` enum values. Current mapping (subject to refinement):

```python
ROLE_TO_CATEGORIES: dict[str, list[Category]] = {
    "marketing_ops":         ["marketing", "analytics_data", "writing"],
    "product_management":    ["productivity", "analytics_data", "research_browsing"],
    "design":                ["design", "creative_video"],
    "content":               ["writing", "creative_video"],
    "engineering":           ["engineering", "research_browsing"],
    "operations":            ["productivity", "automation_agents", "analytics_data"],
    "customer_success":      ["productivity", "writing", "meetings"],
    "sales":                 ["sales", "writing"],
    "founder_non_ai":        ["productivity", "marketing", "writing"],
    "freelance_consulting":  ["productivity", "writing", "design"],
    "student_research":      ["education", "research_browsing", "writing"],
    "other":                 [],
}
```

The map's keys MUST exactly match the `value` field of every option in the `role.primary_function` seed question (`app/seed/questions.json`). An audit test reads the seed JSON directly and asserts the key sets match — drift fails the suite.

The map is product judgement subject to refinement; it lives as a plain dict so updates are a one-line change without a schema migration.

---

## Architectural notes

- **Two-mode dispatch is a deliberate scope-of-the-question decision.** The first three onboarding questions (role, primary stack, daily-ops freeform) are too general to disambiguate at workflow granularity — embedding-based matching against them produces noisy results. Generic role-bucket ranking is faster, deterministic, demoably good enough, and saves an OpenAI call per tap during the highest-friction first-impression period.
- **No filter relaxation on embedding mode.** If the user's profile is too niche to find 5 strong matches, the response returns fewer than 5 (or zero). Padding with weakly-related tools to hit a "5-minimum" would feel like vendor-spam and would erode the *"Recommend honestly, including 'skip this'"* principle from the constitution.
- **Catalog-wide fallback in generic mode is alphabetical.** Deterministic for tests, boring for demos. V1.5+ may sample randomly from the all_time_best pool to produce variety across visits.
- **Embedding mode's first call after every answer pays a re-embed cost.** Profile invalidation bumps `last_invalidated_at` on every `POST /api/answers`; the next match call sees `last_invalidated_at > last_recompute_at` and pays ~500ms to regenerate. Subsequent match calls (e.g., user idle, then re-checks) reuse the cached embedding for ~100ms latency. Acceptable for V1; V1.5+ may move regeneration to a background task.
- **OpenAI failure → generic fallback is a load-bearing graceful-degradation path.** The user never sees a 5xx because of a third-party outage; they see a slightly-less-personalized result with `mode: "generic"` instead of `mode: "embedding"`. Same graceful-degradation pattern as cycle #3's admin approve handler.

## Out of scope (V1 deferrals)

- Frontend (React force-directed graph component) — separate Claude Design track.
- Caller-supplied filters in the request body (e.g., narrow by category or label) — V1.5+ once a frontend has a "refine" UX.
- LLM-ranked starter recs at end-of-onboarding (4–5 with reasoning text) — owned by cycle #6 (`recommendation-engine`).
- Community auto-suggestions at end-of-onboarding (3 communities) — owned by cycle #7 (`communities-and-flat-comments`).
- Tool-to-tool relationship edges (integration / replacement signals) — schema doesn't carry this data; deferred until tools start carrying it.
- Sub-200ms latency target — relaxed per user call ("slow is fine for MVP"). V2 may revisit.
- Caching of generic-mode results — V1.5+ once we observe how often users tap-without-answer.
- Random sampling of catalog-wide fallback for variety — V1 ships alphabetical for determinism.
