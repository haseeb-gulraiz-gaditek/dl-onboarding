# Feature: Catalog Seed and Curation

> **Cycle of origin:** `catalog-seed-and-curation` (archived; see `archive/catalog-seed-and-curation/`)
> **Last reviewed:** 2026-05-01
> **Constitution touchpoints:** `principles.md` (*"Treat the user's profile as theirs"* — labels are user-facing data, not editorial; *"Anti-spam is structural, not enforced"* — admin auth is enforcement, not structure, and explicitly V1-only), `positioning.md` (the catalog underpins matching against the Mesh "context-graph"), `governance.md` (`ADMIN_EMAILS` env allowlist is a deliberate non-amendment to `role_type`).
> **Builds on:** `auth-role-split` (`current_user`, JWT transport).

---

## Intent

Mesh's recommendation engine matches user profiles against a catalog of AI tools. This feature delivers the catalog: schema, loader, admin curation surface, and 547 hand-curated entries researched through an external agent.

The catalog is split across two collections, **by design**:

- **`tools_seed`** — Mesh-curated entries. Owned by this feature.
- **`tools_founder_launched`** — Founder-submitted entries. **NOT created here.** A future founder-launch feature owns that collection.

The two-collection split eliminates slug-collision risk between curated content and founder content. Cross-collection deduplication (the case where a founder launches the same product Mesh has already curated) is intentionally deferred to a future feature when both collections exist and the contention is observable.

## Surface

- **CLI:** `python -m app.seed catalog` — idempotent loader for `app/seed/catalog.json` into `tools_seed`.
- **HTTP, all behind `Depends(require_admin())`:**
  - `GET /admin/catalog?status={pending|approved|rejected|all}` — list catalog entries, optionally filtered.
  - `GET /admin/catalog/{slug}` — single entry by slug.
  - `POST /admin/catalog/{slug}/approve` — mark approved + record reviewer + clear any prior rejection comment.
  - `POST /admin/catalog/{slug}/reject` body `{"comment": "..."}` — mark rejected + record reviewer + save the comment.
- **Reusable artifact:** `app/seed/catalog-research-prompt.md` — self-contained prompt fed to an external research agent (ChatGPT / Claude / Gemini) to generate or refresh the catalog.

`require_admin` reads `ADMIN_EMAILS` (comma-separated, case-insensitive env var) at request time and rejects non-admin emails with `403 admin_only`. This is V1's pragmatic admin gate; full RBAC is V1.5+.

---

## F-CAT-1 — `tools_seed` collection schema

The `tools_seed` collection stores Mesh-curated tool entries. Each row:

```
{
  slug: <string, lowercase-hyphenated, unique>,
  name, tagline, description, url, pricing_summary: <strings>,
  category: <one of 13 enum values>,
  labels: <subset of ["new", "all_time_best", "gaining_traction"]>,
  curation_status: "pending" | "approved" | "rejected",
  rejection_comment: <string | null>,
  source: "manual" | "taaft" | "producthunt" | "futuretools",   // never "founder_launch"
  embedding_vector_id: <string | null>,                           // populated by future weaviate feature
  vote_score: <int>,                                              // denormalized; updated by F-COM-7 (cycle #7)
  created_at: <datetime>,
  last_reviewed_at: <datetime | null>,
  reviewed_by: <string | null>                                    // admin email
}
```

Indexes: unique on `slug`; compound on `(curation_status, category)` for the admin list view.

**Constitutional invariant:** rows with `source: "founder_launch"` MUST NOT exist in this collection. Founder-submitted tools live in a separate `tools_founder_launched` collection (created by a future feature). Loader code defends against accidental cross-collection writes.

The 13-value `category` enum is a closed list: `productivity`, `writing`, `design`, `engineering`, `research_browsing`, `meetings`, `marketing`, `sales`, `analytics_data`, `finance`, `education`, `creative_video`, `automation_agents`.

---

## F-CAT-2 — Catalog research prompt

`app/seed/catalog-research-prompt.md` is a self-contained prompt the user feeds to an external research agent. The agent returns a JSON array of tool entries matching the F-CAT-1 schema. The user reviews and saves the output as `app/seed/catalog.json`.

The prompt is the source-of-truth artifact for the catalog. Catalog refreshes re-run the prompt; quality drift is reviewable as a git diff on `catalog.json`. The prompt encodes the schema, the 150/100/50 distribution across labels, the closed category enum, and the quality bar.

---

## F-CAT-3 — `python -m app.seed catalog`

The CLI loader populates `tools_seed` from `app/seed/catalog.json`.

**Given** `app/seed/catalog.json` is a JSON array of entries matching the F-CAT-1 schema
**When** `python -m app.seed catalog` runs
**Then** each entry is upserted into `tools_seed` keyed by `slug` (idempotent — re-running produces the same DB state)
**And** the loader prints `inserted: N, updated: M, total: K`.

**Defaults applied on insert:** `curation_status = "pending"`, `source = "manual"`, `created_at = now`. `embedding_vector_id`, `last_reviewed_at`, `reviewed_by`, `rejection_comment` default to `null`.

**Validation discipline:** the loader validates the entire file before any DB write. Missing required fields, unknown `category`, unknown `label`, slugs that don't match the lowercase-hyphenated pattern, non-http(s) URLs, and duplicate slugs all cause the loader to exit non-zero with a clear error message and **no partial writes**.

**Founder-launched protection:** before each upsert, the loader checks the existing row at that slug. If `source == "founder_launch"`, the loader silently skips (returns insert/update counts of zero). Defense-in-depth across the collection boundary: such rows should not exist in `tools_seed` at all, but the loader refuses to clobber them if they ever do.

---

## F-CAT-4 — Admin auth (`require_admin`)

`require_admin()` is a FastAPI dependency factory exposing admin endpoints only to authenticated callers whose email is in the `ADMIN_EMAILS` env-var allowlist.

**Given** an authenticated caller whose `email` is in `ADMIN_EMAILS` (case-insensitive match)
**When** they hit any endpoint declared `Depends(require_admin())`
**Then** the dependency yields the user dict (proceeds normally).

**Given** an authenticated caller whose `email` is not in `ADMIN_EMAILS`
**When** they hit an admin endpoint
**Then** the system returns `403 Forbidden` with `{"error": "admin_only"}`.

**Given** an unauthenticated request
**When** it hits an admin endpoint
**Then** the system returns `401 Unauthorized` with `{"error": "auth_required"}` (inherited from `current_user`).

**The caller's `role_type` does not gate admin access.** A `user`-role with an admin email passes; a `user`-role with a non-admin email is rejected. This is intentional — admin access is V1's pragmatic operator gate, not a third role on the constitutional `user|founder` boundary.

---

## F-CAT-5 — Admin catalog endpoints

All endpoints are behind `Depends(require_admin())`.

### `GET /admin/catalog?status={pending|approved|rejected|all}`

Returns the list of catalog entries matching the filter. `status=all` (or omitted) returns every entry. Sorted by `(category, name)` for stable ordering. Returns an array of `ToolPublic`. An invalid `status` value returns `400 status_invalid` with the allowed set in the response.

### `GET /admin/catalog/{slug}`

Returns a single entry. `404 tool_not_found` on unknown slug.

### `POST /admin/catalog/{slug}/approve`

**Given** an entry exists at `slug = X`
**When** an admin POSTs (empty body)
**Then** `curation_status = "approved"`, `last_reviewed_at = now`, `reviewed_by = <admin email>`, `rejection_comment = null` (clears any prior rejection comment).
**And** returns the updated `ToolPublic`.

`404 tool_not_found` on unknown slug.

### `POST /admin/catalog/{slug}/reject`

Body: `{"comment": "<reason>"}`.

**Given** an entry exists at `slug = X`
**When** an admin POSTs with a non-empty, non-whitespace comment
**Then** `curation_status = "rejected"`, `last_reviewed_at = now`, `reviewed_by = <admin email>`, `rejection_comment = <stripped comment>`.

#### Errors

- Missing `comment` field, or empty string → `400 {"error": "field_required", "field": "comment"}` (Pydantic `min_length=1` enforces this at the schema layer).
- Whitespace-only comment → `400 {"error": "comment_invalid"}` (handler-layer guard).
- Unknown slug → `404 tool_not_found`.

---

## F-CAT-6 — `ADMIN_EMAILS` is required at boot

`_REQUIRED_ENV` in `app/main.py` is now `("MONGODB_URI", "JWT_SECRET", "ADMIN_EMAILS")`. The lifespan startup raises immediately if any of the three is unset or blank. `.env.example` documents the new variable with format guidance.

---

## Architectural notes

- **Two-collection design** is the contract. `tools_seed` is sealed against `source: "founder_launch"` writes both at the loader level (check-then-upsert) and by convention. The future founder-launch feature must use a different collection.
- **Catalog refresh = git diff.** Re-running the research prompt produces a new `catalog.json`; the diff is reviewable, the loader is idempotent, and historical entries are preserved unless explicitly removed from the JSON.
- **Admin auth is intentionally V1-temporary.** Hardcoded `ADMIN_EMAILS` env allowlist sidesteps a constitutional `role_type` amendment for solo operation. V1.5+ replaces this with proper RBAC; this spec will be amended at that point.
- **Catalog drift detection deferred.** No automated change detection (URL went 404, pricing changed, tool sunset) — V1.5+. Manual reject-with-comment via the admin UI handles known-bad entries.

## Out of scope (V1 deferrals)

- `tools_founder_launched` collection — owned by a future founder-launch feature
- Automated scraping infrastructure (Celery scrape jobs against TheresAnAIForThat / Product Hunt) — V1.5+
- Bulk admin actions (select-all approve/reject) — V1.5+ if real-world review proves impractical
- Embedding generation for catalog rows — owned by a future weaviate feature
- Cross-collection unified read API — added when first cycle that needs it (likely the recommendation-engine cycle) lands
- Real role-based admin (replacing `ADMIN_EMAILS` allowlist) — V1.5+
- Catalog refresh cron / change detection — V1.5+
