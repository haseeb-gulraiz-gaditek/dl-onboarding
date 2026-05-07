# Iter 8 — Agentic Retrieval (raw research)

LLM orchestrator with tool-use over iters 2–7 of the Mesh stack. Curated 8 papers; biased toward what transfers to a noisy-user→tool recommender with a <5s concierge SLA.

## Papers (year — one-line takeaway, with depth/noise/explainability lens)

1. **ReAct: Synergizing Reasoning and Acting in Language Models** (Yao et al., 2022, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)) — Interleaved Thought→Act→Observation traces let an LLM both plan and call tools; gives us the canonical loop and a human-readable explanation chain "for free," but each step is a model call, so depth costs latency.
2. **Toolformer: Language Models Can Teach Themselves to Use Tools** (Schick et al., 2023, [arXiv:2302.04761](https://arxiv.org/abs/2302.04761)) — Self-supervised tool-call insertion; relevant only as theory in our setting (we'll prompt Claude, not fine-tune), but it justifies treating each Mesh stage as a typed API rather than a hardwired pipeline.
3. **Self-Ask / Compositionality Gap** (Press et al., 2022, [arXiv:2210.03350](https://arxiv.org/abs/2210.03350)) — Explicit follow-up question decomposition narrows the compositionality gap that scaling alone doesn't fix; this is the symbolic/quantifier lever we lack post-iter-7 (1-WL ceiling).
4. **IRCoT: Interleaving Retrieval with CoT** (Trivedi et al., ACL 2023, [arXiv:2212.10509](https://arxiv.org/abs/2212.10509)) — Retrieval steers reasoning, reasoning steers retrieval; +21pt retrieval / +15pt QA over single-shot. Direct template for our orchestrator: `search_text` re-issued with each new derived slot.
5. **FLARE: Forward-Looking Active RAG** (Jiang et al., EMNLP 2023, [arXiv:2305.06983](https://arxiv.org/abs/2305.06983)) — Token-confidence triggers re-retrieval only on low-probability spans; the latency-saver pattern — most Mesh queries should *not* trigger the agent loop.
6. **Self-RAG** (Asai et al., ICLR 2024, [arXiv:2310.11511](https://arxiv.org/abs/2310.11511)) — Trained reflection tokens decide retrieval and critique generations; production-relevant because the *adaptive* retrieve/no-retrieve gate is the only way agentic eats a <5s budget.
7. **Adaptive-RAG** (Jeong et al., NAACL 2024, [arXiv:2403.14403](https://arxiv.org/abs/2403.14403)) — Small classifier routes queries to no-retrieval / single-step / multi-step paths based on complexity; the budget-realistic pattern for Mesh — only ~10–20% of queries warrant the full agent.
8. **Search-o1: Agentic Search-Enhanced Reasoning** (Li et al., EMNLP 2025, [arXiv:2501.05366](https://arxiv.org/abs/2501.05366)) — Reasoning-model-grade agent with a Reason-in-Documents distillation step that compresses retrieved noise before injecting; this is the freshest pattern, and the "compress noisy tool output before feeding back to the planner" idea is exactly what we need to prevent context blowup across iters 5+6+7.
9. **Iter-RetGen** (Shao et al., Findings EMNLP 2023, [arXiv:2305.15294](https://arxiv.org/abs/2305.15294)) — Generation conditions the next retrieval, fixed-step loop instead of free-form ReAct; cheap baseline if free-form Claude orchestration proves too brittle.
10. **InteRecAgent / RecAI** (Huang et al., TOIS 2024, [arXiv:2308.16505](https://arxiv.org/abs/2308.16505)) — LLM-as-brain over query/retrieve/rank tools with memory + dynamic-demo planning; closest published architecture to what we're proposing for Mesh, with a real distillation result (RecLlama) showing a 7B can replace GPT-4 as the planner.
11. **RecMind** (Wang et al., NAACL 2024, [arXiv:2308.14296](https://arxiv.org/abs/2308.14296)) — Self-Inspiring planner that retains all previously explored states (vs CoT/ToT pruning) and competes with fully trained P5; relevant for the "consider counterfactual tool sets" angle.
12. **Chat-Rec** (Gao et al., 2023, [arXiv:2303.14524](https://arxiv.org/abs/2303.14524)) — Earliest LLM-as-rec wrapper, in-context only; included as the floor — we should beat this trivially because we have iters 2–7 underneath.
13. **The Reasoning Trap / tool-hallucination critique** ([arXiv:2510.22977](https://arxiv.org/html/2510.22977v1), 2025) — Stronger reasoning RL *increases* tool hallucination proportionally with task gains; a structural critique we cannot ignore — the better Claude gets at planning, the more confidently it will fabricate `score_triple(s,r,o)` calls on entities that don't exist in our KG.

(13 cited; eight chosen as primary, the rest as flanking critique/baselines.)

## Synthesis — agentic retrieval in the Mesh pipeline

**Loop.** Claude Sonnet receives raw user signal (noisy text + session context). It plans, then invokes Mesh stages as typed tools:

1. `extract_intent(text) -> slots` (iter 2)
2. `search_text(query, field) -> candidates` (iter 5 ColBERT, with `field ∈ {capability, integration, persona}` and optional `negate=[...]`)
3. `score_triple(s, r, o) -> float` (iter 6 ComplEx/RotatE) — for symbolic checks like *(tool, integrates_with, Slack)*
4. `propagate_gnn(user_id, hops, seed_tools) -> ranked` (iter 7 CompGCN)
5. `query_kg_path(start, relation_chain) -> path_score` — for conditional/transitive queries
6. `rerank(candidates, intent) -> ordered` (iter 4 cross-encoder, called last)

The agent observes each result, can discard, refine, branch, or short-circuit, then emits `(ranked_list, explanation_chain)`.

**New depth unlocked.** This is the first iteration with *symbolic* expressivity:
- **Quantifiers / negation:** "tools that integrate with Slack but not Zapier" → two `search_text` calls, intersect, `score_triple` to verify negation. Iters 5–7 can't natively express ¬.
- **Conditional logic:** "if user is technical, prefer API-first tools" — agent branches on a profile slot before dispatching retrieval.
- **Counterfactual exploration:** agent can synthesize candidates the user has *not* tried (iter 7 propagation seeded from KG-neighbors of adopted tools, then `rerank` with iter 4 to filter), producing the "would-adopt-X-they-haven't-tried" signal.
- **Compositional decomposition (Self-Ask):** "Notion alternative for a 5-person remote design team" → break into [Notion-similarity], [team-size constraint], [remote-collab capability] sub-queries, fuse.

**Noise handling.** The LLM can re-plan when a sub-stage returns garbage — bad ColBERT hits trigger a query rewrite; empty GNN propagation triggers a fallback to KG path search; conflicting signals get explicit reconciliation in the trace. This is qualitatively new vs iters 2–7, which fail silently.

**Explainability.** The Thought→Act→Observation trace is the explanation. No more "soft GNN attention weights" hand-waving — we get *"I excluded Asana because score_triple(Asana, integrates_with, GitHub) = 0.12, below threshold."*

**The gap that remains.** Three honest problems:

1. **Latency.** A full ReAct loop with 4–6 tool calls runs 3–8s on Sonnet, before any tool latency. Mesh's <5s concierge SLA is incompatible with running the agent on every query. Adaptive-RAG / FLARE-style gating is mandatory, not optional — we route only ~15% of queries (those flagged compositional/negated/counterfactual) to the agent; the rest stay on the iter 4–7 fast path.
2. **Tool-call hallucination.** Per the Reasoning Trap (2025), confident fabrication grows with planner capability. Claude will invent tool names, pass non-existent entity IDs to `score_triple`, and confabulate observations when tools time out. We need strict argument schemas, KG-membership validation on entity args, and a "tool-call cassette" replay test set.
3. **Eval.** Multi-step agent traces are notoriously hard to grade — no single ground-truth ranking. We'll need trace-level and outcome-level evals separately, plus an LLM-judge with disclosed bias.

Counterfactual reasoning is *partially* unlocked but not principled — the agent can *enumerate* unseen tools but has no causal model of *why* the user would adopt them. That's the next gap.

## Suggested next direction (iter 9)

**Causal / counterfactual matching via uplift modeling.** Pick this over neuro-symbolic boxes (Query2Box solves a different problem — multi-hop logical KG queries — and we already get 80% of that benefit from `query_kg_path` + the agent), over bandits (we don't have the impression volume yet for online exploration to beat offline signals), and over distillation (premature; distill *after* we've validated the agentic teacher beats the iter-4–7 baseline).

Concretely: train an uplift / X-learner model on logged (user, recommended-tool, adopted?) triples, with the iter-7 user/tool embeddings as covariates, to estimate **τ(u, t) = P(adopt | recommended=t, u) − P(adopt | not recommended, u)**. Use τ as the *final* ranking signal after the agent emits its candidate set. This directly answers the counterfactual "would the user adopt X if shown" question that no current iter does — and it composes cleanly with iter 8: the agent generates the candidate set, uplift scores it. Two-stage, interpretable, and the uplift model is a small MLP, so latency is negligible (<50ms). Standard libraries (CausalML, EconML) cover the estimators; the harder part is constructing a reasonable propensity model from logged Mesh data — solvable once we have ~10k logged recommend→outcome pairs.

If logged-data volume isn't there yet at iter-9 time, fall back to **conformal prediction for abstention** (cheap, no training, gives the concierge a principled "I don't know — ask another question" output, which is more valuable in the cold-start regime than any new ranker).

## Sources

- [ReAct (arXiv:2210.03629)](https://arxiv.org/abs/2210.03629)
- [Toolformer (arXiv:2302.04761)](https://arxiv.org/abs/2302.04761)
- [Self-Ask / Compositionality Gap (arXiv:2210.03350)](https://arxiv.org/abs/2210.03350)
- [IRCoT (arXiv:2212.10509)](https://arxiv.org/abs/2212.10509)
- [FLARE (arXiv:2305.06983)](https://arxiv.org/abs/2305.06983)
- [Self-RAG (arXiv:2310.11511)](https://arxiv.org/abs/2310.11511)
- [Adaptive-RAG (arXiv:2403.14403)](https://arxiv.org/abs/2403.14403)
- [Search-o1 (arXiv:2501.05366)](https://arxiv.org/abs/2501.05366)
- [Iter-RetGen (arXiv:2305.15294)](https://arxiv.org/abs/2305.15294)
- [InteRecAgent (arXiv:2308.16505)](https://arxiv.org/abs/2308.16505)
- [RecMind (arXiv:2308.14296)](https://arxiv.org/abs/2308.14296)
- [Chat-Rec (arXiv:2303.14524)](https://arxiv.org/abs/2303.14524)
- [The Reasoning Trap (arXiv:2510.22977)](https://arxiv.org/html/2510.22977v1)
