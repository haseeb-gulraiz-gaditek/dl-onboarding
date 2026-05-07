# Iter 4 — Cross-encoder reranker with structured intent context

**Approach**: top-50 candidates from iter 3 → cross-encoder ingests `(structured_intent_JSON, tool_description)` as one sequence with full cross-attention → top-5 to concierge. Pointwise CE primary (with reasoning trace for explainability); listwise LLM rerank as tiebreaker.

## Top 3 papers
- **Rank1 (Wang 2025, arXiv 2502.18418)** — test-time-compute reranker that emits an explicit reasoning trace before scoring; directly answers Mesh's "concierge needs to explain why" requirement.
- **InsertRank (2025, arXiv 2506.14086)** — injects structured signals (categories, attributes) into the rerank prompt; validates Mesh's design of feeding the JSON intent object verbatim, not paraphrased.
- **RankZephyr (Pradeep 2023, arXiv 2312.02724)** — distilled listwise LLM reranker; shows OSS 7B model can match GPT-4 reranking at fraction of cost. Path to a self-hosted Mesh reranker if Anthropic API costs scale poorly.

Honorable: monoBERT/monoT5 (foundational), RankGPT (pointwise/listwise framing), RankLLaMA (CE on decoder), BGE-Reranker-v2-m3 (production OSS baseline), NV-RerankQA-Mistral (RAG benchmark), Déjean 2024 (CE-vs-LLM efficiency tradeoff at production K).

## Scores
- **depth = 7.5** — full cross-attention enforces conjunctions (`frictions ∩ capabilities ∩ ¬excluded`) and multi-slot reasoning a bi-encoder can't. Rank1-style traces give per-recommendation explanations the concierge can speak. Still bag-of-tokens: `workflow_edges` as directional edges (Notion→Linear, weekly) flatten into co-occurrence. Honest ceiling here.
- **noise = 7.5** — cross-attention robust to paraphrase + noisy JSON. Listwise rerank suffers position bias; pointwise avoids it. Explicit reasoning traces let us audit failure modes.
- **compose = 8.0** — drop-in stage between retrieval and concierge. Slight cost: 200-500ms latency at K=50 even with Haiku-class CE; per-query LLM cost non-trivial at scale. Tunable K balances cost/precision.
- **composite = 7.5·0.5 + 7.5·0.3 + 8.0·0.2 = 3.75 + 2.25 + 1.6 = 7.60**

## Verdict
**ADVANCE** (composite 7.60 ≥ 7.0). Locks in as third permanent stage. Use Haiku for K=50 pointwise rerank with reasoning trace; cache traces for concierge "why this" output.

## Gap left
1. **Workflow edges still flatten into bag-of-tokens.** "Notion → Linear, weekly, Tuesday 4pm" needs a structural representation — a directional edge between two named entities with a temporal attribute. Cross-attention sees the tokens but not the graph.
2. **Per-field exclusion is still soft.** CE may down-weight excluded tools but cannot guarantee exclusion the way a hard filter or per-field MaxSim could.
3. **No multi-hop reasoning yet** ("a tool that connects to Slack which my team uses for X").

## Next direction
**ColBERT-style multi-vector late interaction with per-field encoding.** Each intent slot (frictions, desired_capabilities, excluded_tools, workflow_edges) gets its own set of token vectors; tool descriptions are tokenized and indexed identically. MaxSim per field gives interpretable per-slot scores; **negative MaxSim** on `excluded_tools` enforces hard exclusion in retrieval (not just rerank). Smallest delta from current stack that preserves token-level structure and is the natural ramp to graph-aware retrieval (iter 5+ can replace `workflow_edges` token vectors with explicit edge embeddings from a KG/GNN). Composes additively with iter 2/3/4 — the contrastive head can be retrained on multi-vector outputs.
