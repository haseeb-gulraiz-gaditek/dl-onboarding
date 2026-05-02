# Tasks: founder-launch-submission-and-verification

## Implementation Checklist

### DB layer
- [ ] `app/db/launches.py` — collection access + `ensure_indexes()` (founder_user_id, (verification_status, created_at)); helpers `insert`, `find_by_id`, `find_for_founder(user_id, status?)`, `list_for_admin(status?)`, `update_resolution(id, status, reviewed_by, comment?, slug?)`
- [ ] `app/db/tools_founder_launched.py` — collection access + `ensure_indexes()` (unique on slug); helpers `find_by_slug`, `find_by_id`, `insert`. Sealed against `source != "founder_launch"` writes (defensive guard in `insert`)
- [ ] `app/db/notifications.py` — collection access + `ensure_indexes()` ((user_id, created_at DESC)); helper `insert(user_id, kind, payload)` (no read endpoint in this cycle)
- [ ] Wire all three `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models (Pydantic)
- [ ] `app/models/launch.py` — `LaunchSubmitRequest` (product_url, problem_statement, icp_description, existing_presence_links[]), `LaunchResponse` (the founder-facing shape with status), `LaunchListResponse`, `LaunchAdminCard` (queue list with founder_email), `LaunchAdminListResponse`, `LaunchRejectRequest` (comment with min_length=1, max_length=500)

### Slug derivation
- [ ] `app/launches/slug.py` — `derive_tool_slug(product_url)` (sync helper) plus `find_available_slug(base)` async helper that scans both collections. Module-level constant `MAX_SLUG_SUFFIX = 99`. Raises `RuntimeError` on exhaustion.

### Endpoints — founder side
- [ ] `app/api/founders.py` — `POST /api/founders/launch` (require_role("founder"), validates fields, inserts pending launch), `GET /api/founders/launches` (?status filter), `GET /api/founders/launches/{id}` (404 if not author)

### Endpoints — admin side
- [ ] `app/api/admin_launches.py` — `GET /admin/launches` (?status default pending), `GET /admin/launches/{id}` (joined with founder email), `POST /admin/launches/{id}/approve`, `POST /admin/launches/{id}/reject` (uses cycle #3 require_admin)
- [ ] On approve: derive slug → insert `tools_founder_launched` → update launch row → write `launch_approved` notification → return updated launch
- [ ] On reject: validate comment → update launch row → write `launch_rejected` notification → return updated launch
- [ ] Both approve/reject return 409 `launch_already_resolved` if status != "pending"

### Wiring
- [ ] Mount both routers (founders, admin_launches) in `app/main.py`
- [ ] Extend the global `RequestValidationError` handler for `product_url`, `problem_statement`, `icp_description`, `existing_presence_links` field-required cases (or extend the existing `loc[-1] in (...)` tuple)

### Tests
- [ ] F-LAUNCH-1: founder submits valid launch → 201 + persisted row with verification_status="pending"
- [ ] F-LAUNCH-1: missing product_url → 400 field_required(product_url)
- [ ] F-LAUNCH-1: invalid product_url (not http(s)) → 400 url_invalid
- [ ] F-LAUNCH-1: empty problem_statement → 400 field_required(problem_statement)
- [ ] F-LAUNCH-1: empty icp_description → 400 field_required(icp_description)
- [ ] F-LAUNCH-1: existing_presence_links length > 6 → 400 field_invalid(existing_presence_links)
- [ ] F-LAUNCH-1: user role → 403 role_mismatch; unauthenticated → 401 auth_required
- [ ] F-LAUNCH-1: founder can submit a SECOND launch after first was rejected (append-only)
- [ ] F-LAUNCH-2: GET /api/founders/launches returns only the requesting founder's launches
- [ ] F-LAUNCH-2: ?status=approved filter works
- [ ] F-LAUNCH-2: GET /api/founders/launches/{id} returns 404 if launch belongs to a different founder
- [ ] F-LAUNCH-3: admin queue defaults to status=pending; ?status=approved returns approved
- [ ] F-LAUNCH-3: admin detail includes founder_email
- [ ] F-LAUNCH-3: non-admin caller → 403 admin_required
- [ ] F-LAUNCH-4: approve creates tools_founder_launched row with derived slug + sets is_founder_launched=true + launched_via_id=launch._id
- [ ] F-LAUNCH-4: approve updates the launches row (verification_status, reviewed_by, reviewed_at, approved_tool_slug)
- [ ] F-LAUNCH-4: approve writes a launch_approved notification for the founder
- [ ] F-LAUNCH-4: re-approving an already-approved launch returns 409 launch_already_resolved
- [ ] F-LAUNCH-4: approving a rejected launch returns 409 launch_already_resolved
- [ ] F-LAUNCH-5: reject without comment → 400 field_required(comment)
- [ ] F-LAUNCH-5: reject stores comment + writes launch_rejected notification
- [ ] F-LAUNCH-5: rejecting an already-resolved launch returns 409
- [ ] F-LAUNCH-6: derive_tool_slug strips www., lowercases, kebab-cases the host
- [ ] F-LAUNCH-6: collision in tools_seed forces -2 suffix
- [ ] F-LAUNCH-6: collision in tools_founder_launched ALSO forces suffix (cross-collection scan)
- [ ] F-LAUNCH-7: tools_founder_launched.insert refuses source != "founder_launch" (defensive guard test)
- [ ] F-LAUNCH-8: notifications row has correct shape per kind (launch_approved / launch_rejected)

### Conftest updates
- [ ] `signup_founder_with_token(client, email)` helper (mirrors signup_user_and_join from cycle #7)
- [ ] `submit_test_launch(client, token, **overrides)` helper for the admin-flow tests
- [ ] Use existing `admin_token` fixture from cycle #3 for the admin endpoints

## Validation

### Automated
- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#7 must continue to pass)
- [ ] Spec-delta scenarios verifiably hold in implementation

### Endpoint smokes (live server, real Mongo Atlas)

> Run after `uvicorn app.main:app --reload --port 8000` is up. Use any HTTP client (curl/Postman/HTTPie). Substitute `<jwt>` and `<launch_id>` between calls.

**1. POST /api/founders/launch (F-LAUNCH-1)**
- [ ] Sign up Aamir: `POST /api/auth/signup` with `role_question_answer="launching_product"` → returns founder JWT
- [ ] `POST /api/founders/launch` with `{product_url, problem_statement, icp_description, existing_presence_links}` → 201 with `verification_status: "pending"`
- [ ] Try same call with `role_type=user` JWT → 403 role_mismatch
- [ ] Try with no Authorization header → 401 auth_required
- [ ] Try with empty `problem_statement` → 400 field_required(problem_statement)
- [ ] Try with `product_url: "not-a-url"` → 400 url_invalid

**2. GET /api/founders/launches + /{id} (F-LAUNCH-2)**
- [ ] Aamir GETs `/api/founders/launches` → list contains his row, newest-first
- [ ] `?status=pending` filter returns the row; `?status=approved` returns empty
- [ ] `GET /api/founders/launches/{id}` for own launch → 200
- [ ] Sign up second founder Tara; have her GET Aamir's `{id}` → 404 launch_not_found

**3. GET /admin/launches + /{id} (F-LAUNCH-3)**
- [ ] As `admin@example.com`, `GET /admin/launches` → defaults to status=pending; row visible
- [ ] `GET /admin/launches/{id}` includes `founder_email: "aamir@example.com"`
- [ ] As non-admin user → 403 admin_required

**4. POST /admin/launches/{id}/approve (F-LAUNCH-4)**
- [ ] Admin approves Aamir's launch → 200 with updated launch (`approved_tool_slug` populated)
- [ ] Verify `tools_founder_launched` has the row with `is_founder_launched: true`, `launched_via_id: <launch_id>`, `source: "founder_launch"`
- [ ] Verify `notifications` has a `launch_approved` row for Aamir's user_id
- [ ] Re-approve same launch → 409 launch_already_resolved

**5. POST /admin/launches/{id}/reject (F-LAUNCH-5)**
- [ ] Aamir submits a SECOND launch (append-only test) → 201
- [ ] Admin rejects with `{comment: "ICP too vague"}` → 200 with `rejection_comment` stored
- [ ] Verify `notifications` has a `launch_rejected` row
- [ ] Reject without comment → 400 field_required(comment)
- [ ] Re-reject already-rejected → 409 launch_already_resolved
- [ ] Aamir submits a THIRD launch (append-only after rejection) → 201

**6. Slug collision smoke (F-LAUNCH-6)**
- [ ] Pick an existing seed slug (e.g., `cursor`); submit a launch with `product_url: "https://cursor.com"` → approve → verify new tool's slug is `cursor-2`
- [ ] Submit another launch with same domain → approve → verify slug is `cursor-3`

**7. Constitutional checks**
- [ ] `db.tools_seed.countDocuments({source: "founder_launch"})` === 0 — cycle #3 invariant intact
- [ ] `db.tools_founder_launched.countDocuments({source: {$ne: "founder_launch"}})` === 0 — F-LAUNCH-7 inverse seal intact
- [ ] `POST /api/recommendations` for Maya does NOT include any founder-launched tools (cycle #9 is the cross-over per the C2 amendment)
- [ ] `POST /api/onboarding/match` for Maya does NOT include any founder-launched tools

### Idempotency / re-runs
- [ ] Restart the server; re-fetch `/api/founders/launches` → same rows visible (Mongo persistence working)
- [ ] Run any test that touched the DB twice — no schema drift, no orphan rows
