# Tasks: recommendation-engine

## Implementation Checklist

### Schema + DB
- [ ] `app/db/recommendations.py` — collection access layer; `ensure_indexes()` (unique on user_id); helpers `find_for_user(user_id)`, `upsert_for_user(user_id, picks, generated_at, cache_expires_at)`, `is_cache_valid(rec_doc, profile_doc)` returning bool
- [ ] Wire `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models
- [ ] `app/models/recommendation.py` — `Verdict` literal (`"try"` | `"skip"`); `RecommendationPick` (tool: OnboardingToolCard, verdict, reasoning, score); `RecommendationsResponse` (recommendations list + generated_at + from_cache + optional degraded); plus `RankerPick` and `RankerOutput` Pydantic models for OpenAI structured output

### Ranker
- [ ] `app/recommendations/__init__.py` — empty package init
- [ ] `app/recommendations/ranker.py` — `rank_with_llm(profile, recent_answers, candidates, count)` that calls OpenAI `gpt-5` via `beta.chat.completions.parse(response_format=RankerOutput)`. System prompt enshrines the constitutional principles (recommend honestly, include skip-this where appropriate, reasoning grounded in user's actual answers). Returns a list of `RankerPick` objects; raises on any SDK error so the caller can degrade.

### Engine + cache
- [ ] `app/recommendations/engine.py` — `generate_recommendations(user, count)`:
  - Load profile via `find_profile_by_user_id`
  - Cache check: load existing `recommendations` row; if valid (not expired AND profile.last_invalidated_at <= generated_at), return cached truncated to count, `from_cache=True`
  - Cache miss: ensure_profile_embedding → similarity_search top_k=20 → rank_with_llm → validate slugs against candidate set → upsert cache → return truncated, `from_cache=False`
  - Ranker exception path: log, build degraded picks from similarity_search results (verdict="try", generic reasoning), upsert cache, return with `degraded=True`

### Endpoint
- [ ] `app/api/recommendations.py` — `POST /api/recommendations` behind `Depends(require_role("user"))`. Reads optional `{count?: int}` body, clamps 1..5, defaults 3. Counts user answers; <3 → 400 `no_profile_yet`. Otherwise calls `generate_recommendations`. Returns `RecommendationsResponse`.
- [ ] Mount router in `app/main.py`
- [ ] Extend the global `RequestValidationError` handler if needed for `count` field validation (optional — Pydantic's default coerces to int OK; `min_length`/`max_length` not in scope for this field)

### Tests
- [ ] F-REC-1: founder → 403 role_mismatch
- [ ] F-REC-1: unauthenticated → 401 auth_required
- [ ] F-REC-2: user with 0 answers → 400 no_profile_yet
- [ ] F-REC-2: user with 2 answers → 400 no_profile_yet
- [ ] F-REC-2: user with exactly 3 answers → 200 (recommendations served)
- [ ] F-REC-3: cache hit path returns `from_cache: true` and serves the truncated count
- [ ] F-REC-3: cache hit doesn't call the ranker (verify mock is NOT called)
- [ ] F-REC-4: cache miss (no row yet) calls ensure_profile_embedding + similarity_search + ranker
- [ ] F-REC-4: profile invalidated since generated_at → cache miss, regenerate
- [ ] F-REC-4: cache_expires_at in past → cache miss, regenerate
- [ ] F-REC-4: hallucinated slug from ranker is dropped from response
- [ ] F-REC-5: response shape matches RecommendationsResponse contract
- [ ] F-REC-5: count param: 1, 3, 5 all return that many picks
- [ ] F-REC-5: count param clamping: count=0 → uses default; count=10 → clamps to 5
- [ ] F-REC-6: collection has unique index on user_id (insert two docs same user → second update upserts existing)
- [ ] F-REC-7: ranker raises → response has `degraded: true`, picks have generic reasoning, all verdict=try

### Conftest updates
- [ ] Add `mock_openai_chat` autouse fixture in `tests/conftest.py` that monkey-patches `app.recommendations.ranker.rank_with_llm` to return deterministic top-N picks (verdict="try", reasoning="mock reasoning for {slug}"). Tests that need a failing ranker override locally with `monkeypatch.setattr`.
- [ ] Add `seed_user_with_n_answers_and_embedding(client, email, n)` helper that signs up, inserts N answers, and ensures a profile embedding so embedding-dependent tests don't all repeat the boilerplate.

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1, #2, #3, #4, #5 must continue to pass)
- [ ] Real-world smoke (optional, costs ~$0.01): set OPENAI_API_KEY to a real key (you already have one); sign up Maya; answer 3+ questions; `POST /api/recommendations` returns up to 5 tools with verdict + reasoning fields populated by GPT-5
- [ ] Cache smoke: hit /api/recommendations twice in a row; second call returns `from_cache: true` and is fast (<50ms)
- [ ] Cache invalidation smoke: hit /api/recommendations, then `POST /api/answers` to bump last_invalidated_at, then hit /api/recommendations again — fresh generation, `from_cache: false`
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founder still cannot access recommendations; the verdict field surfaces "skip" guidance per principles.md
