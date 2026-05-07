# Iter 12 — In-context recsys with long-context Sonnet

**Approach**: iter 2 extracts structured intent → iter 5 retrieves top-50 candidates → Sonnet (200k context) listwise-reranks with full chat history + iter-6 KG triples + iter-11 box results attached. No tool calls (unlike iter 8) — single long-context forward pass. Shuffled-bootstrap mitigation (3× rerank passes with permuted candidate order) for Lost-in-the-Middle.

## Top 3 papers
- **LOFT (Lee 2024, arXiv 2406.13121)** — long-context LMs rival dedicated retrievers at small-to-medium catalog scale. Mesh's 300 tools (~45k tokens) fit comfortably; validates the architecture.
- **Lost in the Middle (Liu 2023, arXiv 2307.03172) + Position Bias in LLM Recs (2025, arXiv 2508.02020)** — confirms position bias is real for recommendation specifically; mandates shuffled-bootstrap.
- **LlamaRec (Yue 2023, arXiv 2311.02089)** — small retriever → LLM rerank pattern beats pure long-context. Validates Mesh's iter 5 → iter 12 hybrid.

Honorable: Long Context vs RAG (2025), Self-Route RAG-vs-LC (2024), LongBench (2023), RankGPT (2023), RecICL (2024), Hou 2023 (LLMs as zero-shot rankers).

## Scores
- **depth = 8.0** — full chat-history personalization at *retrieval time* (not training time); paradigm-awareness via tone, hesitations, prior rejections in raw history; conditional reasoning over the candidate set. Cap: Lost-in-the-Middle position bias; hallucination risk if rerank invents tools not in candidate list (mitigation: hard-validate output against catalog).
- **noise = 8.0** — LLM filters its own hallucinations via reasoning; chat-history noise smoothed by long-context comprehension; reasoning trace catches errors before output. Position-bias-induced noise mitigated by shuffled bootstrap.
- **compose = 8.5** — hybrid pattern (small retriever → LLM rerank) is the dominant production architecture per LOFT/LlamaRec/Self-Route. Replaces iter 4 CE rerank for compositional queries; iter 4 stays as fallback for cost-sensitive paths. Cost: $0.03-0.05/query at top-50; full-catalog V1 ($0.6/query) is a non-starter at scale.
- **composite = 8.0·0.5 + 8.0·0.3 + 8.5·0.2 = 4.0 + 2.4 + 1.7 = 8.10**

## Verdict
**ADVANCE** (composite 8.10 ≥ 7.0) — second-highest after iter 8. Locks in as the **V1 reranker** (replaces iter 4 for compositional queries; iter 4 retained for low-cost simple matches).

## Gap left
1. **Cost ceiling.** $0.03-0.05/query × frequent re-recommendations doesn't scale freely. Cache by intent fingerprint where possible.
2. **Latency floor.** ~1-2s end-to-end on hybrid pattern; full-catalog V1 (~5-15s) breaks the concierge SLA.
3. **No replacement for upstream depth.** In-context can't do what iter 6 (typed graph triples) and iter 7 (multi-hop GNN) provide as input features — they're complementary, not substitutes.

## Final recommendation (one-line answer to the loop)
**V1 minimal pipeline = Iter 2 → Iter 5 → Iter 12.** LLM intent extraction; ColBERT per-field MaxSim + negative MaxSim retrieval (top-50); Sonnet long-context listwise rerank with full chat history + KG triples attached. Cost ~$0.03-0.05/query, latency ~1-2s, zero bootstrap data required, personalization depth no embedding-only stack reaches. Iters 6/7/8/10/11 layer in for V1.5–V2; iter 9 activates at V2/V3 once iter 10 has produced ~5k logged outcomes.
