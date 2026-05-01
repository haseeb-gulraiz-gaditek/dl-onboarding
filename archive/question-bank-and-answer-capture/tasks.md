# Tasks: question-bank-and-answer-capture

## Implementation Checklist

### Schema + DB
- [x] Define `app/db/questions.py` collection access layer + `ensure_indexes()` (unique index on `questions.key`, compound `(is_core, active, order)`)
- [x] Define `app/db/answers.py` collection access layer + `ensure_indexes()` (single index on `user_id` for the answered-set lookup)
- [x] Define `app/db/profiles.py` collection access layer + `ensure_indexes()` (unique index on `profiles.user_id`); includes `get_or_create_profile(user)` helper that REJECTS founders (raises ValueError)
- [x] Wire all three new `ensure_indexes()` calls into the FastAPI lifespan in `app/main.py` (after the existing `ensure_user_indexes`)

### Models
- [x] `app/models/question.py` — `QuestionPublic` (client shape; `id` as string), `NextQuestionResponse`, `Option`, `KindLiteral`, `CategoryLiteral`
- [x] `app/models/answer.py` — `AnswerCreate` (request body), `validate_answer_value(question, value)` returning None or "value_invalid" — handles all three kinds (single_select, multi_select, free_text) per F-QB-3 error-path scenarios
- [x] `app/models/profile.py` — `Profile` Pydantic shape; default-value factory lives in `app/db/profiles.py:_new_profile_doc()` to keep DB shape and Pydantic shape in sync

### Seed
- [x] **Research and author 10–15 core questions** in `app/seed/questions.json`. Categories must cover all six: role / stack / workflow / friction / wishlist / budget. Each question has `key`, `text`, `kind`, `options[]` (or empty for free_text), `category`, `order`, `version: 1`, `active: true`, `is_core: true` — **shipped 12 questions** (1 role, 2 stack, 3 workflow, 3 friction, 2 wishlist, 1 budget)
- [x] `app/seed/__init__.py` — module init
- [x] `app/seed/__main__.py` — CLI dispatcher; supports `python -m app.seed questions`
- [x] `app/seed/questions.py` — loader function: validate the whole JSON file first, then upsert by `key`, print `inserted/updated/total`. Exit non-zero on validation failure with no partial writes.

### Endpoints
- [x] `app/api/questions.py` — `GET /api/questions/next` behind `Depends(require_role("user"))`; calls `get_or_create_profile`, finds next unanswered core question by `order`, returns `{done, question}` (F-QB-2). Exposes `compute_next_question` helper for reuse.
- [x] `app/api/answers.py` — `POST /api/answers` behind `Depends(require_role("user"))`; validates value shape against question kind, inserts answer, bumps `profile.last_invalidated_at`, returns next question via shared `compute_next_question` helper (F-QB-3)
- [x] Mount both routers in `app/main.py`; extended global validation handler to map missing `question_id`/`value` to `{error: "field_required", field: ...}`

### Tests (one per Given/When/Then in spec-delta)
- [x] F-QB-1 (seed): seed loads N questions; rerun is idempotent (same DB state, no duplicate keys)
- [x] F-QB-1 (seed): re-running with edited text updates the existing rows
- [x] F-QB-1 (seed): seed with invalid shape exits non-zero with no partial writes
- [x] F-QB-2: user with no profile gets first question; profile created
- [x] F-QB-2: user gets next-in-order question after answering one
- [x] F-QB-2: user who has answered all core questions gets `{done: true, question: null}`
- [x] F-QB-2: founder gets 403 role_mismatch
- [x] F-QB-2: unauthenticated gets 401 auth_required
- [x] F-QB-3: user submits valid `single_select` → answer stored, profile invalidated, next question returned
- [x] F-QB-3: user submits valid `multi_select` array → answer stored
- [x] F-QB-3: user submits valid `free_text` → answer stored
- [x] F-QB-3: invalid `question_id` → 400 question_not_found
- [x] F-QB-3: `single_select` with value not in options → 400 value_invalid
- [x] F-QB-3: `multi_select` with empty array → 400 value_invalid
- [x] F-QB-3: `free_text` with empty string → 400 value_invalid
- [x] F-QB-3: missing `question_id` → 400 field_required
- [x] F-QB-3: missing `value` → 400 field_required
- [x] F-QB-4: profile created on first GET /api/questions/next has the documented shape
- [x] F-QB-4: profile created on first POST /api/answers has the documented shape
- [x] F-QB-4: POST /api/answers updates `last_invalidated_at` to a fresh timestamp
- [x] F-QB-5: `get_or_create_profile` raises when called with a founder user (defense-in-depth audit test)

### Conftest updates
- [x] Add `seed_test_questions` fixture in `tests/conftest.py` that loads 3 questions across 3 kinds (single_select, multi_select, free_text) and 3 categories (role, stack, workflow) into the mongomock DB
- [x] Add `signed_up_user_with_profile` helper that signs up a user, hits `GET /api/questions/next` once (which creates the profile), and returns `{token, user, first}`

## Validation

- [x] All implementation tasks above checked off
- [x] All tests pass (full suite — cycle #1's 19 + cycle #2's 21 = 40 tests, all green)
- [x] Manual smoke: sign up two accounts (user + founder); user calls `/api/questions/next` repeatedly, answers each via `/api/answers`, eventually gets `{done: true}`; founder gets 403 on both endpoints; questions appear in `order` — verified on 2026-05-01
- [x] Spec-delta scenarios verifiably hold in implementation
- [x] No constitutional regression: founder profile cannot be created (`get_or_create_profile` audit test green); `profiles.exportable` is always `true`
