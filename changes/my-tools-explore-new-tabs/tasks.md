# Tasks: my-tools-explore-new-tabs

## Implementation Checklist

### DB layer
- [x] `app/db/user_tools.py` — collection access + `ensure_indexes()` (unique compound (user_id, tool_id), (user_id, last_updated_at DESC)); helpers `find(user_id, tool_id)`, `list_for_user(user_id, status?)`, `upsert_auto_from_profile(user_id, tool_id)`, `upsert_explicit(user_id, tool_id, status)`, `update_status(user_id, tool_id, status)`, `delete(user_id, tool_id)` returning bool
- [x] Wire `ensure_user_tools_indexes` into `app/main.py` lifespan

### Shared tool resolver (F-TOOL-2)
- [x] `app/tools_resolver.py` — `find_tool_anywhere(slug_or_id)` returns `(doc, is_founder_launched)`; accepts both string slug and ObjectId
- [x] `app/recommendations/engine.py` — refactor to import `find_tool_anywhere` from the new shared module; remove the inline `_find_tool_anywhere` helper

### Pydantic models
- [x] `app/models/user_tool.py` — `UserToolSaveRequest` (tool_slug, status?), `UserToolPatchRequest` (status), `UserToolCard` (id, tool: ToolCardWithFlags, source, status, dates), `UserToolListResponse`, `DeleteToolResponse` (deleted: bool)
- [x] `app/models/tool_card.py` — `ToolCardWithFlags` extends `OnboardingToolCard` with `vote_score: int`, `is_founder_launched: bool`. Reuse this in F-TOOL-8/9 responses.
- [x] `app/models/launches_browse.py` — `BrowsedLaunchCard` (tool, launch_meta with founder_display_name + problem_statement + approved_at, in_my_communities), `BrowsedLaunchListResponse`

### Endpoints — me/tools
- [x] `app/api/me_tools.py` — `POST /api/me/tools` (explicit save), `DELETE /api/me/tools/{tool_id}`, `PATCH /api/me/tools/{tool_id}` (status flip), `GET /api/me/tools` (list with optional status filter, hydrated, orphans dropped silently)

### Endpoint — explore (organic catalog)
- [x] `app/api/tools_browse.py` — `GET /api/tools` reads tools_seed only, filters by category/label/q (substring on name+tagline), curation_status="approved", alphabetical with cursor pagination on name; require_role("user")

### Endpoint — new (launches with default join filter)
- [x] `app/api/launches_browse.py` — `GET /api/launches` reads tools_founder_launched joined with launches; default filter on user's joined community memberships intersect target_community_slugs; ?all=true escape hatch; computes in_my_communities per launch; require_role("user")

### Auto-populate hook (F-TOOL-7 + F-QB-3 MODIFIED)
- [x] `app/me/auto_populate_tools.py` (or inline in answers handler) — `auto_populate_from_answer(user_id, question_doc, answer_value)`: only fires for kind="multi_select"; resolves each value via find_tool_anywhere; calls user_tools.upsert_auto_from_profile per resolved tool; per-row exception logged + swallowed
- [x] `app/api/answers.py` — invoke the hook AFTER existing persistence+invalidation; never aborts the response

### Wiring
- [x] Mount routers (me_tools, tools_browse, launches_browse) in `app/main.py`
- [x] Extend RequestValidationError handler if needed for `tool_slug`, `status`, `category`, `label`, `q`, `before`, `limit`, `all`

### Tests
- [x] F-TOOL-1: user_tools collection has unique (user_id, tool_id) — second insert with same pair updates instead of duplicates
- [x] F-TOOL-2: find_tool_anywhere returns (doc, false) for tools_seed entries; (doc, true) for tools_founder_launched entries; (None, False) for unknown
- [x] F-TOOL-3: POST /api/me/tools with valid slug → 201 + row inserted with source=explicit_save
- [x] F-TOOL-3: POST /api/me/tools when row already exists with auto_from_profile → 200 + source promoted to explicit_save
- [x] F-TOOL-3: unknown slug → 404 tool_not_found
- [x] F-TOOL-3: invalid status → 400 field_invalid
- [x] F-TOOL-3: founder caller → 403 role_mismatch
- [x] F-TOOL-4: DELETE removes the row → {deleted: true}
- [x] F-TOOL-4: DELETE when no row exists → {deleted: false} (idempotent)
- [x] F-TOOL-5: PATCH updates status; preserves source
- [x] F-TOOL-5: PATCH when row missing → 404 tool_not_in_mine
- [x] F-TOOL-6: GET /api/me/tools returns rows in last_updated_at DESC order
- [x] F-TOOL-6: ?status filter narrows results
- [x] F-TOOL-6: orphaned rows (tool deleted/rejected) silently dropped from response
- [x] F-TOOL-7: multi_select answer with all-resolving slugs auto-populates user_tools (one row per slug)
- [x] F-TOOL-7: multi_select with mixed resolving + non-resolving slugs only inserts the resolvers
- [x] F-TOOL-7: re-answering same multi_select is idempotent (no duplicate rows)
- [x] F-TOOL-7: explicit_save row is NOT demoted by a subsequent auto_from_profile pass
- [x] F-TOOL-7: free_text answer never triggers auto-populate
- [x] F-TOOL-7: single_select answer never triggers auto-populate
- [x] F-TOOL-7: hook failure (e.g., DB error during one upsert) does NOT abort POST /api/answers
- [x] F-TOOL-8: GET /api/tools defaults to alphabetical first 20; ?before cursor pagination works; last page has next_before=null
- [x] F-TOOL-8: ?category filter narrows; ?label membership filter narrows; ?q substring matches both name and tagline
- [x] F-TOOL-8: pending/rejected tools excluded
- [x] F-TOOL-8: tools_founder_launched entries are NOT in this response (constitutional: organic only)
- [x] F-TOOL-8: founder caller → 403
- [x] F-TOOL-9: default GET /api/launches returns only launches whose target_community_slugs intersect user's memberships
- [x] F-TOOL-9: ?all=true returns all approved launches; in_my_communities reflects intersection (possibly empty)
- [x] F-TOOL-9: user with zero memberships gets empty list on default; full list on ?all=true
- [x] F-TOOL-9: each item includes tool card + launch_meta + in_my_communities
- [x] F-TOOL-9: founder caller → 403

### Conftest updates
- [x] `seed_user_tools_question` fixture: a multi_select question whose option values are valid catalog slugs (use seed_test_catalog or a small inline subset)
- [x] `signup_user_with_membership(client, email, slug)` reuse from cycle #7
- [x] `seed_approved_launch_with_communities` fixture for F-TOOL-9 tests

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green: 238 passing (207 prior + 31 new for cycle #10)
- [x] Auto-populate smoke: covered by `test_multi_select_resolving_slugs_auto_populates` + `test_re_answering_is_idempotent`
- [x] Promotion smoke: covered by `test_save_promotes_existing_auto_row` (auto_from_profile → explicit_save) + `test_explicit_save_not_demoted_by_subsequent_auto_populate` (explicit never demoted)
- [x] Delete smoke: covered by `test_delete_existing_returns_true` + `test_delete_missing_returns_false` (idempotent)
- [x] Browse + filter smoke: covered by `test_default_browse_returns_approved_alphabetical`, `test_category_filter`, `test_label_filter`, `test_q_substring_matches_name`, `test_pending_and_rejected_excluded`, `test_founder_launched_not_in_browse`
- [x] Launches smoke: covered by `test_default_filter_returns_only_joined_community_launches`, `test_user_with_no_memberships_gets_empty_default`, `test_all_query_returns_all_approved_launches`
- [x] Spec-delta scenarios verifiably hold in implementation (F-TOOL-1..9 each have at least one Given/When/Then-aligned test)
- [x] No constitutional regression: `test_founder_launched_not_in_browse` asserts /api/tools is sealed against tools_founder_launched; /api/launches reads only tools_founder_launched + launches via the existing helpers (no tools_seed query path); storage separation intact
