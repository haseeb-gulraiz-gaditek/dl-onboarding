# Proposal: frontend-core

## Problem

Cycles #1-#12 shipped Mesh's API surface end-to-end: signup, onboarding, recommendations, communities, launches, dashboards, notifications. Every endpoint is tested. But there's no browser-facing surface — the system_design v0.1 promises Maya signs up, taps through onboarding, and lives on a dashboard. None of that has a UI yet. Demo day is May 8 (five days). Without a frontend, the demo is curl commands.

The `scratch/mesh-app/` folder has a complete Next.js 14 / React 18 / TypeScript design with 7 pages, animated canvas graphs, and an OKLCH design system — but it runs on mock data. This cycle wires it against the real FastAPI for the five highest-value routes.

## Solution

**Repo layout (monorepo):**
```
dl-onboarding/
├── app/                # FastAPI (unchanged)
├── frontend/           # NEW: Next.js 14 + React 18 + TS
├── tests/              # backend tests (unchanged)
├── specs/, archive/    # SDD artifacts (unchanged)
└── README.md           # documents the two-process layout
```

`app/` stays as-is — renaming to `backend/` would touch 200+ imports + every test + seed CLI + cycle archives. Asymmetric naming is the price of zero backend churn.

**Two new processes in dev:**
- Backend: `python -m uvicorn app.main:app --reload` on `:8000`
- Frontend: `npm run dev` from `frontend/` on `:3000`

**One small backend addition** (the only API gap blocking `/home`):
- `GET /api/me/communities` behind `require_role("user")` — joins `community_memberships` + `communities` and returns `{communities: [CommunityCard]}`. ~30 min work; reuses existing models.

**One small backend cross-cutting change:**
- CORS middleware allowing `http://localhost:3000` (configurable via `CORS_ORIGINS` env var). Required for browser → FastAPI calls.

**Frontend scaffolding (`frontend/`):**
- Init from `scratch/mesh-app/` template — copy `tokens.css`, `components.css`, `Primitives.tsx`, `ToolGraph.tsx`, `CommunityGraph.tsx` as-is.
- `package.json` from mesh-app (Next 14.2.5, React 18.3.1, TS 5.5).
- API client `frontend/src/lib/api.ts` — typed fetch wrapper:
  - Reads `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)
  - Reads JWT from `localStorage["mesh.jwt"]`
  - Sends `Authorization: Bearer <jwt>` on every authed request
  - On 401 → clears JWT + redirects to `/onboarding`
  - Returns typed responses (TS interfaces matching Pydantic models — duplicated by hand for V1; codegen is V1.5)
- Auth helpers `frontend/src/lib/auth.ts` — `signup`, `login`, `logout`, `currentUser` reading the JWT-derived user from `/api/me`.

**Five wired routes:**

1. **`/` landing** — port from mesh-app verbatim. Static. CTAs link to `/onboarding`.

2. **`/onboarding`** — combined signup + tap-question loop:
   - First-time visitor: shows email/password form alongside the first question. On submit, fires `POST /api/auth/signup` with `role_question_answer="finding_tools"`, stores JWT, then proceeds.
   - Subsequent steps: `GET /api/questions/next` → render question card matching `kind` (single_select / multi_select / free_text). On answer, `POST /api/answers` and re-fetch next.
   - Live ToolGraph narrows from accumulated tags. Tags derived client-side: for multi_select questions whose option values are tool slugs (cycle #10 F-TOOL-7 contract), the frontend looks up tags from `MESH_TOOLS` table baked into `ToolGraph.tsx`. For role/friction questions, a static `value → tags[]` map in `frontend/src/lib/tag-map.ts`.
   - When `/api/questions/next` returns `{done: true}` (or after 5 answers), call `POST /api/recommendations` with `count=4`. Render the result panel: 4 picks from `recommendations[]` + 1 from `recommendations[]` whose `verdict="skip"` (or fall back to a generic "skip this" copy if all are `try`). Community pills from `GET /api/communities` (top 3 by member_count).
   - "Enter Mesh" CTA → `/home`.

3. **`/home`** — three-column shell:
   - Left rail: nav glyphs + "Your stack" list = `GET /api/me/tools` (cycle #10) + profile footer with display_name from `/api/me`.
   - Center: greeting (display_name + unread-count from `GET /api/me/notifications/unread-count`); nudge cards = `GET /api/me/notifications` (mapped via `kind` → design's pattern/fresh/mod/skip taxonomy in a frontend helper); Fresh-for-you strip = `POST /api/recommendations` (organic + launches arrays merged, frontend renders both); Your Communities rows = the new `GET /api/me/communities`.
   - Right rail: profile graph (canvas, no API; reads accumulated tags from `/api/me` answers); activity feed HARDCODED for V1 (5 sample rows; documented as V1.5 backend gap).
   - Header: ⌘K opens a placeholder concierge dialog (dropped — V1.5).

4. **`/founders/launch`** — 6-step form mapped to `POST /api/founders/launch`:
   - Step 1: `name` (display only) + `product_url` (required, http(s))
   - Step 2: `category` single-select (mapped into icp_description prefix)
   - Step 3: `replaces` multi-select tools (mapped into icp_description)
   - Step 4: `audience` multi-select roles (mapped into icp_description)
   - Step 5: `pricing` single-select (mapped into icp_description)
   - Step 6: `pitch` longtext → `problem_statement` (or `oneliner` if pitch empty)
   - PLUS: `target_community_slugs` selected via clicking up to 6 nodes on the live CommunityGraph (gated to require ≥1 before submit).
   - PLUS: `existing_presence_links` collected as a single comma-separated input on step 1 (optional).
   - On submit: serializes the mapping → `POST /api/founders/launch` → renders pending state with the picked communities + a "we'll notify you" message.

5. **`/p/[slug]`** — canonical product page wired to `GET /api/tools/{slug}` (cycle #9 F-PUB-4). Renders the unified card + LaunchMeta when `is_founder_launched=true`.

**Documented frontend adaptations (no backend change):**
- Activity feed rendered from a hardcoded array (V1.5: build cross-user activity stream)
- Founder forecast chart on the result page is a cosmetic predictive line — never computed from real data; labeled "predicted" in copy
- Nudge UI taxonomy (pattern/fresh/mod/skip) maps from real notification kinds via a frontend helper
- "Pattern detected" copy for `concierge_nudge` notifications, "fresh" for `launch_approved`-of-a-different-founder cases (handled gracefully)
- Sister rooms / room pulse / multi-message concierge / reasoning trace bars — NOT in this cycle (cycle #14)

## Scope

**In:**
- 1 new backend endpoint (`GET /api/me/communities`)
- CORS middleware on FastAPI
- Frontend scaffold (`frontend/` package + tooling)
- API client + auth helpers + tag-map
- 5 wired routes
- README at repo root documenting the two-process dev layout
- Environment variable for backend `CORS_ORIGINS` and frontend `NEXT_PUBLIC_API_BASE_URL`
- Backend tests for the new `/api/me/communities` endpoint

**Out:**
- httpOnly cookie auth (V1.5 — JWT in localStorage works for V1)
- TypeScript codegen from Pydantic models (duplicate by hand for V1)
- Production build / deployment (`fly.io` deploy is a separate cycle)
- Storybook / component library docs (V1.5)
- E2E tests for the frontend (V1.5)
- Cycle #14 routes: community room, concierge inbox, /tools tabs, founder dashboard, admin queue, header bell

## Risks

1. **CORS misconfiguration locks browser out.** Mitigation: env-var-controlled origins; default to `http://localhost:3000` in dev. Tested in local dev as part of validation smoke.
2. **JWT in localStorage is XSS-vulnerable.** Acceptable for V1 demo; we don't render user-generated content in the frontend yet (cycle #14 introduces the community room). V1.5 hardens by moving to httpOnly cookies.
3. **Onboarding form schema drift.** Backend's question bank seeds dictate what questions appear. The design hardcodes 5; frontend renders WHATEVER `/api/questions/next` returns. If the seed has 15 questions, the user gets 15 — UX will feel longer. Acceptable; covered in the design as "tap-don't-type, however many."
4. **Founders form mapping is opaque.** A founder fills 6 fields; backend stores 5 different fields with concatenation. If admin reads the launch in `/admin/launches/{id}` (cycle #14 surface) the structure is collapsed. Mitigated by including a separator marker in `icp_description` like `\n\n--- audience ---\n` so it's parseable.
5. **Tag map drift.** Frontend's `value → tags[]` lookup is hand-maintained alongside the seed questions. If a future cycle changes a question's options, the tag map can go stale. Documented; cycle #14 or V1.5 considers backend-side tags.
6. **Demo day clock.** Two days for cycle #13 + two for cycle #14 = four days. One-day buffer. If anything slips, founders/launch (route #4) cuts to cycle #14.
