# Tasks: founder-dashboard-and-analytics

## Implementation Checklist

### Aggregation helpers (F-DASH-1)
- [x] `app/founders/__init__.py` — empty package init
- [x] `app/founders/analytics.py` — five async helpers: `matched_count`, `nudge_response_counts`, `total_clicks`, `clicks_by_community`, `clicks_by_surface`. Each scoped by launch_id. Uses MongoDB `aggregate` pipelines or `count_documents` for simple counts. All return zero-typed values on empty result.

### Pydantic models
- [x] `app/models/dashboard.py` — `DashboardLaunchCard` (launch_id, product_url, approved_tool_slug, verification_status, created_at, matched_count, tell_me_more_count, skip_count, total_clicks); `DashboardResponse` (dashboard: list[card]); `LaunchAnalyticsResponse` (launch_id, approved_tool_slug, verification_status, all the headline counts + clicks_by_community + clicks_by_surface dicts)

### Endpoints
- [x] `app/api/founders_dashboard.py` — `GET /api/founders/dashboard` behind require_role("founder"). Resolves the founder's launches via existing `find_for_founder`; runs aggregation helpers per launch concurrently (asyncio.gather); projects into DashboardLaunchCard list.
- [x] `app/api/founders_dashboard.py` — `GET /api/founders/launches/{id}/analytics` behind require_role("founder"). Ownership-gates: 404 if launch not found OR founder_user_id != user._id. Runs the helpers and projects into LaunchAnalyticsResponse.

### Wiring
- [x] Mount the new router in `app/main.py`
- [x] No request-body validation needed (both endpoints are GET); RequestValidationError handler unchanged

### Tests
- [x] F-DASH-1: matched_count counts distinct nudge VIEW engagements
- [x] F-DASH-1: nudge_response_counts returns {tell_me_more, skip} keys with correct counts
- [x] F-DASH-1: total_clicks counts engagements with action=click across surfaces
- [x] F-DASH-1: clicks_by_community groups community_post click engagements by metadata.community_slug
- [x] F-DASH-1: clicks_by_surface groups click engagements by surface
- [x] F-DASH-1: every helper returns zero/empty when no engagements exist for the launch
- [x] F-DASH-2: GET /api/founders/dashboard returns ONLY the requesting founder's launches (not other founders')
- [x] F-DASH-2: dashboard ordered by launches.created_at DESC
- [x] F-DASH-2: pending and rejected launches appear with all-zero metrics
- [x] F-DASH-2: approved launch with engagements shows correct matched/click/nudge counts
- [x] F-DASH-2: user role → 403 role_mismatch; unauthenticated → 401 auth_required
- [x] F-DASH-3: owner founder → 200 with full analytics body
- [x] F-DASH-3: non-owner founder (different founder) → 404 launch_not_found
- [x] F-DASH-3: malformed launch_id → 404 launch_not_found
- [x] F-DASH-3: unknown launch_id → 404 launch_not_found
- [x] F-DASH-3: user caller → 403 role_mismatch
- [x] F-DASH-3: clicks_by_community + clicks_by_surface dicts correctly populated for an approved launch with mixed engagement metadata
- [x] F-DASH-4: empty-engagements launch → all-zero metrics, no errors
- [x] **Anonymization audit**: scan the dashboard + analytics responses byte-for-byte for any field name in {user_id, email, display_name, name, founder_user_id}; assert NONE appear in either response

### Conftest updates
- [x] `seed_engagements_for_launch(launch_id, user_ids, ...)` helper to set up varied engagement rows for the aggregation tests
- [x] Reuse existing `submit_test_launch` + admin approve flow from cycle #8

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#10 must continue to pass)
- [ ] Smoke: founder approves a launch with target_community_slugs=["marketing-ops"]; sign up 3 users; have one click /r/{id}, one tell_me_more, one skip; GET /api/founders/dashboard shows the correct counts
- [ ] Smoke: GET /api/founders/launches/{id}/analytics returns clicks_by_community with the expected breakdown
- [ ] Anonymization smoke: inspect the JSON response — confirm no user_id, no email, no display_name appears anywhere
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founders see ONLY their own launches; analytics reveal aggregate counts only; non-owner founders cannot enumerate launch existence (404 not 403)
