# Feature: Embedding Pipeline (Weaviate-backed)

> **Cycle of origin:** `weaviate-pipeline` (archived; see `archive/weaviate-pipeline/`)
> **Last reviewed:** 2026-05-02
> **Constitution touchpoints:** `principles.md` (*"Treat the user's profile as theirs"* — embeddings live in Mongo for export, replicated to Weaviate for search; *"Anti-spam is structural, not enforced"* — founder users have no profile, so they can never appear in similarity-search results).
> **Builds on:** `auth-role-split` (current_user, role guards), `question-bank-and-answer-capture` (profiles + answers), `catalog-seed-and-curation` (tools_seed + admin approve/reject lifecycle).

> **Architecture name:** the slug is `weaviate-pipeline` for backlog traceability. Implementation uses **MongoDB Atlas (storage)** + **Weaviate Cloud Services (vector search)** + **OpenAI text-embedding-3-small (generation)**. The cycle pivoted mid-implementation from Atlas Vector Search to Weaviate Cloud at the user's call.

---

## Intent

Cycles #5 (`fast-onboarding-match-and-graph`) and #6 (`recommendation-engine`) need a similarity-search primitive: given a profile vector, return the top-k matching tools. This feature delivers that primitive — embeddings generated via OpenAI, stored in two places (Mongo as source of truth, Weaviate as the production search index), queryable through a single helper.

The design preserves Mesh's exportable-profile invariant: every embedding has a Mongo copy, so the user's data leaves with them in pure JSON if they ever want it. Weaviate is a search accelerator, not a parallel data store. If Weaviate is down, search degrades to a Python-side cosine over Mongo documents — slower but functional.

## Surface

### CLI

- `python -m app.embeddings init-weaviate` — one-time schema bootstrap. Creates the `ToolEmbedding` and `ProfileEmbedding` Weaviate classes if they don't exist. Idempotent.
- `python -m app.embeddings backfill-tools` — embeds every approved tool that lacks a Mongo embedding, then publishes to Weaviate. Idempotent.
- `python -m app.embeddings republish-tools` — re-pushes existing Mongo embeddings to Weaviate without re-calling OpenAI. Use after Weaviate downtime or cluster rebuild.

### HTTP

No HTTP endpoints. Cycles #5 and #6 build their own search endpoints atop `similarity_search`.

### Side effects on existing flows

- `POST /admin/catalog/{slug}/approve` — synchronously embeds the tool (Mongo + Weaviate publish). Embedding failures don't roll back the approve (graceful degradation).
- `POST /admin/catalog/{slug}/reject` — clears the Mongo embedding and deletes the Weaviate object. The rejected tool disappears from similarity-search results until re-approved.
- The `embedding` field name was introduced on `tools_seed` and `profiles` (replacing the cycle #2/#3 placeholder name `embedding_vector_id`).

---

## F-EMB-1 — Required env vars at boot

`_REQUIRED_ENV` includes `MONGODB_URI`, `JWT_SECRET`, `ADMIN_EMAILS`, `OPENAI_API_KEY`, `WEAVIATE_URL`, and `WEAVIATE_API_KEY`. The lifespan startup raises `RuntimeError` if any of the six is unset or blank, naming the missing var. `.env.example` documents each with format guidance and links to the OpenAI dashboard and Weaviate Cloud console.

## F-EMB-2 — Tool embedding generation

Tool embeddings are generated synchronously in two paths:

**Backfill CLI:**
```
$ python -m app.embeddings backfill-tools
[backfill] embedded: N, skipped: M, failed: K, total: T
```

**Given** the operator runs the CLI
**When** the command iterates `tools_seed` rows where `curation_status = "approved"` AND `embedding IS null`
**Then** for each row, the system fetches an embedding via OpenAI and writes it to `embedding`, then publishes to Weaviate. The CLI exits 0 if `failed == 0`, else 1.

Rows with other `curation_status` values are not embedded. Rows that already have an embedding count toward `skipped`.

**Synchronous on admin approve:**

**Given** an admin posts `POST /admin/catalog/{slug}/approve`
**When** `set_status(...)` succeeds
**Then** the handler calls `ensure_tool_embedding(slug)` synchronously: (1) generates an embedding via OpenAI, (2) writes it to `tools_seed.embedding`, (3) publishes the embedding to Weaviate's `ToolEmbedding` class.

Failure of step 1 (OpenAI down) leaves the tool approved with `embedding=null`; the next backfill run picks it up. Failure of step 3 (Weaviate down) is logged silently; the next `republish-tools` run picks it up.

## F-EMB-3 — Profile embedding generation (lazy)

`POST /api/answers` continues to do NO embedding work; it only bumps `last_invalidated_at` (per F-QB-3 from cycle #2). Profile embeddings are generated **on demand** when cycles #5 / #6 call `ensure_profile_embedding(user)` to back a similarity-search query.

**Given** a `profiles` row exists for the user
**When** `ensure_profile_embedding(user)` is called
**Then** if `embedding IS null` OR `last_invalidated_at > last_recompute_at`:
1. Build the embeddable text from `profile.role` (if populated) + the user's last 20 answer values.
2. Fetch an embedding via OpenAI.
3. Write it to `profiles.embedding`; bump `last_recompute_at = now`.
4. Publish to Weaviate's `ProfileEmbedding` class.

If the embedding is fresh (`last_recompute_at >= last_invalidated_at` AND `embedding IS NOT null`), the helper is a no-op.

The helper raises `ValueError` if called with a founder user (defense in depth — founder users have no profile per F-QB-5, so this branch is unreachable in production but guarded for safety).

## F-EMB-4 — Weaviate schema + bootstrap CLI

Two classes live in Weaviate:

**`ToolEmbedding`** with properties `slug` (TEXT), `category` (TEXT), `curation_status` (TEXT), `labels` (TEXT_ARRAY). Vector index: HNSW with cosine distance. Vectorizer: none (vectors are computed externally via OpenAI).

**`ProfileEmbedding`** with property `user_id` (TEXT). Same vector index + vectorizer config.

`python -m app.embeddings init-weaviate` creates the classes if missing. Idempotent — re-running on an already-initialized cluster is a no-op.

The Mongo `embedding` field on `tools_seed` and `profiles` is the source of truth (audit / export per the *"Treat the user's profile as theirs"* principle); Weaviate is a search accelerator.

## F-EMB-5 — `similarity_search` helper

```python
async def similarity_search(
    *,
    collection_name: str,         # "tools_seed" or "profiles"
    weaviate_class: str | None,   # "ToolEmbedding" / "ProfileEmbedding" / None
    query_vector: list[float],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]: ...
```

**Three execution paths**, selected automatically:

1. **Mongomock fallback (tests):** if the active Mongo client is `AsyncMongoMockClient`, the helper computes Python-side cosine over Mongo documents whose `embedding` is non-null, applies any filter dict to the Mongo query, and returns the top-k.
2. **Production via Weaviate:** if `weaviate_class` is provided AND a Weaviate connection succeeds, the helper runs `near_vector` with the filter translated to Weaviate's `Filter` expression. The query returns identifier values (slug or user_id); the helper then re-fetches full documents from Mongo in similarity order.
3. **Production fallback (Mongo cosine):** if Weaviate is unreachable for any reason, the helper logs a warning and falls back to the same Python-side cosine path used by tests. Mesh degrades gracefully — slower but functional.

Pass `weaviate_class=None` to force the Mongo cosine path.

## F-EMB-6 — Reject clears the tool's embedding

**Given** an admin posts `POST /admin/catalog/{slug}/reject` with a non-empty comment
**When** `set_status(...)` flips `curation_status` to `"rejected"`
**Then** the handler:
1. Sets `tools_seed.embedding = null` (Mongo).
2. Deletes the corresponding object from Weaviate's `ToolEmbedding` class.

The tool row stays in `tools_seed` (audit trail, future re-approval), but it disappears from similarity-search results. Re-approving the tool re-runs the F-EMB-2 path and the embedding (Mongo + Weaviate) is restored.

---

## Architectural notes

- **Two-store architecture by design.** Mongo is source of truth (data + embeddings). Weaviate is a search accelerator. The Mongo `embedding` field is large (~12 KB per row at 1536 floats) but storage is cheap and the field powers (a) export per the constitutional principle, (b) the test fallback, (c) the production fallback when Weaviate is down.
- **`publish_tool` and `publish_profile` are best-effort writes.** They never fail the calling request; they log on failure. The next backfill / republish picks up missed publishes.
- **`replace()` requires existence; `insert()` requires non-existence.** Weaviate v4's data API doesn't ship a single upsert call; the `_upsert` helper tries insert first, falls back to replace on any error. Discovered during validation when an early publish_tool implementation used `replace` only and failed silently on first run.
- **Schema field rename (`embedding_vector_id` → `embedding`).** Cycle #2 and #3 reserved a placeholder field shaped for an external vector DB reference. This cycle realized the actual storage decision (vectors live inline in Mongo) and renamed the field accordingly. The rename was a code-only change because no production data existed for the old name.
- **Lazy profile embedding is for V1 efficiency, not correctness.** When `POST /api/answers` does NOT regenerate the embedding inline, every answer leaves the profile slightly stale until the next similarity-search call. This is acceptable for V1 because (a) cycle #5's tap-to-answer onboarding doesn't query similarity until after enough taps to make the embedding meaningful, and (b) cycle #6's weekly recommendations call `ensure_profile_embedding` once per generation. V1.5+ may move embedding regeneration to a Celery debounced task (the original system_design plan).

## Out of scope (V1 deferrals)

- HTTP search endpoints — owned by cycle #5 (`/api/onboarding/match`) and cycle #6 (`/api/recommendations`).
- Async embedding orchestration via Celery + Redis — V1.5+ when traffic justifies it.
- Programmatic creation of Weaviate classes via the management API — V1 ships with the manual `init-weaviate` CLI.
- Hardcoded "first-3-questions" generic-recommendation fallback — owned by cycle #5 per a user note (early answers are too generic for embedding-based matching).
- Caching / connection pooling for the OpenAI client — V1 uses the SDK's default client per call.
- Embedding model swap surface (Voyage, Cohere, sentence-transformers) — fixed at OpenAI `text-embedding-3-small` for V1.
- Profile aggregation logic (turning answers into structured profile.role / current_tools / etc.) — owned by a future feature slotted between this and cycle #6.
