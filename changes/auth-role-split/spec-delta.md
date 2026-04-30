# Spec Delta: auth-role-split

## ADDED

### F-AUTH-1 — User signup with role selection

**Given** a visitor without an account
**When** they `POST /api/auth/signup` with `{ email, password, role_question_answer }` where `role_question_answer ∈ {"finding_tools", "launching_product"}`
**Then** the system creates a `users` row with:
- `email` (validated, lowercased)
- `password_hash` (bcrypt, rounds=12)
- `role_type = "user"` if `role_question_answer == "finding_tools"`, else `"founder"`
- `created_at = now`, `last_active_at = now`
- `display_name = email-localpart`

**And** returns `{ jwt, user: { id, email, role_type, display_name } }`
**And** subsequent requests with that JWT are authenticated as this user.

#### Error: duplicate email

**Given** an account with email `E` already exists
**When** signup is called with `email = E`
**Then** the system returns `409 Conflict` with `{"error": "email_already_registered"}` and no row is created.

#### Error: invalid role question answer

**Given** a signup payload
**When** `role_question_answer` is missing or not in `{"finding_tools", "launching_product"}`
**Then** the system returns `400 Bad Request` with `{"error": "role_question_required"}`.

#### Error: weak password

**Given** a signup payload
**When** `password.length < 8`
**Then** the system returns `400 Bad Request` with `{"error": "password_too_short"}`.

#### Error: malformed email

**Given** a signup payload
**When** `email` does not match a basic email regex
**Then** the system returns `400 Bad Request` with `{"error": "email_invalid"}`.

---

### F-AUTH-2 — User login

**Given** an account with email `E` and password `P`
**When** they `POST /api/auth/login` with `{ email: E, password: P }`
**Then** the system returns `{ jwt, user: { id, email, role_type, display_name } }`
**And** updates `users.last_active_at = now`.

#### Error: wrong password

**Given** an account with email `E`
**When** login is called with the correct email but incorrect password
**Then** the system returns `401 Unauthorized` with `{"error": "invalid_credentials"}`.

#### Error: unknown email

**Given** no account exists for email `E`
**When** login is called for `E`
**Then** the system returns `401 Unauthorized` with `{"error": "invalid_credentials"}` — *the same error message as wrong-password, intentional, to avoid leaking account existence.*

---

### F-AUTH-3 — Role-aware request middleware

A FastAPI dependency factory `require_role(role: Literal["user", "founder"])` is exposed for endpoints to decorate with.

**Given** an endpoint declared as `Depends(require_role("user"))`
**When** an authenticated caller with `role_type=user` requests it
**Then** the endpoint executes normally.

**When** an authenticated caller with `role_type=founder` requests it
**Then** the system returns `403 Forbidden` with `{"error": "role_mismatch", "required": "user", "actual": "founder"}`.

**When** an unauthenticated request is made
**Then** the system returns `401 Unauthorized` with `{"error": "auth_required"}`.

(Symmetric behavior for `Depends(require_role("founder"))`.)

---

### F-AUTH-4 — Role is non-transferable at the data layer

**Given** an account with `role_type = X`
**When** any request attempts to change `users.role_type` (via `/api/me`, `PATCH`, direct field write, or any other path)
**Then** the request is rejected; `role_type` remains `X`.

**Implementation contract:** the API layer exposes no endpoint that mutates `role_type`. The `users` Pydantic update model excludes `role_type`. Code review treats any introduction of a `role_type` setter path as a constitutional regression.

---

### F-AUTH-5 — Current-user endpoint

**Given** an authenticated request with a valid JWT
**When** the caller requests `GET /api/me`
**Then** the system returns `{ id, email, role_type, display_name, created_at, last_active_at }`.

**Given** no JWT or an invalid JWT
**When** the caller requests `GET /api/me`
**Then** the system returns `401 Unauthorized` with `{"error": "auth_required"}`.

---

### F-AUTH-6 — Smoke endpoints prove middleware contract

**Given** the role middleware is wired
**When** `GET /api/me/user-only` and `GET /api/me/founder-only` exist (each `Depends(require_role(...))`)
**Then** each returns the current user's payload only when the role matches; otherwise the F-AUTH-3 error contract applies.

These endpoints exist in V1 to verify the middleware contract during manual testing. They MAY be removed in a later cycle once the contract is exercised by real role-gated endpoints.

## MODIFIED

(None — no prior auth surface exists.)

## REMOVED

(None.)
