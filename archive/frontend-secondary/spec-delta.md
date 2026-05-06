# Spec Delta: frontend-secondary

## ADDED

### F-FE2-1 — Global `<HeaderBell />` component

A new component `frontend/src/components/HeaderBell.tsx` mounts on
every authenticated route's header. Behavior:

- On mount (only when `isAuthenticated()`), fires `GET /api/me/notifications/unread-count`.
- The badge shows the count when > 0.
- Click opens a dropdown listing the latest 10 notifications from
  `GET /api/me/notifications?limit=10`. Each row links to its own
  most-relevant destination via the same kind→link rules as
  `/home`'s nudge cards (concierge_nudge → `/p/{tool_slug}`,
  community_reply → `/c/{post.community_slug}` once cycle #14 ships,
  launch_approved → `/p/{tool_slug}`).
- "Mark all read" footer button → `POST /api/me/notifications/read-all`.
- On app open (component mount), also fires `GET /api/me/notifications/banner`.
  If a non-null `concierge_nudge` is returned, surfaces a dismissable
  top-of-page banner (not a modal) with "view tool →" CTA that links
  to `/p/{payload.tool_slug}` and a × dismiss button that calls
  `POST /api/me/notifications/{id}/read` to clear it.
- Returns `null` if not authenticated.

The component is mounted in the layout for every authed route by
each page including it explicitly (Next App Router doesn't have
nested layouts that gate on client state cleanly). `/login` and
`/signup` do NOT include it.

---

### F-FE2-2 — Admin detection probe

`frontend/src/lib/admin.ts` exposes `probeAdminAndCache()`. Called
on `/home` mount when `localStorage["mesh.isAdmin"]` is unset.
Fires `GET /admin/launches?status=pending`:
- 200 → sets `localStorage["mesh.isAdmin"] = "1"`
- 403 → sets `localStorage["mesh.isAdmin"] = "0"`
- network error / other → does nothing (retried on next /home mount)

`isAdmin()` reads the cached flag (returns `false` until probe lands).
Cleared on logout.

The global `<HeaderBell />` reads `isAdmin()` and adds an "Admin"
nav link to the dropdown when true (above "Mark all read"). The
link routes to `/admin/launches`.

---

### F-FE2-3 — `/c/[slug]` community room

Wired against cycle #7. Reads:
- `GET /api/communities/{slug}` for room hero (name, description,
  category, member_count, is_member)
- `GET /api/communities/{slug}/posts` (newest-first; cursor
  pagination with "Load more" button)
- `GET /api/communities` for sister-rooms client-side filter
  (same `category` as current, excluding self)

Writes:
- `POST /api/communities/{slug}/join` and `.../leave`
- `POST /api/posts` with `{community_slug, title, body_md,
  cross_post_slugs: []}` from a compose form
- `POST /api/votes` with `{target_type: "post", target_id, direction: 1|-1}`
- Vote/comment surfaces inline on each thread card

**Filter tabs** (all / hot / verdicts / auto): client-side filters
over the SAME `posts` array; no separate endpoint hits.

**V1 hardcoded sections** (placeholder labeled in UI):
- Room pulse sparkline
- Axis breakdown bars
- Live readers strip
- Room rules

**Founders see read-only view** — compose form + vote buttons
hidden because cycle #7 F-COM-8 makes those endpoints reject
founders at the route layer anyway.

---

### F-FE2-4 — `/concierge` inbox

Three-column layout per the design. Wired against cycle #12.

**Left column (threads list):** `GET /api/me/notifications?limit=50`,
sorted newest-first. Each row shows kind label + when. Active row
highlighted.

**Center (conversation panel):** for the selected notification,
renders ONE message (V1 simplification). Message kind drawn from
the notification's `kind`; payload fields rendered as evidence:
- `concierge_nudge`: "matched against your profile" + payload.tool_slug
- `community_reply`: "X replied to your post" + payload.commenter_display_name
- `launch_approved` / `launch_rejected`: status copy

Reply composer: only for `concierge_nudge` notifications. "Tell me
more" → `POST /api/concierge/respond {action: "tell_me_more"}` +
opens redirect_url in new tab. "Skip" → `POST .../respond
{action: "skip"}`.

**Right column (reasoning trace):** generic per-kind copy. No real
per-notification scoring exposed (V1.5).

---

### F-FE2-5 — `/tools/mine`, `/tools/explore`, `/tools/new` (3 tab pages)

Wired against cycle #10.

**`/tools/mine`** — `GET /api/me/tools`. Optional `?status=using|saved`
client-side filter. Each row links to `/p/{slug}`. Inline
status-flip via `PATCH /api/me/tools/{tool_id}`. Inline unsave via
`DELETE /api/me/tools/{tool_id}` with confirmation.

**`/tools/explore`** — `GET /api/tools` with optional category /
label / `q` filters. "Load more" button uses cursor (`?before=`).
Each card links to `/p/{slug}`. "Save to my tools" inline button
posts to `/api/me/tools` (cycle #10 F-TOOL-3).

**`/tools/new`** — `GET /api/launches`. Default filter (joined
communities only) controlled by an `?all=true` URL toggle exposed
as a UI switch. Each card shows `in_my_communities` badges + link
to `/p/{slug}`.

All three pages share a tab strip header. Tab strip + bell +
content area = 2-column shell (no left rail like /home).

---

### F-FE2-6 — `/founders/launches/[id]/analytics`

Wired against cycle #11 `GET /api/founders/launches/{id}/analytics`.
Founder-role-only. Ownership-gated 404 from backend already; frontend
shows "launch not found" on that case.

Renders:
- Headline counts (matched / tell_me_more / skip / total_clicks)
- `clicks_by_community` as horizontal bar chart (community_slug → count)
- `clicks_by_surface` as small donut/legend
- Constitutional anonymization preserved — never tries to fetch
  user identities, only displays the aggregate counts the backend
  returns

Reachable from each row of the founder `/home` dashboard ("View
analytics →" link added to `FounderLaunchRow`).

---

### F-FE2-7 — `/admin/launches` (admin queue)

Behind probe-detected admin status (UI gate) AND `require_admin()`
backend gate (cycle #3 F-CAT-4).

Lists pending launches: `GET /admin/launches?status=pending`. Tabs
to switch to approved / rejected / all. Each row shows founder
email + product_url + problem_statement + submitted date.

**Approve button** → `POST /admin/launches/{id}/approve`. Inline
"approving…" state; on 200 row updates with the approved status
+ `approved_tool_slug` link → `/p/{slug}`.

**Reject** → progressive disclosure (#5 from tensions). Click
"Reject" reveals an inline textarea (placeholder "why?") + Confirm
button. Confirm → `POST /admin/launches/{id}/reject {comment}`.

---

### F-FE2-8 — `/admin/catalog` (admin tool curation)

Wired against cycle #3 admin endpoints. Reads `GET /admin/catalog`,
filters by `?status=pending|approved|rejected`. Each row shows
slug + name + tagline + category + curation_status.

**Approve** → `POST /admin/catalog/{slug}/approve`.

**Reject** → `POST /admin/catalog/{slug}/reject {comment}` with the
same progressive-disclosure pattern as `/admin/launches`.

---

### F-FE2-9 — Sign-out clears admin cache

`logout()` (cycle #13's auth helper) gains a `localStorage.removeItem("mesh.isAdmin")`
call so the next user doesn't inherit a stale admin flag.

## MODIFIED

### `/home` left rail (cycle #13)

**Before:** Five nav buttons (Home / Nudges / Stack / Communities / Refine profile).
**After:** Same buttons. PLUS, when `isAdmin()` returns true, an
additional "Admin" link → `/admin/launches`. The probe runs on
mount and updates the rail without a full re-render.

### `FreshCard`, `home-stack-item`, nudge cards (cycle #13)

**Before:** Already linked to `/p/{slug}`.
**After:** No change. Documented here for completeness — the
linkability invariant added during cycle #13's audit pass remains
in force; new components introduced in this cycle (`/tools/explore`
cards, `/admin/launches` approved rows) follow the same rule.

### `frontend/src/lib/auth.ts`

**Before:** `logout()` clears `localStorage["mesh.jwt"]`.
**After:** Also clears `localStorage["mesh.isAdmin"]`.

## REMOVED

(None.)
