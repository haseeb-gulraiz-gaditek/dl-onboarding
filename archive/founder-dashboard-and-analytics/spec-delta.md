# Spec Delta: founder-dashboard-and-analytics

## ADDED

### F-DASH-1 — Aggregation helper module

A new module `app/founders/analytics.py` exposes pure-async helpers that aggregate `engagements` rows for one launch. No new collections; reads only.

```python
async def matched_count(launch_id: ObjectId) -> int:
    """Count of distinct users who got a concierge_nudge VIEW
    engagement (the publish-time scan). One per matched user."""

async def nudge_response_counts(launch_id: ObjectId) -> dict[str, int]:
    """Returns {'tell_me_more': N, 'skip': M} from engagement rows
    with surface=concierge_nudge AND action in (tell_me_more, skip).
    Counts distinct user_ids per action."""

async def total_clicks(launch_id: ObjectId) -> int:
    """Count of engagements with action=click for this launch
    (any surface)."""

async def clicks_by_community(launch_id: ObjectId) -> dict[str, int]:
    """Group click engagements with surface=community_post by
    metadata.community_slug. Returns {slug: count}."""

async def clicks_by_surface(launch_id: ObjectId) -> dict[str, int]:
    """Group click engagements by surface across all surfaces.
    Returns {surface: count}."""
```

All five helpers are scoped by `{launch_id}` so the existing
`(launch_id, captured_at DESC)` index covers the queries. Each
helper uses MongoDB's `aggregate` pipeline (or `count_documents` for
the simple cases). At V1 scale (<1000 engagements per launch),
each runs in 10-50ms.

---

### F-DASH-2 — `GET /api/founders/dashboard`

Behind `require_role("founder")`.

Returns a list of the founder's launches (any verification_status), newest-first by `launches.created_at DESC`, with summary metrics inline.

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

Pending and rejected launches still appear with all-zero metrics (no fan-out happened). Approved launches show the actual engagement counts. The dashboard does NOT include the deeper breakdowns (clicks_by_community, clicks_by_surface) — those live on the per-launch analytics endpoint.

**Authentication:**
- Founder caller → returns ONLY their own launches (`founder_user_id == user._id`).
- User caller → `403 role_mismatch`.
- Unauthenticated → `401 auth_required`.

**Anonymization:** the response includes ZERO user-identifying fields. Aggregate counts only.

---

### F-DASH-3 — `GET /api/founders/launches/{id}/analytics`

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

**Anonymization:** zero user-identifying fields. Tests assert this explicitly.

---

### F-DASH-4 — Empty-launch metrics

**Given** a launch with zero `engagements` rows (e.g., pending, or just-approved with no fan-out yet)
**When** the dashboard or analytics endpoint runs the aggregation
**Then** every count is `0` and every dict is `{}` (empty). No null values, no division-by-zero, no errors.

The aggregation helpers return their type-specific zero (`int(0)` or `dict()`) when MongoDB returns an empty pipeline result.

## MODIFIED

(None — cycle #9 already added the `engagements` collection and writes; this cycle only reads.)

## REMOVED

(None.)
