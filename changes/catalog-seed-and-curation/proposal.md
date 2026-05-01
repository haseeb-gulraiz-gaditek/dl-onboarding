# Proposal: catalog-seed-and-curation

## Problem

Mesh's recommendation engine (cycle #6) matches user profiles against a catalog of AI tools. Without the catalog, the concierge has nothing to recommend, the live narrowing graph (cycle #5) has nothing to render, and the founder-side launch flow (cycle #8) has no schema to add to. This cycle delivers the curated catalog — schema, loader, admin surface, and 300 hand-curated entries sourced from a research prompt fed to an external agent.

## Solution

**Two-collection architecture for tools** (per cycle decision):

- `tools_seed` — Mesh-curated entries. Owned by this cycle.
- `tools_founder_launched` — Founder-submitted entries. **NOT touched in this cycle.** Cycle #8 (`founder-launch-submission-and-verification`) creates and populates this collection.

Splitting the collections eliminates slug-collision risk between curated and founder-submitted tools. Downstream cycles (#5 onboarding graph, #6 recommendations, #10 tools page) will read from both via a thin aggregator helper that lands when those cycles need it. Cross-collection deduplication (the case where a founder launches the same tool we've curated) is explicitly deferred to a future cycle.

**Catalog research is outsourced.** `app/seed/catalog-research-prompt.md` is a self-contained prompt the user feeds to an external agent (ChatGPT / Claude / Gemini). The agent returns 300 tool entries as JSON. The user reviews and saves the output as `app/seed/catalog.json`. The seed loader (`python -m app.seed catalog`) validates and upserts.

**Admin UI** at `/admin/catalog` behind a hardcoded `ADMIN_EMAILS` env-var allowlist (no constitutional change to `role_type`). Three actions: list pending, approve, reject (with comment). Bulk operations deferred — V1 admin UI is exception-handling, not batch processing.

## Scope

**In:**

- `tools_seed` collection schema + indexes + access layer (`app/db/tools_seed.py`)
- Pydantic models (`app/models/tool.py`): `Tool`, `ToolPublic`, `ToolReject`, plus `Category` and `Label` enums
- `app/seed/catalog-research-prompt.md` — research prompt
- `app/seed/catalog.json` — populated by the user (this cycle ships the file once the user supplies the agent output)
- `python -m app.seed catalog` loader — idempotent, validate-whole-file-first
- `app/api/admin_catalog.py` admin endpoints:
  - `GET /admin/catalog?status={pending|approved|rejected|all}` — list
  - `GET /admin/catalog/{slug}` — detail
  - `POST /admin/catalog/{slug}/approve` — set `curation_status=approved`
  - `POST /admin/catalog/{slug}/reject` body `{"comment": "..."}` — set `curation_status=rejected`, save the comment
- `app/auth/admin.py` — `require_admin()` FastAPI dependency reading `ADMIN_EMAILS` env var (comma-separated allowlist) and rejecting non-admins with 403
- Tests for loader + admin endpoints + admin auth boundary
- Schema reservation: `curation_status`, `embedding_vector_id`, `source`, `last_reviewed_at`, `reviewed_by`, `rejection_comment` — fields named now, populated as cycles need them

**Out:**

- `tools_founder_launched` collection — cycle #8
- Automated scraping infrastructure — V1.5+
- Bulk admin actions (select-all approve/reject) — V1.5+
- Embedding generation — cycle #4 (`weaviate-pipeline`)
- Cross-collection deduplication helper — future cycle when both collections exist and contention is observed
- Real role-based access control / admin role amendment — V1.5+
- Catalog refresh cron / change detection — V1.5+
- Categorical taxonomy beyond the 13 enum values — V1.5+

## Alternatives Considered

1. **Single `tools` collection with `source` discriminator** — rejected per user call. Two collections eliminate any slug-collision possibility. Downstream cost (fan-out queries) is small and absorbed by a future helper.
2. **Admin role added as constitutional C2 amendment** — rejected. `ADMIN_EMAILS` env allowlist is sufficient for solo V1 operation. Properly governed admin role deferred to V1.5+ when more than one operator exists.
3. **No admin UI in V1; edit JSON + re-run seed** — rejected. User wants a basic approve/reject queue for editorial control over the imported research output.
4. **Inline catalog research (this assistant generates 300 tools in-cycle)** — rejected per user call. Outsourced to a different agent via `catalog-research-prompt.md`. Avoids hallucinated URLs/pricing from a single agent's training data.

## Risks

1. **External agent returns inaccurate data** — fabricated tools, stale URLs, wrong pricing. **Mitigation:** all imports default to `curation_status: pending`. Cycle #4 only embeds `approved` tools. Anything bad gets rejected (with comment) before it reaches users.
2. **300 entries are tedious to review one-by-one** in the admin UI. **Mitigation:** V1 supports per-entry actions only; if real-world review is impractical, bulk operations are a fast-follow cycle. Alternative path: user edits `catalog.json` and re-runs seed (loader is idempotent).
3. **Two-collection design adds query complexity for downstream cycles** (#5, #6, #10). **Mitigation:** explicitly noted in "Out of scope"; first cycle that needs cross-collection reads adds a `find_tools(query)` helper. Documented for the next cycle owner.
4. **`ADMIN_EMAILS` allowlist exposed via env compromise.** **Mitigation:** solo V1 has one admin; JWT_SECRET rotation is an existing recovery path. V1.5+ adds proper RBAC.
5. **`catalog.json` size in repo.** ~50–100 KB for 300 entries. Acceptable; git diffs on catalog refreshes are reviewable.
6. **External agent fails the prompt validation entirely.** **Mitigation:** the loader's whole-file validation surfaces problems with clear error messages; the user re-runs the prompt or hand-edits.

## Rollback

- Drop `tools_seed` collection.
- Remove `app/db/tools_seed.py`, `app/api/admin_catalog.py`, `app/auth/admin.py`, `app/models/tool.py`, the `app/seed/catalog*.{md,json,py}` files.
- Revert this cycle's commits and delete the `catalog-seed-and-curation` branch.

No downstream cycle depends on this cycle's output yet (cycles #4, #5, #6 haven't started). Rollback cost is bounded.
