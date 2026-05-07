# Iter 8 — Agentic retrieval (LLM orchestrator over iters 2–7)

**Approach**: Claude Sonnet agent receives raw user signal; orchestrates typed tools wrapping prior stages — `extract_intent`, `search_text(field)`, `score_triple(s,r,o)`, `propagate_gnn(user_id, hops)`, `query_kg_path(start, relation_chain)`, `rerank(candidates, intent)`. Adaptive-RAG-style gating: only compositional/negated/counterfactual queries (~15%) hit the agent path; rest stay on the fast iter 5→6→7→4 pipeline (<5s concierge SLA).

## Top 3 papers
- **ReAct (Yao 2022, arXiv 2210.03629)** — interleaved Thought/Act/Observation; foundation for all tool-using LLM retrieval. Mesh's explanation chain output is literally the trace.
- **Adaptive-RAG (Jeong 2024, arXiv 2403.14403)** — query-complexity classifier routes simple queries to one-shot retrieval, complex to multi-step agent. Necessary for Mesh's <5s SLA.
- **InteRecAgent (Huang 2023, arXiv 2308.16505)** — LLM-as-orchestrator specifically for recommendation; calls retrieval, ranking, query refinement as tools. Closest production-rec analog.

Honorable: Toolformer (self-supervised tool calls), Self-Ask (decomposition), IRCoT (interleaved CoT + retrieval), FLARE (active retrieval at uncertainty), Self-RAG (critique tokens), Search-o1 (reasoning models calling search), Iter-RetGen (cheap iterative baseline), RecMind, Chat-Rec, The Reasoning Trap 2025 (hallucinated-tool-call critique).

## Scores
- **depth = 8.5** — symbolic reasoning the GNN cannot reach: quantifiers ("any CRM the user already uses"), conditional logic, counterfactual enumeration ("what if user tried X"), multi-hop chains via planned tool calls. Highest depth in the loop. Honest cap: depth is bounded by the underlying tools' precision; agent doesn't add depth where tools are weak.
- **noise = 8.0** — LLM reasoning loop recovers from noisy sub-results, retries with refined params, can ask clarification. Strong tolerance. Risk: hallucinated tool calls compound — strict schema validation + KG-membership checks on entity args mandatory (per "Reasoning Trap" 2025).
- **compose = 9.0** — agentic retrieval IS composition. Every prior stage becomes a tool primitive. Orchestration layer is the framework; nothing rebuilt. Top compose score.
- **composite = 8.5·0.5 + 8.0·0.3 + 9.0·0.2 = 4.25 + 2.4 + 1.8 = 8.45**

## Verdict
**ADVANCE** (composite 8.45 ≥ 7.0) — highest score in the loop. Locks in as the orchestration layer for compositional queries. Adaptive-RAG gates routing; fast path bypasses agent for simple intent matches.

## Gap left
1. **Counterfactual quantification.** Agent enumerates "what if user tried X" candidates but doesn't quantify P(adopt|rec) − P(adopt|no-rec). True uplift requires causal modeling on logged outcomes.
2. **Latency cost.** Multi-second agent path; even with Adaptive-RAG gating, the 15% complex-query subset is slow.
3. **Tool-call brittleness.** Hallucinated entity names, malformed triples, irrelevant tool sequences. Mitigation patterns exist but not eliminated.
4. **Eval is hard.** Agent traces vary; reproducibility for offline eval requires logging full traces.

## Next direction
**Causal uplift modeling.** Train τ(u,t) = P(adopt | recommended) − P(adopt | not recommended) on iter-7 embeddings using logged outcomes (recommendation served vs not, adoption observed vs not). Score the agent's enumerated candidate set by τ rather than match-likelihood. Composes cleanly: agent *generates* candidates with symbolic reasoning, uplift *ranks* by counterfactual lift. Latency-negligible (a single forward pass over already-computed embeddings). Conformal-prediction abstention as fallback when logged data is sparse. Direct attack on gap 1 — the missing counterfactual signal that match-quality alone cannot provide.
