# Spec Delta: catalog-seed-and-curation

## ADDED

### F-CAT-1 — `tools_seed` collection schema

A new MongoDB collection `tools_seed` stores Mesh-curated tool entries.

Each row has the shape:

```
{
  slug: <unique string, lowercase-hyphenated>,
  name: <string>,
  tagline: <string>,
  description: <string>,
  url: <string>,
  pricing_summary: <string>,
  category: <string, one of the 13-value enum>,
  labels: <array, subset of ["new", "all_time_best", "gaining_traction"]>,
  curation_status: "pending" | "approved" | "rejected",
  rejection_comment: <string | null>,         // set when status flips to rejected
  source: "manual",                            // V1 default; future enums reserved (taaft, producthunt, futuretools)
  embedding_vector_id: <string | null>,        // populated by cycle #4
  created_at: <datetime>,
  last_reviewed_at: <datetime | null>,         // bumped on approve / reject
  reviewed_by: <string | null>                 // admin email of the last reviewer
}
```

Indexes: unique on `slug`; compound on `(curation_status, category)` for the admin list view.

**Constitutional invariant:** founder-submitted tool entries do **NOT** live in this collection. Cycle #8 will create a separate `tools_founder_launched` collection. Any code path that writes a row with `source: "founder_launch"` to `tools_seed` is a regression.

---

### F-CAT-2 — Catalog research prompt

A self-contained research prompt at `app/seed/catalog-research-prompt.md` defines the schema, distribution (150 all-time-best + 100 gaining-traction + 50 new = 300), category enum, and quality bar required for catalog entries.

**Given** the user runs the prompt against an external research agent (ChatGPT, Claude, Gemini)
**When** the agent returns a JSON array
**Then** the user saves it to `app/seed/catalog.json` in the repo and proceeds to F-CAT-3.

The prompt itself is the source-of-truth artifact. Catalog refreshes re-run the prompt; quality drift is reviewable as a git diff on `catalog.json`.

---

### F-CAT-3 — `python -m app.seed catalog`

A CLI loader populates `tools_seed` from `app/seed/catalog.json`.

**Given** `app/seed/catalog.json` contains a JSON array of entries matching the F-CAT-1 schema
**When** the operator runs `python -m app.seed catalog`
**Then** each entry is validated and upserted into `tools_seed` keyed by `slug` (idempotent — re-running produces the same DB state)
**And** the loader prints `inserted: N, updated: M, total: K`.

**Defaults applied during load:**
- `curation_status` → `"pending"` if absent in the JSON.
- `source` → `"manual"` if absent.
- `created_at` → set to `now` only on insert (preserved on update).
- `embedding_vector_id`, `last_reviewed_at`, `reviewed_by`, `rejection_comment` → `null`.

**Error: invalid shape.** If any entry is malformed (unknown `category`, unknown `label`, missing required field, options shape wrong) OR if there are duplicate `slug` values, the loader exits non-zero with a clear error message and **no partial writes occur** (validate the whole file before any DB write).

**Error: founder-launched protection.** The loader's upsert filter excludes any document where `source: "founder_launch"`. Even though such rows should never exist in `tools_seed` (they live in `tools_founder_launched`), this guard prevents an accidental cross-collection merge from clobbering data.

---

### F-CAT-4 — Admin auth (`require_admin`)

A FastAPI dependency `require_admin()` reads `ADMIN_EMAILS` (comma-separated env var) and exposes admin endpoints only to authenticated callers whose email is in the allowlist.

**Given** an authenticated caller whose `email` is in `ADMIN_EMAILS`
**When** they hit any endpoint declared `Depends(require_admin())`
**Then** the dependency yields the user dict (proceeds normally).

**Given** an authenticated caller whose `email` is NOT in `ADMIN_EMAILS`
**When** they hit an admin endpoint
**Then** the system returns `403 Forbidden` with `{"error": "admin_only"}`. The caller's `role_type` does not matter — even a `user`-role with a non-admin email is rejected.

**Given** an unauthenticated request
**When** it hits an admin endpoint
**Then** the system returns `401 Unauthorized` with `{"error": "auth_required"}`.

**Given** the `ADMIN_EMAILS` env var is unset or empty
**When** the app boots
**Then** the lifespan startup check raises (existing fail-fast guard from cycle #1) — admin endpoints exist but no caller can satisfy the allowlist, which is a clear misconfiguration. `ADMIN_EMAILS` joins `MONGODB_URI` and `JWT_SECRET` in the required env list.

---

### F-CAT-5 — Admin catalog endpoints

All endpoints below are behind `Depends(require_admin())`.

#### `GET /admin/catalog?status={pending|approved|rejected|all}`

Returns the list of catalog entries matching the requested status. `status=all` (the default if omitted) returns every entry. Response: array of `ToolPublic`.

#### `GET /admin/catalog/{slug}`

Returns a single entry by `slug`. 404 if not found.

#### `POST /admin/catalog/{slug}/approve`

**Given** a catalog entry exists with `slug = X`
**When** an admin POSTs to this endpoint with empty body
**Then** the entry's `curation_status` is set to `"approved"`, `last_reviewed_at = now`, `reviewed_by = <admin email>`, and `rejection_comment = null` (clears any prior rejection comment).
**And** returns the updated `ToolPublic`.

**Error: not found.** Slug doesn't exist → 404 `{"error": "tool_not_found"}`.

#### `POST /admin/catalog/{slug}/reject`

Body: `{ "comment": "<reason>" }` — `comment` is required and non-empty.

**Given** a catalog entry exists with `slug = X`
**When** an admin POSTs with `{comment: "stale URL"}`
**Then** the entry's `curation_status` is set to `"rejected"`, `last_reviewed_at = now`, `reviewed_by = <admin email>`, `rejection_comment = "stale URL"`.

**Error: missing comment.** No comment in body → 400 `{"error": "field_required", "field": "comment"}`.

**Error: empty comment.** Comment is whitespace-only → 400 `{"error": "comment_invalid"}`.

**Error: not found.** Slug doesn't exist → 404 `{"error": "tool_not_found"}`.

---

### F-CAT-6 — `ADMIN_EMAILS` joins required environment

The lifespan-startup `_REQUIRED_ENV` tuple from cycle #1 (`MONGODB_URI`, `JWT_SECRET`) is extended to include `ADMIN_EMAILS`. The app refuses to boot if any of the three is unset or blank. `.env.example` documents the new var.

## MODIFIED

### `_REQUIRED_ENV` in `app/main.py` (added in cycle #1)

**Before:** `_REQUIRED_ENV = ("MONGODB_URI", "JWT_SECRET")`
**After:** `_REQUIRED_ENV = ("MONGODB_URI", "JWT_SECRET", "ADMIN_EMAILS")`

`.env.example` is updated to include `ADMIN_EMAILS=` with a comment explaining the comma-separated format.

### Documented future commitment for the `tools_founder_launched` collection

A note is added to the cycle's spec recording that cycle #8 (`founder-launch-submission-and-verification`) is responsible for creating `tools_founder_launched`, with the same shape minus the seed-curation fields and plus founder-side metadata. This cycle does NOT create that collection.

## REMOVED

(None.)
