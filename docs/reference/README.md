# Reference

External or historical material that supports the venture but isn't itself constitution / architecture / feature / UX. Two big sub-buckets so far:

## Sub-directories

### `algorithm-research/`
A 16-iteration Karpathy-loop research log on the matching-algorithm design space. The final synthesis (`SYNTHESIS.md`) selected the V1 pipeline that cycle #15 (live-narrowing-onboarding) implemented:
- **Iter 5** — ColBERT per-field MaxSim retrieval (substrate; the production live engine uses Weaviate hybrid with similar intent)
- **Iter 12** — Long-context Sonnet listwise rerank (deferred to V1.5; cycle #15 ships hybrid alone)
- Iter 8 (agentic) and Iter 9 (causal uplift) deferred to V2/V3.

`iterations/` keeps the per-iter raw output. `state.yaml` and `log.md` capture loop metadata. Useful if we revisit the algorithm — we have the full reasoning trace.

### `early-thinking/`
The pre-constitution brainstorm files. These were the load-bearing source for the constitution (see `specs/ingestion-log.yaml` ING-001..ING-007). Preserved as historical context — the constitution is the source of truth now, but these files record *why* the constitution says what it says.

- `basic-idea.md` — earliest framing
- `ideas-v1` → `ideas-v4` — successive refinement
- `persona-ideas-v1` / `v2` — persona drafts that became `specs/constitution/personas.md`

## When to add a doc here

- Research output that informed a cycle but doesn't belong inside a single feature spec.
- Externally-sourced material (papers, blog post excerpts, vendor docs) that shapes our thinking.
- Historical artifacts that future contributors might want to trace ("why did we pick this approach over X?").

## Freshness

Reference material has the slowest decay. Check it when you re-visit the underlying decision; otherwise leave it.
