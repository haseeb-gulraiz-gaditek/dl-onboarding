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

---

## Cycle #15 — live-narrowing-onboarding additions

### F-LIVE-1 — `LiveQuestion` model + locked 4-question schema

`app/onboarding/live_questions.py` exposes `LiveQuestion` Pydantic model with `q_index, key, text, helper, kind, sub_dropdowns, options, options_per_role, fallback_options`.

`LIVE_QUESTIONS: list[LiveQuestion]` — 4 locked questions (in-process constant, NOT seeded to Mongo so the classic flow's question bank in `app/seed/questions.json` is unaffected):
- Q1 `dropdowns_3`: job_title (typeable + suggestions) / level / industry
- Q2 `multi_select` chips: role-conditioned daily-stack picks
- Q3 `single_select`: role-conditioned big-task scenarios
- Q4 `single_select`: role-agnostic friction (7 options)

Hand-curated `ROLE_OPTIONS_Q2` / `ROLE_OPTIONS_Q3` cover 13 canonical roles (software_engineer, accountant, doctor, marketer, designer, product_manager, sales, founder, student, lawyer, operations, customer_success, consultant). `FALLBACK_OPTIONS_Q2` / `FALLBACK_OPTIONS_Q3` cover unknown / "other" roles. `ROLE_KEY_MAP` aliases similar job_title values into the canonical role keys.

**Endpoints (auth: `require_role("user")`):**
- `GET /api/onboarding/live-questions` → `{questions: LiveQuestion[]}` (4 entries).
- `GET /api/onboarding/live-questions/{q_index}/options?role={role_value}` → `{options, role_key_resolved}`. 400 for Q1 / Q4 (not role-conditioned). 404 for invalid `q_index`. Unknown role falls back to the question's `fallback_options`.

### F-LIVE-2 — `POST /api/recommendations/live-step`

Behind `require_role("user")`. Pipeline per call:

1. `get_or_create_profile(user)` — ensure a `profiles` row exists (the live flow doesn't go through `/api/questions/next`).
2. `upsert_live_answer(user_id, q_index, value)` — one row per `(user_id, q_index)` in the new `live_answers` collection.
3. Read `get_user_live_answers(user_id)` → `{q_index: value}` map.
4. `live_match(user, q_index, live_answers)` (F-LIVE-2 below).
5. Write the result to the recommendations cache via `upsert_for_user` (F-LIVE-12) so `/home`'s `POST /api/recommendations` returns the same tools instantly.

**Response shape:**
```json
{
  "step": 1..4,
  "top": [{"slug","name","tagline","category","score","layer","reasoning_hook"}],
  "wildcard": {...} | null,
  "count_kept": int,
  "degraded": bool
}
```

`degraded: true` indicates Weaviate hybrid was unreachable and the engine fell back to `similarity_search` (Mongo cosine over the persisted profile vector). Frontend treats it as a dev-only signal (console.info), not user-facing.

**Failure modes:**
- OpenAI embed raises → 503 `{"error": "live_step_unavailable"}`. The `live_answers` row is already persisted so retry is idempotent.

### F-LIVE-3 — `hybrid_search()` helper

`app/embeddings/vector_store.py::hybrid_search(*, weaviate_class, query, vector, alpha, limit, filters=None)` wraps Weaviate v4's `collection.query.hybrid(query=, vector=, alpha=, limit=, filters=)`. Returns `[(properties_dict, score)]` sorted descending. `[]` when client is `None` (Weaviate unreachable). Per-op `query`/`insert` timeouts set in F-LIVE-7.

### F-LIVE-4 — Per-tap profile vector persistence

`live_match` always calls `ensure_profile_embedding(user, force_recompute=True, override_text=profile_text)` before the hybrid query. The `profiles` row is updated with the freshly-computed vector each tap. Mid-flow exit at any step leaves a usable profile vector in Mongo so `/home`'s recommendations engine and the right-rail "Your matches" graph reflect the user's accumulated answers.

`ensure_profile_embedding` (extended from cycle #4) gains two kwargs: `force_recompute=False` (skip the freshness check) and `override_text=None` (use this text instead of building from the `answers` collection).

### F-LIVE-5 — Score-band layer assignment

`app/recommendations/live_engine.py::layer_for(score)` returns the highest band:
- `>= 0.75` → `"niche"`
- `>= 0.65` → `"relevant"`
- `>= 0.55` → `"general"`
- below → `null` (kept in `top` but unlabeled — lenient mode preserves "honest signal" for niche profiles)

`LAYER_BANDS` is a single module constant; tunable in one line.

### F-LIVE-6 — Wildcard selection

`live_match` over-fetches `K + 30` from hybrid_search (the +30 buffer survives the household-name filter in F-LIVE-12). Top-K by score → `top`; the (K+1)th tool, if any, becomes `wildcard`. The frontend renders the wildcard as the "you might not expect" card on the result panel.

### F-LIVE-7 — `WEAVIATE_USE_GRPC` env flag (dev resilience)

`_get_weaviate_client()` reads `WEAVIATE_USE_GRPC` (default `"true"`).

When `"false"`: the v4 client is constructed with `skip_init_checks=True` and a 2s init timeout, configured to fall back to the REST `/v1/graphql` endpoint for queries (slower, but works on networks that block the gRPC subdomain).

When `"true"` (default): init timeout is now **8 seconds** (raised from the original 2s after VPN-routed handshakes consistently exceeded 2s). Per-op `query=10s, insert=10s`. Failure caches `_client = None` so subsequent calls short-circuit without re-trying until process restart.

### F-LIVE-8 — Frontend `/onboarding/live` page

`frontend/src/app/onboarding/live/page.tsx` ships behind the `MESH_ONBOARDING_VARIANT=live` flag. Same visual shell as the classic `/onboarding` (left-pane `ToolGraph` + right-pane `.onb-q-card`):

- **Q1**: 3 dropdowns inside the standard card.
- **Q2**: multi-select chips (role-conditioned via `GET /api/onboarding/live-questions/2/options?role={Q1.job_title}`).
- **Q3**: single-select scenarios (role-conditioned same way).
- **Q4**: single-select friction.

Between taps, a "matching… / Re-reading your profile" loader card replaces the question while `POST /live-step` runs. The graph shows real backend tools (not synthetic) — initial 40 from `GET /api/tools?limit=40`, then replaced after each step with the live-step `top + wildcard`. `gridSlots = graphTools.length` (no cap), so all returned tools sit on the inner ring.

Result panel after Q4 mirrors the classic `.onb-result` grid; the wildcard surfaces as a "you might not expect" card.

### F-LIVE-9 — Feature flag: classic vs live

New env: `MESH_ONBOARDING_VARIANT={"classic","live"}` (default `"classic"`).

`UserPublic.onboarding_variant` mirrors the env. Frontend reads it on `/api/me` and routes:
- `classic` → `/onboarding`
- `live` → `/onboarding/live`

Both routes bidirectionally redirect when the variant doesn't match (e.g., `/onboarding` redirects to `/onboarding/live` if variant=live, and vice versa) so users never strand on a flag-disabled page. Query strings (e.g., `?edit=1`) are preserved across the redirect.

### F-LIVE-10 — Persona walkthrough validation

`validation/approach1/results-live.md` records persona walkthroughs (Sales, Doctor, Marketer, SWE) against the live pipeline. SWE Q4 returns: `github-copilot · cursor · devin · linear · sweep · github-copilot-workspace` (wildcard: `windsurf`) — all engineering AI tools, household names filtered out. Comparable persona-to-niche fit on Sales, Doctor, Marketer.

### F-LIVE-11 — `/api/recommendations/live-state` for refresh persistence

`GET /api/recommendations/live-state` returns the user's saved live answers + the next-unanswered q_index:
```json
{
  "answers": {"1": {...}, "2": {...}, ...},
  "next_step": 1..4 | null
}
```

Frontend uses this on `/onboarding/live` mount to restore questionnaire state after a page refresh. If `next_step === null`, the user already finished all 4 — page jumps to the result panel and re-fires the latest live-step (one OpenAI embed) to repopulate the graph.

`?edit=1` query param overrides the restoration: forces step=1, done=false, but keeps the previously-saved answers pre-filled in the form. "Refine profile" links from `/home` use this to let users re-walk Q1→Q4 with their picks.

### F-LIVE-12 — Live-step writes to recommendations cache + household-name filter

After `live_match` returns, the live-step endpoint upserts a `recommendations` cache doc with `picks` populated from `result.top` (7-day TTL, same shape `engine.py` writes). `/home`'s `POST /api/recommendations` then hits the cache and returns the same tools the user saw at the end of the live flow — instantly, no GPT-5 rerank wait.

Tools tagged `all_time_best` in `tools_seed.labels` are dropped post-hydrate inside `live_match`. The live flow's job is to surface lesser-known fits, not re-recommend ChatGPT/Notion/Slack to people who already use them. Over-fetch is `K + 30` so `count_kept ≈ K` after filtering (household names cluster at the top of hybrid scores).

The `>=3 answers` gate on `POST /api/recommendations` is removed (cycle #6 gate made sense when classic flow was the only path; now blocks `/home` unnecessarily). Engine returns whatever it returns — empty list when nothing matches.

### F-LIVE-13 — Live-flow user data flows into `/home`

`/api/me/profile-summary` extended to merge `live_answers`:
- Q2 `selected_values` become `stack_tools` (with role-conditioned labels resolved from `ROLE_OPTIONS_Q2`).
- All Q1..Q4 values feed `all_answer_values` (powers the right-rail profile graph).
- The early-return on empty classic `answers` was removed so live-only users don't short-circuit.

`count_distinct_answers` (gate behind `/api/recommendations`'s `no_profile_yet` check) was extended to also count `live_answers` rows.

`/home` right-rail "Your matches" graph now uses real `recs.recommendations` tools as `tools` prop to `ToolGraph` (mirrors `/onboarding/live`). Tag chips below the graph are real tool names, each clickable to `/p/{slug}`.

`/home` "Fresh for you" section is always rendered (was hidden when empty); empty state shows a "→ start onboarding" CTA.

### F-LIVE-14 — Founder `/home` enrichments

`FounderHome` gains two new sections (alongside the existing "Your launches" + "Notifications"):

- **"Reach so far"** — only when ≥1 approved launch. 4 stat cards summing across all live launches: `users matched · tell-me-more · skip · total clicks`.
- **"What happens next"** — only when ≥1 pending launch. 6-step pipeline timeline (Submitted → Awaiting verification (in-progress dot) → Approved → Fanned out → Concierge scan → Tracking).

Empty state is a richer card with the value prop ("top 5% by ICP match, human-verified, never CPM") + 4-item prep checklist.

### F-LIVE-15 — `/p/[slug]` upvote + sidebar + matched-count

Two-column layout: main content + 280px sticky sidebar.

**Sidebar:**
- Clickable upvote pill (♡ score). Optimistic update; reverts on POST `/api/votes` failure. `target_type: "tool"`, `target_id: tool.id` (newly exposed). Voting now works on founder-launched tools too (`apply_vote` and `_bump_target_score` fall back to `tools_founder_launched` when slug isn't in `tools_seed`).
- "Open ↗" + "+ Save to my tools" CTAs.
- Metadata grid: category, pricing, source, **matched** (N profiles, accent color, only for founder launches), discuss link.

**Main column:**
- Eyebrow + title + tagline + label/pricing/launch chips.
- "About" — only for curated tools (founder launches duplicate this content via the launch card; About would be redundant).
- "Why this exists" card with structured Problem / Built-for sections (`pre-line` whitespace so the founder's `Who: / Job: / Pain:` lines stay separate). Footer chips: approved-date · `live in N rooms` · **matched N profiles**.
- "Discuss" section: chips deep-linking to each `/c/{slug}` the launch was fanned out to.

**Models:**
- `ProductCard.id` exposed (string ObjectId) for vote target_id.
- `LaunchMeta.target_community_slugs` exposed for discuss links.
- `LaunchMeta.matched_count` exposed; pulled at request time from `app/founders/analytics.py::matched_count(launch_id)` which counts distinct user_ids in `engagements` where `surface=concierge_nudge` and `action=view`.

### F-LIVE-16 — Auto-approver background task (DEMO/TESTING ONLY)

New env: `AUTO_APPROVE_LAUNCHES_AFTER_SECONDS=N` (default 0 = off).

When set, `app/main.py` lifespan spawns a background asyncio task (`app/tasks/auto_approve.py::run_auto_approver_loop`) that polls every 30s for `verification_status: pending` launches older than N seconds and approves them through the same service path as the admin endpoint.

Refactor: extracted approval body from `app/api/admin_launches.py` into `app/launches/approve.py::approve_launch(launch_id, reviewed_by)`. The admin endpoint is now a thin wrapper around the service. Auto-approver passes `reviewed_by="auto-approver@mesh.local"`.

**Production safety**: default OFF. Real launches always require human review. The flag exists for local demo/testing where the founder needs to see the full downstream pipeline (community fan-out, concierge scan, /home reach summary) without waiting for manual admin clicks.

### F-LIVE-17 — Friendly auth error messages

`/signup` and `/login` map backend error codes to plain-English messages:
- `email_already_registered` → "That email is already registered. Try logging in instead." + inline `Log in →` link to `/login`
- `invalid_credentials` → "Wrong email or password."
- `rate_limited` → "Too many attempts. Wait a minute and try again."
- `password_too_short` / `invalid_email` → field-specific copy

---

## Cycle #15 — Weaviate schema extension (BM25 surface)

### F-WV-2 — Extend `ToolEmbedding` class with full-text BM25 properties

`init_weaviate_schema` is now an additive migration: when the class already exists, it calls `collections.config.add_property` to add any properties missing from the spec. Used to extend `ToolEmbedding` with three text properties so the BM25 side of hybrid search has rich phrasing to match against:
- `name` (text)
- `tagline` (text)
- `description` (text)

All `publish_tool` callers (`app/embeddings/lifecycle.py`, `app/launches/publish.py`, `app/embeddings/republish.py`) now include these fields. One-time backfill via `python -m app.embeddings republish-tools` brings existing rows up to spec (546 tools republished cleanly during cycle #15).
