# Spec Delta: fast-onboarding-match-and-graph

## ADDED

### F-MATCH-1 — `POST /api/onboarding/match` endpoint exists

A new endpoint at `POST /api/onboarding/match` is mounted behind `Depends(require_role("user"))`. Empty request body in V1 (caller-supplied filters deferred to V1.5+).

**Given** an authenticated `role_type=user` caller
**When** they `POST /api/onboarding/match`
**Then** the system returns `200 OK` with a JSON body matching the `MatchResponse` schema (see F-MATCH-5).

**Founder caller** → 403 `role_mismatch` (per F-AUTH-3).
**Unauthenticated** → 401 `auth_required` (per F-AUTH-3).

---

### F-MATCH-2 — Mode selection by answered-question count

Before computing the result, the endpoint counts how many distinct `question_id`s the user has answered:

```
answered_count = |{ a.question_id : a in answers WHERE a.user_id = current }|
```

(Distinct because `answers` is append-only — re-answering the same question doesn't double-count.)

- If `answered_count < 3` → **generic mode** (F-MATCH-3).
- If `answered_count >= 3` → **embedding mode** (F-MATCH-4).

The threshold lives as a single constant (`GENERIC_MODE_MAX_ANSWERS = 3`) in `app/onboarding/match.py`; tuning the value is a one-line change.

---

### F-MATCH-3 — Generic mode

**Given** the user is in generic mode
**When** the endpoint runs
**Then** the system:

1. Reads the user's most-recent answer to the question with `key="role.primary_function"`. If absent, the role is `None`.
2. If role is set: looks up `ROLE_TO_CATEGORIES[role]` to get a list of category strings. If the list is empty (e.g., role is `"other"`) OR role is `None`, falls through to the catalog-wide path.
3. Queries `tools_seed` for documents matching:
   ```
   {
     curation_status: "approved",
     category: {$in: <mapped categories>},
     labels: "all_time_best",
   }
   ```
   sorted alphabetical by `name`, limited to 5.
4. If <5 returned (or role mapping missing), runs a fallback query:
   ```
   {
     curation_status: "approved",
     labels: "all_time_best",
   }
   ```
   sorted alphabetical by `name`, limited to 5.
5. Returns those tools in `MatchResponse(mode="generic", tools=[...])`.

No OpenAI call. No Weaviate call. Mongo-only. Latency target: <50ms.

---

### F-MATCH-4 — Embedding mode

**Given** the user is in embedding mode (`answered_count >= 3`)
**When** the endpoint runs
**Then** the system:

1. Calls `ensure_profile_embedding(user)`. If the cached embedding is fresh, this is a no-op. If stale or missing, it calls OpenAI to regenerate (~500ms, V1 acceptable).
2. Loads the user's profile to read `embedding`.
3. Calls `similarity_search(collection_name="tools_seed", weaviate_class="ToolEmbedding", query_vector=embedding, top_k=5, filters={"curation_status": "approved"})`. The cycle-#4 helper handles Weaviate query + Mongo re-fetch + degraded-cosine fallback.
4. Returns the resulting tools in `MatchResponse(mode="embedding", tools=[...])`. No filter relaxation if fewer than 5 results.

**Graceful degradation:** if step 1 (OpenAI) raises, the endpoint logs the exception and falls back to F-MATCH-3 generic-mode behavior so the user still sees tools. The response `mode` field is `"generic"` in this fallback case.

If step 3 returns 0 documents (empty catalog or all rejected), the endpoint returns `MatchResponse(mode="embedding", tools=[])`. Empty list is honest signal, not an error.

---

### F-MATCH-5 — Response shape

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

`tools[]` is ranked: in generic mode, alphabetical by `name`; in embedding mode, by Weaviate cosine descending. Pydantic model: `MatchResponse` with `OnboardingToolCard` sub-shape (no `embedding`, `curation_status`, `created_at`, etc. — only the user-facing fields).

---

### F-MATCH-6 — `ROLE_TO_CATEGORIES` mapping

A closed-list constant in `app/onboarding/role_map.py` mapping each `role.primary_function` enum value to a list of `Category` enum values:

```python
ROLE_TO_CATEGORIES: dict[str, list[Category]] = {
    "marketing_ops": ["marketing", "analytics_data", "writing"],
    "product_management": ["productivity", "analytics_data", "research_browsing"],
    "design": ["design", "creative_video"],
    "content": ["writing", "creative_video"],
    "engineering": ["engineering", "research_browsing"],
    "operations": ["productivity", "automation_agents", "analytics_data"],
    "customer_success": ["productivity", "writing", "meetings"],
    "sales": ["sales", "writing"],
    "founder_non_ai": ["productivity", "marketing", "writing"],
    "freelance_consulting": ["productivity", "writing", "design"],
    "student_research": ["education", "research_browsing", "writing"],
    "other": [],
}
```

The map's keys MUST exactly match the `value` field of every option in the `role.primary_function` seed question. Unknown or absent role values fall through to the catalog-wide fallback (F-MATCH-3 step 4).

This map is product judgement subject to refinement; it lives as a single dict in code so updates are a one-line change without a schema migration.

## MODIFIED

(None. This cycle adds a new endpoint that consumes existing cycle-#4 helpers without modifying them.)

## REMOVED

(None.)
