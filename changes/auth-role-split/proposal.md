# Proposal: auth-role-split

## Problem

Mesh's *"Never let founder accounts post in user communities"* principle (`specs/constitution/principles.md`) is a structural commitment — every other feature in the V1 backlog (communities, launches, recommendations, tools page) depends on a non-transferable role flag existing on every account at the moment of signup. Without auth + role at the foundation, no downstream cycle can start.

## Solution

Email + password authentication on FastAPI with a single signup question — *"What brought you here?"* — that maps user intent to an internal `role_type` of `user` or `founder`. JWT-based session. Role-aware middleware that endpoints can declare a required role on, enforced once at the request boundary.

## Scope

**In:**
- `POST /api/auth/signup` and `POST /api/auth/login` — email + password + the role question
- `GET /api/me` — returns the current authenticated user
- JWT session (HS256, 7-day expiry — transport choice (Authorization header vs httpOnly cookie) decided in `tasks.md`)
- `bcrypt` password hashing (rounds=12)
- `users` collection: `email`, `password_hash`, `role_type` (set at signup, **non-transferable**), `created_at`, `last_active_at`, `display_name` (defaults to email-localpart)
- Role-aware FastAPI dependency factory `require_role(role)` — endpoint declares its required role, middleware rejects mismatched callers with 403
- Two smoke-test endpoints (`GET /api/me/user-only`, `GET /api/me/founder-only`) used to verify the middleware contract

**Out (deferred to later cycles or "as needed"):**
- Email verification flow — V1 trusts the email at signup; add a small cycle later if dead-account rate exceeds 5%
- Password reset flow — admin DB op if anyone gets locked out during the manual cohort
- Rate limiting (`slowapi`, Redis-based, anything else) — defer until traffic justifies it
- Invite tree — a separate cycle slotted before #7 (`communities-and-flat-comments`)
- OAuth / social login, 2FA, account deletion / data export

## Alternatives Considered

1. **OAuth-only (no password)** — rejected. Adds a third-party dependency during a manual user-test phase where you want full control over who is in the system.
2. **Single account class with a mutable role** — rejected. Violates *"Never let founder accounts post in user communities"* — a founder could flip to user, post in communities, flip back. The non-transferable role is a constitutional choice, not UX preference.
3. **Separate auth services per role** — rejected. Two parallel auth surfaces double the bug surface and double the testing while buying nothing.

## Risks

1. **The single role question feels like a binary that some users may misclick.** Mitigation: copy is reviewable; if misclick rate is observable post-launch, copy gets a `/vkf/amend` C0/C1 and the question text is updated. Default-no-answer is not allowed at the API layer.
2. **Non-transferable role surprises users who later want to launch.** A user-account user who ships a product later cannot flip; they must create a second account (different email). This is the deliberate trade-off behind the constitutional principle. Mitigation: surface this explicitly at signup ("This choice cannot be changed later").
3. **No email verification means typos create dead accounts.** Mitigation: acceptable risk for V1; if dead-account rate exceeds 5% in the manual cohort, queue an `email-verification-flow` cycle.
4. **bcrypt cost-factor surprises.** Too low = weak hashes; too high = slow signup/login. Mitigation: `bcrypt.gensalt(rounds=12)` (current 2026 default).

## Rollback

- Drop the `users` collection.
- Delete the auth router from FastAPI.
- Remove the role middleware dependency.
- Revert this cycle's commit and delete the `auth-role-split` branch.

No downstream data depends on this cycle yet (cycle #2 hasn't started). Rollback cost is low and bounded.
