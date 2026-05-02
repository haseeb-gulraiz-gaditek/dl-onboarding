# Feature: Founder Launch Submission + Admin Verification

> **Cycle of origin:** `founder-launch-submission-and-verification` (archived; see `archive/founder-launch-submission-and-verification/`)
> **Last reviewed:** 2026-05-02
> **Constitution touchpoints:** `principles.md` (We Always #3 — *"Separate organic recommendations from launch surfacing"* — storage stays separate via `tools_founder_launched`; *"Default to the user side. Founder value scales with user-side trust."*; *"Anti-spam is structural"* — admin verification gate, no public submission API).
> **Builds on:** `auth-role-split` (`require_role("founder")`, `role_question_answer="launching_product"`), `catalog-seed-and-curation` (`require_admin()` allowlist; sealed-collection invariant inverted in this cycle).

> **Half-cycle, by design.** This feature opens the founder side: submission, admin verification, canonical product-page row in `tools_founder_launched`. Cycle #9 builds on it: dual-fire publish (community feed `kind=launch` post + concierge nudge), redirect tracking, recommendation-engine fan-in (gated by the C2 amendment to We Always #3 committed at the start of this cycle).

---

## Intent

Aamir (the early-stage AI founder persona) needs a launch surface that converts. Product Hunt's 0.25% conversion, X build-in-public's noise floor, and Reddit's hostility to anything promotional all leave him with no qualified-engagement channel. Mesh promises: lightweight verification, distribution into matched communities, concierge nudge to the tightest-fit user subset. Cycle #8 ships the front door — submission + verification — without yet wiring the distribution and recommendation surfaces (those come in #9).

A single submission endpoint, admin queue + approve/reject, and a sealed `tools_founder_launched` collection that holds the canonical product-page row. Approval writes a `notifications` row instead of sending email; cycle #11 will build the inbox UI. No SMTP infrastructure in V1.

## Surface

**HTTP:** 7 endpoints across 2 routers.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST   | `/api/founders/launch` | founder | submit; new row each call |
| GET    | `/api/founders/launches` | founder | own list, optional `?status=` |
| GET    | `/api/founders/launches/{id}` | founder | 404 if not author (no leak) |
| GET    | `/admin/launches` | admin | queue, defaults `?status=pending` |
| GET    | `/admin/launches/{id}` | admin | full + founder email |
| POST   | `/admin/launches/{id}/approve` | admin | derives slug, creates `tools_founder_launched`, notifies |
| POST   | `/admin/launches/{id}/reject` | admin | requires `comment`; notifies |

**Internal modules:**
- `app/db/launches.py` — submission collection, queue queries, atomic resolution via `find_one_and_update` filtered on `verification_status="pending"`.
- `app/db/tools_founder_launched.py` — sealed collection (refuses any `source != "founder_launch"`).
- `app/db/notifications.py` — write-only inbox in V1 (cycle #11 reads).
- `app/launches/slug.py` — `derive_tool_slug(url)` + cross-collection `find_available_slug(base)`.
- `app/api/founders.py` + `app/api/admin_launches.py` — endpoint routers.

**MongoDB collections (created by this cycle):** `launches`, `tools_founder_launched`, `notifications`.

---

## F-LAUNCH-1 — `launches` collection + `POST /api/founders/launch`

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
  approved_tool_slug: string | null,           // populated on approve (F-LAUNCH-4)
  created_at: datetime
}
```

Indexes: `founder_user_id` (founder list); `(verification_status, created_at)` (admin queue, status filter + chronological).

**Endpoint:** `POST /api/founders/launch` behind `require_role("founder")`.

Validations:
- `product_url`: must start with `http://` or `https://`. Empty → 400 `field_required` field=`product_url`. Non-http(s) → 400 `url_invalid`.
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

## F-LAUNCH-2 — Founder read endpoints

`GET /api/founders/launches` behind `require_role("founder")` — returns the requesting founder's own launches, newest-first. Optional `?status=` filter.

`GET /api/founders/launches/{id}` behind `require_role("founder")` — returns one launch IF the requesting founder is the author. Otherwise 404 `launch_not_found` (don't leak existence).

---

## F-LAUNCH-3 — Admin queue + detail

`GET /admin/launches` behind `require_admin()` — list with optional `?status=` (default `pending`). Sorted by `created_at` ASC (oldest first).

`GET /admin/launches/{id}` behind `require_admin()` — full launch + the founder's email (joined from `users`).

`require_admin()` is reused from cycle #3 (the `ADMIN_EMAILS` env allowlist). Non-admin caller → `403 admin_only`.

---

## F-LAUNCH-4 — Admin approve

`POST /admin/launches/{id}/approve` behind `require_admin()`. Empty body.

**Given** a launch with `verification_status: "pending"`
**When** an admin approves it
**Then** the system:

1. Derives a slug from `product_url` (see F-LAUNCH-6).
2. Inserts a `tools_founder_launched` row with the derived slug, founder-supplied fields, `source: "founder_launch"`, `is_founder_launched: true`, `launched_via_id: <launch._id>`, `curation_status: "approved"`, `vote_score: 0`, `embedding: null`, `labels: ["new"]`, `category: "automation_agents"` (placeholder until cycle #9 refines).
3. Updates the `launches` row atomically via `find_one_and_update` filtered on `verification_status="pending"`: sets status to `approved`, `reviewed_by`, `reviewed_at`, `approved_tool_slug`.
4. Writes a `notifications` row (F-LAUNCH-8).
5. Returns `200 OK` with the updated launch document.

Idempotency / concurrency: re-approving an already-resolved launch returns `409 launch_already_resolved`. The atomic filter on `verification_status="pending"` closes the race against concurrent admin clicks.

**Unknown launch id** → `404 launch_not_found`.
**Non-admin caller** → `403 admin_only`.

---

## F-LAUNCH-5 — Admin reject

`POST /admin/launches/{id}/reject` behind `require_admin()`.

Request: `{"comment": "..."}` (1..500 chars after strip; empty → 400 `field_required` field=`comment`).

**Given** a launch with `verification_status: "pending"`
**When** an admin rejects with a comment
**Then** the system:

1. Updates the `launches` row atomically: status=`rejected`, `rejection_comment`, `reviewed_by`, `reviewed_at`.
2. Writes a `notifications` row (F-LAUNCH-8).
3. Returns `200 OK` with the updated launch.

Re-rejecting OR rejecting an already-resolved launch → `409 launch_already_resolved`. **No `tools_founder_launched` row is created on reject.**

---

## F-LAUNCH-6 — Slug derivation + collision suffix

Helper function `derive_tool_slug(product_url) -> str`. Pure synchronous; no DB access.

Algorithm:
1. Parse host from `product_url` via `urllib.parse.urlparse(...).hostname`.
2. Strip leading `www.`.
3. Lowercase. Replace any character outside `[a-z0-9-]` with `-`. Collapse repeated `-`. Strip leading/trailing `-`.
4. If empty after normalization, fall back to `launch-{epoch}`.

Collision scan via `find_available_slug(base)`:
- Scans BOTH `tools_seed.find_one({slug})` AND `tools_founder_launched.find_one({slug})`.
- If neither has the slug, return it.
- On collision, append `-2`, `-3`, ... up to `-99` (`MAX_SLUG_SUFFIX`), scanning both collections each time. If exhausted, raise `RuntimeError`.

**Given** a launch with `product_url: "https://www.acme.io/about"` and no existing `acme-io` slug
**When** approval is processed
**Then** the derived slug is `acme-io`.

> **The host is kept kebab-cased (TLD included)** rather than stripped to the second-level label. Reason: `acme.com`, `acme.io`, `acme.dev` are different products in practice; collapsing them all to `acme` would force collision-suffixes for every common name.

**Given** an existing `acme-io` row in `tools_seed`
**When** a launch is approved with `product_url: "https://acme.io"`
**Then** the derived slug is `acme-io-2`.

---

## F-LAUNCH-7 — `tools_founder_launched` collection

A new MongoDB collection sealed against `source != "founder_launch"` writes (the inverse seal of cycle #3's `tools_seed` invariant). Together they enforce the constitutional "storage stays separate" requirement at the data layer.

Schema (mirrors `tools_seed` for shared fields, plus founder-specific):

```
{
  _id: ObjectId,
  slug: string (unique),
  name, tagline, description, url, pricing_summary: strings,
  category: "automation_agents",                  // single placeholder in V1
  labels: ["new"],                                 // every approved launch
  curation_status: "approved",                     // bypasses cycle #3 pending state
  rejection_comment: null,
  source: "founder_launch",                        // sealed
  is_founder_launched: true,                       // true on every row
  launched_via_id: ObjectId,                       // → launches._id
  embedding: null,                                 // cycle #4 fills lazily
  vote_score: 0,
  created_at: datetime,
  last_reviewed_at: datetime,                      // approval timestamp
  reviewed_by: string                              // admin email
}
```

Unique index on `slug`. Slug uniqueness is GLOBAL across both tool collections by convention (F-LAUNCH-6 enforces).

`app/db/tools_founder_launched.insert(doc)` raises `ValueError` if `doc.source != "founder_launch"` — defense-in-depth even if a future code path tries to write the wrong shape.

---

## F-LAUNCH-8 — `notifications` collection (write-only in V1)

A new MongoDB collection for in-app inbox rows. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId,
  kind: "launch_approved" | "launch_rejected" | string,
  payload: dict,
  read_at: datetime | null,
  created_at: datetime
}
```

Index: `(user_id, created_at DESC)`.

This cycle WRITES rows on approve/reject. **No read endpoint yet** — cycle #11 builds the inbox UI and `GET /api/me/notifications`. Founder sees status by polling `GET /api/founders/launches` in V1.

`payload` shapes:
- `kind: "launch_approved"` → `{launch_id, tool_slug}`.
- `kind: "launch_rejected"` → `{launch_id, comment}`.

---

## Recommendation engine boundary

Per the C2 amendment to `principles.md` We Always #3 (committed at the start of this cycle), well-matched founder launches MAY appear alongside organic recommendations in a separate `launches` slot. **Cycle #9** implements the fan-in: it adds a parallel similarity search against `tools_founder_launched`, applies the threshold gate (cosine > 0.85 OR top 5%), and returns launches in a distinct field on `RecommendationsResponse`. Storage stays separate; ranking pipelines stay separate; the only co-presence is at the response layer.

Cycle #8 leaves `app/recommendations/engine.py` unchanged — `tools_seed`-only. The schema and storage are now in place for #9 to wire up.
