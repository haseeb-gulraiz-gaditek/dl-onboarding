# Spec Delta: question-bank-and-answer-capture

## ADDED

### F-QB-1 — Question seed loader

A one-shot CLI command populates the `questions` collection from `app/seed/questions.json`.

**Given** the seed JSON contains entries with shape `{key, text, kind, options, category, order, version, active}`
**When** the operator runs `python -m app.seed questions`
**Then** each entry is upserted into the `questions` collection by `key` (idempotent — running twice produces the same DB state)
**And** the loader prints `inserted: N, updated: M, total: K`.

**Given** the seed JSON references an existing `key`
**When** the loader runs
**Then** `text`, `kind`, `options`, `order`, `category`, `active` are updated to the JSON's values
**And** `version` is the JSON's `version` (used by clients to invalidate cached questions if needed)
**But** rows in `answers` referencing that question by `question_id` remain valid — answer history survives question edits.

**Given** the seed JSON has invalid shape (missing required field, unknown `kind`)
**When** the loader runs
**Then** the loader exits non-zero, prints which entry was invalid, and **no partial writes occur** (validate the whole file before any insert).

---

### F-QB-2 — `GET /api/questions/next`

**Given** an authenticated `role_type=user` caller
**When** they `GET /api/questions/next`
**Then** the system creates a `profiles` row for this user if none exists (`get_or_create_profile`)
**And** returns the *next unanswered* core question — the one with the lowest `order` among `is_core=true, active=true` questions where the caller has no row in `answers`
**And** the response shape is `{done: false, question: {id, key, text, kind, options, category, order}}`.

**Given** the caller has answered every core active question
**When** they `GET /api/questions/next`
**Then** the response is `{done: true, question: null}`.

**Given** an authenticated `role_type=founder` caller
**When** they `GET /api/questions/next`
**Then** the middleware returns `403 Forbidden` with `{"error": "role_mismatch", "required": "user", "actual": "founder"}` (per F-AUTH-3).

**Given** an unauthenticated request
**When** it calls `GET /api/questions/next`
**Then** the middleware returns `401 Unauthorized` with `{"error": "auth_required"}` (per F-AUTH-3).

---

### F-QB-3 — `POST /api/answers`

**Given** an authenticated `role_type=user` caller
**When** they `POST /api/answers` with `{question_id, value}` where `question_id` is an active question and `value` matches the question's `kind`:
- `kind=single_select`: `value` is a string ∈ `options[].value`
- `kind=multi_select`: `value` is a non-empty array of strings, each ∈ `options[].value`
- `kind=free_text`: `value` is a non-empty string

**Then** the system inserts a new `answers` row with `{user_id, question_id, value, is_typed_other: false, captured_at: now}`
**And** updates the user's profile: `last_invalidated_at = now`
**And** returns the F-QB-2 next-question payload (so the client can chain the flow without a second call).

**Error: question not found**
**Given** a `POST /api/answers` payload
**When** `question_id` does not exist or `active=false`
**Then** the system returns `400` with `{"error": "question_not_found"}`.

**Error: value shape mismatch**
**Given** a `POST /api/answers` payload
**When** `value` does not match the question's `kind` (wrong type, empty array, value not in options)
**Then** the system returns `400` with `{"error": "value_invalid"}`.

**Error: missing fields**
**Given** a `POST /api/answers` payload
**When** `question_id` or `value` is missing
**Then** the system returns `400` with `{"error": "field_required", "field": "question_id"}` (or `"field": "value"`).

**Founder rejection and unauthenticated rejection** — same as F-QB-2.

---

### F-QB-4 — Profile lifecycle

**Given** a user has just signed up via F-AUTH-1
**When** no profile row yet exists for them
**Then** the first call to `GET /api/questions/next` OR `POST /api/answers` creates one with shape:
```
{
  user_id: <ref>,
  role: null,                   # populated by a later aggregation cycle
  current_tools: [],
  workflows: [],
  tools_tried_bounced: [],
  counterfactual_wishes: [],
  budget_tier: null,
  embedding_vector_id: null,    # populated by cycle #4 weaviate-pipeline
  last_recompute_at: null,
  last_invalidated_at: <now>,
  exportable: true,
  created_at: <now>
}
```

**Given** a user has an existing profile
**When** they `POST /api/answers`
**Then** `last_invalidated_at` is updated to `now`
**And** no other profile field is mutated by this cycle (aggregation lives in a future cycle).

**Constitutional invariant:** `profiles.exportable` is always `true`. No field stores opaque (non-serializable) data — embeddings, when added in cycle #4, live in Weaviate and are referenced by `embedding_vector_id`. The Mongo profile remains JSON-exportable to satisfy the principle *"Treat the user's profile as theirs"*.

---

### F-QB-5 — Founder accounts are structurally barred from the question flow

**Given** an account with `role_type=founder`
**When** any code path attempts to create a profile for that account
**Then** the operation fails with a clear error (the `get_or_create_profile` helper rejects founder accounts).

This is a defense-in-depth measure: even if a future cycle accidentally mounts a profile-creating handler without `require_role("user")`, the helper layer refuses. Reinforces `principles.md` *"Never let founder accounts post in user communities"* — founders have no profile, so they cannot be matched by future recommendation logic against user-side launches.

## MODIFIED

### `users` collection (cycle #1 F-AUTH-1)

**Before:** the `users` collection has fields `email`, `password_hash`, `role_type`, `display_name`, `created_at`, `last_active_at`.

**After:** unchanged. This cycle does NOT modify the `users` schema. Profile-related state lives entirely in the new `profiles` collection, joined by `user_id`. Recorded here only to make the boundary explicit for future cycles auditing this spec.

## REMOVED

(None.)
