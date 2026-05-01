# Tasks: catalog-seed-and-curation

## Implementation Checklist

### Schema + DB
- [x] Define `app/db/tools_seed.py` collection access layer + `ensure_indexes()` (unique index on `slug`; compound `(curation_status, category)`)
- [x] Helpers: `upsert_tool_by_slug` (refuses to overwrite rows with `source="founder_launch"` via Mongo `$ne` filter), `find_tool_by_slug`, `list_tools_by_status`, `set_status` (handles approve/reject + reviewer metadata)
- [x] Wire `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models
- [ ] `app/models/tool.py` — `Category` and `Label` literal types matching the prompt's enums; `Tool` (DB shape), `ToolPublic` (client shape with `id` as string), `ToolReject` (request body for reject endpoint), `to_public(doc)` helper

### Admin auth
- [ ] `app/auth/admin.py` — `require_admin()` dependency that reads `ADMIN_EMAILS` env (comma-separated, lowercased), composes `current_user`, and rejects non-admin emails with 403 `admin_only`
- [ ] Add `ADMIN_EMAILS` to `_REQUIRED_ENV` in `app/main.py` so the app refuses to boot with it unset (F-CAT-6)
- [ ] Update `.env.example` with `ADMIN_EMAILS=` and a comment explaining the comma-separated format

### Research prompt + catalog file
- [x] Author `app/seed/catalog-research-prompt.md` (committed at cycle start; see this cycle's first commit)
- [ ] **(USER ACTION)** Run the prompt against an external agent (ChatGPT, Claude, Gemini), save the output verbatim to `app/seed/catalog.json`. This task is checked off when the file lands in the repo via a `[spec]` or `[impl]` commit.

### Seed loader
- [ ] `app/seed/catalog.py` — `load_catalog_file(path)` (pure JSON parse, raises ValueError), `apply_catalog_seed(entries)` (validate-whole-file-then-upsert; raises ValueError on bad input; founder-launched protection; defaults applied per F-CAT-3), `seed_catalog()` (CLI orchestrator)
- [ ] `app/seed/__main__.py` — extend dispatcher to support `python -m app.seed catalog`

### Admin endpoints
- [ ] `app/api/admin_catalog.py` — `GET /admin/catalog?status=...`, `GET /admin/catalog/{slug}`, `POST /admin/catalog/{slug}/approve`, `POST /admin/catalog/{slug}/reject` — all behind `Depends(require_admin())`
- [ ] Mount `admin_catalog` router in `app/main.py`
- [ ] Extend the global `RequestValidationError` handler to map missing `comment` on the reject endpoint to `{error: "field_required", field: "comment"}`

### Tests
- [ ] F-CAT-1 (schema): unique index on `slug` enforced (insert two with same slug → DuplicateKeyError)
- [ ] F-CAT-3 (loader): valid JSON loads N entries; rerun is idempotent; defaults applied (curation_status=pending, source=manual)
- [ ] F-CAT-3 (loader): re-running with edited `tagline` updates the existing row in place
- [ ] F-CAT-3 (loader): seed with bad shape (unknown category) raises ValueError, no partial writes
- [ ] F-CAT-3 (loader): seed with duplicate slugs raises ValueError, no partial writes
- [ ] F-CAT-3 (loader): loader does NOT touch a manually-inserted row with `source="founder_launch"` (defense-in-depth audit)
- [ ] F-CAT-4 (auth): admin email in allowlist passes; non-admin email returns 403 `admin_only`
- [ ] F-CAT-4 (auth): unauthenticated request returns 401 `auth_required`
- [ ] F-CAT-4 (auth): admin email check is case-insensitive (USER@example.com == user@example.com)
- [ ] F-CAT-5: GET /admin/catalog returns all entries by default
- [ ] F-CAT-5: GET /admin/catalog?status=pending filters correctly
- [ ] F-CAT-5: GET /admin/catalog/{slug} returns one entry; 404 on unknown slug
- [ ] F-CAT-5: approve sets status, last_reviewed_at, reviewed_by; clears rejection_comment
- [ ] F-CAT-5: reject with comment sets status, comment, reviewer; rejecting an already-rejected entry overwrites the comment
- [ ] F-CAT-5: reject with missing comment → 400 field_required, field=comment
- [ ] F-CAT-5: reject with whitespace-only comment → 400 comment_invalid
- [ ] F-CAT-5: approve/reject on unknown slug → 404 tool_not_found

### Conftest updates
- [ ] Add `seed_test_catalog` fixture in `tests/conftest.py` that inserts 4–5 fixed tool entries spanning categories and statuses (mix of pending/approved/rejected)
- [ ] Add `admin_token` fixture: signs up a user with email `admin@example.com`, returns the JWT — relies on `ADMIN_EMAILS=admin@example.com` set in conftest's env setup

## Validation

- [ ] All implementation tasks above checked off
- [ ] `app/seed/catalog.json` exists in the repo (300 entries from external agent run)
- [ ] All tests pass (full suite — cycles #1 + #2 must continue to pass)
- [ ] Manual smoke: `ADMIN_EMAILS=<your-email>` in `.env`; sign up that email as a user; run `python -m app.seed catalog`; visit `GET /admin/catalog?status=pending` and see the imported tools; approve one + reject one with a comment; verify the changes via `GET /admin/catalog/{slug}`
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: `tools_seed` does not contain any `source="founder_launch"` rows (audit test green); `ADMIN_EMAILS` is required at boot
