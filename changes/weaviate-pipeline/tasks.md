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
- [ ] `app/embeddings/__init__.py` — empty package init
- [ ] `app/embeddings/openai.py` — async `embed_text(text: str) -> list[float]`. Single OpenAI client per process; uses `OPENAI_API_KEY` from env at call time; model is `text-embedding-3-small`; raises a clear exception on API failure
- [ ] `app/embeddings/atlas.py` — exposes constants `TOOLS_VECTOR_INDEX_NAME`, `TOOLS_VECTOR_INDEX_SPEC`, `PROFILES_VECTOR_INDEX_NAME`, `PROFILES_VECTOR_INDEX_SPEC`. Plus `similarity_search(...)` helper using `$vectorSearch` aggregation with a `mongomock-motor` fallback to Python-side cosine for tests
- [ ] `app/embeddings/lifecycle.py` — `ensure_tool_embedding(slug)`, `clear_tool_embedding(slug)`, `ensure_profile_embedding(user)`. Each idempotent. Profile helper: builds embeddable text from recent answers, calls embed_text, writes embedding + bumps `last_recompute_at`. Refuses founder users.
- [ ] `app/embeddings/__main__.py` — CLI dispatcher; supports `python -m app.embeddings backfill-tools`
- [ ] `app/embeddings/backfill.py` — `backfill_tools()` async function: iterates approved tools with no embedding, calls `ensure_tool_embedding`, prints stats per F-EMB-2 contract

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

- [ ] All implementation tasks above checked off
- [ ] All tests pass (full suite — cycles #1, #2, #3 must continue to pass)
- [ ] In `.env`: set `OPENAI_API_KEY=<your-real-key>`
- [ ] Sign up for Weaviate Cloud Services free sandbox at https://console.weaviate.cloud, create a Sandbox cluster, copy the REST endpoint URL and Admin API key into `.env` as `WEAVIATE_URL` and `WEAVIATE_API_KEY`
- [ ] Run `python -m app.embeddings init-weaviate` once — verify it prints `created: ['ToolEmbedding', 'ProfileEmbedding']` (or `already-existed` on rerun)
- [ ] Run `python -m app.seed catalog` again — verify the existing 547 entries flip to `curation_status: "approved"` (because the loader's default changed)
- [ ] Run `python -m app.embeddings backfill-tools` — verify `[backfill] embedded: 547, skipped: 0, failed: 0, total: 547` (or close)
- [ ] Re-run `python -m app.embeddings backfill-tools` — verify `[backfill] embedded: 0, skipped: 547, failed: 0, total: 547` (idempotency)
- [ ] Manual smoke: in the Mongo shell or Atlas UI, pick one approved tool and confirm `embedding` is a list of 1536 floats
- [ ] Manual smoke: reject one tool via `POST /admin/catalog/{slug}/reject` — verify `embedding` is now `null`. Approve it again — verify `embedding` is back.
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: founder users still cannot have profiles; `ensure_profile_embedding` rejects them
