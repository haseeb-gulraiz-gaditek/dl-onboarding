# Spec Delta: founder-launch-submission-and-verification

## ADDED

### F-LAUNCH-1 — `launches` collection + `POST /api/founders/launch`

A new MongoDB collection `launches` stores founder submissions. Schema:

```
{
  _id: ObjectId,
  founder_user_id: ObjectId,
  product_url: string (http(s)),
  problem_statement: string (1..280 chars),
  icp_description: string (1..500 chars),
  existing_presence_links: [string] (0..6 entries, each http(s)),
  verification_status: "pending" | "approved" | "rejected",
  rejection_comment: string | null,
  reviewed_by: string | null,                  // admin email
  reviewed_at: datetime | null,
  approved_tool_slug: string | null,           // populated on approve (F-LAUNCH-5)
  created_at: datetime
}
```

Indexes:
- `founder_user_id` — founder's submission list.
- `(verification_status, created_at)` — admin queue (status filter + chronological).

**Endpoint:** `POST /api/founders/launch` behind `require_role("founder")`.

Request body:
```json
{
  "product_url": "https://example.com",
  "problem_statement": "...",
  "icp_description": "...",
  "existing_presence_links": ["https://x.com/handle"]
}
```

Validations:
- `product_url`: must start with `http://` or `https://`. Empty/invalid → 400 `field_required` field=`product_url` (or 400 `url_invalid` for non-http(s)).
- `problem_statement`: 1..280 chars after strip. Empty → 400 `field_required` field=`problem_statement`.
- `icp_description`: 1..500 chars after strip. Empty → 400 `field_required` field=`icp_description`.
- `existing_presence_links`: optional list, max 6 entries, each must be http(s). Invalid → 400 `field_invalid` field=`existing_presence_links`.

**Given** an authenticated founder posts a valid body
**When** they `POST /api/founders/launch`
**Then** the system inserts one `launches` row with `verification_status: "pending"` and returns `201 Created` with the inserted document.

**Authenticated user (`role_type=user`)** → `403 role_mismatch`.
**Unauthenticated** → `401 auth_required`.

**Resubmission semantics (append-only):** if the founder has previous rejected launches, this submission creates a NEW row. The `launches` collection is append-only from the founder's perspective; rejected rows stay as historical record.

---

### F-LAUNCH-2 — Founder read endpoints

`GET /api/founders/launches` behind `require_role("founder")` — returns the requesting founder's own launches, newest-first. Optional `?status=` filter (pending|approved|rejected).

`GET /api/founders/launches/{id}` behind `require_role("founder")` — returns one launch IF the requesting founder is the author. Otherwise 404 `launch_not_found` (don't leak existence).

Response shape (per launch):
```json
{
  "id": "...",
  "product_url": "...",
  "problem_statement": "...",
  "icp_description": "...",
  "existing_presence_links": [...],
  "verification_status": "pending",
  "rejection_comment": null,
  "reviewed_by": null,
  "reviewed_at": null,
  "approved_tool_slug": null,
  "created_at": "..."
}
```

---

### F-LAUNCH-3 — Admin queue + detail endpoints

`GET /admin/launches` behind `require_admin()` — list launches with optional `?status=` filter (default `pending`). Sorted by `created_at` ASC (oldest pending first; admins work the queue head-first).

`GET /admin/launches/{id}` behind `require_admin()` — full launch + the founder's email (joined from `users` collection) for context.

`require_admin()` already exists from cycle #3 and uses the `ADMIN_EMAILS` env allowlist. No new admin gate here.

Response (queue list item):
```json
{
  "launches": [
    {
      "id": "...",
      "founder_email": "aamir@example.com",
      "product_url": "...",
      "problem_statement": "...",
      "verification_status": "pending",
      "created_at": "..."
    }
  ]
}
```

---

### F-LAUNCH-4 — Admin approve

`POST /admin/launches/{id}/approve` behind `require_admin()`. Empty body.

**Given** a launch with `verification_status: "pending"`
**When** an admin approves it
**Then** the system:

1. Derives a slug from `product_url` (see F-LAUNCH-6).
2. Inserts a `tools_founder_launched` row with the derived slug, founder-supplied fields, `source: "founder_launch"`, `is_founder_launched: true`, `launched_via_id: <launch._id>`, `curation_status: "approved"`, `vote_score: 0`, `embedding: null` (cycle #4's lifecycle helper will populate it lazily on first read).
3. Updates the `launches` row: `verification_status: "approved"`, `reviewed_by: <admin email>`, `reviewed_at: now()`, `approved_tool_slug: <slug>`.
4. Writes a `notifications` row (F-LAUNCH-7).
5. Returns `200 OK` with the updated launch document.

Idempotency: re-approving an already-approved launch returns `409 launch_already_resolved`. Re-approving a rejected launch ALSO returns `409` (founder must resubmit, F-LAUNCH-1 NOTE).

**Unknown launch id** → `404 launch_not_found`.
**Non-admin caller** → `403 admin_required` (per cycle #3 F-CAT-4).

---

### F-LAUNCH-5 — Admin reject

`POST /admin/launches/{id}/reject` behind `require_admin()`.

Request body:
```json
{ "comment": "Why this didn't pass." }
```

Validations:
- `comment`: 1..500 chars after strip. Empty → 400 `field_required` field=`comment`.

**Given** a launch with `verification_status: "pending"`
**When** an admin rejects with a comment
**Then** the system:

1. Updates the `launches` row: `verification_status: "rejected"`, `rejection_comment: <comment>`, `reviewed_by: <admin email>`, `reviewed_at: now()`.
2. Writes a `notifications` row (F-LAUNCH-7).
3. Returns `200 OK` with the updated launch.

Re-rejecting OR rejecting an already-resolved launch → `409 launch_already_resolved`.

**No `tools_founder_launched` row is created on reject.** The founder must resubmit a new launch (F-LAUNCH-1 append-only contract).

---

### F-LAUNCH-6 — Slug derivation + collision suffix

Helper function `derive_tool_slug(product_url) -> str`. Used by F-LAUNCH-4.

Algorithm:
1. Parse the host from `product_url` (use Python `urllib.parse.urlparse(...).hostname`).
2. Strip leading `www.`.
3. Lowercase. Replace any character not in `[a-z0-9-]` with `-`. Collapse repeated `-`. Strip leading/trailing `-`.
4. If empty after normalization, fall back to `launch-{timestamp}`.
5. Check collision: scan BOTH `tools_seed.find_one({slug})` AND `tools_founder_launched.find_one({slug})`. If neither has the slug, return it.
6. On collision, append `-2`, `-3`, ... up to `-99`, scanning both collections each time. If all variants taken, raise `RuntimeError` (admin sees 500 — this should never happen in practice).

**Given** a launch with `product_url: "https://www.acme.io/about"` and no existing `acme` slug in either collection
**When** approval is processed
**Then** the derived slug is `acme`.

**Given** an existing `acme` row in `tools_seed`
**When** a launch is approved with `product_url: "https://acme.io"`
**Then** the derived slug is `acme-2`.

---

### F-LAUNCH-7 — `tools_founder_launched` collection

A new MongoDB collection `tools_founder_launched`. Sealed against `source != "founder_launch"` writes (the inverse seal of cycle #3's `tools_seed` invariant).

Schema (mirrors `tools_seed` for the shared fields, plus founder-specific):

```
{
  _id: ObjectId,
  slug: string (unique, lowercase-hyphenated),
  name: string,                              // founder-supplied at submission OR derived; F-LAUNCH-4 uses domain stem
  tagline: string,                           // first 100 chars of problem_statement
  description: string,                       // problem_statement + " " + icp_description
  url: string (http(s)),                     // = launch.product_url
  pricing_summary: "Free" | string,          // "Free" placeholder in V1; founder pricing ingestion deferred
  category: "automation_agents",             // single placeholder category in V1; refinement deferred to cycle #9
  labels: ["new"],                           // every approved launch gets the "new" label
  curation_status: "approved",               // bypasses cycle #3 admin pending state
  rejection_comment: null,
  source: "founder_launch",                  // sealed
  is_founder_launched: true,                 // true on every row in this collection
  launched_via_id: ObjectId,                 // → launches._id
  embedding: null,                           // cycle #4's ensure_tool_embedding picks this up
  vote_score: 0,
  created_at: datetime,
  last_reviewed_at: datetime,                // = approval timestamp
  reviewed_by: string                        // admin email
}
```

Unique index on `slug`. The slug index is GLOBAL across both collections by convention (F-LAUNCH-6 enforces this), even though MongoDB's unique index is per-collection.

Helper module `app/db/tools_founder_launched.py` exposes `find_by_slug`, `find_by_id`, and `insert`. The collection access layer is intentionally minimal in this cycle; cycle #9 will add embedding lifecycle hooks.

---

### F-LAUNCH-8 — `notifications` collection (write-only in V1)

A new MongoDB collection `notifications` for in-app inbox rows. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId,
  kind: "launch_approved" | "launch_rejected" | string,
  payload: dict,                              // kind-specific
  read_at: datetime | null,
  created_at: datetime
}
```

Indexes: `(user_id, created_at DESC)`.

This cycle WRITES rows on approve/reject. **No read endpoint yet** — cycle #11 will build the inbox UI and the `GET /api/me/notifications` endpoint. Founder sees status by polling `GET /api/founders/launches`; the notification row is forward-compat scaffolding.

`payload` shapes:
- `kind: "launch_approved"` → `{launch_id, tool_slug}`.
- `kind: "launch_rejected"` → `{launch_id, comment}`.

---

## MODIFIED

### Recommendation engine boundary (cycle #6)

**Before:** `app/recommendations/engine.py` queries only `tools_seed` (via `similarity_search(collection_name="tools_seed", ...)`).

**After:** No code change in this cycle. **Cycle #9** will:

1. Add a parallel `similarity_search(collection_name="tools_founder_launched", ...)` call.
2. Apply the threshold gate (cosine > 0.85 OR top 5% by score).
3. Return launches in a SEPARATE `launches: list[RecommendationPick]` field on `RecommendationsResponse`.

This MODIFIED section is recorded here so cycle #9's spec-delta can reference it; the implementation lives there. The C2 amendment to `principles.md` We Always #3 (committed at the start of this cycle) is the constitutional source for that change.

## REMOVED

(None.)
