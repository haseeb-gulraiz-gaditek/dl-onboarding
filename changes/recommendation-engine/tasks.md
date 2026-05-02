# Tasks: recommendation-engine

## Implementation Checklist

### Schema + DB
- [x] `app/db/recommendations.py` — collection access layer; `ensure_indexes()` (unique on user_id); helpers `find_for_user(user_id)`, `upsert_for_user(user_id, picks, generated_at, cache_expires_at)`, `is_cache_valid(rec_doc, profile_doc)` returning bool
- [x] Wire `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models
- [x] `app/models/recommendation.py` — `Verdict` literal (`"try"` | `"skip"`); `RecommendationPick` (tool: OnboardingToolCard, verdict, reasoning, score); `RecommendationsResponse` (recommendations list + generated_at + from_cache + optional degraded); plus `RankerPick` and `RankerOutput` Pydantic models for OpenAI structured output

### Ranker
- [x] `app/recommendations/__init__.py` — empty package init
- [x] `app/recommendations/ranker.py` — `rank_with_llm(profile, recent_answers, candidates, count)` that calls OpenAI `gpt-5` via `beta.chat.completions.parse(response_format=RankerOutput)`. System prompt enshrines the constitutional principles (recommend honestly, include skip-this where appropriate, reasoning grounded in user's actual answers). Returns a list of `RankerPick` objects; raises on any SDK error so the caller can degrade.

### Engine + cache
- [x] `app/recommendations/engine.py` — `generate_recommendations(user, count)`:
  - Load profile via `find_profile_by_user_id`
  - Cache check: load existing `recommendations` row; if valid (not expired AND profile.last_invalidated_at <= generated_at), return cached truncated to count, `from_cache=True`
  - Cache miss: ensure_profile_embedding → similarity_search top_k=20 → rank_with_llm → validate slugs against candidate set → upsert cache → return truncated, `from_cache=False`
  - Ranker exception path: log, build degraded picks from similarity_search results (verdict="try", generic reasoning), upsert cache, return with `degraded=True`

### Endpoint
- [x] `app/api/recommendations.py` — `POST /api/recommendations` behind `Depends(require_role("user"))`. Reads optional `{count?: int}` body, clamps 1..5, defaults 3. Counts user answers; <3 → 400 `no_profile_yet`. Otherwise calls `generate_recommendations`. Returns `RecommendationsResponse`.
- [x] Mount router in `app/main.py`
- [x] Extend the global `RequestValidationError` handler if needed for `count` field validation (optional — Pydantic's default coerces to int OK; `min_length`/`max_length` not in scope for this field)

### Tests
- [x] F-REC-1: founder → 403 role_mismatch
- [x] F-REC-1: unauthenticated → 401 auth_required
- [x] F-REC-2: user with 0 answers → 400 no_profile_yet
- [x] F-REC-2: user with 2 answers → 400 no_profile_yet
- [x] F-REC-2: user with exactly 3 answers → 200 (recommendations served)
- [x] F-REC-3: cache hit path returns `from_cache: true` and serves the truncated count
- [x] F-REC-3: cache hit doesn't call the ranker (verify mock is NOT called)
- [x] F-REC-4: cache miss (no row yet) calls ensure_profile_embedding + similarity_search + ranker
- [x] F-REC-4: profile invalidated since generated_at → cache miss, regenerate
- [x] F-REC-4: cache_expires_at in past → cache miss, regenerate
- [x] F-REC-4: hallucinated slug from ranker is dropped from response
- [x] F-REC-5: response shape matches RecommendationsResponse contract
- [x] F-REC-5: count param: 1, 3, 5 all return that many picks
- [x] F-REC-5: count param clamping: count=0 → uses default; count=10 → clamps to 5
- [x] F-REC-6: collection has unique index on user_id (insert two docs same user → second update upserts existing)
- [x] F-REC-7: ranker raises → response has `degraded: true`, picks have generic reasoning, all verdict=try

### Conftest updates
- [x] Add `mock_openai_chat` autouse fixture in `tests/conftest.py` that monkey-patches `app.recommendations.ranker.rank_with_llm` to return deterministic top-N picks (verdict="try", reasoning="mock reasoning for {slug}"). Tests that need a failing ranker override locally with `monkeypatch.setattr`.
- [x] Add `seed_user_with_n_answers_and_embedding(client, email, n)` helper that signs up, inserts N answers, and ensures a profile embedding so embedding-dependent tests don't all repeat the boilerplate.

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green (cycles #1, #2, #3, #4, #5 must continue to pass)
- [ ] Real-world smoke (optional, costs ~$0.01): set OPENAI_API_KEY to a real key (you already have one); sign up Maya; answer 3+ questions; `POST /api/recommendations` returns up to 5 tools with verdict + reasoning fields populated by GPT-5
- [ ] Cache smoke: hit /api/recommendations twice in a row; second call returns `from_cache: true` and is fast (<50ms)
- [ ] Cache invalidation smoke: hit /api/recommendations, then `POST /api/answers` to bump last_invalidated_at, then hit /api/recommendations again — fresh generation, `from_cache: false`
- [x] Spec-delta scenarios verifiably hold in implementation
- [x] No constitutional regression: founder still cannot access recommendations; the verdict field surfaces "skip" guidance per principles.md
