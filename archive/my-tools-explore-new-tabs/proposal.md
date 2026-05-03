# Proposal: my-tools-explore-new-tabs

## Problem

Cycles #1-#9 wired both sides of the marketplace end-to-end. Maya gets recommendations and concierge nudges; Aamir submits launches that fan out to her surfaces. But there's no place for Maya to *keep* anything she's adopted, browse the whole catalog when she has time to explore, or see what's launching this week in her communities. The system_design v0.2 pinned this as the **/tools** page with three tabs:

- **/tools/mine** — her current and saved tools.
- **/tools/explore** — the whole curated catalog, browseable.
- **/tools/new** — what founders are launching, defaulted to her joined communities.

Without it, the user-facing surface stops at "here's a recommendation" with no follow-through. The "treat the user's profile as theirs" principle (We Always #2 — full export) implies they need a place to *see* what they've stated, in tool terms, not just answer terms.

This cycle ships the **API only** (consistent with prior cycles); the React frontend is a parallel Claude Design track.

## Solution

A new `user_tools` collection + 5 endpoints behind `require_role("user")` + an auto-populate hook on `POST /api/answers`.

**`user_tools` schema:**
```
{
  _id: ObjectId,
  user_id: ObjectId,
  tool_id: ObjectId,        // resolves in tools_seed OR tools_founder_launched
  source: "auto_from_profile" | "explicit_save" | "manual_add",
  status: "using" | "saved",
  added_at: datetime,
  last_updated_at: datetime
}
```

Unique compound index on `(user_id, tool_id)`: idempotent. Re-answering a multi_select question with the same tools = no-op. Explicit save promotes `source` to `explicit_save` (more specific wins).

**Endpoints (all `require_role("user")`):**
- `POST /api/me/tools` body `{tool_slug, status?}` — explicit save. `status` defaults to `saved`. Resolves slug across both collections.
- `DELETE /api/me/tools/{tool_id}` — unbookmark. Removes the row.
- `PATCH /api/me/tools/{tool_id}` body `{status}` — flip between `using` and `saved`.
- `GET /api/me/tools` (`/tools/mine` backing) — list user's tools, optional `?status=` filter, hydrated with the tool card.
- `GET /api/tools` (`/tools/explore` backing) — alphabetical browse, optional `?category=&label=&q=&before=&limit=`. Reads `tools_seed` only (constitutional separation: organic catalog only). Cursor pagination on `name`.
- `GET /api/launches` (`/tools/new` backing) — newest-first launches. Default filter: only those whose `target_community_slugs` intersect the user's memberships. `?all=true` removes the filter.

**Auto-populate hook:**
On `POST /api/answers`, if the question is `multi_select` AND the answer's value is a list of strings AND each string resolves to a tool slug (in either collection), insert/update one `user_tools` row per slug with `source=auto_from_profile`, `status=using`. Idempotent via the unique index. Free-text answers and substring scans are explicitly out of scope (deferred to V1.5).

**Tool resolution helper:** `find_tool_anywhere(slug)` — scans `tools_seed` first, then `tools_founder_launched`. Returns `(doc, is_founder_launched)`. Reused from cycle #9's `_find_tool_anywhere` (refactor it into a shared module).

## Scope

**In:**
- 1 new collection (`user_tools`).
- 6 endpoints (3 mutation + 3 read).
- Auto-populate hook on `POST /api/answers` (multi_select + slug-valued answers only).
- Cross-collection tool resolution.
- Constitutional separation in /api/tools (organic-only) — launches stay on /api/launches.
- Test suite: F-TOOL-1..7 covering schema, save/delete/patch, list, explore filters, launches default+all, role gating, auto-populate idempotency.

**Out:**
- Substring/LLM tool extraction from free-text answers (V1.5).
- `tried_bounced` / `want_to_try` statuses (V1.5).
- Detailed integration depth tracking (V1.5+).
- Collections / folders (V1.5+).
- Full-text search engine for /api/tools (V1; `?q=` is substring on name + tagline only).
- Sort by popularity / vote_score (V1; alphabetical only — vote_score is in the response, frontend can sort client-side).
- Frontend (parallel React track).

## Risks

1. **Auto-populate misses non-multi-select tool questions.** A free-text answer "I use Notion and Linear" doesn't trigger anything. Mitigation: documented out-of-scope; tool-stack questions in cycle #2's seed need to be authored as multi_select with slug-valued options. If they're not currently, that's a separate question-bank refresh task (not in this cycle).
2. **Cross-collection tool_id resolution.** `tool_id` is an ObjectId; one user's tool could be in either `tools_seed` or `tools_founder_launched`. Mitigation: `find_tool_anywhere` helper. Risk if a tool is moved between collections (shouldn't happen — both sealed by source) the row goes orphan; reads silently drop it. Documented.
3. **Auto-populate vs explicit_save precedence.** A user auto-saves "notion" via answer, then later explicitly bookmarks it. We update `source=explicit_save` so the explicit signal wins. Risk: deleting then re-answering will re-add it as `auto_from_profile` (signal demotion). Acceptable for V1.
4. **/api/launches default filter when user is in zero communities.** Returns empty list — sensible default. The `?all=true` toggle is the escape hatch. Documented.
5. **Pagination cursor on `name`.** Two tools with the same name (rare but possible across catalog refreshes) tie-break on `_id` ASC. Already a pattern from cycle #7. No issue.
6. **Founder accounts on /api/launches.** `require_role("user")` means founders 403. They get their own dashboard in cycle #11; for now, founders use `/api/founders/launches` to see their own.
