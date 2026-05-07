# Algorithm Research — Iteration Log

**Goal**: find a matching algorithm deep enough that any noisy user-feature signal still resolves to the right AI tool. Beyond surface similarity.

**Rubric** (1–10): match_depth (0.5) · noise_robustness (0.3) · composability (0.2). Advance ≥ 7.0.

**Budget**: 2 hours wall-clock, resumable.

---

| # | Approach | Depth | Noise | Compose | Composite | Advance? | Next direction |
|---|----------|------:|------:|--------:|----------:|----------|----------------|
| 1 | Two-tower dense embedding (E5/BGE) + cosine NN | 4.5 | 6.0 | 9.0 | 5.85 | discard (foundational substrate only) | LLM intent/friction extraction layer |
| 2 | LLM intent extraction → embed structured fields | 7.0 | 7.5 | 9.0 | 7.55 | **advance** (capability-claim depth, handles negation+counterfactuals) | Contrastive intent learning on (intent, accepted, rejected) triples |
| 3 | Contrastive head on frozen E5/BGE; triplet/InfoNCE w/ tried-and-bounced negatives | 7.0 | 7.0 | 8.5 | 7.30 | **advance** (paradigm-fit depth; cold-start gate via LLM-synthesized triples) | Cross-encoder reranker with intent context (top-K) |
| 4 | CE rerank on (structured_intent_JSON, tool_desc); Rank1-style reasoning trace | 7.5 | 7.5 | 8.0 | 7.60 | **advance** (conjunctive reasoning + explainability for concierge) | ColBERT multi-vector late interaction with per-field encoding |
| 5 | ColBERT multi-vector per-field MaxSim + negative MaxSim on excluded_tools | 7.0 | 7.5 | 7.5 | 7.25 | **advance** (per-field interpretable retrieval; hard exclusion guarantee) | RotatE KG embeddings on tool-capability-integration graph |
| 6 | KG embeddings (ComplEx primary, RotatE for composition) + KEPLER text init; fuse w/ iter5 via gate | 8.0 | 7.5 | 7.5 | 7.75 | **advance** (typed directed edges as first-class triples; multi-hop composition) | CompGCN/R-GCN tripartite heterograph (user, tool, workflow_concept), warm-started from iter 6 |
| 7 | CompGCN tripartite heterograph (User × Tool × WorkflowConcept) + KGRec rationalization; warm-start from iter6 | 8.0 | 7.5 | 7.5 | 7.75 | **advance** (multi-aspect intent + CF + multi-hop via message passing) | Agentic retrieval — LLM orchestrates iter4/5/6/7 as callable tools |
| 8 | Agentic retrieval: Claude Sonnet orchestrator over typed tools (iters 2-7); Adaptive-RAG gating | 8.5 | 8.0 | 9.0 | 8.45 | **advance** (highest score; symbolic reasoning, counterfactual enumeration, native explanation chain) | Causal uplift modeling τ(u,t)=P(adopt\|rec)−P(adopt\|no-rec) on iter-7 embeddings |
| 9 | Causal uplift τ(u,t) via DragonNet/X-learner/IPS-BPR; conformal abstention for sparse data | 8.5 | 6.0 | 6.5 | 7.35 | **advance (V2/V3 deferred)** — deepest criterion but hard data prerequisite (~5k logs) | Epinet/Thompson-sampling exploration as generator for propensity-logged data |
| 10 | Epinet/Thompson-sampling exploration above iter-8; logs (u, t, action, propensity, outcome) | 7.0 | 7.5 | 8.5 | 7.45 | **advance** (V1.5 bridge — escapes greedy trap; activates iter 9 path) | Query2Box / Concept2Box neuro-symbolic operators for set-and-quantifier reasoning |
| 11 | BetaE / Query2Box / Concept2Box neuro-symbolic ops (∧∨¬∃ in vector space) | 7.5 | 7.5 | 7.5 | 7.50 | **advance** (V1.5 fast path replacing slow LLM agent for compositional queries) | In-context recsys with long-context Sonnet (final algo iter before synthesis) |
| 12 | In-context Sonnet long-context (200k) listwise rerank w/ full chat history + KG + boxes | 8.0 | 8.0 | 8.5 | 8.10 | **advance** (V1 reranker; second-highest score; replaces iter 4 for compositional) | **STOP — write SYNTHESIS** |

---

**Loop terminated** at iter 12. SYNTHESIS.md written. State: `completed`. Resumable by setting `status: running` and `budget_seconds` higher in `state.yaml`.

**Final recommendation**: V1 = `Iter 2 → Iter 5 → Iter 12` (LLM intent extraction → ColBERT per-field retrieval → Sonnet long-context rerank). $0.03–0.05/query, ~1–2s, zero bootstrap data. V1.5/V2/V3 roadmap in SYNTHESIS.md.

**Score curve**: 5.85 → 7.55 → 7.30 → 7.60 → 7.25 → 7.75 → 7.75 → **8.45** → 7.35 → 7.45 → 7.50 → 8.10. Peak at iter 8 (agentic retrieval); plateau at 7.45–8.45 from iter 8 onward = saturation.

---

## Resumed loop (iter 13+)

| # | Approach | Depth | Noise | Compose | Composite | Advance? | Next direction |
|---|----------|------:|------:|--------:|----------:|----------|----------------|
| 13 | GraphRAG community retrieval (Leiden + ArchRAG attribute-aware + HippoRAG-2 PageRank) | 7.5 | 7.0 | 7.5 | 7.35 | **advance** (V1.5 slow-path complement to iter 11; not V1 trunk per GraphRAG-Bench tradeoff) | Conformal prediction abstention over fused retriever score |
| 14 | Conformal prediction abstention (multi-model min-score + ACI); honest-concierge primitive | 7.0 | 8.0 | 8.0 | 7.50 | **advance** (V2; activates at ≥500 calibration pairs; shadow-mode in V1) | Mixture-of-retrievers w/ learned routing supervised by iter-14 conformal signal |
| 15 | Mixture-of-retrievers (MoR) w/ learned routing softmax over {iter 5, 11, 13, 8} | 7.0 | 7.5 | 8.5 | 7.45 | **advance** (V2 routing layer; RRF cold-start default) | Contextual bandit (EXP4/Thompson) online routing w/ RRF as starting expert |
| 16 | Contextual bandit (EXP4/Thompson) online retrieval routing; arms = {iter 5, 11, 13, 8, RRF}; reward = adoption | 7.0 | 8.0 | 8.5 | 7.60 | **advance** (V2/V3 closed loop with regret guarantees; warm-start via iter-9 IPS replay) | **STOP — user requested halt** |

---

**Resumed loop terminated** at iter 16 by user request. State: `completed`. Total iters across both runs: 16 (1 discarded, 14 advanced, 1 deferred).

**Final score curve**: 5.85 → 7.55 → 7.30 → 7.60 → 7.25 → 7.75 → 7.75 → **8.45** → 7.35 → 7.45 → 7.50 → 8.10 → 7.35 → 7.50 → 7.45 → 7.60. Peak iter 8 (agentic). Resumed run added 4 control/routing layers above the V1-trunk algorithm stack.

---

## Addenda

| Ref | Topic | Note |
|-----|-------|------|
| `iter-1-addendum.md` | Post-two-tower successors (genAI era, 2023–2025) | Iter 1 with KAR + RLMRec wrappers re-scores **7.20** (would have advanced, not discarded). TIGER/OneRec/HSTU deferred to V2+. |
