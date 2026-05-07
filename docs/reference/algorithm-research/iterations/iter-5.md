# Iter 5 — ColBERT multi-vector late interaction with per-field encoding

**Approach**: each intent slot (`frictions`, `desired_capabilities`, `excluded_tools`, `workflow_edges`) keeps its own token-vector set; tool catalog indexed once with field-keyed PLAID. Score = mFAR-style adaptive weighted sum of per-field MaxSim + **negative MaxSim** on `excluded_tools` for hard exclusion at retrieval time (not just rerank).

## Top 3 papers
- **ColBERTv2 (Santhanam 2022, arXiv 2112.01488)** — denoised supervision + residual compression collapses index size 6-10×. Production-grade late interaction; baseline architecture for Mesh.
- **mFAR (ICLR 2025, arXiv 2410.20056)** — multi-field adaptive retrieval with learned per-field weights; directly fits Mesh's per-slot scoring need without hand-tuned weights.
- **PLAID (Santhanam 2022, arXiv 2205.09707)** — centroid-pruned ColBERTv2 retrieval; sub-50ms latency at scale. Makes per-field indexing affordable.

Honorable: ColBERT v1 (foundational), COIL (lexical-anchored hybrid), MVR (multi-vector retrieval beyond ColBERT), XTR (token-importance for sparser indexing), ColBERTer (lighter-weight late interaction), PARADE (per-aspect aggregation).

## Scores
- **depth = 7.0** — true per-field granularity; hard exclusion at retrieval time (architectural guarantee, not rerank down-weighting); interpretable per-slot scores for concierge. Honest cap: still token co-occurrence — `workflow_edges` like "Notion→Linear" remain bag-of-tokens. A tool mentioning both names in unrelated contexts scores identically to one that actually bridges them.
- **noise = 7.5** — per-field MaxSim absorbs paraphrase within slots; missing slots degrade gracefully (no penalty); negative MaxSim guarantees `excluded_tools` filtering. Slight overfit risk on small data given more parameters.
- **compose = 7.5** — slots into iter 2 (drives per-field indexing) and iter 4 (rerank stage). Adds infra complexity: per-field indices, mFAR weighting, PLAID compression. Less plug-and-play than the CE rerank but a clear architectural step.
- **composite = 7.0·0.5 + 7.5·0.3 + 7.5·0.2 = 3.5 + 2.25 + 1.5 = 7.25**

## Verdict
**ADVANCE** (composite 7.25 ≥ 7.0). Locks in as fourth permanent stage. Replaces iter 3's single-vector contrastive retrieval with field-aware multi-vector retrieval; iter 3's contrastive head retrains on the multi-vector outputs.

## Gap left
**Typed graph edges remain the unsolved problem.** Late interaction sees `(Notion, Linear)` as two contextualized tokens, never as `(Notion, exports_to, Linear)` — a typed directed triple. Mesh's whole concierge value rests on workflow-granularity matching ("user copies between Notion and Linear weekly"), and that's a graph claim, not a co-occurrence claim. Multi-hop too: "tool that connects to Slack which my team uses for X" needs path traversal, not similarity.

## Next direction
**RotatE-family knowledge graph embeddings on a tool–capability–integration KG, hybridized with the text retrieval stack.** Build a small KG from existing tool integration manifests (Zapier/Pipedream/native API docs): nodes = tools, capabilities, data types; edges = `integrates_with`, `exports_to`, `imports_from`, `syncs_with`. Train RotatE (or ComplEx) embeddings — RotatE's complex-rotation algebra natively handles symmetry / antisymmetry / composition, exactly the relations integration edges need. At query time, the LLM-extracted `workflow_edges` become KG queries (`(Notion, exports_to, ?Linear)`) scored against KG embeddings; combine with MaxSim text score via learned weights. Composes cleanly with iter 4 (CE rerank can use KG-augmented context) and iter 5 (text MaxSim runs in parallel). Bootstrap: integration manifests are public; ~300-tool KG is small enough to train in minutes.
