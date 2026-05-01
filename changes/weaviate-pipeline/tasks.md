# Tasks: weaviate-pipeline

## Implementation Checklist

### Env + dependencies
- [ ] Add `openai>=1.50` to `requirements.txt`
- [ ] Add `OPENAI_API_KEY` to `_REQUIRED_ENV` in `app/main.py` (joins MONGODB_URI, JWT_SECRET, ADMIN_EMAILS) — F-EMB-1
- [ ] Update `.env.example` with `OPENAI_API_KEY=` and a link comment (https://platform.openai.com/api-keys)

### Schema rename: embedding_vector_id → embedding
- [ ] `app/db/profiles.py`: rename in `_new_profile_doc` factory; default `embedding: None`
- [ ] `app/db/tools_seed.py`: rename in `upsert_tool_by_slug` `$setOnInsert`; default `embedding: None`
- [ ] `app/models/profile.py`: rename Pydantic field
- [ ] `app/models/tool.py`: rename Pydantic field; update `to_public()` projection

### Embeddings module
- [ ] `app/embeddings/__init__.py` — empty package init
- [ ] `app/embeddings/openai.py` — async `embed_text(text: str) -> list[float]`. Single OpenAI client per process; uses `OPENAI_API_KEY` from env at call time; model is `text-embedding-3-small`; raises a clear exception on API failure
- [ ] `app/embeddings/atlas.py` — exposes constants `TOOLS_VECTOR_INDEX_NAME`, `TOOLS_VECTOR_INDEX_SPEC`, `PROFILES_VECTOR_INDEX_NAME`, `PROFILES_VECTOR_INDEX_SPEC`. Plus `similarity_search(...)` helper using `$vectorSearch` aggregation with a `mongomock-motor` fallback to Python-side cosine for tests
- [ ] `app/embeddings/lifecycle.py` — `ensure_tool_embedding(slug)`, `clear_tool_embedding(slug)`, `ensure_profile_embedding(user)`. Each idempotent. Profile helper: builds embeddable text from recent answers, calls embed_text, writes embedding + bumps `last_recompute_at`. Refuses founder users.
- [ ] `app/embeddings/__main__.py` — CLI dispatcher; supports `python -m app.embeddings backfill-tools`
- [ ] `app/embeddings/backfill.py` — `backfill_tools()` async function: iterates approved tools with no embedding, calls `ensure_tool_embedding`, prints stats per F-EMB-2 contract

### Cycle #3 modifications
- [ ] `app/seed/catalog.py`: change default `curation_status` from `"pending"` to `"approved"` in `apply_catalog_seed`'s upsert payload; this also affects re-runs of `python -m app.seed catalog`
- [ ] `app/api/admin_catalog.py` approve handler: after `set_status(...)`, call `ensure_tool_embedding(slug)`. If embedding fails, log and continue (graceful degradation per F-EMB-2)
- [ ] `app/api/admin_catalog.py` reject handler: after `set_status(...)`, call `clear_tool_embedding(slug)` per F-EMB-6

### Tests
- [ ] F-EMB-1 (env): missing `OPENAI_API_KEY` → app refuses to boot (exercise the lifespan check, mirror existing tests for the other required vars)
- [ ] F-EMB-2 (lifecycle): `ensure_tool_embedding` populates `embedding` on a tool with no embedding (mock OpenAI client to return a fixed 1536-dim vector)
- [ ] F-EMB-2 (lifecycle): `ensure_tool_embedding` is a no-op on a tool that already has an embedding (idempotent)
- [ ] F-EMB-2 (admin): approve handler triggers `ensure_tool_embedding` and the response shows the populated embedding
- [ ] F-EMB-2 (admin): if OpenAI returns an error during approve, the tool is still approved with `embedding=None`; admin response is 200
- [ ] F-EMB-2 (backfill): backfill embeds all approved-no-embedding tools; prints stats; rerun is a no-op
- [ ] F-EMB-2 (backfill): backfill skips rejected and pending tools (only approved get embedded)
- [ ] F-EMB-3 (profile): `ensure_profile_embedding` populates a fresh profile's embedding
- [ ] F-EMB-3 (profile): no-op on a fresh embedding (`last_recompute_at >= last_invalidated_at` AND `embedding IS NOT null`)
- [ ] F-EMB-3 (profile): regenerates when `last_invalidated_at` is newer than `last_recompute_at`
- [ ] F-EMB-3 (profile): refuses founder user with `ValueError`
- [ ] F-EMB-5 (search): `similarity_search` returns top_k docs in cosine-descending order against an in-memory mongomock dataset (uses Python-side cosine fallback)
- [ ] F-EMB-5 (search): filters narrow the result set
- [ ] F-EMB-5 (search): empty collection returns empty list (no error)
- [ ] F-EMB-6 (reject): reject handler clears `embedding` on the rejected tool
- [ ] F-EMB-6 (reject): re-approving a previously-rejected tool re-embeds it
- [ ] F-CAT-3 modified: seed loader inserts new entries with `curation_status: "approved"` by default (verify by re-loading the catalog and checking a fresh slug's status)

### Conftest updates
- [ ] Set `OPENAI_API_KEY=test-fake-key` in `tests/conftest.py` env setup
- [ ] Add `mock_openai_embed` fixture that monkey-patches `app.embeddings.openai.embed_text` to return a deterministic 1536-dim vector based on the input string's hash. Used by all embedding tests.

## Validation

- [ ] All implementation tasks above checked off
- [ ] All tests pass (full suite — cycles #1, #2, #3 must continue to pass)
- [ ] In `.env`: set `OPENAI_API_KEY=<your-real-key>`
- [ ] Create the two Atlas Vector Search indices via the Atlas UI per the specs in `app/embeddings/atlas.py` (one-time)
- [ ] Run `python -m app.seed catalog` again — verify the existing 547 entries flip to `curation_status: "approved"` (because the loader's default changed)
- [ ] Run `python -m app.embeddings backfill-tools` — verify `[backfill] embedded: 547, skipped: 0, failed: 0, total: 547` (or close)
- [ ] Re-run `python -m app.embeddings backfill-tools` — verify `[backfill] embedded: 0, skipped: 547, failed: 0, total: 547` (idempotency)
- [ ] Manual smoke: in the Mongo shell or Atlas UI, pick one approved tool and confirm `embedding` is a list of 1536 floats
- [ ] Manual smoke: reject one tool via `POST /admin/catalog/{slug}/reject` — verify `embedding` is now `null`. Approve it again — verify `embedding` is back.
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founder users still cannot have profiles; `ensure_profile_embedding` rejects them
