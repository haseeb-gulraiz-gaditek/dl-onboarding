# Tasks: fast-onboarding-match-and-graph

## Implementation Checklist

### Models
- [x] `app/models/onboarding.py` — `OnboardingToolCard`, `MatchMode` literal, `MatchResponse`, `tool_to_card` projection helper

### Role mapping
- [x] `app/onboarding/__init__.py` — empty package init
- [x] `app/onboarding/role_map.py` — `ROLE_TO_CATEGORIES` constant + `categories_for_role(role)` lookup helper

### Mode selection + match logic
- [x] `app/onboarding/match.py` — `GENERIC_MODE_MAX_ANSWERS=3`, `TOP_K=5`, `count_distinct_answers`, `latest_role_for_user`, `generic_match` (role-bucket → fallback), `embedding_match` (ensure_profile_embedding → similarity_search)

### Endpoint
- [x] `app/api/onboarding.py` — `POST /api/onboarding/match` behind `require_role("user")`; dispatches by answered_count; catches embedding-mode exceptions and falls back to generic
- [x] Mount router in `app/main.py`

### Tests
- [x] F-MATCH-1: unauthenticated request returns 401 auth_required
- [x] F-MATCH-1: founder request returns 403 role_mismatch
- [x] F-MATCH-2: 0 answers → generic mode in response
- [x] F-MATCH-2: 2 answers → generic mode in response
- [x] F-MATCH-2: exactly 3 answers → embedding mode in response
- [x] F-MATCH-2: 5 answers → embedding mode in response
- [x] F-MATCH-3: role answered (`marketing_ops`) → 5 tools all from `marketing` category
- [x] F-MATCH-3: role NOT answered → falls back to catalog-wide alphabetical top-5
- [x] F-MATCH-3: role-bucket has <5 (`design`) → falls back to catalog-wide
- [x] F-MATCH-3: returns alphabetical by name (verified via `slugs == sorted(slugs)`)
- [x] F-MATCH-4: ensure_profile_embedding populates the profile embedding on embedding-mode entry
- [x] F-MATCH-4: when similarity returns 0 docs, response is `tools: []`, mode: "embedding"
- [x] F-MATCH-4: when ensure_profile_embedding raises (OpenAI down), endpoint falls back to generic mode and `response.mode == "generic"`
- [x] F-MATCH-5: response shape matches MatchResponse contract (mode + tools list of OnboardingToolCard)
- [x] F-MATCH-6: ROLE_TO_CATEGORIES audit against `app/seed/questions.json` — every option value of `role.primary_function` is a key in the map and vice versa

### Conftest updates
- [x] `insert_dummy_answers(user_id, count)` helper inserts N answers with arbitrary fresh question_ids — used by mode-dispatch tests
- [x] `insert_role_answer(user_id, role_value)` helper for F-MATCH-3 role-bucket tests
- [x] `seed_minimal_catalog` fixture inserts 8 approved all_time_best tools across `marketing` (5), `design` (2), `productivity` (1) — exercises both "bucket no fallback" and "bucket forces fallback" paths
- [x] `seed_role_question` fixture inserts the production-named `role.primary_function` question with production-named option values

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green — 101 tests across cycles #1–#5 (cycle #5: 14 new)
- [x] Direct DB diagnostic: user `hsb@example.com` answered the `role.primary_function` question with `"engineering"`; `generic_match(user)` returns 5 tools all in `engineering` category (AI21 Studio, Aider, Amazon Bedrock, Amazon Q, Anthropic API). Confirms F-MATCH-3 role-bucket path on real production data.
- [x] Direct DB diagnostic: users with no role answer → `latest_role_for_user` returns `None`, `categories_for_role` returns `[]`, generic_match falls back to catalog-wide alphabetical top-5. Confirms F-MATCH-3 fallback path.
- [x] Founder 403 + unauth 401 boundary covered by automated tests `test_founder_returns_403` and `test_unauthenticated_returns_401`
- [x] Spec-delta scenarios verifiably hold in implementation
- [x] No constitutional regression: founder users still cannot have profiles (`ensure_profile_embedding` rejects with `ValueError`); generic-mode fallback path does NOT call OpenAI for users with <3 answers (covered by F-MATCH-2 tests + the OpenAI-failure-fallback test which uses `monkeypatch.setattr` and never triggers when answered_count<3)
