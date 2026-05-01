# Proposal: question-bank-and-answer-capture

## Problem

Mesh's user-side value proposition is a personal AI concierge that learns each user's daily ops in conversation (`personas.md` Maya, `principles.md` *"Tapping IS the ritual"*). The concierge cannot recommend anything without a profile, and the profile is built from a sequence of structured tap-to-answer questions. This cycle delivers the question bank, the answer-capture endpoints, and a profile shell that downstream cycles (`weaviate-pipeline` #4, `recommendation-engine` #6) read from.

Without this layer, no user-side feature past auth can begin.

## Solution

Three new MongoDB collections plus two endpoints, behind `require_role("user")`:

- **`questions`** — seeded from `app/seed/questions.json` with 10–15 hand-authored core questions across categories (role / stack / workflow / friction / wishlist / budget). Linear `order: int` ordering for V1; `next_logic` branching deferred to V1.5.
- **`answers`** — append-only audit trail. One row per tap. Allows answer revisions without losing history.
- **`profiles`** — one per user-role account, created lazily on first `GET /api/questions/next`. Carries placeholder fields for future cycles (`role`, `current_tools`, `workflows`, etc.) but only `last_invalidated_at` is actively set in this cycle.

Endpoints:

- `GET /api/questions/next` — returns the next unanswered core question for the calling user (in `order`), or `{done: true}` if all answered. Creates the profile if missing.
- `POST /api/answers` — writes an answer, bumps `profile.last_invalidated_at`, returns the next question.

Founder accounts (per `principles.md`) are structurally blocked from both endpoints by the existing `require_role("user")` middleware (cycle #1 F-AUTH-3).

Seed loader: `python -m app.seed questions` idempotently upserts the JSON by question `key`.

## Scope

**In:**
- `questions`, `answers`, `profiles` collection schemas + indexes
- Pydantic models + collection access layer for each
- `GET /api/questions/next` + `POST /api/answers` behind `require_role("user")`
- `app/seed/questions.json` (Claude researches and writes the 10–15 questions during this cycle)
- `python -m app.seed questions` idempotent loader
- `get_or_create_profile(user_id)` helper called on first endpoint hit
- Tests for all the above

**Out (deferred to later cycles or "as needed"):**
- Profile *aggregation* logic — inferring `profile.role`, populating `current_tools`, extracting `workflows` from answers. That's a separate cycle (call it `profile-aggregation-from-answers`, slot before `weaviate-pipeline` #4).
- LLM-generated dynamic follow-up questions — V1.5+
- `next_logic` branching — V1 ships strict linear ordering only
- Live narrowing graph (cycle #5 `fast-onboarding-match-and-graph`)
- Tool recommendations from profile (cycle #6 `recommendation-engine`)
- Question-set authoring admin UI — V1.5+

## Alternatives Considered

1. **Hardcoded Python list of questions instead of seed JSON** — rejected. JSON is editable without code changes; future admin UI builds on the same format; symmetric with cycle #3's catalog seed.
2. **Full `next_logic` branching from day one** — rejected. Branching is only valuable once we know which question paths matter, and we don't (zero users). Linear-only V1; V1.5 introduces branching when cohort data justifies it.
3. **Aggregate role / workflows in this cycle** — rejected. Conflates *"store the data"* with *"interpret the data"*. Splitting them keeps spec-deltas tight and lets the aggregation cycle iterate on inference logic without re-doing storage.
4. **Treat `answers` as a key-value blob keyed by question_id (not append-only)** — rejected. Append-only audit trail is consistent with the `principles.md` *"Treat the user's profile as theirs"* tenet — users can see when they answered each question, and revisions are preserved for export.

## Risks

1. **The first 10–15 questions are wrong.** Solo authoring without user feedback risks a question set that doesn't produce useful profiles. Mitigation: questions live in editable JSON; the cohort test (post-V1) validates; question schema includes a `version` field so historical answers stay valid as the bank evolves.
2. **Profile schema locks future fields prematurely.** If cycle #6 needs a field we didn't anticipate, we'd amend the schema mid-flight. Mitigation: profiles is a Mongo doc (additive fields zero-cost). This cycle reserves field *names* (`current_tools: []`, `workflows: []`, etc.) so future cycles fill them in without schema drama.
3. **`POST /api/answers` is not idempotent on the (user, question) pair.** Append-only means duplicate clicks create duplicate rows. Mitigation: not a real risk for V1's tap-to-answer UX (one click per question). Cycle #5's frontend can debounce; alternatively, cycle #5 can add a unique compound index on `(user_id, question_id)` if duplicates become noisy.
4. **Founder hits these endpoints.** `require_role("user")` returns 403; if a frontend bug shows the onboarding flow to a founder, the 403 surfaces it loudly. No data leak.

## Rollback

- Drop `questions`, `answers`, `profiles` collections.
- Remove the two endpoints + the seed script + the seed JSON.
- Revert this cycle's commits.

Cycle #4 (`weaviate-pipeline`) hasn't started, so nothing depends on `profiles.embedding_vector_id` or any other profile field yet. Rollback cost is low and bounded.
