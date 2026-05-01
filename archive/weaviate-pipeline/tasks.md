# Tasks: weaviate-pipeline

## Implementation Checklist

### Env + dependencies
- [x] Add `openai>=1.50` to `requirements.txt`
- [x] Add `OPENAI_API_KEY` to `_REQUIRED_ENV` in `app/main.py` (joins MONGODB_URI, JWT_SECRET, ADMIN_EMAILS) — F-EMB-1
- [x] Update `.env.example` with `OPENAI_API_KEY=` and a link comment (https://platform.openai.com/api-keys)

### Schema rename: embedding_vector_id → embedding
- [x] `app/db/profiles.py`: rename in `_new_profile_doc` factory; default `embedding: None`
- [x] `app/db/tools_seed.py`: rename in `upsert_tool_by_slug` `$setOnInsert`; default `embedding: None`. Also flipped seed default `curation_status` from `"pending"` to `"approved"` per F-CAT-3 MODIFIED in this delta
- [x] `app/models/profile.py`: rename Pydantic field
- [x] `app/models/tool.py`: rename Pydantic field; update `to_public()` projection

### Embeddings module
- [x] `app/embeddings/__init__.py` — empty package init
- [x] `app/embeddings/openai.py` — async `embed_text` wrapper around AsyncOpenAI's `text-embedding-3-small`
- [x] `app/embeddings/vector_store.py` (renamed from `atlas.py` after the Weaviate pivot) — `_get_weaviate_client` lazy lifecycle, `publish_tool` / `delete_tool` / `publish_profile` (best-effort upserts), `similarity_search` with three execution paths (mongomock fallback, Weaviate, Mongo cosine production fallback), `init_weaviate_schema` for the bootstrap CLI
- [x] `app/embeddings/lifecycle.py` — `ensure_tool_embedding(slug)`, `clear_tool_embedding(slug)`, `ensure_profile_embedding(user)` — Mongo-first writes, Weaviate publish best-effort
- [x] `app/embeddings/__main__.py` — CLI dispatcher; supports `init-weaviate`, `backfill-tools`, `republish-tools`
- [x] `app/embeddings/backfill.py` — embeds approved-no-embedding tools and publishes to Weaviate; idempotent
- [x] `app/embeddings/republish.py` — re-publishes existing Mongo embeddings to Weaviate without re-calling OpenAI; added during validation when first publish_tool revealed an upsert bug

### Cycle #3 modifications
- [x] `app/db/tools_seed.py`: changed default `curation_status` from `"pending"` to `"approved"` in `upsert_tool_by_slug`'s `$setOnInsert` payload (the canonical default for the collection); applies to re-runs of `python -m app.seed catalog` automatically
- [x] `app/api/admin_catalog.py` approve handler: after `set_status(...)`, calls `ensure_tool_embedding(slug)` synchronously then re-fetches to include the embedding in the response. Embedding failures don't roll back the approve (graceful degradation per F-EMB-2)
- [x] `app/api/admin_catalog.py` reject handler: after `set_status(...)`, calls `clear_tool_embedding(slug)` per F-EMB-6, then re-fetches so the response shows `embedding: null`

### Tests
- [x] F-EMB-1 (env): missing required env var → app refuses to boot (parametrized over MONGODB_URI / JWT_SECRET / ADMIN_EMAILS / OPENAI_API_KEY)
- [x] F-EMB-2 (lifecycle): `ensure_tool_embedding` populates `embedding` on a tool with no embedding
- [x] F-EMB-2 (lifecycle): `ensure_tool_embedding` is a no-op on a tool that already has an embedding (idempotent)
- [x] F-EMB-2 (lifecycle): `ensure_tool_embedding` is a no-op on missing slug
- [x] F-EMB-2 (admin): approve handler triggers `ensure_tool_embedding` and the response shows the populated embedding
- [x] F-EMB-2 (admin): if OpenAI returns an error during approve, the tool is still approved with `embedding=None`
- [x] F-EMB-2 (backfill): backfill embeds approved-no-embedding tools; idempotent rerun
- [x] F-EMB-2 (backfill): backfill skips rejected and pending tools
- [x] F-EMB-2 (backfill): records failures without aborting the run
- [x] F-EMB-3 (profile): `ensure_profile_embedding` populates a fresh profile's embedding
- [x] F-EMB-3 (profile): no-op on a fresh embedding
- [x] F-EMB-3 (profile): regenerates when `last_invalidated_at` is newer than `last_recompute_at`
- [x] F-EMB-3 (profile): refuses founder user with `ValueError`
- [x] F-EMB-5 (search): `similarity_search` returns top_k docs in cosine-descending order via the mongomock fallback path
- [x] F-EMB-5 (search): filters narrow the result set
- [x] F-EMB-5 (search): empty collection returns empty list
- [x] F-EMB-6 (reject): reject handler clears `embedding` on the rejected tool
- [x] F-EMB-6 (reject): re-approving a previously-rejected tool re-embeds it
- [x] F-CAT-3 modified: seed loader inserts new entries with `curation_status: "approved"` by default (verified by `test_loader_inserts_entries_and_is_idempotent`)

### Conftest updates
- [x] Set `OPENAI_API_KEY=test-fake-key-not-real` in `tests/conftest.py` env setup
- [x] Add `mock_openai_embed` autouse fixture monkey-patching both `app.embeddings.openai.embed_text` and `app.embeddings.lifecycle.embed_text` with a deterministic MD5-based 1536-dim stub. Tests that need a failing-OpenAI override locally with `monkeypatch.setattr`.

## Validation

- [x] All implementation tasks above checked off
- [x] All tests pass — full suite 87 green (cycles #1, #2, #3 unchanged)
- [x] `.env` populated with `OPENAI_API_KEY` (real key)
- [x] Weaviate Cloud Sandbox provisioned; `WEAVIATE_URL` + `WEAVIATE_API_KEY` set in `.env`
- [x] `python -m app.embeddings init-weaviate` → `created: ['ToolEmbedding', 'ProfileEmbedding']`
- [x] One-shot data migration: 545 existing rows flipped from `pending` to `approved` via Mongo update_many (the seed loader only sets defaults on insert, so an additional flip step was needed; added as a learning)
- [x] `python -m app.embeddings backfill-tools` → `[backfill] embedded: 546, skipped: 0, failed: 0, total: 546` — Mongo embeddings written (Weaviate publishes failed silently due to a publish_tool upsert bug discovered during this validation step)
- [x] Bug fix landed (`publish_tool` now uses true insert-or-replace upsert) + new `python -m app.embeddings republish-tools` CLI; ran it → `[republish] published: 546, failed: 0, total: 546` — all 546 tools now in Weaviate
- [x] Spec-delta scenarios verifiably hold in implementation
- [x] No constitutional regression: founder users still cannot have profiles; `ensure_profile_embedding` raises ValueError on founder accounts (covered by `test_ensure_profile_embedding_refuses_founder`)
