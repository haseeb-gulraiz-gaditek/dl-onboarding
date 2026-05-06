# Feature: Frontend Core (Next.js 14)

> **Cycle of origin:** `frontend-core` (archived; see `archive/frontend-core/`)
> **Last reviewed:** 2026-05-06
> **Constitution touchpoints:** `principles.md` (*"Treat the user's profile as theirs"* — every screen renders only what real APIs return; no hardcoded per-user fakes; *"Default to the user side"* — `/home` for founders is a separate dashboard, not a degraded user view).
> **Builds on:** every backend cycle #1-#12; CORS + JWT contract; the design system from `scratch/mesh-app/`.

> **Two-process layout.** Backend (`app/`, FastAPI) and frontend (`frontend/`, Next.js 14 + React 18 + TS) run as independent processes. Backend serves on `:8000`; frontend on `:3000`. CORS is env-controlled.

---

## Intent

Cycles #1-#12 shipped the full API surface. Maya's tap-question loop, recommendations, communities, the founder launch flow, the inbox, the analytics dashboard — every endpoint is tested. Without a frontend, the demo is curl. Cycle #13 wires the design (mesh-app template) against the real APIs for the demo-day primary path.

This cycle deliberately avoids fake/mock data on authenticated screens. Every panel either reads a real endpoint or is removed. The `mesh-app` design's hardcoded sample tools, communities, and activity feeds were stripped during the audit pass.

## Surface

**Repo layout:**
```
dl-onboarding/
├── app/                # FastAPI (unchanged)
├── frontend/           # Next.js 14 + React 18 + TypeScript
└── scripts/dev.sh      # runs both processes
```

**Routes shipped (7):**

| Route | Auth | Purpose |
|-------|------|---------|
| `/` | none | Landing — port from mesh-app; CTAs route to `/signup?role=user|founder` and `/login` |
| `/signup` | none | Email + password + role toggle; pre-selectable via `?role=` query |
| `/login` | none | Email + password; both roles → `/home` |
| `/onboarding` | user | Tap-question loop fed by `/api/questions/next` + `/api/answers`; result panel from `/api/recommendations`; community pills from `/api/communities`. Founders → 403 → redirect to `/home` |
| `/home` | any | Role-aware dashboard (see F-FE-7 below) |
| `/founders/launch` | founder | 5-step form + community picker → `POST /api/founders/launch` → pending screen |
| `/p/[slug]` | any | Canonical product page from `GET /api/tools/{slug}` |

**New backend endpoints in this cycle (2):**
- `GET /api/me/communities` — joined communities (`require_role(user)`); returns `JoinedCommunityCard[]` sorted by `joined_at DESC`. (5 tests.)
- `GET /api/me/profile-summary` — derives stack + tags from raw answers (`require_role(user)`); returns `{stack_tools: [{value, label}], all_answer_values: [string]}`. Stack panel renders these labels directly (not catalog lookup) so the user sees what they actually picked. (5 tests.)

**Cross-cutting backend change:**
- CORS middleware on FastAPI from `CORS_ORIGINS` env var (default `http://localhost:3000`). Allow credentials, all methods + headers.

---

## F-FE-1 — Repo layout (monorepo with sibling packages)

`frontend/` lives next to `app/`. `app/` is NOT renamed to `backend/` — the rename would touch 200+ imports + every test + the seed CLI + cycle archives. Asymmetric naming is documented in `README.md`.

`scripts/dev.sh` runs both processes via `&` with a shared SIGINT trap.

---

## F-FE-2 — `GET /api/me/communities`

Behind `require_role("user")`. Joins `community_memberships` + `communities`. Returns `{communities: [JoinedCommunityCard]}` sorted `joined_at DESC` (with `_id DESC` tie-breaker). Inactive communities silently dropped. Founder caller → 403; unauthenticated → 401.

---

## F-FE-3 — CORS middleware

`app/main.py` adds `CORSMiddleware` reading `CORS_ORIGINS` env (comma-separated; default `http://localhost:3000`). Credentials allowed (forward-compat for cookie auth in V1.5). All methods + headers.

---

## F-FE-4 — Frontend scaffold

Next.js 14.2.5 + React 18.3.1 + TS 5.5. Tokens, components, ToolGraph, CommunityGraph copied verbatim from `scratch/mesh-app/`. Pure CSS; OKLCH palette; canvas 2D animations.

---

## F-FE-5 — API client + auth

`frontend/src/lib/api.ts` — typed fetch wrapper. Reads `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`); injects Bearer header from `localStorage["mesh.jwt"]` when `auth: true` (default); on 401 → clears JWT + `location.assign("/login")`; throws `ApiError` on non-2xx with `{status, body}`.

`frontend/src/lib/auth.ts` — `signup`, `login`, `logout`, `currentUser`, `isAuthenticated` helpers. JWT lives in `localStorage["mesh.jwt"]`.

`frontend/src/lib/api-types.ts` — hand-mirrored TypeScript interfaces for every Pydantic shape the frontend consumes (V1.5: OpenAPI codegen).

---

## F-FE-6 — `/onboarding` (tap-question loop)

User-role-only. Founders get 403 from `/api/questions/next` and the page redirects them to `/home`. Unauthenticated → `/signup`.

Fetches `GET /api/questions/next` → renders the next question (single_select / multi_select / free_text) → posts `POST /api/answers` → re-fetches next. Live ToolGraph narrows from accumulated tags via `tag-map.ts` (multi_select tool slugs + hand-maintained role/friction map).

When `done: true`: calls `POST /api/recommendations {count: 5}`, renders up to 4 `verdict="try"` cards + 1 `verdict="skip"` card + community pills from `GET /api/communities`. Each result tool card links to `/p/{slug}`.

---

## F-FE-7 — `/home` (role-aware dashboard)

**User home (existing 3-column shell):**
- Left rail: nav (Home / Nudges / Stack / Communities / Refine profile, all scroll-to-section in-page; "Refine profile" links to `/onboarding`); "Your stack" list from `GET /api/me/profile-summary` (renders the picked labels directly — not the catalog lookup, which had slug-mismatch surprises); profile + ⏻ logout.
- Center: greeting + unread count from notifications; nudge cards mapping notification kinds to design taxonomy (concierge_nudge → fresh, launch_* → mod, community_reply → pattern); fresh-for-you strip from `POST /api/recommendations` (organic + launches arrays merged, 🚀 tag for launches); your communities from `GET /api/me/communities`.
- Right rail: profile graph fed by tags computed from `all_answer_values` via `tagsForAnswerValue`. Empty state when no answers yet.

**Founder home (separate component):**
- Left rail: "+ New launch" → `/founders/launch`; "At a glance" — total / approved / pending / rejected counts; profile + ⏻ logout.
- Center: greeting; "Your launches" from `GET /api/founders/dashboard` (cycle #11) — each row shows `verification_status` (color-cued), submitted date, `/p/{slug}` link when approved, matched/tell_me_more/skip/click counts when live; notifications inbox.

Founder home does NOT render user-side sections (no stack from profile-summary, no recommendations, no joined communities — those are user-only endpoints).

---

## F-FE-8 — `/founders/launch`

Founder-role-only. 5-step form maps to backend's `POST /api/founders/launch`:

| Step | Fields → Backend |
|------|------------------|
| 1 | name (display only) + product_url (validated http(s) inline) + oneliner + presence (CSV) |
| 2 | category (single-select) — concatenated into `icp_description` |
| 3 | ICP — 3 free-text fields: "who they are", "job to be done", "today's pain" — concatenated with section markers into `icp_description` |
| 4 | pricing (single-select) — concatenated into `icp_description` |
| 5 | pitch (longtext) → `problem_statement` + community picker (1..6 chips) → `target_community_slugs` |

**Community picker:** loads `GET /api/communities` on mount, renders chips inside Step 5's form card (not the side graph pane — `.onb-graph-meta` has `pointer-events: none` so clicks there never fired). Live CommunityGraph in side pane animates from form-derived tags as a visual cue only.

**Per-step gating:** `Continue` only goes primary when current step's required fields are valid. Step 5's submit only goes primary when both pitch text AND ≥1 community picked. URL validated INLINE on step 1 — no end-of-flow surprise.

Submit → POST → pending screen ("Mesh staff verifies within ~24h") → "Back to dashboard" → `/home`.

---

## F-FE-9 — `/p/[slug]`

Reads `GET /api/tools/{slug}` (cycle #9 F-PUB-4). Renders unified card + LaunchMeta block when `is_founder_launched=true`. "Open site" button → tool's external URL. "Save to my tools" button (visible only to user role) → `POST /api/me/tools` (cycle #10).

**Linkability invariant (added in audit pass):** every tool-slug reference in the frontend is clickable to `/p/{slug}`:
- User home left-rail stack rows
- User home Fresh-for-you cards
- User home nudge cards with `tool_slug` payload
- Onboarding result tool cards
- Founder home dashboard rows when approved

---

## F-FE-10 — Dev workflow

Repo root `README.md` documents the two-process layout + commands. `scripts/dev.sh` runs `uvicorn app.main:app` + `npm run dev` concurrently with shared SIGINT trap.

**Env:**
- Backend: `CORS_ORIGINS` (default `http://localhost:3000`)
- Frontend: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`)

---

## Audit invariants

The cycle's later passes enforced these explicitly:

1. **No hardcoded per-user data.** Every authenticated panel either reads a real endpoint or is removed. The original mesh-app design's hardcoded "Recent activity" feed, "profile graph" tag list, and `/founders/launch` sample-community picker were all stripped or replaced with backend reads.
2. **Linkability.** Every tool-slug reference is a clickable `<Link>` to `/p/{slug}`.
3. **Role-aware surfaces.** `/home` renders different layouts for users vs founders. Cross-role data leakage prevented at the route layer (founder hits user-only endpoint → 403, page degrades gracefully or redirects).
4. **No dead nav.** Every nav button either scrolls to an existing in-page section or routes to a real page. The Discover/Profile-toggle items from the original design were removed because their cycle #14 destinations don't exist yet.
5. **Per-step form validation.** Founders never get a step-1 error on step 5. Each step's `Continue` gates on its own required fields.

---

## Out of cycle (deferred to cycle #14)

- `/c/[slug]` community room view *(shipped — cycle #14)*
- `/concierge` inbox *(shipped — cycle #14)*
- `/tools/{mine,explore,new}` tab pages *(shipped — cycle #14)*
- `/founders/launches/[id]/analytics` per-launch detail *(shipped — cycle #14)*
- `/admin/launches`, `/admin/catalog` queue views *(shipped — cycle #14)*
- Header bell + dropdown *(shipped — cycle #14)*
- httpOnly cookie auth (V1.5)
- Activity feed endpoint + UI (V1.5; needs new backend)
- TypeScript codegen from Pydantic (V1.5)
- Production build / deploy

---

## Cycle #14 — frontend-secondary additions

### F-FE2-1 — Global `<HeaderBell />` component

`frontend/src/components/HeaderBell.tsx` mounts on every authenticated route.

- On mount (only when `isAuthenticated()`), fires `GET /api/me/notifications/unread-count`. Badge shows count when > 0.
- Click opens a dropdown listing the latest 10 notifications (`GET /api/me/notifications?limit=10`). Each row links to its own destination via the kind→link rules from `/home` (concierge_nudge → `/p/{tool_slug}`, launch_approved → `/p/{tool_slug}`, community_reply → `/concierge`).
- "Mark all read" footer → `POST /api/me/notifications/read-all`.
- Also fires `GET /api/me/notifications/banner` on mount; non-null `concierge_nudge` surfaces a dismissable top-of-page banner with "view tool →" CTA. × dismiss → `POST /api/me/notifications/{id}/read`.
- Returns `null` if not authenticated.
- Wrapper renders as `position: fixed; top: 16; right: 16; z-index: 60` so it never gets clipped by page chrome. Dropdown is `position: fixed; top: 60; right: 16; z-index: 70` with viewport-clamped width. `mousedown` outside the wrapper closes the dropdown.
- Visible label: a bell SVG + "Inbox" text in a pill (the `◌` glyph used during initial implementation was indistinguishable from the Communities nav glyph).

`/login` and `/signup` do NOT include it.

### F-FE2-2 — Admin detection probe

`frontend/src/lib/admin.ts` exposes `probeAdminAndCache()`. Called on `/home` mount when `localStorage["mesh.isAdmin"]` is unset.

- Fires `GET /admin/launches?status=pending`:
  - 200 → sets `localStorage["mesh.isAdmin"] = "1"`
  - 403 → sets `localStorage["mesh.isAdmin"] = "0"`
  - network error / other → does nothing (retried on next /home mount)
- `isAdmin()` reads the cached flag.
- Cleared on `logout()`.

The global HeaderBell reads `isAdmin()` and adds an "Admin" link to the dropdown footer when true. `/home` left rail (both roles) also adds an "Admin" nav item when the flag is set.

### F-FE2-3 — `/c/[slug]` community room

Wired against cycle #7. Reads `GET /api/communities/{slug}` (hero + is_member), `GET /api/communities/{slug}/posts` (cursor pagination, "Load more"), `GET /api/communities` (sister rooms — same category, exclude self).

Writes: `POST /api/communities/{slug}/{join,leave}`, `POST /api/posts {community_slug, title, body_md, cross_post_slugs:[]}`, `POST /api/votes {target_type:"post", target_id, direction:1|-1}`.

Filter tabs (all/hot/verdicts/auto) are client-side filters over the same posts array.

V1 hardcoded sections (UI-labeled placeholder): room pulse sparkline, axis breakdown bars, live readers strip, room rules.

Founders see the read-only view (compose form + vote buttons hidden); cycle #7 F-COM-8 enforces 403 at the route layer.

### F-FE2-4 — `/concierge` inbox (rendered as "Inbox" in user-visible copy)

Three-column layout. Wired against cycle #12.

- **Left:** `GET /api/me/notifications?limit=50`, newest-first.
- **Center:** for the selected notification, ONE message (V1 simplification). Kind drawn from `notification.kind`; payload fields rendered as evidence.
- **Right:** generic per-kind reasoning copy. No real per-notification scoring exposed (V1.5).

Reply composer only for `concierge_nudge`: "Tell me more" → `POST /api/concierge/respond {action:"tell_me_more"}` + opens redirect_url in new tab. "Skip" → `POST .../respond {action:"skip"}`.

User-visible label is **"Inbox"** in the bell pill, the left-rail nav item, the page header, and the landing footer link. Route stays `/concierge`; backend kinds keep `concierge_*` identifiers.

### F-FE2-5 — `/tools/{mine,explore,new}` tab pages

Wired against cycle #10. Shared tab-strip layout in `frontend/src/app/tools/layout.tsx`.

- `/tools/mine` — `GET /api/me/tools`, optional `?status=using|saved` client-side filter. Inline `PATCH /api/me/tools/{tool_id}` for status flip; inline `DELETE /api/me/tools/{tool_id}` for unsave (with confirmation).
- `/tools/explore` — `GET /api/tools` with optional category/label/`q` filters. "Load more" via `?before=` cursor. Per-card "Save to my tools" button → `POST /api/me/tools`.
- `/tools/new` — `GET /api/launches`, default filter (joined communities only) controlled by `?all=true` UI toggle. Each card shows `in_my_communities` badges.

Every card links to `/p/{slug}`.

### F-FE2-6 — `/founders/launches/[id]/analytics`

Wired against cycle #11 `GET /api/founders/launches/{id}/analytics`. Founder-only. Backend's ownership-gated 404 surfaces as "launch not found" UI.

Renders headline counts (matched / tell_me_more / skip / total_clicks), `clicks_by_community` as horizontal bars, `clicks_by_surface` as donut/legend. Reachable from each `FounderLaunchRow` on `/home` ("View analytics →" link).

Constitutional anonymization preserved — never tries to fetch user identities.

### F-FE2-7 — `/admin/launches` (admin queue)

UI-gated by probe-detected admin status; backend-gated by `require_admin()` (cycle #3 F-CAT-4).

`GET /admin/launches?status=pending` (tabs for approved/rejected/all). Each row: founder email + product_url + problem_statement + submitted date.

- **Approve** → `POST /admin/launches/{id}/approve`. On 200 the row updates to approved status with link to `/p/{approved_tool_slug}`.
- **Reject** → progressive disclosure: click "Reject" reveals an inline textarea (placeholder "why?") + Confirm button; Confirm → `POST /admin/launches/{id}/reject {comment}`.

### F-FE2-8 — `/admin/catalog` (admin tool curation)

`GET /admin/catalog?status=pending|approved|rejected`. Each row: slug + name + tagline + category + curation_status.

- **Approve** → `POST /admin/catalog/{slug}/approve`.
- **Reject** → `POST /admin/catalog/{slug}/reject {comment}` with the same progressive-disclosure textarea pattern as `/admin/launches`.

### F-FE2-9 — Sign-out clears admin cache

`logout()` (cycle #13's auth helper) also clears `localStorage["mesh.isAdmin"]` so the next account doesn't inherit a stale admin flag.

### F-FE2-10 — `/communities` browse page

`/home` cycle #13's "Communities" left-rail item linked to a scroll target; the empty state had no CTA, so first-time users couldn't discover or join rooms without manually typing `/c/{slug}`.

`frontend/src/app/communities/page.tsx`:
- Reads `GET /api/communities` for the full list (both roles).
- For users, also reads `GET /api/me/communities` to compute `joined`. Writes: `POST /api/communities/{slug}/join`, `DELETE /api/communities/{slug}/leave` with confirm.
- Founders see Open→ only (read-only; backend enforces 403 on join).
- Filter tabs (all / role / stack / outcome) over the same array.
- Each card links to `/c/{slug}`.

`/home` rewires:
- Left-rail "Communities" → `<Link href="/communities">` (was scroll-to-section).
- Empty state ("you haven't joined any rooms yet") gains a "→ browse communities" link.
- Joined community rows are now `<Link href="/c/{slug}">` (were divs).
- Founder home gains a "Communities" left-rail item linking to `/communities`.

---

## Cycle #14 — backend / publish-path additions

### F-LAUNCH-7 — Smarter slug + name derivation from product URL

`derive_tool_slug()` in `app/launches/slug.py` strips noise subdomain prefixes (`www.`, `app.`, `my.`, `go.`, `try.`, `get.`, `dashboard.`, `admin.`, `portal.`, `beta.`, `staging.`) idempotently AND strips the TLD before slug normalization.

`admin_approve` in `app/api/admin_launches.py` derives the friendly tool name as title-cased every slug segment (not just the first), so `content-planner` becomes `"Content Planner"` instead of `"Content"`.

Verified mappings:
- `https://app.contentplanner.site` → slug `contentplanner`, name `Contentplanner`
- `https://www.zapier.com` → `zapier` / `Zapier`
- `https://notion.so` → `notion` / `Notion`
- `https://multi-word.tool.app` → `multi-word-tool` / `Multi Word Tool`

### F-EMB-7 — Fast-fail Weaviate init timeout

`_get_weaviate_client()` in `app/embeddings/vector_store.py` passes `AdditionalConfig(timeout=Timeout(init=2, query=5, insert=5))` to `weaviate.use_async_with_weaviate_cloud(...)`.

The first POST `/admin/launches/{id}/approve` on a machine where Weaviate Cloud's gRPC port is unreachable used to hang ~30s on the gRPC health probe before the failure was cached. With a 2s init timeout, the first approve now returns in <3s; subsequent approves short-circuit immediately because `_client` is cached as `None`. Operations under a healthy connection are unaffected.
