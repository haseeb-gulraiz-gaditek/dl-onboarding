# Proposal: weaviate-pipeline

> **Mid-cycle pivot (2026-05-02):** initially scoped this cycle for MongoDB Atlas Vector Search to avoid a second managed service. User opted to switch to **Weaviate Cloud Services free 14-day sandbox** during validation, before the cycle was completed. The proposal/spec-delta were edited in place rather than via `/vkf/amend` because the cycle was still in implementation.

## Problem

Mesh's core value loop — *"the concierge recommends 2–3 tools/week with reasoning"* — depends on matching profile embeddings against tool embeddings. Cycles #2 (`question-bank-and-answer-capture`) and #3 (`catalog-seed-and-curation`) both reserved an `embedding_vector_id` field for "a future feature to populate." This is that feature.

Without embeddings stored and queryable, cycle #5 (`fast-onboarding-match-and-graph`) and cycle #6 (`recommendation-engine`) cannot start — they have nothing to search against.

## Solution

**Lazy embedding architecture with no async infrastructure.**

- **Tool embeddings (write-side, infrequent):**
  - One-shot CLI: `python -m app.embeddings backfill-tools` — embeds every approved tool that has no embedding. Idempotent.
  - Synchronous-on-approve: `POST /admin/catalog/{slug}/approve` blocks ~500ms while it embeds via OpenAI. Admin UX, not user UX, so latency is invisible.
  - Synchronous-on-reject: `POST /admin/catalog/{slug}/reject` clears the embedding (so a rejected tool no longer surfaces in similarity search even though the row stays in the collection).

- **Profile embeddings (read-side, lazy):**
  - `POST /api/answers` does **NO** embedding work. Stays as fast as cycle #2 made it. Just bumps `last_invalidated_at` (already does this).
  - `ensure_profile_embedding(user_id)` helper regenerates the embedding **on demand** when cycle #5 or #6 needs to query. Skipped if `embedding` is fresh (`last_recompute_at >= last_invalidated_at`).

- **Storage:** vectors live **inline in the same Mongo documents** they describe (Atlas Vector Search indexes a field on the document). Field name: `embedding: list[float] | None` — replaces the cycle #2/#3 placeholder field `embedding_vector_id` which was shaped for an external vector DB.

- **Embedding model:** OpenAI `text-embedding-3-small`. 1536 dimensions. ~$0.02 per million tokens. Total cost to embed the 547 catalog entries plus a few hundred profile re-embeds for V1: under $1.

- **Vector store:** MongoDB Atlas Vector Search. Two manually-created Atlas search indices (`tools_seed_vector_index`, `profiles_vector_index`) — schemas documented in `app/embeddings/atlas.py`. User creates them once via Atlas UI; the app boots happily either way (search calls fail with a clear error if the index is missing, but read/write of `embedding` field doesn't depend on the index).

- **No async orchestration in this cycle.** No Celery, no Redis, no FastAPI BackgroundTasks. Every embedding call is synchronous in the request handler that triggers it. User-facing flows (`POST /api/answers`) avoid embedding work entirely.

## Scope

**In:**
- `OPENAI_API_KEY` joins required-at-boot env (alongside `MONGODB_URI`, `JWT_SECRET`, `ADMIN_EMAILS`)
- `app/embeddings/openai.py` — thin client wrapper around `text-embedding-3-small`. Async, one entry point: `embed_text(text: str) -> list[float]`
- `app/embeddings/atlas.py` — Atlas Vector Search index definitions documented as constants; `similarity_search(collection_name, index_name, query_vector, top_k, filters=None) -> list[dict]` helper using the `$vectorSearch` aggregation stage
- `app/embeddings/lifecycle.py` — `ensure_tool_embedding(slug)`, `clear_tool_embedding(slug)`, `ensure_profile_embedding(user)`. Each is idempotent and skips if a fresh embedding already exists
- `app/embeddings/__main__.py` — CLI dispatcher; supports `python -m app.embeddings backfill-tools`
- Modify `app/api/admin_catalog.py` approve to call `ensure_tool_embedding(slug)` synchronously after `set_status`
- Modify `app/api/admin_catalog.py` reject to call `clear_tool_embedding(slug)` synchronously after `set_status`
- Modify `app/seed/catalog.py` defaults: new entries default to `curation_status: "approved"` (per user call — seeded entries are pre-vetted; founder-launched entries in cycle #8 still go through pending→approved)
- Rename `embedding_vector_id` → `embedding` in `tools_seed` (cycle #3) and `profiles` (cycle #2) schemas. Pydantic models updated; default-value factories updated. The MODIFIED section of this spec-delta documents the rename.
- Tests: lifecycle helpers; backfill CLI; approve+reject embedding side-effects; similarity_search returns expected docs with mongomock fallback (mongomock-motor doesn't support `$vectorSearch`, so the search test falls back to a Python-side cosine helper for the test path; production uses Atlas $vectorSearch)
- `.env.example` updated with `OPENAI_API_KEY=`

**Out (deferred to consumer cycles or "as needed"):**
- HTTP endpoints exposing similarity search — owned by cycle #5 (`/api/onboarding/match`) and cycle #6 (`/api/recommendations`)
- Hardcoded "first-3-questions" generic-recommendation fallback — owned by cycle #5 (`fast-onboarding-match-and-graph`); per user call, the first three answers are too generic for embedding-based matching, so cycle #5 will return defaults for those
- Auto-creation of the Atlas Vector Search index via the Atlas Admin API — V1.5+; V1 documents the index spec and the user creates it once via the Atlas UI
- BackgroundTasks / Celery / Redis async infra — V1.5+ when traffic justifies
- Embedding model swap surface (Voyage, Cohere, sentence-transformers) — fixed at OpenAI `text-embedding-3-small` for V1
- Re-embedding on schema change (e.g., a future tool field's text changes how a tool reads) — V1.5+ versioning
- Caching / connection pooling for the OpenAI client — V1 uses the SDK's default client per call

## Alternatives Considered

1. **Weaviate Cloud Services** — rejected. Adds a second managed service to run; sandbox tier expires in 14 days; you already have Atlas. Atlas Vector Search has matured enough since 2023 to be a one-mental-model choice.
2. **Local vector store via Chroma / FAISS** — rejected. Loses durability / cross-restart consistency; embedding state would be ephemeral or require a persistent volume.
3. **`sentence-transformers` BGE-small (in-process)** — rejected. Adds ~500MB Python deps + slow first-call model load + machine-dependent quality variance. Cost-comparable in API mode for V1 traffic.
4. **Voyage AI / Cohere / OpenAI** — rejected the alternatives. OpenAI's `text-embedding-3-small` is the best-known, cheapest-per-token, and most-tested option for English-only V1 content. Voyage is Anthropic's official rec and a fine V1.5+ swap target if quality is insufficient.
5. **Eager embedding via Celery+Redis** (the original backlog plan) — rejected per user call. No async infrastructure in V1.
6. **FastAPI BackgroundTasks** (in-process async after response) — rejected per user call. "Slow is fine for MVP; no async infra preferred."
7. **Synchronous embedding inside `POST /api/answers`** — rejected. Would add ~500ms latency to every onboarding tap. Lazy-on-read sidesteps this entirely.
8. **Keep `embedding_vector_id` as a placeholder field, store vectors in a separate collection** — rejected. Atlas Vector Search indexes fields directly on the document; a separate collection would require manual joins and double the storage.

## Risks

1. **`OPENAI_API_KEY` cost surprise.** Mitigation: `text-embedding-3-small` at $0.02/M tokens is trivially cheap (the entire 547-tool catalog plus a hundred profile re-embeds total < $1). The lazy strategy bounds spend at the rate of recommendation queries, not the rate of taps.
2. **Atlas Vector Search index not created.** If the user forgets to create the search index in Atlas UI, `similarity_search` returns 0 results with a clear `IndexNotFoundError` from the driver. Mitigation: `app/embeddings/atlas.py` documents the exact index spec; cycle #5's match endpoint surfaces the error to the admin clearly.
3. **mongomock-motor lacks `$vectorSearch`.** The test suite cannot exercise the actual Atlas vector search aggregation stage. Mitigation: the test for `similarity_search` falls back to a Python-side cosine helper that operates over the in-memory documents. Production code path unchanged. Documented as a test-only deviation.
4. **OpenAI rate limits / outages.** Synchronous embedding means an OpenAI 429 fails the admin approve action with a 5xx. Mitigation: explicit error handling in the lifecycle helpers translates upstream errors into clear 503s with retry guidance; admin re-clicks approve later.
5. **Schema rename `embedding_vector_id` → `embedding` is a breaking change for any code that reads the old name.** Mitigation: only cycle #2 and cycle #3 specs reference the old name; both are updated in this spec-delta's MODIFIED section. No production data exists yet (no cycle that wrote a value to `embedding_vector_id`), so there's nothing to migrate.
6. **The "weaviate-pipeline" slug is misleading once the implementation lands.** Mitigation: the canonical spec at `specs/features/weaviate-pipeline/spec.md` will note in its title that the cycle ships Atlas Vector Search, not Weaviate. Slug stays for backlog traceability.

## Rollback

- Drop the `embedding` field from `tools_seed` and `profiles` documents.
- Delete the Atlas Vector Search indices.
- Remove `app/embeddings/`.
- Revert this cycle's commits.
- Restore `curation_status: "pending"` as the seed loader default if the approval-by-default behavior is unwanted.

No downstream cycle depends on this yet (cycles #5, #6 haven't started). Rollback cost is bounded.
