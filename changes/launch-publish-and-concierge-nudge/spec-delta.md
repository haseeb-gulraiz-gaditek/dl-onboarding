# Spec Delta: launch-publish-and-concierge-nudge

## ADDED

### F-PUB-1 — `engagements` collection

A new MongoDB collection `engagements` logs per-event signals on launches. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId | null,                  // null when redirect can't resolve
  launch_id: ObjectId,
  surface: "concierge_nudge" | "community_post" | "recommendation_slot" | "product_page" | "redirect",
  action: "click" | "skip" | "tell_me_more" | "view",
  metadata: dict,                             // surface-specific (e.g., {community_slug, post_id})
  captured_at: datetime
}
```

Indexes: `(launch_id, captured_at DESC)` for per-launch analytics, `(user_id, captured_at DESC)` for skip-feedback (V1.5+).

This collection is WRITE-only in V1. No GET endpoint exposes it; future cycles add the founder analytics surface.

---

### F-PUB-2 — Synchronous publish orchestrator

A new module `app/launches/publish.py` exposes `publish_launch(launch, admin_email)`. Called from `POST /admin/launches/{id}/approve` AFTER the existing tool-row insert (F-LAUNCH-4 step 2) and BEFORE the launch-row update (step 3).

Steps:

1. **Embed ICP** — call `embed_text(launch.icp_description)` (cycle #4 lifecycle). Store the vector for steps 3 and 4.
2. **Embed and publish the launch tool** — call `ensure_tool_embedding` against the just-inserted `tools_founder_launched` row so it's immediately queryable for the recommendation fan-in (F-PUB-6).
3. **Fan-out community posts** — for each slug in `launch.target_community_slugs`:
   - Resolve community by slug; skip silently if no longer active.
   - Insert a `posts` row: `community_id` = the community, `cross_posted_to: []` (single-target per post; the multi-community fan-out is the LIST of posts, not cross-posting), `author_user_id` = founder, `title` = first 80 chars of `problem_statement`, `body_md` = `problem_statement + "\n\n" + icp_description`, `attached_launch_id` = launch._id.
   - Write an `engagements` row: `surface: "community_post", action: "view"` keyed to launch (founder-side analytics).
4. **Concierge nudge scan** — `similarity_search(collection_name="profiles", weaviate_class=PROFILE_CLASS, query_vector=icp_vector, top_k=5)`. For each matched profile:
   - Skip if profile.user_id == launch.founder_user_id (defensive; founders shouldn't have profiles, but defensive nonetheless).
   - Write a `notifications` row: `kind: "concierge_nudge"`, `payload: {launch_id, tool_slug, score}`.
   - Write an `engagements` row: `surface: "concierge_nudge", action: "view"`.
   - Bump `recommendations.cache_expires_at = now()` for that user (so the next call re-runs and includes the new launch).
5. **Return summary** — the admin approve response gains `publish_summary: {community_posts_count, nudge_count}`.

Failures (per step) are logged but do not abort approval. The launch is approved even if a single community post or nudge fails. Documented because the alternative (partial-rollback) is more dangerous than partial-success.

**Latency:** ~1-3s with the V1 user count. Synchronous. If it ever bites, V1.5 swaps in a 202-Accepted + status poll pattern.

---

### F-PUB-3 — `GET /r/{launch_id}` redirect tracking

Unauthenticated endpoint. Logs an engagement, 302s to the launch's `product_url`.

Query params:
- `u`: user-hash (HMAC-SHA256 of user_id keyed on `JWT_SECRET`, first 16 hex chars). Optional. If present and resolvable, the engagement row gets the user_id.
- `s`: surface — one of `concierge_nudge | community_post | recommendation_slot | product_page`. Defaults to `redirect` if missing or invalid.

**Given** an authenticated client with a known user_id and a valid launch_id
**When** the user clicks `/r/{launch_id}?u={hmac}&s=concierge_nudge`
**Then** the system writes an `engagements` row `{user_id, launch_id, surface: "concierge_nudge", action: "click"}` and returns `302 Found` with `Location: <launch.product_url>`.

**Unknown launch_id** → `404 launch_not_found`.
**Approved launch's tool was deleted somehow** → still 302 to `product_url` from the launch row (the URL is the source of truth).
**Hash unresolvable / missing** → still 302; engagement row gets `user_id: null`.

`make_user_hash(user_id)` and `resolve_user_hash(hash)` live in `app/launches/redirect.py`.

---

### F-PUB-4 — `GET /api/tools/{slug}` canonical product page (slim)

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

When `is_founder_launched=true`, `launch` contains:
```json
{
  "founder_email": "aamir@example.com",
  "founder_display_name": "aamir",
  "problem_statement": "...",
  "icp_description": "...",
  "approved_at": "..."
}
```

**Unknown slug** → `404 tool_not_found`.

---

### F-PUB-5 — `POST /api/concierge/respond`

Behind `require_role("user")`. Caller responds to a concierge nudge.

Request:
```json
{
  "launch_id": "<oid>",
  "action": "tell_me_more" | "skip"
}
```

**Given** an authenticated user has been nudged about a launch
**When** they respond with `tell_me_more`
**Then** the system writes an `engagements` row `{user_id, launch_id, surface: "concierge_nudge", action: "tell_me_more"}` and returns `{"redirect_url": "/r/<launch_id>?u=<hmac>&s=concierge_nudge"}`.

**On `skip`** — writes an `engagements` row `{action: "skip"}` and returns `{"redirect_url": null}`. No skip-feedback downweighting in V1 (deferred to V1.5; the engagement row is the durable signal for the future implementation).

**Unknown launch_id** → `404 launch_not_found`.
**Founder caller** → `403 role_mismatch`.

---

### F-PUB-6 — Recommendation engine fan-in (activates C2 amendment)

**Engine change:** `app/recommendations/engine.py` runs a parallel similarity search over `tools_founder_launched` after the existing `tools_seed` search. Logic:

1. After the existing `similarity_search(collection_name="tools_seed", ...)`, run `similarity_search(collection_name="tools_founder_launched", weaviate_class=TOOL_CLASS, query_vector=profile_embedding, top_k=5, filters={"curation_status": "approved"})`.
2. Validate each candidate — drop any without an embedding (degraded similarity = 0.0).
3. Hydrate each into a `RecommendationPick`: `tool` = OnboardingToolCard projection (cycle #5 schema), `verdict: "try"`, `reasoning: "New launch matched against your profile."`, `score` = cosine from similarity_search ranking.
4. Return up to 5; no LLM ranker call — these are surfaced as-is at low cost.

**Cache schema change:** `recommendations` rows gain a `launch_picks` field. On cache hit, both `picks` and `launch_picks` are served; on cache miss, both are regenerated.

**`RecommendationsResponse` change:** gains `launches: list[RecommendationPick]`. Each entry's `tool` has `is_founder_launched=true`. The two arrays NEVER share entries.

The two arrays are returned in the SAME response, but the engine pipelines stay separate: organic ranks via gpt-5; launches do not call gpt-5 (cost + latency saver, also keeps the constitutional principle "Founder payments never move an organic ranking score" intact — launches have no opportunity to influence organic ordering because they're never in the same ranking pass).

**Given** a user with a profile embedding and three approved tools_founder_launched rows with embeddings
**When** they `POST /api/recommendations`
**Then** the response includes `recommendations: [...]` (organic) and `launches: [...]` (up to 5 launches by cosine score, separate field).

---

### F-PUB-7 — Notification kinds: `concierge_nudge`

Extends the `notifications.kind` enum (introduced in F-LAUNCH-8) with `concierge_nudge`. Payload shape:

```json
{
  "launch_id": "<oid>",
  "tool_slug": "...",
  "score": 0.87
}
```

V1 still has no read endpoint; cycle #11 will surface these in the inbox UI. The publish orchestrator (F-PUB-2) writes one row per matched user.

## MODIFIED

### F-LAUNCH-1 — `launches` schema and submission body

**Before:** Submission schema and request body do not include `target_community_slugs`.

**After:** `launches` schema gains:
```
target_community_slugs: [string]   // 1..6 active community slugs picked by founder
```

`POST /api/founders/launch` request body gains:
```
target_community_slugs: list[str]   // required, length 1..6, each must be an active community
```

Validations:
- Length 1..6 → else 400 `field_invalid` field=`target_community_slugs`.
- Each slug must resolve to an `is_active` community → else 400 `community_not_found`.
- Duplicates → 400 `field_invalid` field=`target_community_slugs`.

**Migration:** existing rows from cycle #8 testing read with empty `target_community_slugs`. The publish orchestrator (F-PUB-2 step 3) skips silently when the list is empty.

---

### F-REC-5 — `RecommendationsResponse` shape

**Before:** Response includes `recommendations`, `generated_at`, `from_cache`, `degraded`.

**After:** Response also includes `launches: list[RecommendationPick]` (default `[]`). Per F-PUB-6.

```json
{
  "recommendations": [...],
  "launches": [...],          // NEW: up to 5 founder-launched picks by similarity
  "generated_at": "...",
  "from_cache": false,
  "degraded": false
}
```

Backward compat: clients that ignore the field continue to work; the field always exists (even if empty).

---

### F-REC-6 — `recommendations` collection schema

**Before:** Cache row stores `picks: [...]`.

**After:** Cache row also stores `launch_picks: [...]` (same shape as `picks`). Cache invalidation is shared — both are regenerated together on a cache miss.

## REMOVED

(None.)
