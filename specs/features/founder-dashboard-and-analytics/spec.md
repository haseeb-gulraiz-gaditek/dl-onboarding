# Feature: Founder Dashboard + Per-Launch Analytics

> **Cycle of origin:** `founder-dashboard-and-analytics` (archived; see `archive/founder-dashboard-and-analytics/`)
> **Last reviewed:** 2026-05-03
> **Constitution touchpoints:** `principles.md` We Always #2 (*"Treat the user's profile as theirs"* — analytics never expose user identities; aggregate counts only); We Never #2 (*"Never let founder accounts post in user communities"* — read-only dashboard, no founder-side write surfaces into user spaces); Design Tenet 2 (*"Default to the user side"* — when granular per-user data would help the founder but cost user privacy, we choose anonymity).
> **Builds on:** `auth-role-split` (`require_role("founder")`), `founder-launch-submission-and-verification` (`launches.find_for_founder`), `launch-publish-and-concierge-nudge` (`engagements` collection — the source data for every aggregation in this cycle).

> **Read-only feature.** This cycle adds NO new collections, NO new write paths, NO new event sources. Aggregations run on demand against `engagements` rows already being written by cycle #9.

---

## Intent

Cycle #9 fanned approved launches into three user-facing surfaces and wrote `engagements` rows for every meaningful action. Cycle #11 closes the founder feedback loop: Aamir hits "submit," admin approves, fan-out happens, and now he can finally *see* what happened.

Two read endpoints behind `require_role("founder")`:

- **`GET /api/founders/dashboard`** — the founder's launches with summary metrics inline. One row per launch, newest-first.
- **`GET /api/founders/launches/{id}/analytics`** — per-launch detail with `clicks_by_community` and `clicks_by_surface` breakdowns. Ownership-gated: non-owner founders get `404 launch_not_found` (no existence leak).

**Constitutional posture:** every response carries aggregate counts only — never `user_id`, `email`, `display_name`, or any identifying field. Tests recursively scan the JSON for forbidden keys; future field additions that leak identity will fail the audit automatically.

## Surface

**HTTP:** 2 new endpoints (both `GET`, behind `require_role("founder")`).

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/founders/dashboard` | own launches with inline summary metrics |
| GET | `/api/founders/launches/{id}/analytics` | per-launch detail; ownership-gated 404 |

**Internal modules:**
- `app/founders/analytics.py` — five pure-async aggregation helpers; each scoped by `launch_id`.
- `app/api/founders_dashboard.py` — endpoint router.
- `app/models/dashboard.py` — `DashboardLaunchCard`, `DashboardResponse`, `LaunchAnalyticsResponse`. Anonymization invariant baked into the schemas (no user-identity fields exist).

**MongoDB collections:** none new. Reads `engagements` (cycle #9), `launches` (cycle #8). The existing `(launch_id, captured_at DESC)` index covers all aggregation pipelines.

---

## F-DASH-1 — Aggregation helper module

`app/founders/analytics.py` exposes five pure-async helpers. Each is scoped by `launch_id`; each returns a typed zero on empty results (no exceptions, no nulls).

```python
async def matched_count(launch_id: ObjectId) -> int:
    """Distinct users who got a concierge_nudge VIEW (publish-time scan)."""

async def nudge_response_counts(launch_id: ObjectId) -> dict[str, int]:
    """{'tell_me_more': N, 'skip': M} — distinct users per action."""

async def total_clicks(launch_id: ObjectId) -> int:
    """Engagements with action=click (any surface)."""

async def clicks_by_community(launch_id: ObjectId) -> dict[str, int]:
    """Group community_post click engagements by metadata.community_slug."""

async def clicks_by_surface(launch_id: ObjectId) -> dict[str, int]:
    """Group click engagements by surface across all surfaces."""
```

`matched_count` and `nudge_response_counts` use MongoDB `$group` pipelines on `user_id` to enforce **distinct-user** semantics — a single user nudged twice for the same launch counts once.

---

## F-DASH-2 — `GET /api/founders/dashboard`

Behind `require_role("founder")`. Returns the founder's launches (any verification_status), newest-first by `launches.created_at DESC`, with inline summary metrics.

Per-launch aggregations run concurrently via `asyncio.gather`.

Response:
```json
{
  "dashboard": [
    {
      "launch_id": "<oid>",
      "product_url": "https://acme.io",
      "approved_tool_slug": "acme-io",
      "verification_status": "approved",
      "created_at": "...",
      "matched_count": 4,
      "tell_me_more_count": 1,
      "skip_count": 2,
      "total_clicks": 3
    },
    {
      "launch_id": "<oid>",
      "product_url": "https://other.io",
      "approved_tool_slug": null,
      "verification_status": "pending",
      "created_at": "...",
      "matched_count": 0,
      "tell_me_more_count": 0,
      "skip_count": 0,
      "total_clicks": 0
    }
  ]
}
```

Pending and rejected launches appear with all-zero metrics (no fan-out happened). The dashboard does NOT include the deeper breakdowns (`clicks_by_community`, `clicks_by_surface`) — those live on the per-launch analytics endpoint.

**Authentication:**
- Founder caller → returns ONLY their own launches (`founder_user_id == user._id`).
- User caller → `403 role_mismatch`.
- Unauthenticated → `401 auth_required`.

**Anonymization:** zero user-identifying fields. Asserted by `test_dashboard_response_contains_no_user_identifying_fields`.

---

## F-DASH-3 — `GET /api/founders/launches/{id}/analytics`

Behind `require_role("founder")`. Ownership-gated: only the launch's `founder_user_id` author may read it.

**Given** an authenticated founder owns launch `{id}`
**When** they `GET /api/founders/launches/{id}/analytics`
**Then** the system returns `200 OK` with the analytics body below.

**Given** the launch is owned by a DIFFERENT founder
**When** they GET it
**Then** the system returns `404 launch_not_found` (no existence leak; mirrors cycle #8 F-LAUNCH-2).

**Given** the launch_id is malformed or doesn't exist
**Then** the system returns `404 launch_not_found`.

**User caller** → `403 role_mismatch`.
**Unauthenticated** → `401 auth_required`.

Response:
```json
{
  "launch_id": "<oid>",
  "approved_tool_slug": "acme-io",
  "verification_status": "approved",
  "matched_count": 4,
  "tell_me_more_count": 1,
  "skip_count": 2,
  "total_clicks": 3,
  "clicks_by_community": {
    "marketing-ops": 2,
    "weekly-launches": 1
  },
  "clicks_by_surface": {
    "community_post": 3,
    "concierge_nudge": 0
  }
}
```

**Anonymization:** zero user-identifying fields. Asserted by `test_analytics_response_contains_no_user_identifying_fields`.

---

## F-DASH-4 — Empty-launch metrics

**Given** a launch with zero `engagements` rows (e.g., pending, or just-approved with no fan-out yet)
**When** the dashboard or analytics endpoint runs the aggregation
**Then** every count is `0` and every dict is `{}` (empty). No null values, no division-by-zero, no errors.

The aggregation helpers return their type-specific zero (`int(0)` or `dict()`) when MongoDB returns an empty pipeline result.

---

## Anonymization (constitutional invariant)

The analytics surface is the most natural place for a user-identity leak: the founder wants to know who matched. The constitutional answer is *no, only how many*. Three-layer enforcement:

1. **Schema layer:** `DashboardLaunchCard` and `LaunchAnalyticsResponse` have NO field that names a user (no `user_id`, no `email`, no `display_name`).
2. **Helper layer:** `matched_count` / `nudge_response_counts` `$group` by `user_id` then `$count` (or `$sum`) — they consume user_ids but never project them out.
3. **Test layer:** two audit tests recursively walk the response JSON looking for the forbidden key set. A future field addition that leaks identity will fail these tests automatically — no human review required.

**Out of V1 scope (privacy-driven):**
- Decline reasons (skip "why" — aggregate skip count only).
- DM-with-users (founders never write into user-facing surfaces).
- Per-user matched lists or heat maps.
- Retention cohort analysis (V1.5+).
