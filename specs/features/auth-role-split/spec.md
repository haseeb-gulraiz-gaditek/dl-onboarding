# Feature: Authentication and Role-Split

> **Cycle of origin:** `auth-role-split` (archived; see `archive/auth-role-split/`)
> **Last reviewed:** 2026-04-30
> **Constitution touchpoints:** `principles.md` (*"Never let founder accounts post in user communities"*, *"Anti-spam is structural, not enforced"*), `personas.md` (Maya — `role_type=user`; Aamir — `role_type=founder`).

---

## Intent

Mesh's two-sided product needs every account to carry a non-transferable role flag from the moment of signup. The role flag is the structural foundation that lets every downstream feature (communities, launches, recommendations, the founder dashboard) enforce the user-founder boundary at the request layer instead of through moderation. This feature delivers that flag and the auth surface it travels through.

A single signup question captures user intent — *"What brought you here?"* with answers `finding_tools` (→ `role_type=user`) or `launching_product` (→ `role_type=founder`) — and the answer is locked into the account at insert. There is no API path that mutates `role_type` afterward; a user who later wants to launch a product creates a second account.

## Surface

- `POST /api/auth/signup` — create account
- `POST /api/auth/login` — authenticate, receive JWT
- `GET /api/me` — read current user
- `GET /api/me/user-only` — smoke endpoint behind `require_role("user")`
- `GET /api/me/founder-only` — smoke endpoint behind `require_role("founder")`

JWT transport: `Authorization: Bearer <token>` header. HS256, 7-day expiry. Configured via `JWT_SECRET` and `JWT_EXPIRY_DAYS` environment variables.

---

## F-AUTH-1 — Signup with role selection

**Given** a visitor without an account
**When** they `POST /api/auth/signup` with `{ email, password, role_question_answer }` where `role_question_answer ∈ {"finding_tools", "launching_product"}`
**Then** the system creates a `users` row with `email` (lowercased), `password_hash` (bcrypt, rounds=12), `role_type = "user"` if `role_question_answer == "finding_tools"` else `"founder"`, `created_at = now`, `last_active_at = now`, `display_name = email-localpart`
**And** returns `{ jwt, user: { id, email, role_type, display_name, created_at, last_active_at } }`

### Errors

- **Duplicate email** — existing email returns `409 Conflict` with `{"error": "email_already_registered"}` and no row is created.
- **Invalid role question answer** — missing or not in the allowed set returns `400` with `{"error": "role_question_required"}`.
- **Weak password** — `password.length < 8` returns `400` with `{"error": "password_too_short"}`.
- **Malformed email** — non-email string returns `400` with `{"error": "email_invalid"}`.

---

## F-AUTH-2 — Login

**Given** an account with email `E` and password `P`
**When** they `POST /api/auth/login` with `{ email: E, password: P }`
**Then** the system returns `{ jwt, user: { ... } }` and updates `users.last_active_at = now`.

### Errors

- **Wrong password** — returns `401` with `{"error": "invalid_credentials"}`.
- **Unknown email** — returns `401` with `{"error": "invalid_credentials"}` *— intentionally the same message as wrong-password to avoid leaking account existence.*

---

## F-AUTH-3 — Role-aware request middleware

A FastAPI dependency factory `require_role(role: Literal["user", "founder"])` is exposed for endpoints to declare a required role.

**Given** an endpoint declared as `Depends(require_role("user"))`:

- An authenticated caller with matching `role_type` is allowed through.
- An authenticated caller with the wrong `role_type` receives `403 Forbidden` with `{"error": "role_mismatch", "required": "user", "actual": "founder"}`.
- An unauthenticated request receives `401 Unauthorized` with `{"error": "auth_required"}`.

The behavior is symmetric for `require_role("founder")`.

---

## F-AUTH-4 — Role is non-transferable

**Given** an account with `role_type = X`
**When** any request attempts to change `users.role_type` (via `/api/me`, a PATCH/PUT/POST on any user resource, a re-signup with the same email and a different answer, or any other path)
**Then** `role_type` remains `X`.

**Implementation contract:**
- The API exposes no endpoint that accepts a `role_type` write.
- The Pydantic models for any update operation on `users` exclude `role_type` from their accepted fields.
- A re-signup with a duplicate email returns `409` (per F-AUTH-1) without mutating the existing row.
- An audit test (`tests/test_role_immutability.py`) confirms PATCH/PUT/POST on the user resource with a `role_type` body are rejected (404 or 405).

Code review treats any introduction of a `role_type` write path as a constitutional regression against the principle *"Never let founder accounts post in user communities"*.

---

## F-AUTH-5 — Current-user endpoint

**Given** an authenticated request with a valid JWT
**When** `GET /api/me` is called
**Then** the system returns `{ id, email, role_type, display_name, created_at, last_active_at }`.

**Given** no JWT or an invalid/expired JWT
**When** `GET /api/me` is called
**Then** the system returns `401 Unauthorized` with `{"error": "auth_required"}`.

---

## F-AUTH-6 — Smoke endpoints prove middleware contract

`GET /api/me/user-only` and `GET /api/me/founder-only` exist behind `require_role(...)` to verify the middleware contract during manual testing. They return the F-AUTH-5 payload only when the role matches; otherwise the F-AUTH-3 error contract applies.

These endpoints MAY be removed in a later cycle once the contract is exercised by real role-gated endpoints in production code.

---

## Architectural notes

- **Password hashing:** bcrypt with `rounds=12` (2026 default). Tunable in `app/auth/passwords.py` if signup/login latency becomes hashing-bound.
- **JWT signing:** HS256 with the secret read from `JWT_SECRET` at request time. App refuses to boot if `JWT_SECRET` or `MONGODB_URI` is unset or blank (lifespan startup check).
- **Email storage:** lowercased on insert; unique index on `users.email` enforces case-insensitive uniqueness at the storage layer.
- **JWT transport choice — header, not cookie:** Mesh V1 uses `Authorization: Bearer`. The decision is documented in the docstring of `app/auth/jwt.py`. A future cycle MAY introduce httpOnly cookie transport behind a same-origin proxy if XSS-resistance becomes a load-bearing concern.

## Out of scope (V1 deferrals)

The following are explicitly NOT part of this feature and will be addressed in later cycles or as needed:

- Email verification flow (signup trusts the email)
- Password reset flow (admin DB op if anyone gets locked out during the manual cohort)
- Rate limiting (no slowapi, no Redis-backed limits)
- Invite tree / invite-code redemption (a separate cycle slotted before `communities-and-flat-comments`)
- OAuth / social login, 2FA, account deletion / data export
