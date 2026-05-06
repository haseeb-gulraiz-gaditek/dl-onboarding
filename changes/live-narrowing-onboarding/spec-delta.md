# Spec Delta: live-narrowing-onboarding

## ADDED

### F-LIVE-1 — `LiveQuestion` model + locked 4-question schema

`app/onboarding/live_questions.py` exposes:

```python
class LiveQuestion(BaseModel):
    q_index: int                # 1..4
    key: str                    # "role.identity" / "stack.daily_open" / ...
    text: str                   # display copy
    kind: Literal["dropdowns_3", "multi_select", "single_select"]
    options: list[Option] | None         # None for dropdowns_3
    options_per_role: dict[str, list[Option]] | None   # Q2/Q3 only
    fallback_options: list[Option] | None              # Q2/Q3 only

LIVE_QUESTIONS: list[LiveQuestion] = [Q1, Q2, Q3, Q4]   # locked
```

The schema is loaded as an in-process constant (NOT seeded to Mongo). `Q1` is
three dropdowns: job title (typeable + suggestions), level, industry. `Q2` is
multi-select chips, role-conditioned. `Q3` is single-select scenario, role-
conditioned. `Q4` is single-select friction (role-agnostic). Copy locked from
`validation/onboarding-v1-locked.md`.

`options_per_role` covers ~12 hand-curated roles (Software Engineer, Accountant,
Doctor, Marketer, Designer, Product Manager, Sales, Founder, Student, Lawyer,
Operations, Customer Success, Consultant). `fallback_options` (a generic
~12-tool list) is used when the user's Q1 job title isn't in the
`options_per_role` map.

**Given** a caller `GET /api/onboarding/live-questions`
**When** the user is authenticated as `role_type=user`
**Then** the response is `{questions: LiveQuestion[]}` with 4 entries.

**Given** a caller `GET /api/onboarding/live-questions/{q_index}/options?role={role_value}`
**When** `q_index in {2, 3}` and the role exists in `options_per_role`
**Then** the response returns the role-specific options array. If role unknown,
returns `fallback_options`. If `q_index in {1, 4}`, returns 400.

---

### F-LIVE-2 — `POST /api/recommendations/live-step`

Behind `require_role("user")`. Founders → 403. Unauthenticated → 401.

**Request:**
```json
{ "q_index": 1..4, "answer_value": <answer payload> }
```

`answer_value` shape varies by question kind:
- `dropdowns_3` (Q1): `{"job_title": str, "level": str, "industry": str}`
- `multi_select` (Q2): `{"selected_values": list[str]}`
- `single_select` (Q3 / Q4): `{"selected_value": str}`

**Response:**
```json
{
  "step": 1..4,
  "top": [
    {
      "slug": "notion",
      "name": "Notion",
      "tagline": "...",
      "score": 0.84,
      "layer": "relevant",
      "reasoning_hook": "matches your daily-open list"
    },
    ...
  ],
  "count_kept": 20 | 15 | 10 | 6,
  "wildcard": { ... single tool object outside top band ... }
}
```

**Pipeline (per step):**

1. Persist the answer to the `answers` collection (existing pattern). Multiple
   answers to the same `q_index` overwrite via the live flow's `answer_id`
   convention (one row per `(user_id, q_index)`); old answers stay in the
   collection (append-only) but only the latest is read for profile_text.
2. Build `profile_text` from all of the user's live answers so far (structured
   paragraph; keys → human phrases).
3. Call `ensure_profile_embedding(user, force_recompute=True)` — bumps
   `last_invalidated_at` and regenerates the OpenAI vector. ~250–400ms.
4. Run `hybrid_search()` (F-LIVE-3) with:
   - `query = profile_text` (BM25 side)
   - `vector = profile.embedding` (vector side)
   - `alpha = ALPHA_SCHEDULE[q_index]` = `[0.3, 0.5, 0.7, 0.8][q_index-1]`
   - `limit = K_SCHEDULE[q_index] + 1` = `[20, 15, 10, 6][q_index-1] + 1`
   - `filters = {"curation_status": "approved"}`
5. Hydrate full tool data from Mongo by slug (`tools_seed`).
6. Apply score-band layers using thresholds `LAYER_BANDS = {"general": 0.55,
   "relevant": 0.65, "niche": 0.75}`. Each tool gets `layer = highest band
   whose threshold it meets`.
7. Pick the wildcard: the lowest-scoring tool from the `+1` over-fetch (i.e.,
   intentionally pull from outside the top band to surface variety).
8. Return.

Latency target: <800ms (down from backlog's 200ms). The OpenAI embed dominates;
~350ms typical, ~600ms worst case. Hybrid + Mongo hydrate + layer-label total
<50ms.

**Failure modes:**
- OpenAI embed raises → 503 with `{"error": "embed_unavailable"}`. The frontend
  shows "matching paused — try again" and the answer is already persisted, so
  retry is idempotent.
- Weaviate hybrid raises (gRPC blocked, BM25 module disabled, etc.) → fall back
  to `similarity_search()` (existing pure-vector path). Response includes
  `degraded: true`. The user sees results.
- Both Weaviate AND Mongo profile lookup fail → 503 with
  `{"error": "live_step_unavailable"}`.

---

### F-LIVE-3 — `hybrid_search()` helper

`app/embeddings/vector_store.py` gains:

```python
async def hybrid_search(
    *, weaviate_class: str,
    query: str,
    vector: list[float],
    alpha: float,
    limit: int,
    filters: dict[str, str] | None = None,
) -> list[tuple[dict, float]]:
    """Run Weaviate v4 hybrid: BM25 keyword + vector cosine, alpha-blended.
    Returns [(properties_dict, score)] sorted descending. None client → []."""
```

Wraps `client.collections.use(weaviate_class).query.hybrid(query=query,
vector=vector, alpha=alpha, limit=limit, filters=...)` per Weaviate v4 API.
Score is `o.metadata.score` from the response. Same None-client short-circuit
as `similarity_search`.

When `WEAVIATE_USE_GRPC=false` (F-LIVE-7) and the cluster is REST-only,
Weaviate-Python falls back to REST `/v1/graphql` for hybrid; same response
shape, ~3× slower.

---

### F-LIVE-4 — Per-tap profile vector persistence

The `/api/recommendations/live-step` endpoint always calls
`ensure_profile_embedding(user, force_recompute=True)` BEFORE returning. This
guarantees:

- If a user abandons after Q2, their profile reflects 2 answers and the next
  `/home` load (or any future call to `/api/recommendations`) reads that
  profile vector.
- The cycle #6 cached-recommendations engine continues to work unchanged. After
  Q4 completes, the persisted vector is the same one cycle #6 reads from.

`ensure_profile_embedding` already exists from cycle #4; the only change is
that the live-step pipeline always passes `force_recompute=True` to bypass the
"only re-embed if invalidated" check. Re-embedding 4× per onboarding session is
acceptable cost.

---

### F-LIVE-5 — Score-band layer assignment

`app/recommendations/live_engine.py::layer_for(score)` returns the highest band
the score qualifies for:

```python
LAYER_BANDS: dict[str, float] = {
    "niche":    0.75,
    "relevant": 0.65,
    "general":  0.55,
}
def layer_for(score: float) -> str | None:
    if score >= 0.75: return "niche"
    if score >= 0.65: return "relevant"
    if score >= 0.55: return "general"
    return None  # below floor; excluded from top
```

Tools below 0.55 cosine are excluded entirely (the response top can be shorter
than `K_SCHEDULE[q_index]`). This preserves "honest signal" — niche profiles
return what they return.

**Tunable.** Single module constant. Persona walkthrough at end of cycle may
adjust; document the values used.

---

### F-LIVE-6 — Wildcard selection

To preserve the constitution's "concierge surprise factor" (cross-cluster
surfacing), every response includes one wildcard tool from outside the top
band. Implementation:

1. Over-fetch: request `K + 1` from hybrid_search.
2. Take top-K by score as the main `top` list.
3. The (K+1)th result becomes the wildcard.

If hybrid returns fewer than K+1 results (niche profile), wildcard is `null`.
The frontend handles null gracefully (no wildcard chip rendered).

---

### F-LIVE-7 — `WEAVIATE_USE_GRPC` env flag (dev resilience)

`_get_weaviate_client()` in `app/embeddings/vector_store.py` reads
`WEAVIATE_USE_GRPC` (default `"true"`). When set to `"false"`:

- The v4 client is configured with `additional_config=AdditionalConfig(
  grpc_secure=False, ...)` and `skip_init_checks=True` so it never attempts
  the gRPC health probe.
- Queries (`hybrid`, `near_vector`, etc.) go over REST `/v1/graphql`.
- Inserts/updates also go over REST.

Logged once at startup: `[vector_store] WEAVIATE_USE_GRPC=false; using REST-
only mode (slower but works on networks that block gRPC)`.

Production keeps `WEAVIATE_USE_GRPC=true` (default) — gRPC is materially
faster. Dev sets it `false` when the local network blocks gRPC port.

---

### F-LIVE-8 — Frontend `/onboarding/live` page

`frontend/src/app/onboarding/live/page.tsx`:

- Reads question schema from `GET /api/onboarding/live-questions`.
- Per-question UI:
  - Q1: three dropdowns side-by-side, "Continue" enables when all three set.
  - Q2: chips fed by `GET /api/onboarding/live-questions/2/options?role={Q1.job_title}`. Multi-select, "Continue" enables on ≥1 selection.
  - Q3: same but single-select.
  - Q4: single-select friction list (no role conditioning).
- After each "Continue", calls `POST /api/recommendations/live-step` with the
  answer. Shows "Updating…" placeholder during the embed (250–800ms).
- Right pane animates the shrinking ranked list (20 → 15 → 10 → 6). Each tool
  shows its score + layer chip ("general" / "relevant" / "niche") + a
  reasoning hook from the response.
- Wildcard chip surfaces below the top list, labeled "you might not expect →".
- Top-right "save & exit" link routes to `/home` — answers + profile already
  persisted, so they pick up where they left off.
- After Q4: "See your full match →" routes to `/home`. Existing
  recommendation-engine cache populates from the now-final profile vector.

---

### F-LIVE-9 — Feature flag: classic vs live

New env: `MESH_ONBOARDING_VARIANT={"classic","live"}`. Default `"classic"`.

`/api/me` response gains `onboarding_variant` field (mirrors the env). Frontend
reads it on mount and routes:
- `classic` → existing `/onboarding`
- `live` → new `/onboarding/live`

Setting is per-deploy in V1; per-user A/B framework deferred to V1.5+.

`require_role("user")` still gates both flows. Founders never see either.

---

### F-LIVE-10 — Persona walkthrough validation

`validation/approach1/results-live.md` records:
- ACCA / SWE / Doctor personas walked through Q1–Q4.
- Per-step: which top-K tools surfaced, score, layer, wildcard.
- Subjective grade: "would Maya/the persona find this list useful?"
- Comparison vs the no-embedding baseline (`results.md`).

Run as a smoke test before merging the cycle. Used to tune `LAYER_BANDS` if
needed.

---

## MODIFIED

### `fast-onboarding-match-and-graph` (cycle #5)

**Before:** sole onboarding flow; `POST /api/onboarding/match` is the
recommendation surface during onboarding.

**After:** classic flow stays as-is, behind the `MESH_ONBOARDING_VARIANT=
classic` flag (default). New live flow is parallel, behind
`MESH_ONBOARDING_VARIANT=live`. Both share the underlying `tools_seed`,
`profiles`, and `answers` collections. No code changes to `/api/onboarding/
match` or its spec — the live flow uses a different endpoint.

### `weaviate-pipeline` (cycle #4)

**Before:** `vector_store.py` exposes `similarity_search()` (pure vector cosine)
and `_get_weaviate_client()` always uses gRPC.

**After:** also exposes `hybrid_search()` (F-LIVE-3). `_get_weaviate_client()`
honours `WEAVIATE_USE_GRPC` env var (F-LIVE-7) — `"false"` configures REST-
only mode. No schema change to `ToolEmbedding` / `ProfileEmbedding`.

### `recommendation-engine` (cycle #6)

**Before:** `engine.py` reads the profile vector and runs cosine + GPT-5
reranker, caches in Mongo for 7 days.

**After:** unchanged. The engine reads the same persisted profile vector that
the live flow now writes per-tap. After Q4 completes, the cache populates
naturally.

## REMOVED

(None.)
