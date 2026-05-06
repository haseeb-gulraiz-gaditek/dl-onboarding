# Integration plan — wiring Approach 1 into the FastAPI/React app

This is a roadmap, not a commitment. The validation experiment lives at
`validation/approach1/` — fully decoupled from the running app. If the
metrics review says "ship it," follow this plan to plug it into Mesh.

---

## Current state of the app's recommendation stack

| Layer | Module | What it does |
|---|---|---|
| Storage | `app/db/tools_seed.py` | 547-tool catalog, Mongo `tools_seed` collection |
| Embeddings | `app/embeddings/lifecycle.py`, `vector_store.py` | OpenAI embeddings → Weaviate `ToolEmbedding` class |
| Generic match | `app/onboarding/match.py` | Pre-3-answers: role → categories → all_time_best |
| Embedding match | `app/onboarding/match.py::embedding_match` | Post-3-answers: profile vector × Weaviate similarity |
| Final ranker | `app/recommendations/engine.py` | similarity top-20 → GPT-5 ranker → 5 picks |
| Cache | `app/db/recommendations.py` | Per-user, 7-day TTL |

**Approach 1 is a different engine** — same input shape (onboarding
answers), different output (top-K live narrowing instead of
similarity+LLM-pick-5), and it does no LLM call at runtime.

---

## Pluggability: 3 wiring options

### Option A — New endpoint alongside (cheapest, most reversible)

```
POST /api/recommendations/live-narrow
Request:  { answers: { Q1: {...}, Q2: [...], Q3: "...", Q4: "..." } }
Response: { step: "Q3", top: [{slug, name, score, breakdown}, ...], count_kept: 50 }
```

- **Backend changes**: new module `app/recommendations/feature_engine.py`
  re-implementing `feature_scorer.score_tool` against
  `tools_seed_collection`. Reads tagged features from a *new*
  Mongo collection `tool_features` (one doc per slug, written by a
  port of `validation/approach1/tag_features.py`).
- **Migration path**: copy `catalog_features.json` into Mongo via a
  new seeder script `app/seed/tool_features.py`. Idempotent upsert
  by slug.
- **Frontend changes**: new page `frontend/src/app/onboarding/live/`
  using the 4 questions from `validation/onboarding-v1-locked.md`,
  calling `/live-narrow` after each answer and animating the kept-count.
- **Risk**: zero — old engine untouched, can A/B with a query param
  or feature flag.
- **Effort**: ~2 days.

### Option B — Replace the embedding+GPT-5 path

Drop Weaviate + GPT-5 ranker in `app/recommendations/engine.py`,
replace `similarity_search` with `feature_engine.rank_tools`,
keep the cache + response shape.

- **Risk**: high — changes shipped behavior; tests for `engine.py`
  and `match.py` will break and need rewrite.
- **Effort**: ~3 days + test rewrite.
- **Only do this if**: A1 metrics clearly beat the embedding+GPT-5
  baseline AND the 7-day cache is acceptable to drop (A1 is fast
  enough that caching matters less).

### Option C — Feature-flagged inside `engine.py`

Add `MESH_REC_BACKEND={embedding|features}` env var; `engine.py`
branches between the existing path and the A1 path.

- **Risk**: medium — adds branching complexity.
- **Effort**: ~1.5 days.
- **Only do this if**: you want to A/B in production with the same
  endpoint shape.

**Recommendation**: Option A first, evaluate, then collapse to B if
the A1 path wins.

---

## Mongo schema — `tool_features` collection (Option A/B/C all need it)

```ts
{
  slug: string,                       // PK, FK to tools_seed.slug
  industry: string[],                 // closed enum, see schema.py INDUSTRIES
  role_fit: string[],                 // free-form
  stack_integrations: string[],       // free-form, tool names
  task_shape: string[],               // closed enum
  paradigm: string[],                 // closed enum
  excluded_paradigms: string[],       // closed enum, hard-veto dim
  setup_tolerance: "under_2min"|"around_10min"|"willing_to_customize",
  capabilities: string[],             // free-form
  maturity_required: "low"|"medium"|"high",
  tagged_at: Date,
  tagged_by: "gpt-4o-mini"|"manual",
}
```

**Indexes**:
```
tool_features_slug_unique      [slug ASC]
tool_features_industry         [industry ASC]   // for fast Q1 prefilter
```

**Backfill**: port `validation/approach1/tag_features.py` to
`app/seed/tool_features.py`, run once on deploy. Re-run when
`tools_seed` adds new tools (script is already resumable — only tags
slugs not in `tool_features`).

---

## Live-narrowing semantics (the part the doc cares about)

The doc says soft narrowing — 300 → 150 → 100 → 50 → 10 — and a tool
that drops out at step N can come back at step N+1. The validation
script's current implementation **does NOT** allow this: each step
filters from the previous step's surviving set.

For production, the spec requires re-scoring the *full catalog* at
every step (not just survivors), then taking top-K. This is fine
performance-wise: 547 × 7 dims × Python = sub-50ms.

```python
# pseudocode for the live-narrow endpoint
for q_idx, answer in enumerate(answers):
    user_vec = extend_vector(user_vec, answer)
    ranked = rank_tools(user_vec, FULL_CATALOG)  # always full
    cap = NARROW_SCHEDULE[q_idx]
    ws_send({"step": q_idx, "top": ranked[:cap]})
```

Update validation script to match before integration.

---

## Open issues to resolve before shipping

1. **Catalog coverage gap.** The 547-tool catalog is missing
   audit-specific (DataSnipper, MindBridge, Caseware) and
   physician-specific (Suki, Nuance DAX, Heidi Health) tools. A1
   surfacing personal-finance apps for ACCA is the catalog's fault,
   not the scorer's. Block #1 before any integration: add the
   role-specific verticals.
2. **Industry enum granularity.** `finance_accounting` lumps
   audit + corporate accounting + personal finance + crypto. Either
   split the enum (audit, corporate_finance, personal_finance,
   tax) or use a multi-label industry tagging.
3. **Equal weights are wrong.** Hand-eyeballed: `industry`, `role`,
   `setup` dominate; `stack` and `paradigm` are diluted. Tune via a
   small grid search once we have eyeball-validated gold ranks.
4. **Hard exclusion dim is currently a black box.** `excluded_paradigms`
   silently zeros a tool. Production should surface "skipped: X" so
   the UI can render *why*.

---

## Cutover checklist (when A1 wins eyeball)

- [ ] Port `tag_features.py` → `app/seed/tool_features.py`
- [ ] Add `tool_features` Mongo collection + indexes
- [ ] Run feature seeder against approved tools
- [ ] Add `app/recommendations/feature_engine.py` with `score_tool` /
      `rank_tools` (copy from `validation/approach1/feature_scorer.py`)
- [ ] Add `app/recommendations/feature_extractor.py` to derive
      UserVector from onboarding answers (rules-first, LLM-fallback
      for ambiguous Q3/Q4)
- [ ] Add `POST /api/recommendations/live-narrow` endpoint
- [ ] Add `/onboarding/live` page in frontend
- [ ] Wire SSE or POST-per-step for live updates
- [ ] Add Pytest coverage for the scorer + extractor
- [ ] Decide: keep embedding+GPT-5 engine? (Option A) or retire?
      (Option B)
