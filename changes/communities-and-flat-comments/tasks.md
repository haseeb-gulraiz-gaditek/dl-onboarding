# Tasks: communities-and-flat-comments

## Implementation Checklist

### DB layer
- [ ] `app/db/communities.py` — collection access + `ensure_indexes()` (unique on slug, compound on (is_active, category)); helpers `find_by_slug`, `list_active`, `bump_member_count(community_id, delta)`
- [ ] `app/db/community_memberships.py` — collection access + `ensure_indexes()` (unique compound on (user_id, community_id)); helpers `is_member`, `add`, `remove`
- [ ] `app/db/posts.py` — collection access + `ensure_indexes()` (compound (community_id, created_at), (cross_posted_to, created_at), single on author_user_id); helpers `insert`, `find_by_id`, `feed_for_community(community_id, before, limit)`, `bump_comment_count`, `bump_vote_score`
- [ ] `app/db/comments.py` — collection access + `ensure_indexes()` (compound (post_id, created_at)); helpers `insert`, `for_post`, `bump_vote_score`
- [ ] `app/db/votes.py` — collection access + `ensure_indexes()` (unique compound on (user_id, target_type, target_id)); helper `apply_vote(user_id, target_type, target_id, direction)` returning the new direction (0 = removed)
- [ ] Wire all six `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models (Pydantic)
- [ ] `app/models/community.py` — `CommunityResponse`, `CommunityListResponse`, `CommunityDetailResponse` (with is_member)
- [ ] `app/models/post.py` — `PostCreateRequest` (community_slug, cross_post_slugs[], title, body_md), `PostResponse` (with author + user_vote + counts), `PostListResponse`, `PostDetailResponse` (post + inlined comments)
- [ ] `app/models/comment.py` — `CommentCreateRequest`, `CommentResponse`
- [ ] `app/models/vote.py` — `VoteRequest` (target_type literal, target_id, direction literal), `VoteResponse` (voted, current_direction)

### Vote application logic (shared)
- [ ] `app/community/voting.py` — `apply_vote(user_id, target_type, target_id, direction)`:
  - Resolve target row by (target_type, target_id); if not found → return None (caller maps to 400)
  - Look up existing vote
  - Three-way branch: insert / toggle-off / flip-direction
  - Apply `vote_score` delta on the target collection (posts.vote_score, comments.vote_score, tools_seed.vote_score)
  - Returns `{current_direction: int, delta: int}`

### Endpoints
- [ ] `app/api/communities.py` — `GET /api/communities` (list active), `GET /api/communities/{slug}` (with is_member), `POST /api/communities/{slug}/join`, `POST /api/communities/{slug}/leave`
- [ ] `app/api/posts.py` — `POST /api/posts` (create + cross-post validation), `GET /api/communities/{slug}/posts` (newest-first cursor pagination), `GET /api/posts/{id}` (with comments + user_vote)
- [ ] `app/api/comments.py` — `POST /api/comments` (with body validation, post-existence check, comment_count bump, last_activity_at bump)
- [ ] `app/api/votes.py` — `POST /api/votes` dispatching to `apply_vote`
- [ ] Mount all four routers in `app/main.py`
- [ ] Extend the global `RequestValidationError` handler if needed for `title`, `body_md` field-required cases (or rely on the existing `loc[-1] in (...)` branch — extend the tuple if more fields surface)

### Seed
- [ ] `app/seed/communities.json` — 10 hand-authored entries covering role/stack/outcome axes
- [ ] `app/seed/__main__.py` — extend with `communities` subcommand calling a new `app.seed.communities.load()` function (mirrors cycle #3's catalog seeder pattern: idempotent upsert-by-slug, prints inserted/updated/total)
- [ ] `app/db/communities.py` — add `upsert_by_slug(doc)` if not already present (used by the seed CLI)

### Tools seed schema bump
- [ ] No code change required — `vote_score` is added implicitly when first written. Add a brief note at the top of `app/db/tools_seed.py` documenting the field in the schema comment, and reference F-COM-7.

### Tests
- [ ] F-COM-1: `GET /api/communities` lists active sorted by name; founder can also list
- [ ] F-COM-1: `GET /api/communities/{slug}` 404 on unknown slug; returns is_member: false for non-member, true after join
- [ ] F-COM-2: join is idempotent (second call still 200, member_count not double-counted)
- [ ] F-COM-2: leave is idempotent (returns left: false when not a member; member_count floors at 0)
- [ ] F-COM-2: founder cannot join AND cannot leave (both → 403 role_mismatch)
- [ ] F-COM-3: create post with valid body returns 201 + persisted row; `attached_launch_id: null`
- [ ] F-COM-3: cross_post_slugs > 2 → 400 cross_post_invalid
- [ ] F-COM-3: cross_post_slugs containing the home slug → 400 cross_post_invalid
- [ ] F-COM-3: cross_post_slugs duplicates → 400 cross_post_invalid
- [ ] F-COM-3: missing/empty title → 400 field_required(title)
- [ ] F-COM-3: founder cannot create post → 403
- [ ] F-COM-3: unknown community_slug → 404 community_not_found
- [ ] F-COM-4: feed returns newest-first; cursor pagination via ?before&limit works; last page returns next_before: null
- [ ] F-COM-4: feed includes posts that cross-posted INTO the community (not just home community)
- [ ] F-COM-4: GET /api/posts/{id} includes comments newest-first + user_vote
- [ ] F-COM-5: create comment increments post.comment_count and bumps last_activity_at
- [ ] F-COM-5: parent_comment_id from client is silently ignored (stored as null)
- [ ] F-COM-5: empty body_md → 400 field_required(body_md)
- [ ] F-COM-5: founder cannot comment → 403
- [ ] F-COM-6: first vote inserts row + bumps vote_score by direction
- [ ] F-COM-6: re-vote same direction toggles off (deletes row, decrements vote_score)
- [ ] F-COM-6: re-vote opposite direction flips (updates row, vote_score swings 2*direction)
- [ ] F-COM-6: invalid target_id → 400 target_invalid; invalid target_type → 400
- [ ] F-COM-6: founder cannot vote → 403
- [ ] F-COM-7: voting on a tool updates `tools_seed.vote_score`; toggle/flip work for tools too
- [ ] F-COM-8: each write endpoint has a founder-403 test (already covered by F-COM-2..6 founder tests; this is just the audit pass)
- [ ] F-COM-9: seed CLI inserts 10 communities on first run; second run results in 0 inserted, 10 updated; --check would diff (defer to cycle #11+)

### Conftest updates
- [ ] `seed_test_communities` fixture that inserts 3 small communities for endpoint tests
- [ ] `signup_user_and_join(client, email, slugs[])` helper for membership-dependent tests
- [ ] Reuse `signup_founder` helper from cycle #1 for the role-block tests

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#6 must continue to pass)
- [ ] Seed CLI smoke: `python -m app.seed communities` against the live MongoDB Atlas DB, twice — first run inserts 10, second updates 10
- [ ] Endpoint smoke: sign up Maya + a founder; Maya joins a community, posts, comments, upvotes; founder gets 403 on every write endpoint
- [ ] Cross-post smoke: post with `cross_post_slugs: [other-slug]` appears in BOTH community feeds
- [ ] Tool-vote smoke: upvote a tool by id → `tools_seed.vote_score` increments; flip → swings by 2; toggle → returns to 0
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founders blocked from all 5 community write endpoints; reads work for both roles
