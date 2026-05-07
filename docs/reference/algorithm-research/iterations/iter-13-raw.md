# Iter 13 — GraphRAG / community-detection-aware retrieval

Goal: replace iter-8 multi-hop agent for queries like *"tool that connects to Slack which my team uses for X"* with deterministic community-routed traversal over the iter-6 KG.

## Papers

1. **From Local to Global: A Graph RAG Approach to Query-Focused Summarization** — Edge et al., MSR (2024). Builds an LLM-extracted entity graph, runs hierarchical Leiden, generates per-community summaries; map-reduces partial answers across communities. Gives multi-hop *breadth* via summary routing rather than agentic hop expansion. https://arxiv.org/abs/2404.16130
2. **LightRAG: Simple and Fast Retrieval-Augmented Generation** — Guo et al. (2024). Dual-level retrieval: low-level (entity/relation) + high-level (themes), with incremental graph updates. Cheaper than GraphRAG, friendlier at small scale because it skips global community summaries when low-level matches suffice. https://arxiv.org/abs/2410.05779
3. **HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs** — Gutiérrez et al., NeurIPS 2024. KG + Personalized PageRank from query entities; up to +20% on multi-hop QA vs SOTA dense. PPR is the cheapest form of "navigable community" — works at our edge count without explicit clustering. https://arxiv.org/abs/2405.14831
4. **HippoRAG 2 / From RAG to Memory** — Jiménez-Gutiérrez et al. (2025). Embeds full query against nodes *and* triples (not just entities), fixing HippoRAG's single-entity bottleneck and lifting sense-making and associativity simultaneously. Strong fit for slot-filled queries like Mesh's. https://arxiv.org/abs/2502.14802
5. **From Louvain to Leiden: guaranteeing well-connected communities** — Traag, Waltman, van Eck (2019). Foundational: Leiden's refinement phase fixes Louvain's disconnected-community pathology. Critical for a 1k–3k-edge tool KG where one bad split flattens an entire integration cluster. https://arxiv.org/abs/1810.08473
6. **ArchRAG: Attributed Community-based Hierarchical RAG** — Wang et al., AAAI 2026. Weighted Leiden over *attributed* communities (uses node attributes, not just edges) + LLM-driven hierarchical index; beats GraphRAG on accuracy and tokens. The attribute-aware variant is closest to what Mesh needs (capability tags, integration types). https://arxiv.org/abs/2502.09891
7. **HybridRAG: Integrating KGs and Vector Retrieval** — Sarmah et al. (2024). Concatenates KG-traversal context with vector-retrieved chunks; consistently beats either alone on faithfulness in finance QA. Direct template for fusing iter-13 community context with iter-5 dense. https://arxiv.org/abs/2408.04948
8. **When to use Graphs in RAG (GraphRAG-Bench)** — Xiang et al., ICLR 2026. Honest benchmark: GraphRAG is **−13.4% acc on Natural Questions**, only **+4.5% on HotpotQA multi-hop**, **2.3× latency**. Wins live on hierarchical/structural queries; lose on lookup. Sets expectations for Mesh. https://arxiv.org/abs/2506.05690

## Synthesis — GraphRAG in Mesh

**Pipeline.** Offline: take iter-6 tool–capability–integration KG → run weighted Leiden (node attrs = capability/integration tags, ArchRAG-style) at 2–3 resolutions → for each community, Sonnet generates a 3–5 line summary covering dominant capabilities, integration neighborhood, representative tools. Online: iter-2 clarifier emits slot dict → embed slots → top-k community summaries → expand to entities within (LightRAG dual-level) or run PPR seeded by matched entities (HippoRAG-2 query-to-triple) → fuse with iter-5 dense passages via RRF → iter-12 cross-encoder rerank.

**New depth.** Multi-hop ("Slack-integrated → analytics → my-team-uses-X") becomes a 1–2-hop community lookup instead of an iter-8 agent loop. Community summaries act as structural priors: smooth over single-edge noise, surface integration neighborhoods that no single embedding captures.

**Honest gap at our scale.** 300 tools → ~1k–3k edges. Leiden likely produces 8–20 communities; many will be trivially small (3–5 tools), so per-community LLM summaries risk overfitting and the hierarchy collapses to ~2 useful levels. GraphRAG-Bench's −13.4% on lookup queries is a real risk for the long tail of "what's the best X?" head queries. ArchRAG's attribute-weighted Leiden + HippoRAG-2's query-to-triple matching are the right mitigations; pure Edge-2024 GraphRAG is overkill. Community drift on auto-extracted edges is the second risk — but iter-6 KG is curated, not LLM-extracted, so this is much smaller for us than for the original GraphRAG setting.

**Residual gap.** Even with community routing + hybrid fusion, the system has *no calibrated way to know when to fall back to iter-8 agent*. GraphRAG will confidently route to a wrong community on out-of-distribution slot combinations and serve plausible-but-wrong tools.

## Suggested next direction (iter-14)

**Conformal prediction abstention** on the fused retriever score. Calibrate a coverage-controlled score threshold per query type; below threshold → abstain from direct answer and *route to iter-8 agentic retrieval* (or ask a clarifier follow-up). This directly fixes the residual gap above: GraphRAG handles the easy + structurally-routable 80%, conformal abstention catches the OOD tail and hands it to the slow path with provable coverage guarantees. Mixture-of-retrievers gives marginal lift but no honest "I don't know"; agent distillation is premature until we know which queries the agent actually wins on. Conformal is the smallest, most rigorous bolt-on.
