# Spec Delta: communities-and-flat-comments

## ADDED

### F-COM-1 — `communities` collection + listing endpoints

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

```json
{
  "communities": [
    { "slug": "marketing-ops", "name": "Marketing Ops", "description": "...", "category": "role", "member_count": 0 }
  ]
}
```

`GET /api/communities/{slug}` — open to any authenticated caller. Returns a single community + the requesting user's `is_member` flag.

**Given** an authenticated user
**When** they `GET /api/communities/marketing-ops`
**Then** the system returns `200 OK` with `{community: {...}, is_member: bool}`.

**Unknown slug** → `404 community_not_found`.
**Unauthenticated** → `401 auth_required`.

---

### F-COM-2 — Join / leave membership

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

`POST /api/communities/{slug}/join` — idempotent. If already a member, returns 200 with the existing row. Otherwise inserts and bumps `communities.member_count` by 1.

`POST /api/communities/{slug}/leave` — idempotent. If not a member, 200 with `{left: false}`. Otherwise deletes the row and decrements `member_count` (floor 0).

**Founder caller** → `403 role_mismatch` on join AND leave (founders never appear in `community_memberships`).

---

### F-COM-3 — `posts` collection + create endpoint

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
  "cross_post_slugs": ["productivity-tools"],
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

---

### F-COM-4 — Post listing + detail endpoints

`GET /api/communities/{slug}/posts` — newest-first ordering. Open to any authenticated caller. Pagination: optional `?before=<iso8601>&limit=<int>` cursor on `created_at` (limit 1..50, default 20). Returns posts whose `community_id` matches OR `slug` is in `cross_posted_to`.

```json
{
  "posts": [
    {
      "id": "...",
      "community_slug": "marketing-ops",
      "cross_posted_to": ["productivity-tools"],
      "author": { "id": "...", "display_name": "maya" },
      "title": "...",
      "body_md": "...",
      "vote_score": 4,
      "comment_count": 2,
      "user_vote": 1,
      "created_at": "...",
      "last_activity_at": "..."
    }
  ],
  "next_before": "2026-05-02T12:00:00Z"
}
```

`user_vote` reflects the requesting user's vote on the post (1, -1, or 0).

`GET /api/posts/{id}` — single post + inlined flat comments (newest-first, max 200; pagination deferred to V1.5).

```json
{
  "post": { ...same shape... },
  "comments": [
    { "id": "...", "author": {...}, "body_md": "...", "vote_score": 1, "user_vote": 0, "created_at": "..." }
  ]
}
```

**Unknown post id** → `404 post_not_found`.
**Unauthenticated** → `401 auth_required`.

---

### F-COM-5 — `comments` collection + create endpoint

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

Request:
```json
{ "post_id": "<id>", "body_md": "..." }
```

Validations:
- `body_md`: 1..5000 chars after strip → else 400 `field_required` field=`body_md`.
- `post_id` must resolve to an existing post → else 404 `post_not_found`.

On insert: increments `posts.comment_count` and updates `posts.last_activity_at = now()`. Returns `201 Created` with the new comment.

`parent_comment_id` is silently set to `null` regardless of what the client sends (forward-compat for V1.5 threading).

**Founder caller** → `403 role_mismatch`.

---

### F-COM-6 — `votes` collection + vote endpoint

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

Request:
```json
{ "target_type": "post", "target_id": "<id>", "direction": 1 }
```

Semantics (idempotent + toggle):
- No existing vote → insert, increment target's `vote_score` by `direction`, return `{voted: true, current_direction: <d>}`.
- Existing vote with same direction → DELETE (toggle off), decrement target's `vote_score` by `direction`, return `{voted: false, current_direction: 0}`.
- Existing vote with opposite direction → UPDATE direction, adjust target's `vote_score` by `2*direction`, return `{voted: true, current_direction: <d>}`.

Validations:
- `target_type` must be one of three; `direction` must be ±1; `target_id` must resolve to a row of the corresponding kind → else 400 `target_invalid`.

**Founder caller** → `403 role_mismatch`.

---

### F-COM-7 — Tool voting hooks `tools_seed.vote_score`

When `target_type=tool`, vote_score adjustments described in F-COM-6 are applied to the matching `tools_seed` row's `vote_score` field. The field is added to the `tools_seed` schema with default 0 (existing rows continue to read as 0 due to MongoDB's missing-field semantics).

This drives the "likes count" on the product page rendered by future cycles. No new endpoint is exposed — voting on a tool goes through the same `POST /api/votes` as posts and comments.

**Given** a tool with `vote_score: 4` and a user who has not voted on it
**When** they `POST /api/votes` with `{target_type: "tool", target_id: <slug or id>, direction: 1}`
**Then** the tool's `vote_score` becomes `5`, the response is `{voted: true, current_direction: 1}`.

> NOTE: `target_id` for tools accepts the tool's `_id`. Slug-based voting is deferred (clients always have the id from F-CAT lookups).

---

### F-COM-8 — Founder write-block

The constitutional principle "Never let founder accounts post in user communities" is enforced structurally on every write endpoint introduced in this cycle:

- `POST /api/communities/{slug}/join`
- `POST /api/communities/{slug}/leave`
- `POST /api/posts`
- `POST /api/comments`
- `POST /api/votes`

All are behind `Depends(require_role("user"))`. Founders calling any of them → `403 role_mismatch`. Read endpoints (`GET /api/communities/*`, `GET /api/posts/{id}`) are open to authenticated callers regardless of role.

---

### F-COM-9 — Seed CLI for 10 starter communities

A new subcommand `python -m app.seed communities` loads `app/seed/communities.json` into the `communities` collection. Idempotent: upsert-by-slug. Hand-authored 10-entry seed file shipped in this cycle, covering 3 axes:

- **Role:** marketing-ops, design, engineering, product-management, content-creation
- **Stack:** notion-power-users, figma-power-users
- **Outcome:** weekly-launches, side-projects, ai-curious

Each entry: `{slug, name, description, category}`. Description is one sentence (~15 words). The CLI prints `[seed-communities] inserted: N, updated: M, total: T`.

## MODIFIED

### `tools_seed` schema (cycle #3)

**Before:** Schema does not include a `vote_score` field.
**After:** Schema includes `vote_score: int (default 0)`. Existing rows read as 0 via MongoDB's missing-field semantics; no migration required. Field is updated by F-COM-7 when a user votes on a tool.

## REMOVED

(None.)
