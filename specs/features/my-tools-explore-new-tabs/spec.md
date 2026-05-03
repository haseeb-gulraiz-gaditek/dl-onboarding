# Feature: /tools — Mine, Explore, New

> **Cycle of origin:** `my-tools-explore-new-tabs` (archived; see `archive/my-tools-explore-new-tabs/`)
> **Last reviewed:** 2026-05-03
> **Constitution touchpoints:** `principles.md` We Always #2 (*"Treat the user's profile as theirs"* — `/tools/mine` is the user-facing surface for the tools they've stated/saved); We Always #3 (*"Separate organic recommendations from launch surfacing"* — `/api/tools` is sealed against `tools_founder_launched`; `/api/launches` is sealed against `tools_seed`).
> **Builds on:** `auth-role-split` (`require_role`), `catalog-seed-and-curation` (`tools_seed`), `question-bank-and-answer-capture` (the F-QB-3 hook), `communities-and-flat-comments` (`community_memberships` for the joined-community filter), `founder-launch-submission-and-verification` (`tools_founder_launched`, `launches.target_community_slugs`), `recommendation-engine` (engine refactored to use the shared resolver).

---

## Intent

Cycles #1-#9 wired the marketplace end-to-end but left no place for the user to *keep* anything. Recommendations come and go; communities are read; launches surface and fade. The /tools page gives Maya the persistent surface that "treat the profile as theirs" implies:

- **/tools/mine** — current and saved tools, auto-populated from her own answers when the question is structured enough to resolve, plus explicit bookmarks she's chosen herself.
- **/tools/explore** — the whole curated catalog she can browse when she has time.
- **/tools/new** — what founders are launching, defaulted to communities she's joined.

This cycle ships the API only. The React frontend is a parallel Claude Design track.

## Surface

**HTTP:** 6 endpoints + 1 modified route.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST   | `/api/me/tools` | user | explicit save; promotes existing auto rows |
| DELETE | `/api/me/tools/{tool_id}` | user | idempotent unbookmark |
| PATCH  | `/api/me/tools/{tool_id}` | user | flip status; preserves source |
| GET    | `/api/me/tools` | user | list (mine), `?status=` filter, orphans dropped |
| GET    | `/api/tools` | user | explore — tools_seed only, alphabetical cursor |
| GET    | `/api/launches` | user | new — default-filtered to joined communities; `?all=true` |
| POST   | `/api/answers` | user | MODIFIED — auto-populate hook fires after persistence |

**Internal modules:**
- `app/db/user_tools.py` — sealed-by-source collection access; idempotent upsert helpers.
- `app/tools_resolver.py` — `find_tool_anywhere(slug_or_id)` shared resolver (replaces cycle #9's inline helper).
- `app/me/auto_populate_tools.py` — best-effort hook called from `POST /api/answers`.
- `app/api/me_tools.py`, `app/api/tools_browse.py`, `app/api/launches_browse.py` — endpoint routers.

**MongoDB collections:** `user_tools` (new). No other collections added.

---

## F-TOOL-1 — `user_tools` collection

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

**Source precedence** (F-TOOL-3 / F-TOOL-7): `explicit_save` > `manual_add` > `auto_from_profile`. An `explicit_save` row is NEVER demoted by a later answer-driven update; `auto_from_profile` IS upgraded to `explicit_save` on explicit save.

---

## F-TOOL-2 — Cross-collection tool resolution helper

`app/tools_resolver.py` exposes `find_tool_anywhere(slug_or_id) -> tuple[doc | None, is_founder_launched: bool]`. Scans `tools_seed` first, then `tools_founder_launched`. Accepts either a string slug or an `ObjectId`.

Replaces cycle #9's inline `_find_tool_anywhere` in `app/recommendations/engine.py` (refactored as part of this cycle).

---

## F-TOOL-3 — `POST /api/me/tools` (explicit save)

Behind `require_role("user")`. Request body: `{tool_slug, status?: "using" | "saved"}` (status defaults to `saved`).

**Given** an authenticated user explicitly saves a tool that doesn't yet exist in their `user_tools`
**When** they `POST /api/me/tools` with `{tool_slug, status}`
**Then** the system inserts a `user_tools` row with `source="explicit_save"`, the requested status, `added_at = last_updated_at = now()`. Returns `200 OK` with the row + hydrated tool card.

**Given** the same tool already exists in their `user_tools` (from prior auto-populate)
**When** they explicit-save it
**Then** the row is updated: `source="explicit_save"` (promotion), `status` = the requested value, `last_updated_at = now()`. Returns `200 OK`.

**Errors:** unknown slug → `404 tool_not_found`. Founder caller → `403 role_mismatch`.

---

## F-TOOL-4 — `DELETE /api/me/tools/{tool_id}`

Idempotent unbookmark. `tool_id` is the tool's ObjectId (NOT the user_tools row id).

**Given** a row exists for `(user_id, tool_id)` → returns `200 OK {deleted: true}` and removes it.
**Given** no row exists → returns `200 OK {deleted: false}` (idempotent).

Founder → `403`.

---

## F-TOOL-5 — `PATCH /api/me/tools/{tool_id}` (status flip)

Behind `require_role("user")`. Request: `{status: "using" | "saved"}`.

Updates `status` and `last_updated_at`; **`source` is preserved** (an explicit_save row stays explicit). Missing row → `404 tool_not_in_mine`.

---

## F-TOOL-6 — `GET /api/me/tools` (the `/tools/mine` backing)

Behind `require_role("user")`. Optional `?status=using|saved` filter. Sort: `last_updated_at DESC` with `_id DESC` tie-breaker.

Response:
```json
{
  "tools": [
    {
      "id": "<user_tools._id>",
      "tool": { ...OnboardingToolCard fields..., "vote_score": 0, "is_founder_launched": false },
      "source": "explicit_save",
      "status": "using",
      "added_at": "...",
      "last_updated_at": "..."
    }
  ]
}
```

`tool` is hydrated via `find_tool_anywhere`. **Orphan-drop:** rows whose tool no longer resolves OR whose tool's `curation_status` is no longer `"approved"` are silently dropped from the response. The orphaned `user_tools` row stays — periodic cleanup is a V1.5 concern.

---

## F-TOOL-7 — Auto-populate hook on `POST /api/answers`

After a successful `POST /api/answers` (cycle #2 F-QB-3), the answer is inspected:

**Given** the answered question is `kind: "multi_select"` AND the answer's `value` is a list of strings AND each string resolves to a tool slug via `find_tool_anywhere`
**When** the answer is persisted
**Then** for each resolved tool, the system upserts a `user_tools` row:
  - On insert: `source="auto_from_profile"`, `status="using"`, `added_at = last_updated_at = now()`.
  - On existing row with `source="auto_from_profile"`: `last_updated_at = now()` (no source/status change).
  - On existing row with `source="explicit_save"` or `"manual_add"`: NO-OP (explicit signal wins; F-TOOL-3 precedence rule).

Free-text answers, single_select answers, and slug strings that don't resolve are silently skipped — no exception, no warning. The hook is **best-effort**: a failure inside the auto-populate path does NOT abort the answer-write.

> Substring/LLM extraction from free-text is deferred to V1.5+. V1 only auto-populates from structurally-typed multi_select answers.

---

## F-TOOL-8 — `GET /api/tools` (the `/tools/explore` backing)

Behind `require_role("user")`. **Reads `tools_seed` ONLY** (constitutional separation: organic catalog only; founder-launched browsing happens via F-TOOL-9).

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

Founder → `403`.

---

## F-TOOL-9 — `GET /api/launches` (the `/tools/new` backing)

Behind `require_role("user")`. Reads `tools_founder_launched` joined with `launches`.

Default behavior: returns approved launches whose `target_community_slugs` intersect the user's `community_memberships`. Newest-first by `reviewed_at DESC` with `_id DESC` tie-breaker.

Optional query params:
- `all`: `true` removes the joined-community filter.
- `before`: cursor on `reviewed_at`.
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
      "in_my_communities": ["marketing-ops"]
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
**Then** the system returns ALL approved launches; `in_my_communities` reflects which (if any) of each launch's communities the user is in (possibly empty list).

**Given** the user has zero memberships and does NOT pass `?all=true`
**Then** the response is empty (`launches: []`).

Founder → `403`. (Founders use `/api/founders/launches` to see their own.)

---

## Constitutional boundary (audit trail)

- `/api/tools` reads `tools_seed` only. Test `test_founder_launched_not_in_browse` asserts the seal.
- `/api/launches` reads `tools_founder_launched` only.
- The recommendation engine (cycle #6 / cycle #9) keeps its parallel-search-but-separate-arrays pattern; this cycle refactored only the helper, not the structure.
- The F-QB-3 auto-populate hook touches `user_tools` but never any tool collection (read-only via `find_tool_anywhere`).
- `find_tool_anywhere` is the ONLY documented place where both tool collections are queried in one call. Any future code path that needs both must go through it.
