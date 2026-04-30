# Tasks: auth-role-split

## Implementation Checklist

### Project scaffolding (pre-cycle bootstrap — done once, inherited by future cycles)
- [x] Create `requirements.txt` with: `fastapi`, `uvicorn[standard]`, `motor` (async MongoDB), `bcrypt`, `pyjwt`, `pydantic[email]`, `python-dotenv`, `pytest`, `pytest-asyncio`, `httpx`, `mongomock-motor` (V1: single combined file for runtime + dev)
- [x] Project layout: `app/main.py` (FastAPI app + `GET /health`), `app/api/` (routers), `app/db/mongo.py` (Motor client, env-driven URI), `app/models/` (Pydantic schemas), `tests/`
- [x] `.env.example` listing required vars: `MONGODB_URI`, `JWT_SECRET`, `JWT_EXPIRY_DAYS=7`
- [x] `docker-compose.yml` for local MongoDB (Mongo 7+ image, port 27017, named volume) — single service, single command to run
- [x] `README` snippet at repo root or `app/README.md`: how to install deps, run Mongo (`docker compose up`), run the dev server (`uvicorn app.main:app --reload --port 8000`), run tests (`pytest`)
- [x] `pytest.ini` with async mode = `auto`, testpaths=`tests`, pythonpath=`.`

### Schema + DB
- [x] Define MongoDB `users` collection schema: `email`, `password_hash`, `role_type` (`"user"` | `"founder"`), `created_at`, `last_active_at`, `display_name`
- [x] Add unique index on `users.email` (case-insensitive — store lowercased)
- [x] Confirm `role_type` has no API mutation path (no setter, no PATCH, not in any update model)

### Auth core
- [x] Implement `hash_password(plain) -> str` and `verify_password(plain, hash) -> bool` using `bcrypt` with `rounds=12`
- [x] Implement `issue_jwt(user) -> str` and `decode_jwt(token) -> claims` using HS256 + `JWT_SECRET` env var (7-day expiry)
- [x] **Decide JWT transport** (Authorization header OR httpOnly cookie) — document the choice in a comment at the top of the auth router before implementing → **Authorization header (Bearer token)**, documented at top of `app/auth/jwt.py`

### Endpoints
- [x] `POST /api/auth/signup` — validate payload (email regex, password ≥ 8, `role_question_answer ∈ {"finding_tools", "launching_product"}`), insert user, return JWT + user payload (F-AUTH-1)
- [x] `POST /api/auth/login` — verify credentials, update `last_active_at`, return JWT + user payload (F-AUTH-2)
- [x] `GET /api/me` — return current user (F-AUTH-5)
- [x] `GET /api/me/user-only` — smoke endpoint behind `require_role("user")` (F-AUTH-6)
- [x] `GET /api/me/founder-only` — smoke endpoint behind `require_role("founder")` (F-AUTH-6)

### Middleware
- [x] FastAPI dependency `current_user` — parse JWT, load user, return user object or raise 401 (F-AUTH-5 error path)
- [x] FastAPI dependency factory `require_role(role: Literal["user", "founder"])` — composes `current_user`, raises 403 on role mismatch (F-AUTH-3)

### Tests (one per Given/When/Then in spec-delta)
- [x] F-AUTH-1: signup happy path — `finding_tools` → `role_type=user`
- [x] F-AUTH-1: signup happy path — `launching_product` → `role_type=founder`
- [x] F-AUTH-1: signup duplicate email → 409
- [x] F-AUTH-1: signup invalid role_question_answer → 400
- [x] F-AUTH-1: signup weak password → 400
- [x] F-AUTH-1: signup malformed email → 400
- [x] F-AUTH-2: login happy path → JWT issued, `last_active_at` updated
- [x] F-AUTH-2: login wrong password → 401 invalid_credentials
- [x] F-AUTH-2: login unknown email → 401 invalid_credentials (same error message as wrong password)
- [x] F-AUTH-3: middleware accepts matching role
- [x] F-AUTH-3: middleware rejects mismatched role with 403
- [x] F-AUTH-3: middleware rejects unauthenticated with 401
- [x] F-AUTH-4: no API path mutates `role_type` (audited test — attempt PATCH /api/me with `{role_type: "..."}` returns 4xx and DB row is unchanged)
- [x] F-AUTH-5: `/api/me` returns user payload with valid JWT
- [x] F-AUTH-5: `/api/me` returns 401 with no JWT or invalid JWT

## Validation

- [ ] All implementation tasks above checked off
- [ ] All tests pass
- [ ] Manual smoke: sign up two accounts (different emails, one each role), confirm `/api/me/user-only` 200s for the user account and 403s for the founder account; symmetric for `/api/me/founder-only`
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: `role_type` is set on insert only, never written by any API path
