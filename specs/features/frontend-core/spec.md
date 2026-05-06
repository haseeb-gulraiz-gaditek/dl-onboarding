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

- `/c/[slug]` community room view
- `/concierge` inbox
- `/tools/{mine,explore,new}` tab pages (cycle #10 backend)
- `/founders/launches/[id]/analytics` per-launch detail (cycle #11 backend has it)
- `/admin/launches`, `/admin/catalog` queue views
- Header bell + dropdown
- httpOnly cookie auth (V1.5)
- Activity feed endpoint + UI (V1.5; needs new backend)
- TypeScript codegen from Pydantic (V1.5)
- Production build / deploy
