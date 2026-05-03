# Proposal: launch-publish-and-concierge-nudge

## Problem

Cycle #8 opened the founder side: submission, admin verification, the canonical `tools_founder_launched` row. But that row sits dormant — no user ever encounters it. Aamir submits, gets approved, and nothing happens for him or his target users. The "qualified engagement" promise (the whole reason a founder uses Mesh) is unkept.

Cycle #9 wires the publish surface end-to-end. When admin approves a launch, the system fans the launch into three places at once:

1. **Community feed** — a `posts` row in each of the founder's target communities (1-6 picked at submission), `attached_launch_id` set, links to the canonical product page.
2. **Concierge nudge** — Weaviate similarity query against the launch's ICP embedding, top-5 profiles by similarity get a `concierge_nudge` notification.
3. **Recommendations slot** — `POST /api/recommendations` gains a `launches: list[RecommendationPick]` field, populated from the same threshold gate. Activates the C2 amendment to `principles.md` We Always #3 (committed at the start of cycle #8).

Plus a click-tracking redirect (`/r/{launch_id}?u={hash}&s={surface}`) writes an `engagements` row and 302s to the founder's product URL, and a slim canonical product page (`GET /api/tools/{slug}`) returns the tool card + launch metadata + likes count.

## Solution

**Modifications:**
- F-LAUNCH-1 (cycle #8): submission body + schema gain `target_community_slugs: list[str]` (1-6 validated active communities). Existing rows read with empty default.
- F-REC-5 (cycle #6): `RecommendationsResponse` gains `launches: list[RecommendationPick]`. Engine runs a second similarity search over `tools_founder_launched`, keeps top-5 by score, drops anything below a low cosine sanity floor (0.0; effectively no floor, just for safety against negative scores).

**Additions (synchronous fan-out at admin approve):**
- `engagements` collection: per-event log for clicks / dwell / skip / tell_me_more. Schema CPA-ready for V1.5 billing.
- `app/launches/publish.py` — orchestrator called from inside `/admin/launches/{id}/approve` AFTER the existing tool-row + notification work. Steps:
  1. Embed `launch.icp_description` (cycle #4 lifecycle).
  2. Insert one `posts` row per target community (`attached_launch_id` set, no `kind` field — cycle #7 deliberately omitted it).
  3. Similarity search profiles vs the ICP embedding; take top-5 by score.
  4. Write a `concierge_nudge` notification per matched user.
  5. Bump `tools_founder_launched.embedding` via the existing tool-embedding lifecycle (so it's queryable for the recommendation fan-in immediately).
- `GET /r/{launch_id}` — unauthenticated redirect with HMAC user-hash. Writes engagement, 302s to `product_url`.
- `GET /api/tools/{slug}` — slim canonical product page. Reads BOTH `tools_seed` and `tools_founder_launched`; includes `is_founder_launched` flag.
- `POST /api/concierge/respond` — user accepts (`tell_me_more`) or skips (`skip`) a nudge. Writes engagement; for `tell_me_more`, returns the same `/r/{launch_id}?...` redirect URL. (Skip-feedback downweighting deferred to V1.5.)

**Recommendation fan-in:**
- `app/recommendations/engine.py` runs a parallel similarity search over `tools_founder_launched`, applies threshold gate (top-5 by score, no floor for V1).
- Hydrates each launch into a `RecommendationPick` with `verdict: "try"`, generic reasoning ("New launch matched against your profile"), `score` from cosine.
- Cache row gains `launch_picks` field.
- Returned in `RecommendationsResponse.launches` (separate from `recommendations`).

**Engagement helper:**
- `app/launches/redirect.py` — `make_user_hash(user_id)` (HMAC-SHA256 of user_id with `JWT_SECRET`, first 16 hex chars), `resolve_user_hash(hash, candidates?)` (search). For V1 we resolve by scanning recent users with a cached map; constant-time isn't critical for the redirect.

## Scope

**In:**
- 1 new collection (`engagements`).
- 1 new schema field per cycle modification (`launches.target_community_slugs`, `recommendations.launch_picks`, `RecommendationsResponse.launches`).
- 4 new endpoints: `GET /r/{launch_id}`, `GET /api/tools/{slug}`, `POST /api/concierge/respond`, plus the modified `POST /api/founders/launch` validating target communities.
- Synchronous publish orchestrator wired into admin approve.
- Recommendation engine fan-in (top-5 launches by similarity).
- Tests: F-PUB-1..7 covering target communities, fan-out posts, concierge nudges, recommendation slot, redirect tracking, product page, role gating.

**Out:**
- Skip-feedback downweighting (V1.5).
- Dwell-time client beacon + GET /r/.../dwell (V1.5).
- Top-1% high-signal-skip follow-up question (V1.5).
- HN-style hot ranking on launch posts (cycle #7 already deferred).
- Founder UTM preservation in the redirect (V1 — strip nothing, but no UTM injection either).
- Per-community gravity tuning (deferred).
- Background scan on a schedule / re-publish (V1.5+; if the founder edits their ICP later, we don't re-scan).
- Founder analytics dashboard (engagement counts denormalized but no aggregator endpoint).

## Risks

1. **Synchronous publish latency.** Embedding + similarity search + N posts + N notifications inside admin approve. Worst case ~5s with 100s of users, ~12s with 1000s. Mitigation: V1 user count is small; if it bites, switch to a 202-Accepted + status-poll pattern in V1.5.
2. **Recommendation cache invalidation across collections.** When admin approves a launch, all existing `recommendations` cache rows are stale (the new launch should appear in the launches slot for matched users). Mitigation: bump `recommendations.cache_expires_at` to NOW for the matched users at publish time. Documented as a known cost: rec engine re-runs for those users on next call.
3. **HMAC user-hash leak risk.** The `?u=` param is sent in plain URLs. If an attacker can guess hashes for known user_ids, they can impersonate engagement. Mitigation: 16 hex chars (64 bits) of HMAC keyed on `JWT_SECRET` is enough collision resistance for click-tracking; we accept that it's not cryptographically perfect for V1 since an attacker forging clicks doesn't gain much.
4. **`tools_founder_launched.embedding` staleness.** If founder edits their product description (V1.5 feature), the embedding goes stale. Mitigation: nothing in V1 — there's no edit endpoint. Documented.
5. **Constitutional separation.** Founder-launched results ARE in the recommendations response now (per C2 amendment). Risk: a future spec writer assumes commingling is OK and merges them into a single ranked list. Mitigation: tests assert the `launches` field is structurally separate, and the spec calls out the boundary loudly.
6. **Notification flood.** A founder approving 5 launches in a day could generate 25+ nudges per top user. Mitigation: V1 doesn't dedupe — admin queue is naturally slow (24h SLA). V1.5+ can rate-limit per-user.
