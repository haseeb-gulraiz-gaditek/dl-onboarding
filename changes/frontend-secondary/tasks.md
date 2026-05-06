# Tasks: frontend-secondary

## Implementation Checklist

### Shared infrastructure
- [ ] `frontend/src/lib/admin.ts` — `probeAdminAndCache()` and `isAdmin()` reading `localStorage["mesh.isAdmin"]`
- [ ] `frontend/src/lib/auth.ts` — `logout()` also clears `mesh.isAdmin`
- [ ] `frontend/src/components/HeaderBell.tsx` — global bell + admin nav + banner; reads `/api/me/notifications/{unread-count, banner}`; mark-all-read action; only renders when authenticated

### TypeScript types
- [ ] Extend `frontend/src/lib/api-types.ts` with: `PostCreateRequest`, `PostListResponse`, `PostCard`, `CommentCard`, `VoteRequest`, `VoteResponse`, `LaunchAnalyticsResponse`, `BrowsedLaunchListResponse`, `ToolsBrowseResponse`, `LaunchAdminCard`, `LaunchAdminListResponse`, `LaunchAdminDetail`, `MarkAllReadResponse`

### Routes — community room
- [ ] `frontend/src/app/c/[slug]/page.tsx` — hero (`GET /api/communities/{slug}`) + sister rooms (client-side from `GET /api/communities`) + thread feed (`GET /api/communities/{slug}/posts`) + compose form (`POST /api/posts`) + vote buttons (`POST /api/votes`)
- [ ] Filter tabs (all/hot/verdicts/auto) — client-side filter over the same posts array
- [ ] V1 hardcoded room pulse / axis breakdown / live readers / room rules (clearly labeled placeholder)
- [ ] "Load more" button using cursor pagination
- [ ] Founder visiting `/c/[slug]`: read-only (compose + vote hidden)

### Route — concierge inbox
- [ ] `frontend/src/app/concierge/page.tsx` — three-column layout: threads list (left, `GET /api/me/notifications?limit=50`); conversation single-message (center, kind-aware rendering); generic reasoning trace (right)
- [ ] Reply composer — only for `concierge_nudge`: tell-me-more + skip via `POST /api/concierge/respond`
- [ ] Mark-as-read on thread click

### Routes — /tools tabs
- [ ] `frontend/src/app/tools/layout.tsx` — shared tab strip (mine / explore / new)
- [ ] `frontend/src/app/tools/mine/page.tsx` — `GET /api/me/tools` + `?status` filter; inline status flip (PATCH) + unsave (DELETE) with confirm
- [ ] `frontend/src/app/tools/explore/page.tsx` — `GET /api/tools` with category/label/q filters + "Load more" cursor; "Save" button per card → POST /api/me/tools
- [ ] `frontend/src/app/tools/new/page.tsx` — `GET /api/launches`; ?all toggle exposed as UI switch; in_my_communities badge per card

### Route — founder analytics
- [ ] `frontend/src/app/founders/launches/[id]/analytics/page.tsx` — `GET /api/founders/launches/{id}/analytics`; headline counts; clicks_by_community bars; clicks_by_surface donut/legend; 404 state
- [ ] Founder `/home` dashboard rows (cycle #13) gain "View analytics →" link to this page

### Routes — admin
- [ ] `frontend/src/app/admin/launches/page.tsx` — `GET /admin/launches?status=`; status tabs; approve button + progressive-disclosure reject (textarea + confirm)
- [ ] `frontend/src/app/admin/catalog/page.tsx` — `GET /admin/catalog?status=`; same approve/reject pattern; reject takes `comment`
- [ ] `/admin/launches` row links to `/p/{approved_tool_slug}` once approved

### /home integration
- [ ] `/home` (both roles) mounts `<HeaderBell />`
- [ ] `/home` calls `probeAdminAndCache()` on mount
- [ ] `/home` left rail conditionally adds "Admin" item when `isAdmin()`
- [ ] Founder `/home` adds "Admin" link too if probe returned 200

### Header bell on every authed route
- [ ] Mount `<HeaderBell />` in `/c/[slug]`, `/concierge`, `/tools/*`, `/founders/launches/[id]/analytics`, `/admin/*`, `/founders/launch`, `/p/[slug]`
- [ ] Confirm `<HeaderBell />` does NOT mount on `/login` or `/signup`

### Smoke / build
- [ ] `npm run build` passes; all 13+ routes compile
- [ ] `npx tsc --noEmit` clean

## Validation

- [ ] All implementation tasks above checked off
- [ ] Backend test suite still 286 green (no backend code change in this cycle)
- [ ] Smoke (community room): join a community, post a thread, upvote, see counts update
- [ ] Smoke (concierge): notification appears in inbox, mark-read transitions UI, "tell me more" opens redirect URL
- [ ] Smoke (/tools/mine): save a tool from explore tab, status flip works, unsave removes the row
- [ ] Smoke (/tools/explore): category filter narrows results, "Load more" extends list
- [ ] Smoke (/tools/new): launches default filter shows only joined-community matches; ?all toggle reveals all
- [ ] Smoke (founder analytics): approved launch row → analytics page renders bars + counts
- [ ] Smoke (admin): admin email lands on /home; "Admin" link visible; /admin/launches lists pending; reject reveals textarea
- [ ] Smoke (header bell): visible on every authed route except /login + /signup; banner appears on app open when an unread concierge_nudge exists
- [ ] No constitutional regression: founders still 403'd from POST /api/posts/comments/votes; admin endpoints still require_admin; concierge inbox respects role-agnostic semantics from cycle #12
