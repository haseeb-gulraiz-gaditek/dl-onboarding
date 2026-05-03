# Proposal: founder-dashboard-and-analytics

## Problem

Cycle #9 fans an approved launch into three user-facing surfaces (community feed, concierge nudges, recommendation slot) and writes engagement rows for every meaningful action. But the founder — Aamir, the launch author — has no way to see the result of all that fan-out. He approves a launch, hits send (figuratively), and silence. The "qualified engagement" promise is unverifiable from his side.

Without a dashboard, the founder can't:
- Tell whether a launch is performing.
- Distinguish a launch with high reach (clicks across communities) from one with deep engagement (concierge nudges → tell_me_more → click).
- Decide whether his next launch should target the same communities or different ones.

This cycle gives founders a read-only analytics surface backed by the existing `engagements` collection. No new state, no Celery — synchronous MongoDB aggregation per request. At V1 scale (<1000 engagements per launch) this is well under 100ms.

## Solution

Two new endpoints behind `require_role("founder")`:

- `GET /api/founders/dashboard` — list of the founder's launches with summary metrics inline (matched count, click count, nudge response counts). One row per launch, newest-first.
- `GET /api/founders/launches/{id}/analytics` — per-launch detail view. Same headline metrics + `clicks_by_community` and `clicks_by_surface` breakdowns. Ownership-gated: non-author returns `404 launch_not_found` (no existence leak, mirrors cycle #8 F-LAUNCH-2 pattern).

**Aggregation:** read-time via MongoDB aggregation pipelines on `engagements`. The pipelines are launch-scoped (`{launch_id: <oid>}` filter), so the existing `(launch_id, captured_at DESC)` index covers them. No denormalized counters; no new collections.

**Anonymization (constitutional):** analytics responses NEVER include `user_id`, `email`, `display_name`, or any identifying field. Aggregate counts only. The principle *"Treat the user's profile as theirs"* applies at the analytics layer — founders see how many users matched, never which.

**Out of scope from the backlog item:**
- Dwell-time histogram — cycle #9 deferred the dwell beacon to V1.5; we have no data to histogram. Documented.
- Decline reasons — privacy boundary; aggregate skip count only.
- DM-with-users — no founder-to-user direct messaging in V1 (constitutional: founders don't write into user surfaces).
- Retention cohort analysis — V1.5+.

## Scope

**In:**
- 2 new endpoints + 1 shared aggregation helper module.
- MongoDB aggregation pipelines: matched count, click count, per-community clicks, per-surface clicks, nudge response counts.
- Pydantic models: `DashboardLaunchCard`, `DashboardResponse`, `LaunchAnalyticsResponse`.
- Tests: F-DASH-1..6 covering dashboard list, analytics detail, ownership gate, role gate, anonymization audit, empty-engagements case (zero divisions).

**Out:**
- Dwell-time histogram (deferred — no source data).
- Decline reasons (privacy).
- Founder DM (anti-spam principle).
- Retention cohort (V1.5+).
- Denormalized counters (premature optimization).
- Real-time push (polling is fine; founder dashboard is not a high-frequency surface).
- Frontend (parallel React track).

## Risks

1. **Aggregation latency at scale.** V1 expects <1000 engagements per launch; pipeline runs in 10-50ms. If a single founder posts hundreds of launches with high traffic each, dashboard load time grows linearly. Mitigation: V1.5+ swaps to denormalized counters when this hits.
2. **Anonymization regressions on future field additions.** Tests assert no user-identifying fields in responses; a future field that leaks user data needs explicit test coverage. Documented in spec.
3. **Cycle #9 exception swallowing.** publish_launch swallows per-step errors, so `matched_count` from the dashboard can be lower than expected if the concierge scan partially failed. The dashboard reports what's actually in `engagements` — accurate, just not always equal to "intent." Documented.
4. **Empty-launch edge case.** A launch with zero engagements returns all-zero metrics, not 404. Test covers this. Division-by-zero in any rate calculation is guarded.
5. **Ownership leak via id enumeration.** Non-author founder hitting `/api/founders/launches/{id}/analytics` MUST get 404, not 403, to avoid confirming the launch exists. Mirrors cycle #8 F-LAUNCH-2.
