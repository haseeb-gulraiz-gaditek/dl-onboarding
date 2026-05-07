# Iter 7 — CompGCN tripartite heterograph (User × Tool × WorkflowConcept)

**Approach**: heterograph with three node types (User, Tool, WorkflowConcept = capabilities/frictions/data_types) and typed edges (`has_friction`, `uses`, `rejected`, `has_capability`, `exports_to`, `imports_from`, etc.). CompGCN backbone (composition operator = TransE/ComplEx/RotatE — warm-start from iter 6 weights, no rework). HGT-style typed attention as an option. Joint loss: link-prediction (KG completion) + recommendation BPR with iter 5 rejected edges as hard negatives.

## Top 3 papers
- **CompGCN (Vashishth ICLR 2020, arXiv 1911.03082)** — composition operator IS RotatE/ComplEx, so iter 6 weights initialize directly. Multi-relational message passing without per-relation parameter explosion.
- **HGT (Hu WWW 2020, arXiv 2003.01332)** — typed multi-head attention over heterograph; learned per-edge-type weights better than R-GCN's basis decomposition for sparse small graphs.
- **KGRec (Yang KDD 2023, arXiv 2307.02759)** — self-supervised rationalization down-weights noisy KG edges during message passing — directly addresses Mesh's risk that LLM-extracted edges contain noise.

Honorable: R-GCN (foundational), HAN (metapath attention), KGAT (KG+CF foundational), KGIN (intent-aware aggregation — semantically close to Mesh's intent slots), LightGCN (simplification baseline), GraphSAGE (inductive for new tools), MetaHIN (cold-start), GIN/1-WL (compositional ceiling), oversmoothing survey (depth limit).

## Scores
- **depth = 8.0** — multi-aspect intent reasoning emerges via message passing through user→friction→tool→capability→tool paths; CF signal emerges from user-tool edges propagating through similar users. Multi-hop = depth-of-network. Cap: 1-WL expressiveness bound (some structurally distinct graphs are indistinguishable to MPNN); oversmoothing past 3 layers; structural-only — can't represent quantifiers, negation operators, conditional probabilities natively.
- **noise = 7.5** — message passing aggregates over noisy single edges; KGRec rationalization suppresses unreliable edges. Risk: GNN *trusts* the graph — bad LLM-extracted intent edges propagate. Mitigation: edge attention weights, PU loss, conformal abstention.
- **compose = 7.5** — warm-starts from iter 6; node text features from iter 5; output user/tool embeddings flow into iter 4 rerank as additional context features. Training pipeline cost: heterograph construction, scheduled retraining as user/tool data accumulate.
- **composite = 8.0·0.5 + 7.5·0.3 + 7.5·0.2 = 4.0 + 2.25 + 1.5 = 7.75**

## Verdict
**ADVANCE** (composite 7.75 ≥ 7.0). Locks in as sixth stage. GNN embeddings replace iter 3's contrastive head once enough user-tool edges accumulate (~500 interactions); until then, contrastive head remains as substitute.

## Gap left
1. **1-WL compositional ceiling.** MPNNs can't distinguish certain graph structures; complex queries with quantifiers ("a tool that connects to *any* CRM the user already uses") need a more expressive substrate.
2. **Oversmoothing at depth.** Real value sits at 4–6 hop reasoning chains, but GNNs degrade past 3 layers.
3. **Soft explanations.** Concierge needs "we recommend X because A→B→C"; GNN attention is a heatmap, not a chain. iter 4 reasoning trace remains the explanation source.
4. **No exploration / counterfactual.** GNN ranks based on past interactions; doesn't model "what if user tried X they haven't tried yet."

## Next direction
**Agentic retrieval — LLM-as-orchestrator over iter 4/5/6/7 as callable tools.** A Claude Sonnet agent receives the user's intent and reasons step-by-step, calling: `search_text(query, field)`, `score_triple(s,r,o)`, `propagate_gnn(user_id, hops)`, `rerank(candidates)`. The LLM does the *symbolic reasoning* the GNN architecture can't (quantifiers, negations, conditional logic) and emits the explanation chain the concierge needs. Composes with everything: agent calls existing stages as primitives; nothing rebuilt. Direct attack on gaps 1, 3, 4. Target architecture for Mesh V2 concierge.
