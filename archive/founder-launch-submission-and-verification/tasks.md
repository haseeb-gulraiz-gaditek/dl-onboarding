# Tasks: founder-launch-submission-and-verification

## Implementation Checklist

### DB layer
- [x] `app/db/launches.py` — collection access + `ensure_indexes()` (founder_user_id, (verification_status, created_at)); helpers `insert`, `find_by_id`, `find_for_founder(user_id, status?)`, `list_for_admin(status?)`, `update_resolution(id, status, reviewed_by, comment?, slug?)`
- [x] `app/db/tools_founder_launched.py` — collection access + `ensure_indexes()` (unique on slug); helpers `find_by_slug`, `find_by_id`, `insert`. Sealed against `source != "founder_launch"` writes (defensive guard in `insert`)
- [x] `app/db/notifications.py` — collection access + `ensure_indexes()` ((user_id, created_at DESC)); helper `insert(user_id, kind, payload)` (no read endpoint in this cycle)
- [x] Wire all three `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models (Pydantic)
- [x] `app/models/launch.py` — `LaunchSubmitRequest` (product_url, problem_statement, icp_description, existing_presence_links[]), `LaunchResponse` (the founder-facing shape with status), `LaunchListResponse`, `LaunchAdminCard` (queue list with founder_email), `LaunchAdminListResponse`, `LaunchRejectRequest` (comment with min_length=1, max_length=500)

### Slug derivation
- [x] `app/launches/slug.py` — `derive_tool_slug(product_url)` (sync helper) plus `find_available_slug(base)` async helper that scans both collections. Module-level constant `MAX_SLUG_SUFFIX = 99`. Raises `RuntimeError` on exhaustion.

### Endpoints — founder side
- [x] `app/api/founders.py` — `POST /api/founders/launch` (require_role("founder"), validates fields, inserts pending launch), `GET /api/founders/launches` (?status filter), `GET /api/founders/launches/{id}` (404 if not author)

### Endpoints — admin side
- [x] `app/api/admin_launches.py` — `GET /admin/launches` (?status default pending), `GET /admin/launches/{id}` (joined with founder email), `POST /admin/launches/{id}/approve`, `POST /admin/launches/{id}/reject` (uses cycle #3 require_admin)
- [x] On approve: derive slug → insert `tools_founder_launched` → update launch row → write `launch_approved` notification → return updated launch
- [x] On reject: validate comment → update launch row → write `launch_rejected` notification → return updated launch
- [x] Both approve/reject return 409 `launch_already_resolved` if status != "pending"

### Wiring
- [x] Mount both routers (founders, admin_launches) in `app/main.py`
- [x] Extend the global `RequestValidationError` handler for `product_url`, `problem_statement`, `icp_description`, `existing_presence_links` field-required cases (or extend the existing `loc[-1] in (...)` tuple)

### Tests
- [x] F-LAUNCH-1: founder submits valid launch → 201 + persisted row with verification_status="pending"
- [x] F-LAUNCH-1: missing product_url → 400 field_required(product_url)
- [x] F-LAUNCH-1: invalid product_url (not http(s)) → 400 url_invalid
- [x] F-LAUNCH-1: empty problem_statement → 400 field_required(problem_statement)
- [x] F-LAUNCH-1: empty icp_description → 400 field_required(icp_description)
- [x] F-LAUNCH-1: existing_presence_links length > 6 → 400 field_invalid(existing_presence_links)
- [x] F-LAUNCH-1: user role → 403 role_mismatch; unauthenticated → 401 auth_required
- [x] F-LAUNCH-1: founder can submit a SECOND launch after first was rejected (append-only)
- [x] F-LAUNCH-2: GET /api/founders/launches returns only the requesting founder's launches
- [x] F-LAUNCH-2: ?status=approved filter works
- [x] F-LAUNCH-2: GET /api/founders/launches/{id} returns 404 if launch belongs to a different founder
- [x] F-LAUNCH-3: admin queue defaults to status=pending; ?status=approved returns approved
- [x] F-LAUNCH-3: admin detail includes founder_email
- [x] F-LAUNCH-3: non-admin caller → 403 admin_required
- [x] F-LAUNCH-4: approve creates tools_founder_launched row with derived slug + sets is_founder_launched=true + launched_via_id=launch._id
- [x] F-LAUNCH-4: approve updates the launches row (verification_status, reviewed_by, reviewed_at, approved_tool_slug)
- [x] F-LAUNCH-4: approve writes a launch_approved notification for the founder
- [x] F-LAUNCH-4: re-approving an already-approved launch returns 409 launch_already_resolved
- [x] F-LAUNCH-4: approving a rejected launch returns 409 launch_already_resolved
- [x] F-LAUNCH-5: reject without comment → 400 field_required(comment)
- [x] F-LAUNCH-5: reject stores comment + writes launch_rejected notification
- [x] F-LAUNCH-5: rejecting an already-resolved launch returns 409
- [x] F-LAUNCH-6: derive_tool_slug strips www., lowercases, kebab-cases the host
- [x] F-LAUNCH-6: collision in tools_seed forces -2 suffix
- [x] F-LAUNCH-6: collision in tools_founder_launched ALSO forces suffix (cross-collection scan)
- [x] F-LAUNCH-7: tools_founder_launched.insert refuses source != "founder_launch" (defensive guard test)
- [x] F-LAUNCH-8: notifications row has correct shape per kind (launch_approved / launch_rejected)

### Conftest updates
- [x] `signup_founder_with_token(client, email)` helper (mirrors signup_user_and_join from cycle #7)
- [x] `submit_test_launch(client, token, **overrides)` helper for the admin-flow tests
- [x] Use existing `admin_token` fixture from cycle #3 for the admin endpoints

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green: 185 passing (154 prior + 31 new for cycle #8)
- [x] Submission smoke: covered by `test_founder_submit_valid_returns_201_and_pending`
- [x] Admin queue smoke: covered by `test_admin_queue_defaults_to_pending` + `test_approve_creates_founder_launched_tool`
- [x] Slug collision smoke: covered by `test_collision_in_tools_seed_forces_suffix` + `test_collision_in_tools_founder_launched_forces_suffix` (cross-collection scan exercised). Note: actual derived slug for `acme.io` is `acme-io` (host kept kebab-cased; documented in spec)
- [x] Reject smoke: covered by `test_reject_stores_comment_and_writes_notification`
- [x] Constitutional check: `test_tools_founder_launched_refuses_wrong_source` enforces the inverse seal at the helper level (matches cycle #3's `source != "founder_launch"` seal in `tools_seed.upsert_tool_by_slug`); approve path only writes through `insert_fl_tool` with `source: "founder_launch"`
- [x] Spec-delta scenarios verifiably hold in implementation (F-LAUNCH-1..8 each have at least one Given/When/Then-aligned test)
- [x] No constitutional regression: recommendation engine (`app/recommendations/engine.py`) still queries only `tools_seed`; cycle #9 is the cross-over point per the C2 amendment to `principles.md` We Always #3
