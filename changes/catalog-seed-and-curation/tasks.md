# Tasks: catalog-seed-and-curation

## Implementation Checklist

### Schema + DB
- [x] Define `app/db/tools_seed.py` collection access layer + `ensure_indexes()` (unique index on `slug`; compound `(curation_status, category)`)
- [x] Helpers: `upsert_tool_by_slug` (refuses to overwrite rows with `source="founder_launch"` via Mongo `$ne` filter), `find_tool_by_slug`, `list_tools_by_status`, `set_status` (handles approve/reject + reviewer metadata)
- [x] Wire `ensure_indexes` into the FastAPI lifespan in `app/main.py`

### Models
- [x] `app/models/tool.py` — `Category`, `Label`, `CurationStatus`, `Source` literal types matching the prompt's enums; `ToolPublic` (client shape), `ToolReject` (request body for reject endpoint), `to_public(doc)` helper

### Admin auth
- [x] `app/auth/admin.py` — `require_admin()` dependency that reads `ADMIN_EMAILS` env (comma-separated, lowercased), composes `current_user`, and rejects non-admin emails with 403 `admin_only`
- [x] Add `ADMIN_EMAILS` to `_REQUIRED_ENV` in `app/main.py` so the app refuses to boot with it unset (F-CAT-6)
- [x] Update `.env.example` with `ADMIN_EMAILS=` and a comment explaining the comma-separated format

### Research prompt + catalog file
- [x] Author `app/seed/catalog-research-prompt.md` (committed at cycle start; see this cycle's first commit)
- [ ] **(USER ACTION)** Run the prompt against an external agent (ChatGPT, Claude, Gemini), save the output verbatim to `app/seed/catalog.json`. This task is checked off when the file lands in the repo via a `[spec]` or `[impl]` commit.

### Seed loader
- [x] `app/seed/catalog.py` — `load_catalog_file(path)` (pure JSON parse, raises ValueError), `apply_catalog_seed(entries)` (validate-whole-file-then-upsert; raises ValueError on bad input; founder-launched protection via `upsert_tool_by_slug`; defaults applied per F-CAT-3), `seed_catalog()` (CLI orchestrator)
- [x] `app/seed/__main__.py` — extended dispatcher to support `python -m app.seed catalog` (alongside the existing `questions` command)

### Admin endpoints
- [x] `app/api/admin_catalog.py` — `GET /admin/catalog?status=...`, `GET /admin/catalog/{slug}`, `POST /admin/catalog/{slug}/approve`, `POST /admin/catalog/{slug}/reject` — all behind `Depends(require_admin())`. Reject endpoint also rejects whitespace-only comments at the handler layer (Pydantic min_length=1 catches empty string at the schema layer)
- [x] Mount `admin_catalog` router in `app/main.py`
- [x] Extend the global `RequestValidationError` handler to map missing `comment` on the reject endpoint to `{error: "field_required", field: "comment"}`

### Tests
- [x] F-CAT-3 (loader): valid JSON loads N entries; rerun is idempotent; defaults applied (curation_status=pending, source=manual)
- [x] F-CAT-3 (loader): re-running with edited `tagline` updates the existing row in place
- [x] F-CAT-3 (loader): seed with bad shape (unknown category) raises ValueError, no partial writes
- [x] F-CAT-3 (loader): seed with duplicate slugs raises ValueError, no partial writes
- [x] F-CAT-3 (loader): invalid URL raises (additional shape check)
- [x] F-CAT-3 (loader): loader does NOT touch a manually-inserted row with `source="founder_launch"` (defense-in-depth audit)
- [x] F-CAT-4 (auth): admin email in allowlist passes
- [x] F-CAT-4 (auth): non-admin email returns 403 `admin_only`
- [x] F-CAT-4 (auth): unauthenticated request returns 401 `auth_required`
- [x] F-CAT-4 (auth): admin email check is case-insensitive (ADMIN@example.com == admin@example.com)
- [x] F-CAT-5: GET /admin/catalog returns all entries by default
- [x] F-CAT-5: GET /admin/catalog?status=pending filters correctly
- [x] F-CAT-5: GET /admin/catalog?status=blah returns 400 status_invalid (extra: status whitelist)
- [x] F-CAT-5: GET /admin/catalog/{slug} returns one entry
- [x] F-CAT-5: GET /admin/catalog/{slug} 404 on unknown slug
- [x] F-CAT-5: approve sets status, last_reviewed_at, reviewed_by; clears rejection_comment (verified on a previously-rejected entry)
- [x] F-CAT-5: reject with comment sets status, comment, reviewer
- [x] F-CAT-5: reject with missing comment → 400 field_required, field=comment
- [x] F-CAT-5: reject with empty string comment → 400 field_required (Pydantic min_length=1)
- [x] F-CAT-5: reject with whitespace-only comment → 400 comment_invalid (handler-layer guard)
- [x] F-CAT-5: approve unknown slug → 404 tool_not_found
- [x] F-CAT-5: reject unknown slug → 404 tool_not_found

### Conftest updates
- [x] Set `ADMIN_EMAILS=admin@example.com,manager@example.com` in `tests/conftest.py` env setup so admin auth tests have a stable allowlist
- [x] Add `seed_test_catalog` fixture inserting 3 tool entries (one each: pending / approved / rejected-with-comment) spanning three categories
- [x] Add `admin_token` fixture: signs up `admin@example.com` (in allowlist) and returns `{token, email}`
- [x] Add `non_admin_token` fixture: signs up `maya@example.com` (NOT in allowlist) for negative-path tests

## Validation

- [ ] All implementation tasks above checked off
- [ ] `app/seed/catalog.json` exists in the repo (300 entries from external agent run)
- [ ] All tests pass (full suite — cycles #1 + #2 must continue to pass)
- [ ] Manual smoke: `ADMIN_EMAILS=<your-email>` in `.env`; sign up that email as a user; run `python -m app.seed catalog`; visit `GET /admin/catalog?status=pending` and see the imported tools; approve one + reject one with a comment; verify the changes via `GET /admin/catalog/{slug}`
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: `tools_seed` does not contain any `source="founder_launch"` rows (audit test green); `ADMIN_EMAILS` is required at boot
