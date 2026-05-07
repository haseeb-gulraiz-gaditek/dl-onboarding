# Iter 7 — Relational GNN over a Tripartite User–Tool–WorkflowConcept Heterograph

## Papers

1. **Modeling Relational Data with Graph Convolutional Networks (Schlichtkrull et al., 2017/2018)** — R-GCN: per-relation weight matrices with basis decomposition give the canonical multi-relational message-passing primitive; established that an encoder over a relational graph improves DistMult-style link prediction by ~30% on FB15k-237, validating the "stack a GNN on top of KG embeddings" recipe we'd warm-start from iter 6. [arxiv.org/abs/1703.06103](https://arxiv.org/abs/1703.06103)

2. **CompGCN: Composition-Based Multi-Relational GCNs (Vashishth et al., ICLR 2020)** — Jointly embeds nodes *and* relations, using KG composition operators (sub, mult, ccorr) on each edge, so it scales with O(relations) instead of O(relations × hidden²) like R-GCN; generalizes GCN/R-GCN/Directed-GCN as special cases — this is the right backbone for Mesh because our edge types (`has_friction`, `has_capability`, `exports_to`) carry semantic content we want preserved through depth. [arxiv.org/abs/1911.03082](https://arxiv.org/abs/1911.03082)

3. **Heterogeneous Graph Attention Network — HAN (Wang et al., WWW 2019)** — Two-level attention: node-level over metapath-neighbors, then semantic-level across metapaths; teaches us that for User→Friction→Tool vs User→Uses→Tool, *which path matters* should itself be learned, not hardcoded. Caveat: hand-designed metapaths don't scale to many edge types. [arxiv.org/abs/1903.07293](https://arxiv.org/abs/1903.07293)

4. **Heterogeneous Graph Transformer — HGT (Hu et al., WWW 2020)** — Replaces metapaths with node/edge-type-aware attention parameters and HGSampling for mini-batching; trained on 179M-node Open Academic Graph and beats baselines 9–21%. For Mesh: handles arbitrary edge-type combinations without metapath enumeration, plus the relative-temporal-encoding hook is useful when we add session order to user→uses→Tool. [arxiv.org/abs/2003.01332](https://arxiv.org/abs/2003.01332)

5. **KGAT: Knowledge Graph Attention Network (Wang et al., KDD 2019)** — Folds the user-item bipartite graph and the item-side KG into one collaborative knowledge graph, then runs attentive propagation; the canonical "CF + KG via GNN" recipe. Directly maps onto our User—uses—Tool plus Tool—has_capability—WorkflowConcept fusion. [arxiv.org/abs/1905.07854](https://arxiv.org/abs/1905.07854)

6. **KGIN: Learning Intents behind Interactions with KG for Recommendation (Wang et al., WWW 2021)** — Inserts a latent "intent" layer between user and item, where each intent is an attentive combination of KG relations, plus relational-path-aware aggregation with independence regularization. This is the closest match to Mesh's iter-2 slot structure — intents are first-class — and gives interpretable "which relational path triggered this rec" explanations we want for the reasoning trace. [arxiv.org/abs/2102.07057](https://arxiv.org/abs/2102.07057)

7. **LightGCN (He et al., SIGIR 2020)** — Strips feature transform + nonlinearity from GCN; pure neighborhood averaging plus layer-combination beats NGCF by ~16%. Reminds us not to over-engineer: at the small-graph regime, the heaviest CompGCN may underperform a thin LightGCN-on-heterograph baseline; we should run both. [arxiv.org/abs/2002.02126](https://arxiv.org/abs/2002.02126)

8. **GraphSAGE: Inductive Representation Learning on Large Graphs (Hamilton et al., NeurIPS 2017)** — Sample-and-aggregate framework that generates embeddings for *unseen* nodes from features. This is the cold-start lifeline: a brand new user with iter-2 slot features gets an embedding without retraining. Inductive setup is non-negotiable for Mesh. [arxiv.org/abs/1706.02216](https://arxiv.org/abs/1706.02216)

9. **MetaHIN: Meta-learning on HINs for Cold-start Recommendation (Lu et al., KDD 2020)** — MAML-style co-adaptation over metapath-augmented support sets; addresses the new-user / new-tool case GraphSAGE alone doesn't fully solve when even features are sparse. [dl.acm.org/doi/10.1145/3394486.3403207](https://dl.acm.org/doi/10.1145/3394486.3403207)

10. **A Survey on Oversmoothing in GNNs (Rusch et al., 2023) + How Powerful are GNNs (Xu et al., ICLR 2019)** — Two critique anchors: (a) node features collapse exponentially with depth, so >3 layers usually hurts, capping multi-hop reasoning unless we add residuals/PairNorm/jumping-knowledge; (b) message-passing is bounded by 1-WL — it cannot distinguish certain structurally distinct subgraphs (e.g., 6-cycle vs two 3-cycles), so our heterograph cannot encode arbitrary tool-composition logic. [arxiv.org/abs/2303.10993](https://arxiv.org/abs/2303.10993) · [arxiv.org/abs/1810.00826](https://arxiv.org/abs/1810.00826)

## Synthesis — Tripartite CompGCN in the Mesh pipeline

**Graph construction.** Three node types: `User`, `Tool`, `WorkflowConcept` (capabilities, frictions, data types — all extracted from iter-2 slots and the iter-6 KG). Edge types: `user—has_friction—Concept`, `user—uses/rejected—Tool`, `Tool—has_capability—Concept`, `Tool—exports_to/imports_from—Tool`, plus inverse relations. `WorkflowConcept` nodes glue the user-side and tool-side together: a noisy user message lands as a fuzzy distribution over Concept nodes, and message passing from User → Concept → Tool surfaces tools whose capabilities match — without ever needing exact text alignment.

**Warm start.** Initialize node embeddings from iter 6: `Tool` and `Concept` from ComplEx/RotatE+KEPLER, `User` from a pooled iter-2 slot encoding (or zero-init for new users, relying on inductive aggregation). Initialize relation embeddings from iter-6 relation vectors.

**Architecture.** CompGCN backbone (composition-aware, scales with #relations, generalizes R-GCN), 2–3 layers with residuals + JumpingKnowledge to defer oversmoothing. Optionally HGT-style typed attention if metapath bias hurts. GraphSAGE-style neighbor sampling for inductive cold-start on new users/tools.

**Training.** Multi-task: (i) link-prediction loss on `user—uses—Tool` (positive vs negative-sampled tools, with `rejected` edges as hard negatives — natural fit for iter-5's negative MaxSim signal); (ii) auxiliary KG completion on `Tool—has_capability—Concept` to keep the backbone faithful to the KG. BPR or InfoNCE; iter-3 contrastive head can be retrained on GNN outputs.

**What new depth this reaches.** (a) *Multi-aspect intent*: a user's friction set is a multiset of Concept nodes — message passing naturally aggregates them rather than treating intent as one vector. (b) *Multi-hop CF*: User → Tool → exports_to → Tool surfaces "users like you adopt tool B *after* tool A" without explicit sequence modeling. (c) *Smoothing as feature, not bug, at depth 2*: noisy single edges from an LLM-misparsed slot get diluted by the rest of the neighborhood, which is exactly the noise model iter 2 produces.

**What the GNN does NOT solve.**
- *Graph-structure trust*: GNN assumes edges are reliable; if iter-2 hallucinates `has_friction` edges, smoothing helps only up to a point — bad edges with high degree corrupt embeddings.
- *Oversmoothing >3 layers*: hard ceiling on reasoning hops without architectural tricks (PairNorm, residual, GCNII).
- *True cold-start*: a brand-new user with zero edges and only raw text — GraphSAGE needs *features*, MetaHIN needs *support tasks*; neither fully covers a single-message stranger.
- *1-WL ceiling*: cannot represent compositional tool logic ("tools that pipe to tools that export CSV but not Notion") — that's a structural query the GNN cannot answer in one forward pass.
- *Explanation*: even with KGIN-style intent attention, GNN explanations are softer than path-based reasoning.

## Suggested next direction — Iter 8: agentic retrieval (LLM-as-orchestrator)

Pick **agentic retrieval** as the next iteration. Rationale: the residual gaps after iter 7 are (a) reasoning-shaped — multi-step queries the GNN can't compose in 3 layers; (b) trust-shaped — when the LLM-extracted graph is wrong, we need a system that can re-query, decompose, and verify; and (c) explanation-shaped — users want a trace, not a softmax. None of those are GNN-architecture problems; they're orchestration problems.

Concretely: an LLM agent receives the user message, decomposes it into sub-queries, and decides per sub-query which retriever to call — iter 5 ColBERT for lexical/text grounding, iter 6 KG embeddings for triple checks, iter 7 GNN for collaborative + multi-hop signal, iter 4 cross-encoder for final rerank. The agent assembles a reasoning trace as it goes, which doubles as the iter-4 explanation. This is the natural next move because each preceding iteration becomes a *callable tool* rather than a fixed pipeline stage — and it directly attacks the 1-WL and oversmoothing ceilings by letting the LLM perform the compositional reasoning the GNN structurally cannot.

Alternatives considered and deferred: neuro-symbolic (Query2Box / Concept2Box) is more principled for compositional queries but heavyweight to train and our query distribution isn't clean enough to warrant box embeddings yet; causal/uplift modeling is the right move *after* the recommender is good, not before; mixture-of-retrievers without an orchestrator just shuffles the fusion problem to a static gate.
