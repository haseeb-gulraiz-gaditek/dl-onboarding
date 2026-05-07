# Iter 13 — GraphRAG community-detection retrieval

**Approach**: weighted Leiden (ArchRAG attribute-aware) clustering over iter-6 KG → Sonnet-generated per-community summaries at 2–3 hierarchical resolutions → query-time slot embeddings match summaries first, HippoRAG-2-style query-to-triple matching within selected community, fuse with iter-5 dense via RRF, rerank by iter-12.

## Top 3 papers
- **Microsoft GraphRAG (Edge 2024, arXiv 2404.16130)** — foundational community-summary architecture; multi-hop QA gains via hierarchical Leiden + Sonnet-generated summaries.
- **HippoRAG-2 (Gutiérrez 2025, arXiv 2502.14802)** — query-to-triple PageRank over the KG matches Mesh's "directional integration edges" pattern more naturally than community-level only.
- **GraphRAG-Bench (2025, arXiv 2506.05690)** — honest critique: GraphRAG loses **−13.4%** on lookup queries, gains only **+4.5%** on multi-hop, costs **2.3× latency**. Tells us GraphRAG fits the slow path, not the trunk.

Honorable: LightRAG (dual entity+relation), Leiden foundations (Traag 2019), ArchRAG (attribute-aware communities, AAAI 2026), HybridRAG (KG+vector), MoR (mixture of retrievers, deferred candidate).

## Scores
- **depth = 7.5** — multi-hop traversal at retrieval speed; structural priors from community membership; HippoRAG-2 PageRank captures iterative reasoning the GNN sometimes oversmooths. Cap: at 300 tools, the KG yields only 8–20 communities with a flat 2-level hierarchy — pure Edge-2024 GraphRAG is overkill; ArchRAG + HippoRAG-2 hybrid is the right adaptation.
- **noise = 7.0** — community structure averages over individual edge noise; iter-6 KG is curated (not LLM-extracted), reducing community-drift risk. But community boundaries are unstable on small graphs; summaries can drift across re-runs.
- **compose = 7.5** — fuses with iter 5 (RRF), reads iter-6 KG directly, output reranked by iter 12. Adds index complexity: community detection + Sonnet summary generation pipeline + per-resolution caches. Re-run on KG updates.
- **composite = 7.5·0.5 + 7.0·0.3 + 7.5·0.2 = 3.75 + 2.1 + 1.5 = 7.35**

## Verdict
**ADVANCE** (composite 7.35 ≥ 7.0) — modest, near threshold. Honest scoring reflects small-graph limits. Slots into V1.5 alongside iter 11 as a *complementary slow-path retriever*: iter 11 (boxes) for symbolic conjunctions, iter 13 (GraphRAG) for multi-hop integration chains. **Not a V1 trunk addition** per GraphRAG-Bench tradeoff.

## Gap left
1. **No calibrated fallback decision.** Pipeline now has multiple retrieval paths (iter 5 dense, iter 11 boxes, iter 13 GraphRAG, iter 8 agent), each with strengths. No principled way to know *which* path's output to trust on OOD queries — currently a learned gate, but uncalibrated.
2. **Summary drift across rebuilds.** Community summaries change with each Leiden re-run; user-facing explanations may shift even when underlying tools don't.
3. **Community-detection cost** at frequent KG refreshes.

## Next direction
**Conformal prediction abstention layer over the fused retriever score.** Calibrate per-path uncertainty using held-out (intent, accepted_tool) pairs; output a *prediction set* with coverage guarantees. When fused score's prediction set is empty or too large, abstain → escalate to iter-8 agent or ask the concierge for clarification. Composes with everything: each retriever (iter 5, 11, 13) gets a calibrated p-value; mixture gate becomes meaningful. Directly addresses gap 1; deferred candidates (mixture-of-retrievers, agent distillation) only matter once we know *when* to use which path.
