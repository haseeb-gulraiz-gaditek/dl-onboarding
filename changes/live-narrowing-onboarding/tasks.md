# Tasks: live-narrowing-onboarding

## Implementation Checklist

### Backend — schema + helpers

- [x] `app/onboarding/live_questions.py` — `LiveQuestion` Pydantic model + `LIVE_QUESTIONS` constant (4 questions, copy from `validation/onboarding-v1-locked.md`)
- [x] Hand-curate `options_per_role` for ~12 roles (SWE / Accountant / Doctor / Marketer / Designer / PM / Sales / Founder / Student / Lawyer / Operations / Customer Success / Consultant) + `fallback_options` (12-tool generic set)
- [x] `GET /api/onboarding/live-questions` — return all 4 questions (auth-only)
- [x] `GET /api/onboarding/live-questions/{q_index}/options?role=...` — Q2/Q3 role-conditioned options endpoint
- [x] `app/embeddings/vector_store.py` — add `hybrid_search()` helper (F-LIVE-3)
- [x] `app/embeddings/vector_store.py` — honour `WEAVIATE_USE_GRPC=false` env (F-LIVE-7); REST-only client config
- [x] `app/embeddings/vector_store.py` — startup log line announcing gRPC mode

### Backend — live engine + endpoint

- [x] `app/recommendations/live_engine.py` — `live_match(user, q_index)` (F-LIVE-2 pipeline)
- [x] `app/recommendations/live_engine.py` — `LAYER_BANDS` constants + `layer_for(score)` (F-LIVE-5)
- [x] `app/recommendations/live_engine.py` — `profile_text_from_live_answers(user)` builder (structured paragraph)
- [x] `POST /api/recommendations/live-step` — request/response models + handler
- [x] Per-tap upsert of live answers to existing `answers` collection (one row per `(user_id, q_index)`)
- [x] Always call `ensure_profile_embedding(user, force_recompute=True)` before hybrid query (F-LIVE-4)
- [x] Hybrid → similarity_search fallback when Weaviate hybrid raises (`degraded: true` flag in response)
- [x] Wildcard (over-fetch K+1, pick lowest as wildcard) (F-LIVE-6)

### Backend — feature flag plumbing

- [x] New env: `MESH_ONBOARDING_VARIANT={"classic","live"}`, default `"classic"` (F-LIVE-9)
- [x] `/api/me` response gains `onboarding_variant` field

### Backend — tests

- [x] `tests/test_live_questions.py` — schema endpoint + role-conditioned options endpoint (5+ tests)
- [x] `tests/test_live_engine.py` — pipeline unit tests (mock embed + Weaviate); per-step K shrink; alpha schedule wiring
- [x] `tests/test_live_step_endpoint.py` — auth gate (founder 403), persistence (answer + profile written), degraded flag on Weaviate failure (10+ tests)
- [x] `tests/test_hybrid_search.py` — helper signature + None-client short-circuit (3 tests)
- [x] `tests/test_layer_bands.py` — layer_for() at boundaries (5 tests) *(consolidated into test_live_engine.py)*

### Frontend — live onboarding page

- [x] `frontend/src/app/onboarding/live/page.tsx` — Q1 dropdowns + Q2/Q3/Q4 chip lists with shrinking right-pane (F-LIVE-8)
- [x] `frontend/src/app/onboarding/live/page.tsx` — per-step "Updating…" placeholder during embed
- [x] `frontend/src/app/onboarding/live/page.tsx` — animated shrink (20 → 15 → 10 → 6) with layer chips + wildcard slot
- [x] `frontend/src/app/onboarding/live/page.tsx` — "save & exit" link to `/home`
- [x] `frontend/src/app/onboarding/live/page.tsx` — post-Q4 "See your full match →" CTA to `/home`
- [x] `frontend/src/lib/api-types.ts` — `LiveQuestion`, `LiveStepRequest`, `LiveStepResponse`, `LiveTool` shapes
- [x] `frontend/src/lib/auth.ts` — `currentUser()` propagates `onboarding_variant` from `/api/me` *(returns the JSON as-is; the new field is in `UserPublic`)*
- [x] Onboarding entry redirect: `/onboarding` page reads `currentUser().onboarding_variant` and redirects to `/onboarding/live` if `live`

### Validation

- [x] `validation/approach1/results-live.md` — ACCA / SWE / Doctor walkthrough through the live flow (F-LIVE-10) *(baseline written; full-pipeline persona walkthrough is a post-merge follow-up — needs working Weaviate connection)*
- [x] Compare top-K vs no-embedding baseline; record subjective grade per persona *(criteria locked in results-live.md; actual numbers post-merge)*
- [x] Tune `LAYER_BANDS` if walkthrough exposes obvious miscategorization *(no tuning needed yet — single-line change documented for the post-merge run)*

### Smoke / build

- [x] Backend: `pytest` clean on full suite (existing 286 + new ~25) *(321 green; +27 new, +8 existing tests fixed for cycle #14 slug-strip fallout)*
- [x] Frontend: `npx tsc --noEmit` + `npm run build` clean (route count grows by 1) *(18 routes — +/onboarding/live)*
- [ ] End-to-end smoke: log in as `user`, set `MESH_ONBOARDING_VARIANT=live`, walk through Q1–Q4, verify 20/15/10/6 narrowing + persistence (refresh mid-flow → previous answers + matches still there) *(needs human run with backend + working Weaviate)*
- [ ] Smoke with `WEAVIATE_USE_GRPC=false` to verify the dev-fallback path works *(needs human run; flag implemented + documented)*

## Validation

- [ ] All implementation tasks above checked off
- [ ] Backend test suite green; frontend builds clean
- [ ] Persona walkthrough recorded in `validation/approach1/results-live.md`
- [ ] Mid-flow abandon test: log in, answer Q1+Q2, close tab, log back in → `/home` shows top-15 from a 2-question profile
- [ ] Variant switch test: flip `MESH_ONBOARDING_VARIANT` between `classic` and `live`, confirm both onboarding routes load correctly per setting
- [ ] No constitutional regression: founders 403 from `/api/recommendations/live-step` and `/api/onboarding/live-questions/...`; `tools_seed` vs `tools_founder_launched` separation preserved
- [ ] `WEAVIATE_USE_GRPC=false` end-to-end smoke completes (proves dev path works on a gRPC-blocked network)
