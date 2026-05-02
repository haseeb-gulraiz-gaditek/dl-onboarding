# Proposal: founder-launch-submission-and-verification

## Problem

Mesh is a two-sided platform; cycles #1–#7 built the user side end-to-end (auth, questions, profiles, embeddings, fast match, recommendations, communities). The founder side is dark — Aamir (the early-stage AI founder persona) can sign up but has no way to submit a launch.

Cycle #8 is the first half of the founder flow. It opens submission, builds the admin verification surface, and lays the canonical product-page row in the dedicated `tools_founder_launched` collection. Cycle #9 will then take an approved launch and (a) surface it in user-side communities via a `kind=launch` post, (b) nudge tightest-match users via the concierge, (c) fan it into recommendation results when match score clears the threshold (per the C2 amendment to We Always #3).

Without this cycle, the founder persona has no path through Mesh and the constitutional invariant *"Default to the user side. Founder value scales with user-side trust"* has no founder-side surface to validate.

## Solution

Three new MongoDB collections + ~6 endpoints, with the verification gate behind the existing `require_admin()` allowlist (cycle #3 pattern reused).

**Collections:**
- `launches` — one row per submission. Append-only on resubmission (rejected launch → founder submits a new one).
- `tools_founder_launched` — one row per APPROVED launch. Mirrors `tools_seed` shape but `source: "founder_launch"` and gains `is_founder_launched: true`, `launched_via_id: ObjectId`. Sealed by the constitutional invariant from cycle #3 (no `tools_seed` rows ever bear `source: "founder_launch"`).
- `notifications` — generic in-app inbox row. Cycle #8 only writes `kind: "launch_approved"` rows; cycle #11+ adds the read endpoint and other kinds. (Replaces SMTP for V1 per user call.)

**Endpoints:**

Founder side (`require_role("founder")`):
- `POST /api/founders/launch` — submit. Validates URL + required fields. Inserts a `launches` row with `verification_status: "pending"`.
- `GET /api/founders/launches` — founder lists their own submissions (any status).
- `GET /api/founders/launches/{id}` — founder reads one of their own launches.

Admin side (`require_admin()`):
- `GET /admin/launches` — pending queue, optional `?status=` filter.
- `GET /admin/launches/{id}` — full submission for review.
- `POST /admin/launches/{id}/approve` — flip status to `approved`, derive slug from `product_url`, create `tools_founder_launched` row, write a `launch_approved` notification for the founder.
- `POST /admin/launches/{id}/reject` — flip status to `rejected`, store `rejection_comment`, write a `launch_rejected` notification.

**Founder signup** stays at the existing `/api/auth/signup` (cycle #1) with `role_question_answer="launching_product"`; no new signup endpoint.

**Slug derivation:** parse the product URL's registrable domain, sanitize to lowercase-hyphenated. Collision suffix scans BOTH `tools_seed` AND `tools_founder_launched` to avoid conflicts.

## Scope

**In:**
- 3 collections with indexes.
- 6 endpoints (3 founder + 4 admin — wait 7 total counting list+detail on each side).
- Founder write-block on user-side endpoints already enforced by cycle #1 + #7; no change needed.
- Slug derivation + collision suffix (scans both tool collections).
- Notification rows on approve/reject (no read endpoint yet).
- Resubmission as a NEW `launches` row (append-only).
- Test suite: F-LAUNCH-1..7 covering submission, founder visibility, admin queue + approve + reject + slug + notification, role gating.

**Out:**
- Email / SMTP (deferred; replaced by `notifications` rows for V1).
- Notification *read* endpoint (cycle #11).
- Cross-posting / community feed surface for launches (cycle #9).
- Concierge nudge for launches (cycle #9).
- Recommendation engine fan-in for launches (cycle #9, gated by the C2 amendment).
- Click-through redirect tracking `/r/:launch_id` (cycle #9).
- Founder dashboard analytics (matched count, etc.) (cycle #9 / #10).
- Founder profile editing (V1.5+).
- React frontend for founder side (parallel Claude Design track).

## Risks

1. **Slug collision rate.** Product URLs frequently share registrable domain bits ("ai-something" is everywhere). Mitigation: `-2`, `-3` numeric suffix, scanning both collections. Worst case the slug has a digit; still readable.
2. **Append-only resubmissions clutter the admin queue.** Mitigation: admin queue endpoint defaults to `?status=pending`, hiding rejected/approved rows. Founder lists endpoint shows all of their own.
3. **`tools_founder_launched` shape divergence from `tools_seed`.** Two collections that almost-but-not-quite share a schema is a maintenance hazard for cycle #9's recommendation fan-in. Mitigation: bake the shared fields (slug, name, tagline, description, url, category, labels, vote_score, embedding) into a documented "tool card" contract used by both collections; cycle #9 will reuse `OnboardingToolCard` projection.
4. **Notification rows orphaned without an inbox.** Cycle #11 builds the read endpoint. Until then, notifications are write-only — useful for testing and future use, harmless if ignored.
5. **No email = founder doesn't know they were approved.** Mitigation: documented as the V1 trade-off; cycle #11 plus optional SMTP later. Demo day flow is admin-mediated.
6. **`is_founder_launched` rendering hint** on the canonical product page (system_design promised it). The flag is stored in this cycle; rendering is a frontend concern, deferred.
