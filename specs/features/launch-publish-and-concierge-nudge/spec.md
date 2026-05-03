# Feature: Launch Publish + Concierge Nudge

> **Cycle of origin:** `launch-publish-and-concierge-nudge` (archived; see `archive/launch-publish-and-concierge-nudge/`)
> **Last reviewed:** 2026-05-03
> **Constitution touchpoints:** `principles.md` We Always #3 (the C2 amendment from cycle #8 — launches MAY appear alongside organic recs in a separate slot, gated by match-quality threshold; storage and ranking pipelines stay separate); *"Recommend honestly, including 'skip this.'"* (the concierge nudge surfaces what's wrong via the same skip mechanic); *"Default to the user side"* (founder value scales with user-side trust — even nudges have to be high-signal).
> **Builds on:** `auth-role-split` (`require_role`), `catalog-seed-and-curation` (`tools_seed`/`tools_founder_launched` separation), `weaviate-pipeline` (`embed_text`, `similarity_search`), `fast-onboarding-match-and-graph` (`OnboardingToolCard`), `recommendation-engine` (cache + response shape, both modified here), `communities-and-flat-comments` (`posts.attached_launch_id` field reserved in #7), `founder-launch-submission-and-verification` (the launch row this fans out).

> **Activates the C2 amendment.** The principle was amended at the start of cycle #8 to allow launches to appear in recommendations. Cycle #9 wires the actual fan-in. Storage stays separate (organic in `tools_seed`, launches in `tools_founder_launched`); the engine queries both via parallel `similarity_search`; the response carries them in distinct fields. Founder payments still cannot move an organic ranking score because organics and launches are never in the same ranking pass.

---

## Intent

Cycle #8 opened the founder side but the approved launch sat dormant. Cycle #9 wires it into three user-facing surfaces in a single synchronous fan-out at admin approve:

1. **Community feed.** A `posts` row (no `kind` field — cycle #7 design — but `attached_launch_id` set) appears in each of the founder's 1-6 target communities. Same posts table, same vote/comment surfaces.
2. **Concierge nudge.** Top-5 profile matches by similarity to the launch's ICP embedding get a `concierge_nudge` notification. Their `recommendations` cache is bumped to `now()` so the next call regenerates with the launch in the `launches` slot.
3. **Recommendation slot.** `RecommendationsResponse` gains a `launches` field. The engine runs a parallel `similarity_search` over `tools_founder_launched`, surfacing top-5 by score with no LLM ranker call. NEVER commingled with organic recs.

Plus: an unauthenticated `GET /r/{launch_id}` redirect that logs an `engagements` row and 302s to the product URL; a slim `GET /api/tools/{slug}` canonical product page that reads both tool collections; a `POST /api/concierge/respond` endpoint where the user accepts (`tell_me_more`) or skips a nudge.

## Surface

**HTTP:** 3 new endpoints + 3 modified.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET    | `/r/{launch_id}` | none | unauth redirect; HMAC user-hash; 302 to product_url |
| GET    | `/api/tools/{slug}` | any auth | canonical product page (slim); reads both collections |
| POST   | `/api/concierge/respond` | user | tell_me_more / skip on a nudge |
| POST   | `/api/founders/launch` | founder | MODIFIED: `target_community_slugs` now required (1..6) |
| POST   | `/admin/launches/{id}/approve` | admin | MODIFIED: triggers `publish_launch` orchestrator after the existing tool insert |
| POST   | `/api/recommendations` | user | MODIFIED: response gains `launches` slot |

**Internal modules:**
- `app/db/engagements.py` — write-only event log; CPA-ready for V1.5 billing.
- `app/launches/publish.py` — synchronous 5-step orchestrator (`publish_launch`).
- `app/launches/redirect.py` — `make_user_hash` / `resolve_user_hash` (HMAC-SHA256 keyed on `JWT_SECRET`, 16 hex chars).
- `app/api/redirect.py`, `app/api/tools.py`, `app/api/concierge.py` — endpoint routers.

**MongoDB collections (new):** `engagements`. Plus modifications to existing `launches` (target_community_slugs field), `recommendations` (launch_picks field), and `tools_founder_launched` (embedding lazily populated by `_ensure_fl_tool_embedding`).

---

## F-PUB-1 — `engagements` collection

A new MongoDB collection `engagements` logs per-event signals on launches. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId | null,                  // null when redirect can't resolve
  launch_id: ObjectId,
  surface: "concierge_nudge" | "community_post" | "recommendation_slot" | "product_page" | "redirect",
  action: "click" | "skip" | "tell_me_more" | "view",
  metadata: dict,                             // surface-specific
  captured_at: datetime
}
```

Indexes: `(launch_id, captured_at DESC)` for per-launch analytics, `(user_id, captured_at DESC)` for skip-feedback (V1.5+).

Write-only in V1. No GET endpoint. Future cycles add the founder analytics surface.

---

## F-PUB-2 — Synchronous publish orchestrator

`app/launches/publish.py` exposes `publish_launch(launch_doc, tool_slug)`. Called from `POST /admin/launches/{id}/approve` AFTER the existing tool-row insert (F-LAUNCH-4 step 2) and the launch-row update (step 3).

Steps:

1. **Embed ICP** — `embed_text(launch.icp_description)` (cycle #4 lifecycle).
2. **Embed the founder-launched tool** — `_ensure_fl_tool_embedding(tool_slug)` so the recommendation fan-in (F-PUB-6) has something to query immediately. Note: this is the founder-collection equivalent of cycle #4's `ensure_tool_embedding`, which only handles `tools_seed`.
3. **Fan-out community posts** — for each slug in `launch.target_community_slugs`:
   - Resolve community by slug; skip silently if no longer active.
   - Insert a `posts` row: `community_id` = the community, `cross_posted_to: []`, `author_user_id` = founder, `title` = first 80 chars of `problem_statement`, `body_md` = `problem_statement + "\n\n" + icp_description`, `attached_launch_id` = launch._id.
   - Write an `engagements` row: `surface: "community_post", action: "view"`.
4. **Concierge nudge scan** — `similarity_search(collection_name="profiles", weaviate_class=PROFILE_CLASS, query_vector=icp_vector, top_k=5)`. For each matched profile:
   - Skip if profile.user_id == launch.founder_user_id (defensive).
   - Write `notifications` row: `kind: "concierge_nudge"`, `payload: {launch_id, tool_slug}`.
   - Write `engagements` row: `surface: "concierge_nudge", action: "view"`.
   - Bump `recommendations.cache_expires_at = now()` for that user.
5. **Return summary** — `{community_posts_count, nudge_count}`. The admin approve response includes this as `publish_summary`.

Per-step exceptions are logged but do NOT abort approval. Partial-success is recorded; rollback would be more dangerous.

> **Threshold gate:** top-5 by similarity, no cosine floor. At V1 user counts a fixed cosine floor wouldn't hold weight (most launches would nudge zero users); the `top_k=5` cap is the meaningful limit. V1.5+ may add a learned threshold once user count grows.

---

## F-PUB-3 — `GET /r/{launch_id}` redirect tracking

Unauthenticated. Logs an engagement, 302s to the launch's `product_url`.

Query params:
- `u`: user-hash. HMAC-SHA256 of user_id keyed on `JWT_SECRET`, first 16 hex chars (64 bits). Optional. If present and resolvable, the engagement row gets the user_id.
- `s`: surface — one of `concierge_nudge | community_post | recommendation_slot | product_page`. Defaults to `redirect` if missing or invalid.

**Given** an authenticated client with a known user_id and a valid launch_id
**When** the user clicks `/r/{launch_id}?u={hmac}&s=concierge_nudge`
**Then** the system writes an `engagements` row `{user_id, launch_id, surface: "concierge_nudge", action: "click"}` and returns `302 Found` with `Location: <launch.product_url>`.

**Unknown launch_id** → `404 launch_not_found`.
**Hash unresolvable / missing** → still 302; engagement row gets `user_id: null`.

`make_user_hash(user_id)` and `resolve_user_hash(hash)` live in `app/launches/redirect.py`. The HMAC isn't crypto-grade — an attacker forging clicks gains nothing meaningful, so 64 bits is enough collision-resistance for V1.

---

## F-PUB-4 — `GET /api/tools/{slug}` canonical product page

Open to any authenticated caller. Returns a unified tool card for either `tools_seed` OR `tools_founder_launched`.

Lookup order: `tools_seed` first, then `tools_founder_launched`. First hit wins.

Response:
```json
{
  "tool": {
    "slug": "...",
    "name": "...",
    "tagline": "...",
    "description": "...",
    "url": "...",
    "pricing_summary": "...",
    "category": "...",
    "labels": [...],
    "vote_score": 4,
    "is_founder_launched": false
  },
  "launch": null  // populated only when is_founder_launched=true
}
```

When `is_founder_launched=true`, `launch` contains `{founder_email, founder_display_name, problem_statement, icp_description, approved_at}`.

**Unknown slug** → `404 tool_not_found`.

---

## F-PUB-5 — `POST /api/concierge/respond`

Behind `require_role("user")`. Caller responds to a concierge nudge.

Request: `{launch_id: <oid>, action: "tell_me_more" | "skip"}`.

**Given** an authenticated user has been nudged about a launch
**When** they respond with `tell_me_more`
**Then** the system writes an `engagements` row `{user_id, launch_id, surface: "concierge_nudge", action: "tell_me_more"}` and returns `{"accepted": true, "redirect_url": "/r/<launch_id>?u=<hmac>&s=concierge_nudge"}`.

**On `skip`** — writes an `engagements` row `{action: "skip"}` and returns `{"accepted": true, "redirect_url": null}`.

> **Skip-feedback downweighting deferred to V1.5.** The engagement row is the durable signal for the future implementation; cycle #9 just records.

**Unknown launch_id** → `404 launch_not_found`.
**Founder caller** → `403 role_mismatch`.

---

## F-PUB-6 — Recommendation engine fan-in (activates C2 amendment)

`app/recommendations/engine.py` runs a parallel similarity search over `tools_founder_launched` after the existing `tools_seed` search:

1. After the existing `similarity_search(collection_name="tools_seed", ...)`, run `similarity_search(collection_name="tools_founder_launched", weaviate_class=TOOL_CLASS, query_vector=profile_embedding, top_k=5, filters={"curation_status": "approved"})`.
2. Validate each candidate — skip any without an embedding.
3. Hydrate each into a `RecommendationPick`: `tool` = `OnboardingToolCard` projection (cycle #5 schema), `verdict: "try"`, `reasoning: "New launch matched against your profile."`, `score` = cosine from similarity_search ranking.
4. Return up to 5; **no gpt-5 ranker call** — these surface as-is at low cost AND keep the constitutional principle "Founder payments never move an organic ranking score" intact (organics and launches are never in the same ranking pass).

**Given** a user with a profile embedding and an approved founder-launched tool whose ICP matches
**When** they `POST /api/recommendations`
**Then** the response includes `recommendations: [...]` (organic, gpt-5-ranked) AND `launches: [...]` (up to 5 founder launches by cosine score). The two arrays NEVER share entries.

Cache schema (F-REC-6 MODIFIED): `recommendations` rows gain a `launch_picks` field. Both `picks` and `launch_picks` regenerate together on cache miss; both serve from cache on hit.

`RecommendationsResponse` schema (F-REC-5 MODIFIED): gains a `launches: list[RecommendationPick]` field (default `[]`).

---

## F-PUB-7 — Notification kind: `concierge_nudge`

Extends the `notifications.kind` enum (introduced in F-LAUNCH-8) with `concierge_nudge`. Payload shape:

```json
{
  "launch_id": "<oid>",
  "tool_slug": "..."
}
```

V1 still has no read endpoint; cycle #11 will surface these in the inbox UI. The publish orchestrator (F-PUB-2) writes one row per matched user.

---

## Constitutional boundary (audit trail)

- `tools_seed` is sealed against `source: "founder_launch"` writes (cycle #3 invariant — preserved).
- `tools_founder_launched` is sealed against any other source (cycle #8 inverse seal — preserved).
- The recommendation engine queries BOTH collections via separate `similarity_search` calls; the gpt-5 ranker only sees organic candidates.
- Launches are returned in `RecommendationsResponse.launches`, never in `RecommendationsResponse.recommendations`. Test `test_approved_launch_appears_in_launches_slot` asserts the structural separation.
- Cycle #7's "founder cannot post via /api/posts" invariant is preserved: the launch fanout uses `app.db.posts.insert` directly (an internal helper), not the route. The route gate (`require_role("user")`) is unchanged.
