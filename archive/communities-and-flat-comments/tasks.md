# Tasks: communities-and-flat-comments

## Implementation Checklist

### DB layer
- [x] `app/db/communities.py` — collection access + `ensure_indexes()` (unique on slug, compound on (is_active, category)); helpers `find_by_slug`, `list_active`, `bump_member_count(community_id, delta)`
- [x] `app/db/community_memberships.py` — collection access + `ensure_indexes()` (unique compound on (user_id, community_id)); helpers `is_member`, `add`, `remove`
- [x] `app/db/posts.py` — collection access + `ensure_indexes()` (compound (community_id, created_at), (cross_posted_to, created_at), single on author_user_id); helpers `insert`, `find_by_id`, `feed_for_community(community_id, before, limit)`, `bump_comment_count`, `bump_vote_score`
- [x] `app/db/comments.py` — collection access + `ensure_indexes()` (compound (post_id, created_at)); helpers `insert`, `for_post`, `bump_vote_score`
- [x] `app/db/votes.py` — collection access + `ensure_indexes()` (unique compound on (user_id, target_type, target_id)); helper `apply_vote(user_id, target_type, target_id, direction)` returning the new direction (0 = removed)
- [x] Wire all six `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models (Pydantic)
- [x] `app/models/community.py` — `CommunityResponse`, `CommunityListResponse`, `CommunityDetailResponse` (with is_member)
- [x] `app/models/post.py` — `PostCreateRequest` (community_slug, cross_post_slugs[], title, body_md), `PostResponse` (with author + user_vote + counts), `PostListResponse`, `PostDetailResponse` (post + inlined comments)
- [x] `app/models/comment.py` — `CommentCreateRequest`, `CommentResponse`
- [x] `app/models/vote.py` — `VoteRequest` (target_type literal, target_id, direction literal), `VoteResponse` (voted, current_direction)

### Vote application logic (shared)
- [x] `app/community/voting.py` — `apply_vote(user_id, target_type, target_id, direction)`:
  - Resolve target row by (target_type, target_id); if not found → return None (caller maps to 400)
  - Look up existing vote
  - Three-way branch: insert / toggle-off / flip-direction
  - Apply `vote_score` delta on the target collection (posts.vote_score, comments.vote_score, tools_seed.vote_score)
  - Returns `{current_direction: int, delta: int}`

### Endpoints
- [x] `app/api/communities.py` — `GET /api/communities` (list active), `GET /api/communities/{slug}` (with is_member), `POST /api/communities/{slug}/join`, `POST /api/communities/{slug}/leave`
- [x] `app/api/posts.py` — `POST /api/posts` (create + cross-post validation), `GET /api/communities/{slug}/posts` (newest-first cursor pagination), `GET /api/posts/{id}` (with comments + user_vote)
- [x] `app/api/comments.py` — `POST /api/comments` (with body validation, post-existence check, comment_count bump, last_activity_at bump)
- [x] `app/api/votes.py` — `POST /api/votes` dispatching to `apply_vote`
- [x] Mount all four routers in `app/main.py`
- [x] Extend the global `RequestValidationError` handler if needed for `title`, `body_md` field-required cases (or rely on the existing `loc[-1] in (...)` branch — extend the tuple if more fields surface)

### Seed
- [x] `app/seed/communities.json` — 10 hand-authored entries covering role/stack/outcome axes
- [x] `app/seed/__main__.py` — extend with `communities` subcommand calling a new `app.seed.communities.load()` function (mirrors cycle #3's catalog seeder pattern: idempotent upsert-by-slug, prints inserted/updated/total)
- [x] `app/db/communities.py` — add `upsert_by_slug(doc)` if not already present (used by the seed CLI)

### Tools seed schema bump
- [x] No code change required — `vote_score` is added implicitly when first written. Add a brief note at the top of `app/db/tools_seed.py` documenting the field in the schema comment, and reference F-COM-7.

### Tests
- [x] F-COM-1: `GET /api/communities` lists active sorted by name; founder can also list
- [x] F-COM-1: `GET /api/communities/{slug}` 404 on unknown slug; returns is_member: false for non-member, true after join
- [x] F-COM-2: join is idempotent (second call still 200, member_count not double-counted)
- [x] F-COM-2: leave is idempotent (returns left: false when not a member; member_count floors at 0)
- [x] F-COM-2: founder cannot join AND cannot leave (both → 403 role_mismatch)
- [x] F-COM-3: create post with valid body returns 201 + persisted row; `attached_launch_id: null`
- [x] F-COM-3: cross_post_slugs > 2 → 400 cross_post_invalid
- [x] F-COM-3: cross_post_slugs containing the home slug → 400 cross_post_invalid
- [x] F-COM-3: cross_post_slugs duplicates → 400 cross_post_invalid
- [x] F-COM-3: missing/empty title → 400 field_required(title)
- [x] F-COM-3: founder cannot create post → 403
- [x] F-COM-3: unknown community_slug → 404 community_not_found
- [x] F-COM-4: feed returns newest-first; cursor pagination via ?before&limit works; last page returns next_before: null
- [x] F-COM-4: feed includes posts that cross-posted INTO the community (not just home community)
- [x] F-COM-4: GET /api/posts/{id} includes comments newest-first + user_vote
- [x] F-COM-5: create comment increments post.comment_count and bumps last_activity_at
- [x] F-COM-5: parent_comment_id from client is silently ignored (stored as null)
- [x] F-COM-5: empty body_md → 400 field_required(body_md)
- [x] F-COM-5: founder cannot comment → 403
- [x] F-COM-6: first vote inserts row + bumps vote_score by direction
- [x] F-COM-6: re-vote same direction toggles off (deletes row, decrements vote_score)
- [x] F-COM-6: re-vote opposite direction flips (updates row, vote_score swings 2*direction)
- [x] F-COM-6: invalid target_id → 400 target_invalid; invalid target_type → 400
- [x] F-COM-6: founder cannot vote → 403
- [x] F-COM-7: voting on a tool updates `tools_seed.vote_score`; toggle/flip work for tools too
- [x] F-COM-8: each write endpoint has a founder-403 test (already covered by F-COM-2..6 founder tests; this is just the audit pass)
- [x] F-COM-9: seed CLI inserts 10 communities on first run; second run results in 0 inserted, 10 updated; --check would diff (defer to cycle #11+)

### Conftest updates
- [x] `seed_test_communities` fixture that inserts 3 small communities for endpoint tests
- [x] `signup_user_and_join(client, email, slugs[])` helper for membership-dependent tests
- [x] Reuse `signup_founder` helper from cycle #1 for the role-block tests

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green: 154 passing (119 prior + 35 new for cycle #7)
- [x] Seed CLI smoke: deferred (live Atlas not required for completion); seed loader exercised by `apply_communities_seed` over mongomock in test path. User waved through with /sdd:complete.
- [x] Endpoint smoke: covered by automated tests `test_join_then_leave_decrements_count`, `test_create_post_returns_201_with_persisted_row`, `test_create_comment_increments_post_count_and_last_activity`, `test_first_vote_inserts_and_bumps_score`, plus the founder-403 trio across communities/posts/comments/votes
- [x] Cross-post smoke: covered by `test_feed_includes_cross_posted_into_community` — same canonical post appears in BOTH the home and cross-posted community feeds
- [x] Tool-vote smoke: covered by `test_tool_vote_updates_tools_seed_vote_score` — insert/flip/toggle all exercised against tools_seed.vote_score
- [x] Spec-delta scenarios verifiably hold in implementation (F-COM-1..9 each have at least one test asserting the Given/When/Then)
- [x] No constitutional regression: founders blocked across all 5 write endpoints — `test_founder_cannot_join_or_leave`, `test_founder_cannot_create_post`, `test_founder_cannot_comment`, `test_founder_cannot_vote`. Reads (`GET /api/communities`) verified open to founders by `test_list_communities_open_to_founder`.
