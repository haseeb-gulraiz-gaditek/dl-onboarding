# Proposal: frontend-secondary

## Problem

Cycle #13 wired the demo-day primary path: landing, signup/login,
onboarding, /home (role-aware), founders/launch, /p/[slug]. That's
five routes plus auth — enough for a credible end-to-end story.
But several backend cycles still have NO frontend surface:

  - cycle #7 `/api/communities/{slug}/posts` (community room) → no UI
  - cycle #12 inbox endpoints (banner, list, mark-read) → only
    minimal nudge cards on /home
  - cycle #10 `/api/me/tools`, `/api/tools`, `/api/launches` → no
    /tools tab pages exist; /home rail shows stack but there's no
    full browse / save management surface
  - cycle #11 `/api/founders/dashboard` is wired on founder /home,
    but `/api/founders/launches/{id}/analytics` (per-launch detail
    with clicks_by_community + clicks_by_surface) → no UI
  - cycle #3 `/admin/catalog/*` and cycle #8 `/admin/launches/*`
    queue + approve/reject → no UI; admins can only curl

This cycle wires those surfaces minimally — enough for demo
completeness without designing the V1.5 polish (multi-message
concierge threads, room pulse analytics, sister-rooms endpoint,
notification preferences, etc., all explicitly deferred).

## Solution

**6 new routes + 1 global component:**

| Route | Backend |
|---|---|
| `/c/[slug]` | community room — feed/compose/vote (cycle #7) |
| `/concierge` | inbox list + banner + mark-read (cycle #12) |
| `/tools/mine` | `GET/POST/PATCH/DELETE /api/me/tools` (cycle #10) |
| `/tools/explore` | `GET /api/tools` with filters (cycle #10) |
| `/tools/new` | `GET /api/launches` with `?all` (cycle #10) |
| `/founders/launches/[id]/analytics` | `GET /api/founders/launches/{id}/analytics` (cycle #11) |
| `/admin/launches` + `/admin/catalog` | cycle #3 + #8 admin endpoints |

**Plus a global `<HeaderBell />` component** mounted on every authed
route's header — reads `GET /api/me/notifications/unread-count` and
`GET /api/me/notifications/banner` on app open. Banner surfaces the
most-recent unread `concierge_nudge` as a dismissable top toast.
Bell click opens a dropdown with the 10 most-recent notifications +
"Mark all read" action. Same component used on /home, /c/[slug],
/concierge, /tools/*, /founders/launches/{id}/analytics.

**Admin detection (no backend change):** on /home mount, probe
`GET /admin/launches?status=pending` once. If 200 → cache
`localStorage["mesh.isAdmin"] = "1"`. Show "Admin" nav item in the
global header when set. If 403 → ignore. Cleared on logout.

**Concierge inbox (V1):** each notification renders as ONE message
in the conversation panel. The design's multi-message
opening/finding/evidence/recommendation/math thread structure is
explicitly V1.5 (would need a new `concierge_messages` collection
backend). Right rail "reasoning trace" uses generic per-kind copy
("matched on profile similarity", etc.) — no real per-notification
scoring exposed yet.

**Community room V1 simplifications:**
- Sister rooms: client-side computed from `category` via `GET /api/communities`
- Room pulse sparkline + axis breakdown + live readers: HARDCODED
  (documented backend gaps)
- Room rules: HARDCODED per slug (no `rules` field on community
  schema in V1)
- Filter tabs (all / hot / verdicts / auto): client-side filters
  over the same `GET .../posts` feed

**/tools pagination:** "Load more" button using cycle #10's
`?before` cursor. Simpler than infinite scroll; doesn't fight the
cursor model.

**/admin/launches reject:** progressive-disclosure UX —
"Reject" button reveals an inline textarea + Confirm button. No
modal/popover.

## Scope

**In:**
- 6 new wired routes
- 1 global header component (bell + admin link + logout)
- Admin probe + localStorage cache
- /admin/launches list + approve + reject (with comment)
- /admin/catalog list + approve + reject
- Per-launch analytics view at /founders/launches/[id]/analytics
- Sister-rooms client-side computation
- Tool resolver for save/unsave on /p/[slug] (already wired in
  cycle #13, no change)

**Out (explicit V1.5 deferrals):**
- Multi-message concierge threads (needs new backend collection)
- Real reasoning-trace scoring per notification
- Room pulse analytics endpoint
- Sister rooms endpoint
- Live-readers presence
- Notification preferences ("tune what gets through")
- Activity feed (cross-user stream)
- Free-form concierge chat (⌘K)
- Per-launch reach forecast model
- httpOnly cookie auth
- TypeScript codegen
- Production deploy

## Risks

1. **Admin probe call on every /home mount.** One extra request per
   page load; small (~50ms) and cached in localStorage afterwards.
   Acceptable. Risk: env-var change in `ADMIN_EMAILS` not reflected
   until logout. Documented as known.
2. **Hardcoded sister rooms / room pulse** marked clearly in the UI
   (no fake data passing as real per cycle #13's audit lessons).
   Risk surface: a future contributor might mistake the hardcoded
   sparkline for live data. Mitigation: code comment + UI label
   ("placeholder").
3. **Concierge V1 single-message limit** — design's "evidence with
   3 quotes" UX is missing. Acceptable for V1 since the backend
   doesn't carry that data. Frontend renders payload.tool_slug or
   payload.comment generically.
4. **/tools/explore filter combinations** — backend accepts
   `category`, `label`, `q`, but only one of each at a time.
   Frontend respects this; users can't combine multiple categories.
   Documented.
5. **Header bell on auth-only pages.** `/login` and `/signup` should
   NOT mount the bell (no JWT yet). Component checks `isAuthenticated`
   and returns null.
