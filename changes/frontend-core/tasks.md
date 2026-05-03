# Tasks: frontend-core

## Implementation Checklist

### Backend addition (one new endpoint + CORS)
- [x] `app/db/community_memberships.py` — extend `find_for_user(user_id)` if needed (already exists; verify it returns docs joinable with communities)
- [x] `app/api/me_communities.py` — `GET /api/me/communities` behind require_role("user"). Returns `{communities: [...]}` with `joined_at DESC` ordering. Each entry projects CommunityCard + `joined_at`.
- [x] `app/models/community.py` — add `JoinedCommunityCard` (CommunityCard + joined_at: datetime); reuse to_community_card
- [x] Mount the router in `app/main.py`
- [x] Add CORSMiddleware to `app/main.py` reading `CORS_ORIGINS` env (comma-separated; default "http://localhost:3000"). Allow credentials, all methods, all headers.
- [x] `.env.example` — add `CORS_ORIGINS=http://localhost:3000` line

### Backend tests for the new endpoint
- [x] F-FE-2: GET /api/me/communities returns the user's joined communities sorted by joined_at DESC
- [x] F-FE-2: founder caller → 403 role_mismatch
- [x] F-FE-2: unauthenticated → 401 auth_required
- [x] F-FE-2: user with zero memberships → returns empty list

### Frontend scaffold
- [x] Create `frontend/` directory at repo root
- [x] Copy `package.json`, `tsconfig.json`, `next.config.js`, `next-env.d.ts`, `.eslintrc.json`, `.gitignore` from `scratch/mesh-app`
- [x] Copy `src/styles/*` from scratch/mesh-app
- [x] Copy `src/components/{Primitives,ToolGraph,CommunityGraph}.tsx` unchanged
- [x] Copy `src/lib/types.ts` (we'll extend it for API types)
- [x] `frontend/.env.local.example` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

### API client + auth
- [x] `frontend/src/lib/api.ts` — typed fetch wrapper (get/post/patch/del); reads NEXT_PUBLIC_API_BASE_URL; injects Bearer header from localStorage; on 401 clears JWT + redirects to /onboarding; throws ApiError on non-2xx
- [x] `frontend/src/lib/api-types.ts` — TS interfaces mirroring app/models/*: AuthResponse, UserPublic, NextQuestionResponse, AnswerCreate, RecommendationsResponse, RecommendationPick, OnboardingToolCard, CommunityCard, JoinedCommunityCard, NotificationCard, UserToolCard, ToolCardWithFlags, ProductPageResponse, LaunchSubmitRequest, LaunchResponse
- [x] `frontend/src/lib/auth.ts` — signup, login, logout, currentUser; persists JWT to localStorage["mesh.jwt"]
- [x] `frontend/src/lib/tag-map.ts` — tagsForOptionValue helper: tool slugs → tag arrays from baked MESH_TOOLS table; role/friction strings → hand-maintained map mirroring scratch/mesh-app's hardcoded data

### Routes (5)
- [x] `frontend/src/app/layout.tsx` — copy from scratch/mesh-app
- [x] `frontend/src/app/page.tsx` (landing) — copy from scratch/mesh-app; static, no API
- [x] `frontend/src/app/(landing)/_sections.tsx` + `_sections2.tsx` — copy from scratch/mesh-app
- [x] `frontend/src/app/onboarding/page.tsx` — wire signup form + GET /api/questions/next loop + POST /api/answers + result via POST /api/recommendations + GET /api/communities pills. Tags via tag-map. CTA → /home.
- [x] `frontend/src/app/home/page.tsx` — left rail (stack from /api/me/tools, profile from /api/me) + center (notifications, recommendations, /api/me/communities) + right (canvas profile graph + hardcoded activity feed)
- [x] `frontend/src/app/founders/launch/page.tsx` — 6-step form + CommunityGraph community-picker + serializer maps form → POST /api/founders/launch payload + pending screen on success
- [x] `frontend/src/app/p/[slug]/page.tsx` — canonical product page from GET /api/tools/{slug}; "Save to my tools" button (only for user role) → POST /api/me/tools

### Repo wiring
- [x] Top-level `README.md` — add "Two-process layout" section + dev commands
- [x] `scripts/dev.sh` — bash script running uvicorn + npm run dev concurrently (uses `&`/`wait`/trap SIGINT)
- [x] `.gitignore` updates if needed (frontend/.next, frontend/node_modules)

### Smoke prep (no automated frontend tests in this cycle)
- [x] Verify `npm install` + `npm run dev` boots the Next.js app
- [x] Verify `npm run build` succeeds (catches TS errors)
- [x] Verify `npm run type-check` passes

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full backend test suite green (cycles #1-#12 must continue to pass)
- [ ] Backend tests for /api/me/communities pass
- [ ] Smoke: with both processes running, sign up via /onboarding → answer 5 questions → land on /home → see your stack, your communities, nudges, fresh-for-you populated from real DB
- [ ] Smoke: fill /founders/launch as a founder → POST /api/founders/launch row appears in launches collection
- [ ] Smoke: /p/<seed-tool-slug> shows the tool card; /p/<acme-io> after admin approval shows founder LaunchMeta
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: existing 276 tests still green; new endpoint enforces require_role(user); CORS doesn't expose admin endpoints to public origins
