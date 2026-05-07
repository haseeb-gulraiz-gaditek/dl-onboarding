# Iter 11 — Query2Box / BetaE neuro-symbolic operators

**Approach**: parse intent JSON into a tree of logical ops (∧, ∨, ¬, ∃) → compose boxes (Query2Box / Concept2Box) or Beta distributions (BetaE) from entity/concept embeddings → answer = entities inside the resulting region → re-rank by cosine to iter-5 text candidates. Replaces iter-8 agent's slow LLM path for common compositional queries with a single-digit-ms vector op.

## Top 3 papers
- **BetaE (Ren & Leskovec, NeurIPS 2020, arXiv 2010.11465)** — Beta-distribution embeddings; uniquely supports **negation natively** (Query2Box doesn't). Mesh's `excluded_tools` constraint becomes a first-class operator.
- **Concept2Box (Huang ACL Findings 2023, arXiv 2307.01933)** — entity ↔ concept hierarchies in shared box space; fits Mesh's "tools belong to capability concepts" structure (Tool ⊆ has_capability(Summarization) ⊆ AI_Assistant_Class).
- **GNN-QE (Zhu ICML 2022)** — hybrid GNN + logical query embedding; demonstrates how to compose iter-7's heterograph with iter-11's box ops without rebuilding either.

Honorable: Query2Box (foundational), ConE (cone-based, hierarchy-aware), LMPNN (ICLR 2023, message-passing logical solver), CLMPT (KDD 2024, transformer-based query answering), Neural-Symbolic KG Reasoning survey 2024 (closed-world critique).

## Scores
- **depth = 7.5** — native ∧∨¬∃∃ in retrieval-space, no LLM round-trip. Real lift over iter-8 on compositional queries. Cap: closed-world (entities/relations only as seen at training); depth-3+ nested composition compounds error; new entities need retraining or KEPLER-style text-init proxies.
- **noise = 7.5** — boxes are robust to single-entity noise (region averages over many points); BetaE's probabilistic semantics handle uncertainty natively. Risk: small-KG training scarcity at Mesh launch reduces sharpness.
- **compose = 7.5** — feeds iter 8 (agent calls box solver as a fast tool primitive — slow path becomes fallback), iter 5 (boxes complement multi-vector retrieval), iter 6 (entities = box centers, warm-start from KG embeddings). Slight cost: box index + retraining pipeline as catalog grows.
- **composite = 7.5·0.5 + 7.5·0.3 + 7.5·0.2 = 3.75 + 2.25 + 1.5 = 7.50**

## Verdict
**ADVANCE** (composite 7.50 ≥ 7.0). Locks in as V1.5 fast path for compositional queries; iter-8 agent becomes fallback when box answer set is empty or low-confidence.

## Gap left
1. **Closed-world ceiling.** Box ops only resolve queries over entities seen at training time. For brand-new tools or just-launched integrations, there's no embedding yet.
2. **No long-context personalization at query time.** Mesh's concierge has full chat history per user — currently only iter 2 sees it (intent extraction). A long-context model could re-personalize at every query.
3. **Saturation explicit.** Iters 8–11 all scored 7.45–8.45. Marginal value-per-iter has flattened. Diminishing returns.

## Next direction
**In-context recommendation with long-context Sonnet (1M tokens) — final algorithm iter before synthesis.** Pack the user's full chat history + structured intent + iter-5 top-50 candidates + iter-6 KG triples + iter-11 box-op results into a single Sonnet prompt; let the model produce the final ranking + reasoning trace in one pass. Tests whether long-context replaces the multi-stage pipeline for *small* catalogs (Mesh's 300 tools fit entirely in context) — possibly a V1 simplification path. After iter 12, **write SYNTHESIS** — composition strategy across V1/V1.5/V2/V3 with activation thresholds and latency budgets.
