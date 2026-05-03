# Feature: Question Bank and Answer Capture

> **Cycle of origin:** `question-bank-and-answer-capture` (archived; see `archive/question-bank-and-answer-capture/`)
> **Last reviewed:** 2026-05-01
> **Constitution touchpoints:** `principles.md` (*"Tapping IS the ritual"*, *"Treat the user's profile as theirs"*, *"Never let founder accounts post in user communities"*), `personas.md` (Maya's onboarding flow), `pmf-thesis.md` (load-bearing assumption: profile depth → recommendation quality).
> **Builds on:** `auth-role-split` (F-AUTH-3 `require_role`, F-AUTH-4 non-transferable role).

---

## Intent

The personal AI concierge cannot recommend tools without a profile. The profile is built from a sequence of structured tap-to-answer questions stored in the `questions` collection. This feature delivers the question bank, the answer-capture endpoints, and a profile shell that downstream cycles (`weaviate-pipeline`, `recommendation-engine`) read from.

Three new collections (`questions`, `answers`, `profiles`) plus two endpoints behind `require_role("user")`. Founders are structurally barred — they have no profile, so the matching engine in future cycles cannot match a launch against a founder. The profile is created lazily on the user's first onboarding call and remains JSON-exportable forever.

## Surface

- `GET /api/questions/next` — return the next unanswered core question, or `{done: true}` if all answered. Creates the profile if missing.
- `POST /api/answers` — write an answer, bump `profile.last_invalidated_at`, return the next question via the same response shape.
- CLI: `python -m app.seed questions` — idempotent loader that validates `app/seed/questions.json` end-to-end and upserts into the `questions` collection by stable `key`.

Both endpoints inherit role enforcement from cycle #1's `require_role("user")` middleware (F-AUTH-3): founder → 403 `role_mismatch`, unauthenticated → 401 `auth_required`.

---

## F-QB-1 — Question seed loader

**Given** `app/seed/questions.json` contains entries with shape `{key, text, kind, options, category, order, version, active, is_core}`
**When** `python -m app.seed questions` runs
**Then** each entry is upserted into the `questions` collection by stable `key` (idempotent — running twice produces the same DB state)
**And** the loader prints `inserted: N, updated: M, total: K`.

Re-running with edited `text` (or any other field) updates the existing rows in place; rows in `answers` referencing those questions remain valid (answer history survives question edits).

**Validation discipline:** the loader validates the entire file before any DB write. If any entry is malformed (unknown `kind`, unknown `category`, missing required field, options shape wrong, duplicate key), the loader exits non-zero and **no partial writes occur**.

V1 ships with 12 hand-authored questions covering all six categories: 1 role, 2 stack, 3 workflow, 3 friction, 2 wishlist, 1 budget. LLM-generated dynamic follow-ups are deferred to V1.5+.

---

## F-QB-2 — `GET /api/questions/next`

**Given** an authenticated `role_type=user` caller
**When** they `GET /api/questions/next`
**Then** the system creates a `profiles` row for this user if none exists
**And** returns `{done: false, question: {id, key, text, kind, options, category, order}}` for the unanswered core question with the lowest `order`.

**Given** the caller has answered every active core question
**When** they `GET /api/questions/next`
**Then** the response is `{done: true, question: null}`.

Founder caller → 403 `role_mismatch` per F-AUTH-3.
Unauthenticated → 401 `auth_required` per F-AUTH-3.

V1 uses strict linear ordering by `questions.order`. Branching (`next_logic`) is deferred to V1.5+.

---

## F-QB-3 — `POST /api/answers`

**Given** an authenticated `role_type=user` caller
**When** they `POST /api/answers` with `{question_id, value}` and `value` matches the question's `kind`:

| `kind` | accepted `value` |
|---|---|
| `single_select` | a string ∈ `options[].value` |
| `multi_select` | a non-empty array of strings, each ∈ `options[].value` |
| `free_text` | a non-empty string (whitespace-only is rejected) |

**Then** the system appends a row to `answers` with `{user_id, question_id, value, is_typed_other: false, captured_at: now}`
**And** updates `profile.last_invalidated_at = now`
**And** runs the F-TOOL-7 auto-populate hook (cycle #10 MODIFIED): when the question is `multi_select` and each value resolves to a tool slug via `find_tool_anywhere`, one `user_tools` row is upserted per resolved tool with `source="auto_from_profile"`. The hook is best-effort — failures are logged and swallowed; the response shape and status code are unchanged.
**And** returns the next-question payload (chained — no second round trip).

`answers` is append-only — re-answering the same question creates a new row. The next-question algorithm treats any row in `answers` for a given question as "answered" and skips it.

### Errors

- `question_id` not found or `active=false` → 400 `{"error": "question_not_found"}`
- `value` shape mismatch (wrong type, empty array/string, value not in options) → 400 `{"error": "value_invalid"}`
- Missing `question_id` or `value` in payload → 400 `{"error": "field_required", "field": "<name>"}`
- Founder caller → 403 `role_mismatch`
- Unauthenticated → 401 `auth_required`

---

## F-QB-4 — Profile lifecycle

**Given** a user signs up via F-AUTH-1
**When** no profile row yet exists for them
**Then** the first call to `GET /api/questions/next` OR `POST /api/answers` creates one with the documented schema:

```
{
  user_id,
  role: null,                  // populated by a future aggregation cycle
  current_tools: [],
  workflows: [],
  tools_tried_bounced: [],
  counterfactual_wishes: [],
  budget_tier: null,
  embedding_vector_id: null,   // populated by cycle weaviate-pipeline
  last_recompute_at: null,
  last_invalidated_at: <now>,
  exportable: true,
  created_at: <now>
}
```

Each subsequent `POST /api/answers` updates `last_invalidated_at` to `now`. No other profile field is mutated by this feature; aggregation logic (inferring `role`, populating `current_tools`/`workflows`/etc. from answers) is a separate future cycle.

**Constitutional invariant:** `profiles.exportable` is always `true`. No field stores opaque (non-serializable) data — vector embeddings live in Weaviate (cycle `weaviate-pipeline`) and are referenced by `embedding_vector_id`. The Mongo profile remains JSON-exportable to satisfy *"Treat the user's profile as theirs"*.

---

## F-QB-5 — Founders structurally barred from profiles

**Given** an account with `role_type=founder`
**When** any code path attempts to create a profile for that account
**Then** the operation fails with `ValueError` from `app.db.profiles.get_or_create_profile`.

This guard is independent of the `require_role("user")` middleware on the endpoints. Even if a future cycle accidentally mounts a profile-creating handler without that dependency, the helper layer refuses. Founders have no profile, so the matching logic in cycle `recommendation-engine` cannot match user-side launches against a founder. Code review treats any introduction of a founder→profile path as a constitutional regression against the principle *"Never let founder accounts post in user communities"*.

---

## Architectural notes

- **Storage layout:** `questions` (seeded, mostly static), `answers` (append-only audit trail, one row per tap), `profiles` (one per user, lazily created).
- **Indexes:** `questions.key` unique (for seed upsert) + compound `(is_core, active, order)`; `answers.user_id`; `profiles.user_id` unique.
- **Append-only `answers` rationale:** preserves a user's ability to see when they answered each question and lets users revise answers without losing prior context. Aligned with `principles.md` *"Treat the user's profile as theirs"* — the answer history is part of what the user owns.
- **Defense-in-depth role guard:** `require_role("user")` at the endpoint AND `get_or_create_profile` rejecting founders at the data layer. Either alone would be sufficient for V1; both is paranoia worth keeping while role-gating is young.

## Out of scope (V1 deferrals)

- Profile aggregation logic (inferring `role`, populating `current_tools`/`workflows`/`tools_tried_bounced`/`counterfactual_wishes`/`budget_tier` from answers) — separate future cycle, slot before `weaviate-pipeline`
- LLM-generated dynamic follow-up questions — V1.5+
- `next_logic` branching in the question bank — V1.5+
- Question-set authoring admin UI — V1.5+
- Live narrowing graph in onboarding (cycle `fast-onboarding-match-and-graph`)
- Tool recommendations from profile (cycle `recommendation-engine`)
