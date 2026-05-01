# Spec Delta: weaviate-pipeline

## ADDED

### F-EMB-1 — `OPENAI_API_KEY` is required at boot

`_REQUIRED_ENV` extends from `("MONGODB_URI", "JWT_SECRET", "ADMIN_EMAILS")` to include `OPENAI_API_KEY`. App refuses to boot if any of the four is unset or blank. `.env.example` documents the new var with format guidance and a link to the OpenAI dashboard.

---

### F-EMB-2 — Tool embedding generation

Two paths produce tool embeddings: a one-shot CLI for backfill, and synchronous calls inside the admin approve handler.

#### Backfill CLI

**Given** the operator runs `python -m app.embeddings backfill-tools`
**When** the command starts
**Then** for every row in `tools_seed` where `curation_status = "approved"` AND `embedding IS null`, the system fetches an embedding from OpenAI and writes it to the row's `embedding` field.

The command prints `embedded: N, skipped: M, failed: K, total: T` where:
- `embedded`: rows that now have a fresh embedding
- `skipped`: rows that already had `embedding` populated (idempotent)
- `failed`: rows where the OpenAI call returned an error (the row is left as-is; the command continues)
- `total`: rows considered

Rows with `curation_status` other than `"approved"` are not embedded. The command exits 0 if `failed == 0`, else exits 1.

#### Synchronous on admin approve

**Given** an admin posts `POST /admin/catalog/{slug}/approve`
**When** `set_status(...)` succeeds and returns the updated row
**Then** the handler synchronously calls `ensure_tool_embedding(slug)`, which (if the row's `embedding` is null) fetches an embedding from OpenAI and writes it.
**And** the response payload includes the (now-populated) row.

Failure of the embedding step does NOT roll back the approve action. If OpenAI is unreachable, the tool is approved without an embedding; the next backfill run picks it up.

---

### F-EMB-3 — Profile embedding generation (lazy, on-read)

`POST /api/answers` continues to do NO embedding work; it only bumps `last_invalidated_at` per F-QB-3.

A new helper `ensure_profile_embedding(user)` is exposed for **future cycles** (#5, #6) to call when they need a current profile embedding for similarity search.

**Given** a `profiles` row exists for the user
**When** `ensure_profile_embedding(user)` is called
**Then** if `embedding IS null` OR `last_invalidated_at > last_recompute_at`, the system synthesizes the profile's embeddable text from the user's recent answers, fetches an embedding from OpenAI, writes it to `embedding`, and bumps `last_recompute_at = now`.

If the embedding is fresh (`last_recompute_at >= last_invalidated_at` AND `embedding IS NOT null`), the helper is a no-op.

The helper refuses to run on a founder-role user (defense in depth — founders have no profile per F-QB-5 anyway, so this branch is unreachable in production but guarded for safety).

---

### F-EMB-4 — Atlas Vector Search index definitions

Two manually-created Atlas search indices, schemas documented as constants in `app/embeddings/atlas.py`.

**`tools_seed_vector_index`** on `tools_seed` collection:
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "curation_status"
    },
    {
      "type": "filter",
      "path": "category"
    },
    {
      "type": "filter",
      "path": "labels"
    }
  ]
}
```

**`profiles_vector_index`** on `profiles` collection:
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

V1 ships with these specs documented; the user creates the indices once via the Atlas UI. The app does NOT auto-create them — programmatic creation requires the Atlas Admin API which is V1.5+.

---

### F-EMB-5 — `similarity_search` helper

A reusable async helper for cycles #5 and #6:

```python
async def similarity_search(
    *,
    collection_name: str,
    index_name: str,
    query_vector: list[float],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
```

**Given** a `query_vector` of length 1536, an existing collection name, and an existing Atlas Search index name
**When** `similarity_search` is called
**Then** the system runs an Atlas `$vectorSearch` aggregation against the index and returns up to `top_k` documents in similarity-descending order.

Optional `filters` are applied via `$vectorSearch.filter` (e.g., `{"curation_status": "approved", "category": "productivity"}`).

If the index does not exist, the underlying driver raises a clear error; the helper does not swallow it.

**Test-time exception:** `mongomock-motor` does not support `$vectorSearch`. The test suite uses a Python-side cosine fallback to exercise the helper's contract. Production code path is unchanged; the fallback is detected by checking the client class (`AsyncMongoMockClient`).

---

### F-EMB-6 — Reject clears the tool's embedding

**Given** an admin posts `POST /admin/catalog/{slug}/reject` with a non-empty comment
**When** `set_status(...)` flips `curation_status` to `"rejected"`
**Then** the handler synchronously calls `clear_tool_embedding(slug)`, which sets the row's `embedding = null`.

A rejected tool retains its row (for audit trail and future re-approval) but is invisible to similarity search because its embedding is gone. Re-approving a previously-rejected tool re-runs `ensure_tool_embedding` (F-EMB-2 path) and the embedding comes back.

## MODIFIED

### Field rename: `embedding_vector_id` → `embedding`

**Affected specs:** `specs/features/question-bank-and-answer-capture/spec.md` (cycle #2 profile schema), `specs/features/catalog-seed-and-curation/spec.md` (cycle #3 tool schema).

**Before:** `embedding_vector_id: <string | null>` — placeholder field shaped for a foreign reference into a separate vector store (Weaviate).

**After:** `embedding: <list[float] | null>` — the actual vector stored inline in the same Mongo document. Atlas Vector Search indexes the field directly.

The rename includes:
- `app/db/profiles.py`'s `_new_profile_doc` factory
- `app/db/tools_seed.py`'s `upsert_tool_by_slug` `$setOnInsert` payload
- `app/models/profile.py` Pydantic shape
- `app/models/tool.py` Pydantic shape

No production data exists yet for either field, so the rename is a code-only change with no migration.

### Cycle #3 seed-loader default: `curation_status: "pending"` → `"approved"`

**Affected spec:** `specs/features/catalog-seed-and-curation/spec.md` (F-CAT-3 "Defaults applied").

**Before:** new entries default to `curation_status: "pending"` so an admin reviews them before they enter the recommendation pipeline.

**After:** new entries default to `curation_status: "approved"`. Per user call: the seed catalog is already curated through the external research prompt + the user's review of `catalog.json`; a second approval step is theatre. **Founder-launched entries (cycle #8) still go through `pending → approved` review** — that's where the queue earns its keep.

The admin reject-with-comment endpoint stays. Approve becomes "re-approve a previously-rejected entry" rather than "first approval."

### Cycle #3 `POST /admin/catalog/{slug}/approve` side effect

**Affected spec:** F-CAT-5 approve endpoint.

**Before:** the handler set `curation_status = "approved"`, `last_reviewed_at`, `reviewed_by`, and cleared `rejection_comment`. That was the entire effect.

**After:** the handler additionally calls `ensure_tool_embedding(slug)` synchronously after the status update. On OpenAI failure, the approve still succeeds (graceful degradation per F-EMB-2); the embedding is filled by the next backfill run.

### Cycle #3 `POST /admin/catalog/{slug}/reject` side effect

**Affected spec:** F-CAT-5 reject endpoint.

**Before:** the handler set `curation_status = "rejected"`, recorded the comment, recorded the reviewer.

**After:** the handler additionally calls `clear_tool_embedding(slug)` synchronously per F-EMB-6. The rejected tool is removed from the recommendation pipeline.

### `_REQUIRED_ENV` in `app/main.py`

**Before:** `("MONGODB_URI", "JWT_SECRET", "ADMIN_EMAILS")`
**After:** `("MONGODB_URI", "JWT_SECRET", "ADMIN_EMAILS", "OPENAI_API_KEY")`

`.env.example` is updated to include `OPENAI_API_KEY=` with a link comment.

## REMOVED

(None.)
