# Tasks: fast-onboarding-match-and-graph

## Implementation Checklist

### Models
- [ ] `app/models/onboarding.py` — `OnboardingToolCard` (subset of ToolPublic with only user-facing fields: slug, name, tagline, description, url, pricing_summary, category, labels), `MatchResponse` (mode discriminator + tools list). `tool_to_card(doc)` projection helper

### Role mapping
- [ ] `app/onboarding/__init__.py` — empty package init
- [ ] `app/onboarding/role_map.py` — `ROLE_TO_CATEGORIES` constant per F-MATCH-6 + `categories_for_role(role)` lookup helper that returns `[]` for unknown / None roles

### Mode selection + match logic
- [ ] `app/onboarding/match.py` — `GENERIC_MODE_MAX_ANSWERS = 3` constant; `count_distinct_answers(user_id)` helper using `app.db.answers`; `latest_role_for_user(user_id)` helper that finds the most-recent answer to the `role.primary_function` question (returns string or None); `generic_match(user)` returns up to 5 tools per F-MATCH-3 (role-bucket query → fallback to all_time_best); `embedding_match(user)` returns up to 5 tools per F-MATCH-4 (ensure_profile_embedding → similarity_search)

### Endpoint
- [ ] `app/api/onboarding.py` — `POST /api/onboarding/match` behind `Depends(require_role("user"))`. Calls `count_distinct_answers`, dispatches to `generic_match` or `embedding_match`, wraps in MatchResponse. Catches OpenAI exceptions in embedding mode and falls back to generic mode (logs warning, response mode = "generic")
- [ ] Mount router in `app/main.py`

### Tests
- [ ] F-MATCH-1: unauthenticated request returns 401 auth_required
- [ ] F-MATCH-1: founder request returns 403 role_mismatch
- [ ] F-MATCH-2: 0 answers → generic mode in response
- [ ] F-MATCH-2: 2 answers → generic mode in response
- [ ] F-MATCH-2: exactly 3 answers → embedding mode in response
- [ ] F-MATCH-2: 5 answers → embedding mode in response
- [ ] F-MATCH-3: role answered → tools belong to mapped categories
- [ ] F-MATCH-3: role NOT answered → falls back to catalog-wide all_time_best
- [ ] F-MATCH-3: when role-bucket query returns <5, falls through to catalog-wide all_time_best
- [ ] F-MATCH-3: returns alphabetical by name
- [ ] F-MATCH-4: ensure_profile_embedding is called when entering embedding mode
- [ ] F-MATCH-4: similarity_search results returned in cosine order
- [ ] F-MATCH-4: when similarity returns 0 docs, response is `tools: []`, mode: "embedding"
- [ ] F-MATCH-4: when ensure_profile_embedding raises (OpenAI down), endpoint falls back to generic mode and response.mode == "generic"
- [ ] F-MATCH-5: response shape matches MatchResponse contract (mode + tools list of OnboardingToolCard)
- [ ] F-MATCH-6: ROLE_TO_CATEGORIES has every role.primary_function seed value as a key (audit test against the seed JSON)

### Conftest updates
- [ ] Add `signed_up_user_with_n_answers(client, email, n)` helper in `tests/conftest.py` that signs up a user, walks `/api/questions/next` and `/api/answers` n times answering with deterministic values
- [ ] Add `seed_minimal_catalog` fixture that inserts ~6 tools spanning 3 categories with `all_time_best` labels and approved status — small enough to make assertions tight

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1, #2, #3, #4 must continue to pass)
- [ ] Manual smoke: sign up Maya as a user; before any answers → `POST /api/onboarding/match` returns mode="generic" with 5 catalog-wide all_time_best tools; answer the role question with `marketing_ops` → match returns 5 tools from the marketing/analytics/writing categories; answer two more questions → match still in generic mode; answer the third question → match flips to embedding mode and returns 5 tools by Weaviate similarity
- [ ] Manual smoke: sign up Aamir as a founder → `POST /api/onboarding/match` returns 403 role_mismatch
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founder users still cannot have profiles (`ensure_profile_embedding` rejects); generic-mode fallback path does not call OpenAI for users with <3 answers
