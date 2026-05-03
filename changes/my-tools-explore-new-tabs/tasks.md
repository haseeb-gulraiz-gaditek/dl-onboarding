# Tasks: my-tools-explore-new-tabs

## Implementation Checklist

### DB layer
- [ ] `app/db/user_tools.py` — collection access + `ensure_indexes()` (unique compound (user_id, tool_id), (user_id, last_updated_at DESC)); helpers `find(user_id, tool_id)`, `list_for_user(user_id, status?)`, `upsert_auto_from_profile(user_id, tool_id)`, `upsert_explicit(user_id, tool_id, status)`, `update_status(user_id, tool_id, status)`, `delete(user_id, tool_id)` returning bool
- [ ] Wire `ensure_user_tools_indexes` into `app/main.py` lifespan

### Shared tool resolver (F-TOOL-2)
- [ ] `app/tools_resolver.py` — `find_tool_anywhere(slug_or_id)` returns `(doc, is_founder_launched)`; accepts both string slug and ObjectId
- [ ] `app/recommendations/engine.py` — refactor to import `find_tool_anywhere` from the new shared module; remove the inline `_find_tool_anywhere` helper

### Pydantic models
- [ ] `app/models/user_tool.py` — `UserToolSaveRequest` (tool_slug, status?), `UserToolPatchRequest` (status), `UserToolCard` (id, tool: ToolCardWithFlags, source, status, dates), `UserToolListResponse`, `DeleteToolResponse` (deleted: bool)
- [ ] `app/models/tool_card.py` — `ToolCardWithFlags` extends `OnboardingToolCard` with `vote_score: int`, `is_founder_launched: bool`. Reuse this in F-TOOL-8/9 responses.
- [ ] `app/models/launches_browse.py` — `BrowsedLaunchCard` (tool, launch_meta with founder_display_name + problem_statement + approved_at, in_my_communities), `BrowsedLaunchListResponse`

### Endpoints — me/tools
- [ ] `app/api/me_tools.py` — `POST /api/me/tools` (explicit save), `DELETE /api/me/tools/{tool_id}`, `PATCH /api/me/tools/{tool_id}` (status flip), `GET /api/me/tools` (list with optional status filter, hydrated, orphans dropped silently)

### Endpoint — explore (organic catalog)
- [ ] `app/api/tools_browse.py` — `GET /api/tools` reads tools_seed only, filters by category/label/q (substring on name+tagline), curation_status="approved", alphabetical with cursor pagination on name; require_role("user")

### Endpoint — new (launches with default join filter)
- [ ] `app/api/launches_browse.py` — `GET /api/launches` reads tools_founder_launched joined with launches; default filter on user's joined community memberships intersect target_community_slugs; ?all=true escape hatch; computes in_my_communities per launch; require_role("user")

### Auto-populate hook (F-TOOL-7 + F-QB-3 MODIFIED)
- [ ] `app/me/auto_populate_tools.py` (or inline in answers handler) — `auto_populate_from_answer(user_id, question_doc, answer_value)`: only fires for kind="multi_select"; resolves each value via find_tool_anywhere; calls user_tools.upsert_auto_from_profile per resolved tool; per-row exception logged + swallowed
- [ ] `app/api/answers.py` — invoke the hook AFTER existing persistence+invalidation; never aborts the response

### Wiring
- [ ] Mount routers (me_tools, tools_browse, launches_browse) in `app/main.py`
- [ ] Extend RequestValidationError handler if needed for `tool_slug`, `status`, `category`, `label`, `q`, `before`, `limit`, `all`

### Tests
- [ ] F-TOOL-1: user_tools collection has unique (user_id, tool_id) — second insert with same pair updates instead of duplicates
- [ ] F-TOOL-2: find_tool_anywhere returns (doc, false) for tools_seed entries; (doc, true) for tools_founder_launched entries; (None, False) for unknown
- [ ] F-TOOL-3: POST /api/me/tools with valid slug → 201 + row inserted with source=explicit_save
- [ ] F-TOOL-3: POST /api/me/tools when row already exists with auto_from_profile → 200 + source promoted to explicit_save
- [ ] F-TOOL-3: unknown slug → 404 tool_not_found
- [ ] F-TOOL-3: invalid status → 400 field_invalid
- [ ] F-TOOL-3: founder caller → 403 role_mismatch
- [ ] F-TOOL-4: DELETE removes the row → {deleted: true}
- [ ] F-TOOL-4: DELETE when no row exists → {deleted: false} (idempotent)
- [ ] F-TOOL-5: PATCH updates status; preserves source
- [ ] F-TOOL-5: PATCH when row missing → 404 tool_not_in_mine
- [ ] F-TOOL-6: GET /api/me/tools returns rows in last_updated_at DESC order
- [ ] F-TOOL-6: ?status filter narrows results
- [ ] F-TOOL-6: orphaned rows (tool deleted/rejected) silently dropped from response
- [ ] F-TOOL-7: multi_select answer with all-resolving slugs auto-populates user_tools (one row per slug)
- [ ] F-TOOL-7: multi_select with mixed resolving + non-resolving slugs only inserts the resolvers
- [ ] F-TOOL-7: re-answering same multi_select is idempotent (no duplicate rows)
- [ ] F-TOOL-7: explicit_save row is NOT demoted by a subsequent auto_from_profile pass
- [ ] F-TOOL-7: free_text answer never triggers auto-populate
- [ ] F-TOOL-7: single_select answer never triggers auto-populate
- [ ] F-TOOL-7: hook failure (e.g., DB error during one upsert) does NOT abort POST /api/answers
- [ ] F-TOOL-8: GET /api/tools defaults to alphabetical first 20; ?before cursor pagination works; last page has next_before=null
- [ ] F-TOOL-8: ?category filter narrows; ?label membership filter narrows; ?q substring matches both name and tagline
- [ ] F-TOOL-8: pending/rejected tools excluded
- [ ] F-TOOL-8: tools_founder_launched entries are NOT in this response (constitutional: organic only)
- [ ] F-TOOL-8: founder caller → 403
- [ ] F-TOOL-9: default GET /api/launches returns only launches whose target_community_slugs intersect user's memberships
- [ ] F-TOOL-9: ?all=true returns all approved launches; in_my_communities reflects intersection (possibly empty)
- [ ] F-TOOL-9: user with zero memberships gets empty list on default; full list on ?all=true
- [ ] F-TOOL-9: each item includes tool card + launch_meta + in_my_communities
- [ ] F-TOOL-9: founder caller → 403

### Conftest updates
- [ ] `seed_user_tools_question` fixture: a multi_select question whose option values are valid catalog slugs (use seed_test_catalog or a small inline subset)
- [ ] `signup_user_with_membership(client, email, slug)` reuse from cycle #7
- [ ] `seed_approved_launch_with_communities` fixture for F-TOOL-9 tests

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#9 must continue to pass)
- [ ] Smoke: as Maya, answer a multi_select question whose values are catalog slugs; GET /api/me/tools shows them with source=auto_from_profile, status=using
- [ ] Smoke: POST /api/me/tools {tool_slug:"<auto-added>", status:"saved"} promotes source to explicit_save
- [ ] Smoke: DELETE /api/me/tools/{tool_id} removes; second DELETE returns deleted:false
- [ ] Smoke: GET /api/tools?category=design&label=all_time_best returns only matching seed rows; founder-launched tools NOT in the list
- [ ] Smoke: founder approves a launch with target_community_slugs=["marketing-ops"]; Maya joins marketing-ops; GET /api/launches shows the launch; user without membership gets empty list (until ?all=true)
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: /api/tools is sealed against tools_founder_launched; /api/launches is sealed against tools_seed; storage separation preserved
