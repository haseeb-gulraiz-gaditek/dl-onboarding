# Tasks: launch-publish-and-concierge-nudge

## Implementation Checklist

### DB layer
- [ ] `app/db/engagements.py` — collection access + `ensure_indexes()` ((launch_id, captured_at DESC), (user_id, captured_at DESC)); helper `insert(user_id?, launch_id, surface, action, metadata={})`
- [ ] Wire `ensure_engagement_indexes` into `app/main.py` lifespan

### Cycle #8 schema modification (F-LAUNCH-1 MODIFIED)
- [ ] `app/db/launches.py` — `insert()` gains `target_community_slugs` param; persisted on the row
- [ ] `app/models/launch.py` — `LaunchSubmitRequest` gains `target_community_slugs: list[str]` (Field min_length=1, max_length=6); `LaunchResponse` and `LaunchAdminDetail` echo it
- [ ] `app/api/founders.py` POST /launch — validate slugs (length 1..6, each resolves to active community, no duplicates); on failure 400 field_invalid or 400 community_not_found
- [ ] Existing cycle #8 tests need touch-ups: every `submit_test_launch` payload now needs `target_community_slugs`. Update conftest helper default.

### Publish orchestrator
- [ ] `app/launches/publish.py` — `publish_launch(launch_doc, admin_email)` with the 5-step flow:
  1. `embed_text(icp_description)` for the ICP vector
  2. `ensure_tool_embedding(tool_slug)` so the rec fan-in sees it
  3. fan-out: one `posts.insert` per `target_community_slugs` entry (skip silently if community no longer active or list is empty); `attached_launch_id` set; engagement row per post
  4. concierge scan: `similarity_search(collection_name="profiles", weaviate_class=PROFILE_CLASS, query_vector=icp_vec, top_k=5)`; per matched profile → notification (`concierge_nudge`) + engagement (`view`) + bump rec cache expiry to now()
  5. return `{community_posts_count, nudge_count}`
- [ ] Per-step exception handling: log + continue; never abort approval

### Admin approve hook (cycle #8)
- [ ] `app/api/admin_launches.py` — after the existing `insert_fl_tool` and `update_resolution`, call `publish_launch(...)`. Include `publish_summary` in the response model
- [ ] `app/models/launch.py` — `LaunchResponse` gains optional `publish_summary` (only populated on the approve response, not on founder reads); add a sibling `LaunchApproveResponse` if cleaner

### Redirect tracking
- [ ] `app/launches/redirect.py` — `make_user_hash(user_id)` (HMAC-SHA256 with JWT_SECRET, first 16 hex chars); `resolve_user_hash(hash, candidates)` scans recent users
- [ ] `app/api/redirect.py` — `GET /r/{launch_id}?u={hash}&s={surface}` — unauthenticated; resolves user via hash if present; writes engagement; 302 to `launch.product_url`
- [ ] Mount in `app/main.py`; verify it does NOT collide with /api/* prefixes (uses /r/ root)

### Canonical product page
- [ ] `app/api/tools.py` — `GET /api/tools/{slug}` reads tools_seed first, then tools_founder_launched; returns unified card + optional launch metadata for founder-launched tools
- [ ] `app/models/tool_page.py` — `ProductPageResponse` (tool: ToolCard, launch: LaunchMeta | None); ToolCard reuses OnboardingToolCard fields plus `is_founder_launched` and `vote_score`

### Concierge response endpoint
- [ ] `app/api/concierge.py` — `POST /api/concierge/respond` behind require_role("user"). Validates launch_id; writes engagement; for tell_me_more returns `{redirect_url}` with hashed user param

### Recommendation engine fan-in (F-PUB-6 — F-REC-5/6 MODIFIED)
- [ ] `app/recommendations/engine.py` — after existing tools_seed similarity_search, run a parallel one over tools_founder_launched (top_k=5, curation_status=approved); hydrate to RecommendationPick with verdict="try" + generic reasoning; NO gpt-5 call for these
- [ ] `app/db/recommendations.py` — cache schema gains `launch_picks: []`; upsert writes both
- [ ] `app/models/recommendation.py` — `RecommendationsResponse` gains `launches: list[RecommendationPick]` (default empty list)
- [ ] `_build_response` projects both `picks` and `launch_picks` from the cached row; hydrates from BOTH `tools_seed` AND `tools_founder_launched` depending on which collection the slug resolves in (helper: `find_tool_anywhere(slug)`)
- [ ] Update cache invalidation: `is_cache_valid` already covers TTL+invalidation; the publish orchestrator bumps rec cache `cache_expires_at` to now() for matched users

### Wiring
- [ ] Mount routers (redirect, tools, concierge) in `app/main.py`
- [ ] Extend RequestValidationError handler if needed for `target_community_slugs`, `launch_id`, `action`

### Tests
- [ ] F-LAUNCH-1 MODIFIED: submit without target_community_slugs → 400 field_invalid (now required)
- [ ] F-LAUNCH-1 MODIFIED: target_community_slugs containing unknown slug → 400 community_not_found
- [ ] F-LAUNCH-1 MODIFIED: target_community_slugs > 6 → 400 field_invalid
- [ ] F-LAUNCH-1 MODIFIED: target_community_slugs duplicates → 400 field_invalid
- [ ] F-PUB-1: publish_launch writes one engagement per community post with surface="community_post"
- [ ] F-PUB-2: approve fans out posts to ALL target_community_slugs (verify via /api/communities/{slug}/posts feed)
- [ ] F-PUB-2: approve scans profiles via similarity_search and writes top-5 concierge_nudge notifications
- [ ] F-PUB-2: approve bumps recommendations.cache_expires_at to now() for matched users
- [ ] F-PUB-2: failure in fan-out (e.g., one community deleted between submission and approve) does NOT abort approval; partial success is recorded
- [ ] F-PUB-3: GET /r/{launch_id}?u=<valid-hash>&s=concierge_nudge → 302 to product_url + engagement row with user_id
- [ ] F-PUB-3: GET /r/{launch_id} with missing/invalid u → 302 + engagement row with user_id=null
- [ ] F-PUB-3: GET /r/{unknown_id} → 404 launch_not_found
- [ ] F-PUB-4: GET /api/tools/{slug} for tools_seed entry → tool card, is_founder_launched=false, launch=null
- [ ] F-PUB-4: GET /api/tools/{slug} for tools_founder_launched entry → tool card, is_founder_launched=true, launch={founder_email, problem_statement, ...}
- [ ] F-PUB-4: unknown slug → 404 tool_not_found
- [ ] F-PUB-5: POST /api/concierge/respond {action:"tell_me_more"} → engagement + redirect_url
- [ ] F-PUB-5: POST /api/concierge/respond {action:"skip"} → engagement, redirect_url=null
- [ ] F-PUB-5: founder caller → 403; unknown launch → 404
- [ ] F-PUB-6: recommendations response includes `launches: []` (default empty when no launches exist)
- [ ] F-PUB-6: with one approved launch matched against user's profile, response.launches has 1 entry with is_founder_launched=true
- [ ] F-PUB-6: launch picks AND organic picks coexist; verify they're in DIFFERENT response fields (no overlap)
- [ ] F-PUB-6: cache hit re-serves both arrays; cache miss regenerates both
- [ ] F-PUB-7: concierge_nudge notification has correct payload shape (launch_id, tool_slug, score)

### Conftest updates
- [ ] Update `submit_test_launch` default to include `target_community_slugs: ["marketing-ops"]`; add `seed_test_communities` to fixtures used by launch tests
- [ ] `prepare_user_for_recs_with_embedding` reused; new fixture `seed_approved_launch(client, admin_token, target_slugs)` for the publish/recommendation tests

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#8 must continue to pass)
- [ ] Submission smoke: founder submits with target_community_slugs=["marketing-ops","weekly-launches"]; verify launch row stores them
- [ ] Approve smoke: admin approves; verify (a) tool row in tools_founder_launched, (b) two posts in target communities (visible via GET /api/communities/{slug}/posts), (c) up-to-5 concierge_nudge notifications, (d) engagement rows for each
- [ ] Redirect smoke: GET /r/{launch_id}?u=<hash>&s=concierge_nudge → 302 to product_url
- [ ] Recommendation fan-in smoke: user with profile embedding hits POST /api/recommendations → response.launches contains the launch
- [ ] Constitutional check: launches array is structurally separate from recommendations array; never overlapping
- [ ] No constitutional regression: founder still cannot post via /api/posts (cycle #7 invariant); the launch-fanout path is admin-triggered and uses internal posts.insert helper directly
