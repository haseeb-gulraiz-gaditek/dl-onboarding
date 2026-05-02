# Feature: Communities + Flat Comments + Voting

> **Cycle of origin:** `communities-and-flat-comments` (archived; see `archive/communities-and-flat-comments/`)
> **Last reviewed:** 2026-05-02
> **Constitution touchpoints:** `principles.md` (*"Never let founder accounts post in user communities"* — structurally enforced via `require_role("user")` on every write endpoint; *"Anti-spam is structural, not enforced"* — role-split is the spam fence, no moderation queue or content scanning in V1; *"Default to the user side"* — communities feel like users live there, founders read but don't write).
> **Builds on:** `auth-role-split` (`require_role`), `catalog-seed-and-curation` (`tools_seed.vote_score` denormalized field added by this cycle).

> **Scope deliberately narrow:** No threading, no HN ranking, no moderation queue, no karma gates, no edit/delete, no user-created communities, no notifications fanout. Each was discussed and cut to keep V1 buildable in the demo-day window. Schema reserves `parent_comment_id` and `flagged`/`flag_reasons` for the future expansions.

---

## Intent

Maya doesn't just want recommendations — she wants to live somewhere. Without communities, Mesh is a recommender; recommenders are commodity. The principle "communities feel like users live there" is the moat.

Cycle #7 ships the structural shell: communities (Mesh-staff-spawned), posts with up-to-3-community fan-out via single canonical row, flat comments, and voting that targets posts, comments, OR tools directly (driving the "likes count" on the product page). All five write endpoints sit behind `require_role("user")` so the constitutional invariant "never let founder accounts post in user communities" is enforced at the route boundary, not by content rules.

Cycle #8 (founder-launch) and #9 (launch-publish) build on this surface: a launch becomes a post via `attached_launch_id` (always null in #7), with the founder-side creation flow living on a separate endpoint that bypasses the user-only post route.

## Surface

**HTTP:** 9 endpoints across 4 routers.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET    | `/api/communities` | any auth | list active, sorted by name |
| GET    | `/api/communities/{slug}` | any auth | detail + `is_member` flag |
| POST   | `/api/communities/{slug}/join` | user | idempotent |
| POST   | `/api/communities/{slug}/leave` | user | idempotent; member_count floors at 0 |
| GET    | `/api/communities/{slug}/posts` | any auth | newest-first; `?before&limit` cursor |
| POST   | `/api/posts` | user | `community_slug` + ≤2 `cross_post_slugs` |
| GET    | `/api/posts/{id}` | any auth | post + comments inline + per-target `user_vote` |
| POST   | `/api/comments` | user | flat (parent_comment_id silently null) |
| POST   | `/api/votes` | user | post / comment / tool with three-way semantics |

**Internal modules:**
- `app/db/{communities,community_memberships,posts,comments,votes}.py` — collection access layers + `ensure_indexes()`.
- `app/community/voting.py` — shared `apply_vote()` orchestrating insert / toggle-off / flip across all three target types.
- `app/seed/communities.{py,json}` — idempotent seed CLI for 10 hand-authored communities.
- `app/api/{communities,posts,comments,votes}.py` — endpoint routers.

**MongoDB collections (all created by this cycle):** `communities`, `community_memberships`, `posts`, `comments`, `votes`. Plus a denormalized `vote_score` field on the existing `tools_seed` collection (F-COM-7).

---

## F-COM-1 — `communities` collection + listing endpoints

A new MongoDB collection `communities` stores Mesh-staff-spawned communities. Schema:

```
{
  _id: ObjectId,
  slug: string (unique, lowercase, kebab-case),
  name: string,
  description: string,
  category: "role" | "stack" | "outcome",
  member_count: int (denormalized; bumped by F-COM-2),
  is_active: bool (default true),
  mod_user_ids: [ObjectId] (Mesh staff; empty in V1),
  created_at: datetime
}
```

Unique index on `slug`. Compound index `(is_active, category)` for the listing endpoint.

**Endpoints:**

`GET /api/communities` — open to any authenticated caller (user or founder). Returns active communities sorted by `name` ASC.

`GET /api/communities/{slug}` — open to any authenticated caller. Returns a single community + the requesting user's `is_member` flag.

**Given** an authenticated user
**When** they `GET /api/communities/marketing-ops`
**Then** the system returns `200 OK` with `{community: {...}, is_member: bool}`.

**Unknown slug** → `404 community_not_found`.
**Unauthenticated** → `401 auth_required`.

---

## F-COM-2 — Join / leave membership

A new MongoDB collection `community_memberships` records per-user-community joins. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId,
  community_id: ObjectId,
  joined_at: datetime,
  joined_via: "manual" | "signup_pick" | "concierge_suggestion"
}
```

Unique compound index on `(user_id, community_id)`.

**Endpoints (both behind `require_role("user")`):**

`POST /api/communities/{slug}/join` — idempotent. If already a member, returns 200 with `joined: false`. Otherwise inserts and bumps `communities.member_count` by 1.

`POST /api/communities/{slug}/leave` — idempotent. If not a member, 200 with `left: false`. Otherwise deletes the row and decrements `member_count` (floor 0).

**Founder caller** → `403 role_mismatch` on join AND leave (founders never appear in `community_memberships`).

> NOTE: `add()` uses check-then-insert rather than insert-and-catch-DuplicateKeyError because mongomock-motor doesn't reliably enforce compound unique indexes; the production race window is closed by the unique index on `(user_id, community_id)`.

---

## F-COM-3 — `posts` collection + create endpoint

A new MongoDB collection `posts`. Schema:

```
{
  _id: ObjectId,
  community_id: ObjectId,                  // home community
  cross_posted_to: [ObjectId],              // up to 2 extras; distinct from community_id
  author_user_id: ObjectId,
  title: string (1..200 chars),
  body_md: string (0..10000 chars),
  attached_launch_id: ObjectId | null,      // populated by cycle #8; always null in #7
  vote_score: int (denormalized; default 0; updated by F-COM-6),
  comment_count: int (denormalized; default 0; updated by F-COM-5),
  flagged: bool (default false),
  flag_reasons: [string] (default []),
  created_at: datetime,
  last_activity_at: datetime
}
```

Indexes:
- `(community_id, created_at DESC)` — primary feed query.
- `(cross_posted_to, created_at DESC)` — feed query for cross-posted appearances.
- `author_user_id` — user's post history.

**Endpoint:** `POST /api/posts` behind `require_role("user")`.

Request body:
```json
{
  "community_slug": "marketing-ops",
  "cross_post_slugs": ["weekly-launches"],
  "title": "...",
  "body_md": "..."
}
```

Validations:
- `title`: 1..200 chars (after strip). Empty → 400 `field_required` field=`title`.
- `body_md`: 0..10000 chars.
- `community_slug` must resolve to an active community → else 404 `community_not_found`.
- `cross_post_slugs`: optional, max 2 entries, each must resolve to an active community, all distinct from `community_slug` and each other → else 400 `cross_post_invalid`.

**Given** an authenticated user posts a valid body
**When** they `POST /api/posts`
**Then** the system inserts one row, sets `attached_launch_id: null`, returns `201 Created` with the inserted document.

**Founder caller** → `403 role_mismatch`.

> **Cross-post integrity note:** a single canonical row is shared across home + cross-posted communities. Votes and comments attach to that one row, not per-community copies. Trade-off accepted: ranking integrity > per-community vote signal.

---

## F-COM-4 — Post listing + detail endpoints

`GET /api/communities/{slug}/posts` — newest-first ordering with `_id DESC` as the deterministic tie-breaker (rapid bursts can share a microsecond). Open to any authenticated caller. Pagination: optional `?before=<iso8601>&limit=<int>` cursor on `created_at` (limit 1..50, default 20). Returns posts whose `community_id` matches OR `slug` is in `cross_posted_to`.

```json
{
  "posts": [
    {
      "id": "...",
      "community_slug": "marketing-ops",
      "cross_posted_to": ["weekly-launches"],
      "author": { "id": "...", "display_name": "maya" },
      "title": "...",
      "body_md": "...",
      "vote_score": 4,
      "comment_count": 2,
      "user_vote": 1,
      "attached_launch_id": null,
      "flagged": false,
      "created_at": "...",
      "last_activity_at": "..."
    }
  ],
  "next_before": "2026-05-02T12:00:00Z"
}
```

`user_vote` reflects the requesting user's vote on the post (1, -1, or 0). When the page is the last (response length < limit), `next_before` is `null`.

`GET /api/posts/{id}` — single post + inlined flat comments (newest-first, `_id DESC` tie-break, max 200; pagination deferred).

**Unknown post id** → `404 post_not_found`.
**Unauthenticated** → `401 auth_required`.

---

## F-COM-5 — `comments` collection + create endpoint

A new MongoDB collection `comments`. Schema:

```
{
  _id: ObjectId,
  post_id: ObjectId,
  parent_comment_id: ObjectId | null,       // RESERVED: always null in V1
  author_user_id: ObjectId,
  body_md: string (1..5000 chars),
  vote_score: int (default 0),
  flagged: bool (default false),
  flag_reasons: [string] (default []),
  created_at: datetime
}
```

Index: `(post_id, created_at DESC)`.

**Endpoint:** `POST /api/comments` behind `require_role("user")`.

Validations:
- `body_md`: 1..5000 chars after strip → else 400 `field_required` field=`body_md`.
- `post_id` must resolve to an existing post → else 404 `post_not_found`.

On insert: increments `posts.comment_count` and updates `posts.last_activity_at = now()`. Returns `201 Created` with the new comment.

`parent_comment_id` is silently set to `null` regardless of what the client sends (forward-compat for V1.5 threading; current schema rejects unknown body fields by Pydantic default but the route reads only the declared keys).

**Founder caller** → `403 role_mismatch`.

---

## F-COM-6 — `votes` collection + vote endpoint

A new MongoDB collection `votes`. Schema:

```
{
  _id: ObjectId,
  user_id: ObjectId,
  target_type: "post" | "comment" | "tool",
  target_id: ObjectId,
  direction: 1 | -1,
  cast_at: datetime
}
```

Unique compound index on `(user_id, target_type, target_id)`.

**Endpoint:** `POST /api/votes` behind `require_role("user")`.

Semantics (idempotent + toggle):
- No existing vote → INSERT, target's `vote_score` += direction, return `{voted: true, current_direction: <d>}`.
- Existing vote with same direction → DELETE (toggle off), target's `vote_score` -= direction, return `{voted: false, current_direction: 0}`.
- Existing vote with opposite direction → UPDATE direction, target's `vote_score` += `2*direction`, return `{voted: true, current_direction: <d>}`.

Validations:
- `target_type` must be one of three; `direction` must be ±1; `target_id` must resolve to a row of the corresponding kind → else 400 `target_invalid`.

**Founder caller** → `403 role_mismatch`.

---

## F-COM-7 — Tool voting hooks `tools_seed.vote_score`

When `target_type=tool`, vote_score adjustments described in F-COM-6 are applied to the matching `tools_seed` row's `vote_score` field (added in this cycle to the existing collection; missing-field reads as 0 for legacy rows).

This drives the "likes count" on the product page rendered by future cycles. No new endpoint is exposed — voting on a tool goes through the same `POST /api/votes` as posts and comments. `target_id` accepts the tool's `_id`; slug-based voting is deferred (clients always have the id from F-CAT lookups).

**Given** a tool with `vote_score: 4` and a user who has not voted on it
**When** they `POST /api/votes` with `{target_type: "tool", target_id: "<oid>", direction: 1}`
**Then** the tool's `vote_score` becomes `5`, the response is `{voted: true, current_direction: 1}`.

---

## F-COM-8 — Founder write-block (constitutional)

The principle "Never let founder accounts post in user communities" is enforced structurally on every write endpoint introduced in this cycle:

- `POST /api/communities/{slug}/join`
- `POST /api/communities/{slug}/leave`
- `POST /api/posts`
- `POST /api/comments`
- `POST /api/votes`

All are behind `Depends(require_role("user"))`. Founders calling any of them → `403 role_mismatch`. Read endpoints (`GET /api/communities/*`, `GET /api/posts/{id}`) are open to authenticated callers regardless of role — founders can browse but not write.

This is anti-spam by structure, not by enforcement. There is no content scanner, rate limiter, or moderation queue in V1; the role-split is the spam fence.

---

## F-COM-9 — Seed CLI for 10 starter communities

A new subcommand `python -m app.seed communities` loads `app/seed/communities.json` into the `communities` collection. Idempotent: upsert-by-slug.

10 hand-authored entries cover 3 axes:

- **Role:** marketing-ops, design-shop, engineering-bench, product-loop, creator-studio
- **Stack:** notion-power-users, figma-power-users
- **Outcome:** weekly-launches, side-projects, ai-curious

Each entry: `{slug, name, description, category}`. The CLI prints `[seed-communities] inserted: N, updated: M, total: T`.

**Future expansion path:** the seed file is the source-of-truth artifact. Adding communities = appending to JSON + re-running the CLI. User-created communities are explicitly out of scope for V1 (and probably V1.5+); the surface stays Mesh-curated.
