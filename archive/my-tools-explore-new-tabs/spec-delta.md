# Spec Delta: my-tools-explore-new-tabs

## ADDED

### F-TOOL-1 — `user_tools` collection

A new MongoDB collection `user_tools` stores per-user tool ownership. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId,
  tool_id: ObjectId,                         // resolves in tools_seed OR tools_founder_launched
  source: "auto_from_profile" | "explicit_save" | "manual_add",
  status: "using" | "saved",
  added_at: datetime,
  last_updated_at: datetime
}
```

Indexes:
- Unique compound on `(user_id, tool_id)` — idempotent inserts.
- `(user_id, last_updated_at DESC)` — primary list query.

`status` is restricted to `"using" | "saved"` in V1. `tried_bounced` and `want_to_try` are reserved for V1.5+.

`source` precedence rule (F-TOOL-3): an `explicit_save` row is never demoted to `auto_from_profile` by a later answer-driven update. `auto_from_profile` is upgraded to `explicit_save` on explicit save.

---

### F-TOOL-2 — Cross-collection tool resolution helper

A new module `app/tools_resolver.py` exposes `find_tool_anywhere(slug_or_id)`:

```python
async def find_tool_anywhere(slug_or_id: str | ObjectId) -> tuple[dict | None, bool]:
    """Returns (doc, is_founder_launched). Scans tools_seed first,
    then tools_founder_launched. Slug-keyed OR id-keyed."""
```

Replaces cycle #9's inline `_find_tool_anywhere` in `app/recommendations/engine.py`; engine refactored to use the shared helper.

---

### F-TOOL-3 — `POST /api/me/tools` (explicit save)

Behind `require_role("user")`.

Request body:
```json
{ "tool_slug": "cursor", "status": "saved" }
```

Validations:
- `tool_slug`: must resolve via `find_tool_anywhere` → else 404 `tool_not_found`.
- `status`: optional, defaults to `"saved"`. Must be `"using" | "saved"` → else 400 `field_invalid` field=`status`.

**Given** an authenticated user explicitly saves a tool that doesn't yet exist in their `user_tools`
**When** they `POST /api/me/tools` with `{tool_slug, status}`
**Then** the system inserts a `user_tools` row with `source="explicit_save"`, the requested status, `added_at = last_updated_at = now()`. Returns `201 Created` with the row + hydrated tool card.

**Given** the same tool already exists in their `user_tools` (from prior auto-populate)
**When** they explicit-save it
**Then** the row is updated: `source="explicit_save"` (promotion), `status` = the requested value, `last_updated_at = now()`. Returns `200 OK` with the updated row.

**Founder caller** → `403 role_mismatch`.

---

### F-TOOL-4 — `DELETE /api/me/tools/{tool_id}` (unbookmark)

Behind `require_role("user")`. `tool_id` is the tool's ObjectId (NOT the user_tools row id).

**Given** a row exists for `(user_id, tool_id)`
**When** the user deletes it
**Then** the row is removed; returns `200 OK` with `{deleted: true}`.

**Given** no row exists**
**When** the user deletes
**Then** returns `200 OK` with `{deleted: false}` (idempotent).

**Founder caller** → `403`.

---

### F-TOOL-5 — `PATCH /api/me/tools/{tool_id}` (status flip)

Behind `require_role("user")`.

Request body: `{status: "using" | "saved"}`.

Validations:
- `status`: required, must be one of two → else 400 `field_invalid`.
- A `user_tools` row must exist for `(user_id, tool_id)` → else 404 `tool_not_in_mine`.

Updates `status` and `last_updated_at`. `source` is preserved. Returns `200 OK` with the updated row + hydrated tool card.

---

### F-TOOL-6 — `GET /api/me/tools` (the `/tools/mine` backing)

Behind `require_role("user")`.

Optional `?status=using|saved` filter. Sort: `last_updated_at DESC` (with `_id DESC` tie-breaker).

Response:
```json
{
  "tools": [
    {
      "id": "<user_tools._id>",
      "tool": { ...OnboardingToolCard fields..., "is_founder_launched": false },
      "source": "explicit_save",
      "status": "using",
      "added_at": "...",
      "last_updated_at": "..."
    }
  ]
}
```

`tool` is hydrated via `find_tool_anywhere`. Rows whose tool no longer resolves (curation status flipped to rejected, or row deleted) are silently dropped from the response. The orphaned `user_tools` row stays — periodic cleanup is a V1.5 concern.

---

### F-TOOL-7 — Auto-populate hook on `POST /api/answers`

After a successful `POST /api/answers` (cycle #2's F-QB-3), the answer is inspected:

**Given** the answered question is `kind: "multi_select"` AND the answer's `value` is a list of strings AND each string resolves to a tool slug via `find_tool_anywhere`
**When** the answer is persisted
**Then** for each resolved tool, the system upserts a `user_tools` row:
  - On insert: `source="auto_from_profile"`, `status="using"`, `added_at = last_updated_at = now()`.
  - On existing row with `source="auto_from_profile"`: `last_updated_at = now()` (no source/status change).
  - On existing row with `source="explicit_save"` or `"manual_add"`: NO-OP (explicit signal wins; F-TOOL-3 precedence rule).

Free-text answers, single_select answers, and slug strings that don't resolve are silently skipped — no exception, no warning. The hook is best-effort: a failure inside the auto-populate path does NOT abort the answer-write.

---

### F-TOOL-8 — `GET /api/tools` (the `/tools/explore` backing)

Behind `require_role("user")`. Reads `tools_seed` ONLY (constitutional separation: organic catalog only; founder-launched browsing happens via F-TOOL-9).

Query params (all optional):
- `category`: exact match on `category` enum.
- `label`: membership in `labels` array.
- `q`: case-insensitive substring match on `name` OR `tagline`.
- `before`: cursor — return tools whose `name > before` (alphabetical pagination).
- `limit`: 1..50, default 20.

Filter on `curation_status="approved"` always. Sort: `name ASC` with `_id ASC` tie-breaker.

Response:
```json
{
  "tools": [
    { ...OnboardingToolCard fields..., "vote_score": 4, "is_founder_launched": false }
  ],
  "next_before": "Notion"   // null on last page
}
```

**Founder caller** → `403`.

---

### F-TOOL-9 — `GET /api/launches` (the `/tools/new` backing)

Behind `require_role("user")`. Reads `tools_founder_launched` joined with `launches` for metadata.

Default behavior: returns approved launches whose `target_community_slugs` intersect the user's `community_memberships`. Newest-first by approval date (`reviewed_at DESC` with `_id DESC` tie-breaker).

Optional query params:
- `all`: `true` removes the joined-community filter (returns all approved launches).
- `before`: cursor on `reviewed_at` for pagination.
- `limit`: 1..50, default 20.

Response:
```json
{
  "launches": [
    {
      "tool": { ...OnboardingToolCard fields..., "vote_score": 0, "is_founder_launched": true },
      "launch_meta": {
        "founder_display_name": "aamir",
        "problem_statement": "...",
        "approved_at": "..."
      },
      "in_my_communities": ["marketing-ops"]   // intersection of launch.target_community_slugs and user's memberships
    }
  ],
  "next_before": "..."
}
```

**Given** an authenticated user is a member of `marketing-ops`
**When** they `GET /api/launches`
**Then** the system returns approved launches whose `target_community_slugs` includes `marketing-ops`.

**Given** the same user passes `?all=true`
**When** they `GET /api/launches?all=true`
**Then** the system returns ALL approved launches, with `in_my_communities` reflecting which (if any) of each launch's communities the user is in.

**Founder caller** → `403 role_mismatch`. (Founders use `/api/founders/launches` to see their own.)

## MODIFIED

### F-QB-3 — `POST /api/answers` (cycle #2)

**Before:** F-QB-3 persists the answer + bumps `profile.last_invalidated_at`.

**After:** After the existing persistence + invalidation, the auto-populate hook (F-TOOL-7) runs against the just-persisted answer. The hook is best-effort and does NOT affect the response shape or status code; failures inside the hook are logged and swallowed.

The response shape of `POST /api/answers` is unchanged.

### `app/recommendations/engine.py` (cycle #6 / cycle #9)

**Before:** `_find_tool_anywhere` is a private helper inside `engine.py`.

**After:** Refactored to import from the shared `app/tools_resolver.py` (F-TOOL-2). No behavior change; deduplication only.

## REMOVED

(None.)
