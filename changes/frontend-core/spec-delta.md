# Spec Delta: frontend-core

## ADDED

### F-FE-1 — Repo layout (monorepo)

The repo gains a sibling `frontend/` directory next to `app/`. Two-process dev:

```
dl-onboarding/
├── app/                # FastAPI (cycles #1-#12; unchanged)
├── frontend/           # NEW: Next.js 14 App Router
├── tests/              # backend pytest suite (unchanged)
├── specs/, archive/    # SDD artifacts (unchanged)
└── README.md           # documents the two-process layout
```

`app/` is NOT renamed to `backend/` — sweeping import + test + CLI churn outweighs the aesthetic gain. README documents the asymmetry. Build, test, and deploy commands stay independent per package.

---

### F-FE-2 — `GET /api/me/communities` (backend addition)

A new endpoint behind `require_role("user")`. Returns the requesting user's joined communities.

Response:
```json
{
  "communities": [
    {
      "id": "<oid>",
      "slug": "marketing-ops",
      "name": "Marketing Ops",
      "description": "...",
      "category": "role",
      "member_count": 42,
      "joined_at": "2026-05-03T..."
    }
  ]
}
```

Sort: `community_memberships.joined_at DESC` (most-recently-joined first).

**Given** an authenticated user with three community memberships
**When** they `GET /api/me/communities`
**Then** the system returns `200 OK` with the three communities in `joined_at DESC` order, each enriched with the community fields.

**User caller** → returns own list.
**Founder caller** → `403 role_mismatch`.
**Unauthenticated** → `401 auth_required`.

`joined_at` is the only field added to `CommunityCard` for this endpoint. Other consumers of `CommunityCard` (cycle #7 F-COM-1) ignore the field.

---

### F-FE-3 — CORS middleware on FastAPI

`app/main.py` gains FastAPI's `CORSMiddleware` configured from a `CORS_ORIGINS` env var (comma-separated). Default in dev: `http://localhost:3000`. Methods: all. Headers: `Authorization, Content-Type, *`. Credentials: `True` (forward-compat for cookie auth in V1.5).

`_REQUIRED_ENV` does NOT add `CORS_ORIGINS` — absence falls back to dev default.

In production, `CORS_ORIGINS` is set to the deployed frontend URL.

---

### F-FE-4 — Frontend scaffold

`frontend/` initialized from the `scratch/mesh-app/` template:

- `package.json`: Next 14.2.5, React 18.3.1, TypeScript 5.5
- `tsconfig.json`: strict mode, `@/*` → `./src/*` paths
- `next.config.js`: `reactStrictMode: true`
- `next-env.d.ts`, `.eslintrc.json`, `.gitignore`
- `src/styles/`: tokens.css, components.css, globals.css, landing.css, onboarding.css, home.css, founders.css (community.css, concierge.css ride along but unused in this cycle)
- `src/components/`: `Primitives.tsx`, `ToolGraph.tsx`, `CommunityGraph.tsx` from mesh-app, unmodified

The `scratch/mesh-app/` folder is left as historical reference — NOT deleted (it's the design source).

---

### F-FE-5 — API client + auth (frontend)

`frontend/src/lib/api.ts` exports a typed `api` object:

```ts
api.get<T>(path: string, opts?: ApiOpts): Promise<T>
api.post<T>(path: string, body?: unknown, opts?: ApiOpts): Promise<T>
api.patch<T>(path: string, body?: unknown, opts?: ApiOpts): Promise<T>
api.del<T>(path: string, opts?: ApiOpts): Promise<T>
```

- Reads `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).
- For authed requests (`opts.auth = true` is the default), reads `localStorage["mesh.jwt"]` and sends `Authorization: Bearer <jwt>`.
- On `401` response: clears `localStorage["mesh.jwt"]` and triggers `window.location.assign("/onboarding")`.
- On non-2xx, throws an `ApiError` with `{status, body}` for the caller to handle (e.g., 400 `field_required`).
- Returns parsed JSON typed via the call-site generic.

`frontend/src/lib/auth.ts` exports:
- `signup({email, password, role_question_answer})` → `{user, jwt}` (calls `/api/auth/signup`, persists JWT)
- `login({email, password})` → `{user, jwt}`
- `logout()` → clears JWT + redirects to `/`
- `currentUser()` → `User | null` (calls `/api/me` on first invocation; cached)

TypeScript interfaces for response shapes live in `frontend/src/lib/api-types.ts`, hand-mirrored from the Pydantic models in `app/models/*`. V1.5 considers OpenAPI-driven codegen.

---

### F-FE-6 — `/onboarding` route (signup + tap-question loop + result)

A combined onboarding flow at `/onboarding`:

**Stage 1 — first-time signup:**
The page checks for `localStorage["mesh.jwt"]`. If absent, the question card is replaced with an email/password form alongside a one-line "I'm finding my right AI tools" preselected radio. On submit, `POST /api/auth/signup` with `role_question_answer="finding_tools"`. JWT stored, page re-renders.

**Stage 2 — tap loop:**
- `GET /api/questions/next` → renders the next question.
- For `kind: single_select` → option buttons; click auto-advances (existing design).
- For `kind: multi_select` → checkbox-style options + Continue button.
- For `kind: free_text` → input + save; Continue.
- On every answer, `POST /api/answers` with `{question_id, value}`.
- The live ToolGraph derives tags from accumulated answers via `frontend/src/lib/tag-map.ts`. This module exposes `tagsForOptionValue(value: string): string[]` — for tool-slug values it consults a baked-in `MESH_TOOLS` map; for role/friction strings it looks up a hand-maintained map mirroring the design's hardcoded data.

**Stage 3 — result:**
After 5 answers (or when `/api/questions/next` returns a sentinel signaling completion — TBD; V1 simply counts answers), the page calls `POST /api/recommendations` with `{count: 5}`. Renders:
- Up to 4 cards from `recommendations[]` where `verdict: "try"` (or any verdict if the count drops below 4).
- 1 "skip this" card from `recommendations[]` where `verdict: "skip"` if present; otherwise a generic "skip a hyped one we don't recommend" placeholder.
- `launches[]` array (cycle #9 F-PUB-6) is also rendered as a small "fresh launches" footer if non-empty.
- Community pills: `GET /api/communities` → top 3 by `member_count`.

"Enter Mesh" CTA navigates to `/home`.

---

### F-FE-7 — `/home` route

Three-column shell wired against:

| Surface | Endpoint |
|---|---|
| Greeting + unread count | `GET /api/me/notifications/unread-count` (cycle #12) |
| Nudge cards | `GET /api/me/notifications?unread_only=true&limit=4` (cycle #12), mapped to design taxonomy |
| Fresh-for-you strip | `POST /api/recommendations` — render `recommendations[]` first, then `launches[]` cards with a small "🚀 launch" tag |
| Your stack list | `GET /api/me/tools` (cycle #10) |
| Your communities | `GET /api/me/communities` (F-FE-2) |
| Profile name | `GET /api/me` (cycle #1) |
| Activity feed | HARDCODED 5 sample rows; comment marks V1.5 |
| Profile graph (right) | renders accumulated tags from `/api/me` answers; canvas-only, no API |

Notification → nudge UI mapping (frontend helper):
- `concierge_nudge` → `kind: "fresh"` (launch matched the user's profile)
- `launch_approved` → `kind: "mod"` (a founder you'd like is launching) — only relevant if a future cycle wires this for users
- `community_reply` → `kind: "pattern"` (community activity)
- everything else → `kind: "fresh"` fallback

---

### F-FE-8 — `/founders/launch` route

6-step form. Maps to `POST /api/founders/launch`:

| Form field | Backend field |
|---|---|
| `name` (text) | display only — NOT persisted |
| `product_url` (text, http(s)) | `product_url` (required) |
| `oneliner` (text) | folded into `problem_statement` if `pitch` empty |
| `category` (single-select) | concatenated into `icp_description` (prefix `Category: ...`) |
| `replaces` (multi-select tools) | concatenated into `icp_description` (`Replaces: a, b, c`) |
| `audience` (multi-select roles) | concatenated into `icp_description` (`Audience: roles`) |
| `pricing` (single-select) | concatenated into `icp_description` (`Pricing: ...`) |
| `pitch` (longtext, optional) | `problem_statement` (overrides oneliner) |
| `target_community_slugs` (1..6) | `target_community_slugs` — picked via clicking nodes on the live CommunityGraph |
| `existing_presence_links` (text, comma-separated, optional) | parsed → `existing_presence_links: list[str]` |

The icp_description concatenation uses `\n\n` separators with section markers so admins reading the raw doc can parse:

```
Category: AI / agent
Audience: Solo founders, Staff PMs
Pricing: Per-seat SaaS
Replaces: Notion, Linear
```

Submit handler validates: product_url is http(s), problem_statement non-empty, target_community_slugs has 1..6 entries. POSTs to `/api/founders/launch`. On success, navigates to a pending screen showing the picked communities + "we'll notify you when it's approved" copy.

---

### F-FE-9 — `/p/[slug]` route

Canonical product page wired to `GET /api/tools/{slug}` (cycle #9 F-PUB-4). Renders:
- Tool card (slug, name, tagline, description, url, pricing_summary, category, labels, vote_score, is_founder_launched)
- LaunchMeta block when `is_founder_launched=true` (founder display name, problem_statement, approved_at)
- "Save to my tools" button → `POST /api/me/tools` (cycle #10) — only visible to user-role accounts; hidden for founders

---

### F-FE-10 — Frontend dev workflow

Repo root `README.md` gains a section documenting:

1. Backend: `python -m uvicorn app.main:app --reload --port 8000`
2. Frontend: `cd frontend && npm install && npm run dev`
3. Env: backend reads `CORS_ORIGINS`; frontend reads `NEXT_PUBLIC_API_BASE_URL`
4. Demo flow: open `http://localhost:3000` → land → onboarding → home

A new optional script `scripts/dev.sh` runs both processes via `&` (no Procfile / concurrently dependency for V1).

## MODIFIED

### `app/main.py` (cycles #1-#12)

**Before:** No CORS middleware.
**After:** `app.add_middleware(CORSMiddleware, ...)` at startup; origins from `CORS_ORIGINS` env (default `http://localhost:3000`); credentials allowed; all methods + headers.

### Top-level `README.md`

**Before:** STD-002 + STD-001 framing only; no frontend mention.
**After:** Adds a "Two-process layout" section pointing at `app/` and `frontend/` plus the dev commands.

## REMOVED

(None.)
