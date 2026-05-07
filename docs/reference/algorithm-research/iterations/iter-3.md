# Iter 3 — Contrastive intent learning on triples

**Approach**: small projection head on frozen E5/BGE; InfoNCE/triplet loss over `(intent, accepted_tool, rejected_tool)`; `excluded_tools` from iter 2 = ready hard negatives. 4-tier negative scheme: in-batch → `excluded_tools` → tried-and-bounced (highest weight) → ANCE-mined later.

## Top 3 papers
- **RocketQA (Qu, NAACL 2021)** — cross-batch + denoised hard negatives; specifically addresses the false-negative trap that Mesh's noisy "tried-and-bounced" labels create. Directly applicable.
- **SimCSE (Gao, EMNLP 2021)** — proves a small contrastive head on a frozen base encoder is sufficient; validates Mesh's cheap-add architecture.
- **Few-Shot Cold-Start Rec (Hao, APWeb 2020)** — meta-learning init for sub-100 examples; flags that Mesh's first-50-users regime needs synthesized or pre-trained init, not from-scratch.

Honorable: BPR (foundational pairwise loss), ANCE (global hard-neg mining for later), TOIS 2023 contrastive-recsys survey (collapse + false-negative caveats), Robinson 2021 (hard-negs cause collapse without temperature control).

## Scores
- **depth = 7.0** — captures paradigm-fit by pulling accepted closer than capability-near-neighbor rejected. Reaches "qualitative fit" depth iter 2 cannot. Still a bi-encoder — workflow-edge composition (Notion→Linear, time-conditioned) remains flattened.
- **noise = 7.0** — supervised triples filter noise through the loss; RocketQA-style denoising handles ambiguous bounces. False-negative risk on small data; needs temperature tuning + synthesized triples bootstrap.
- **compose = 8.5** — projection head plugs onto iter 2's structured embeddings; downstream rerank/GNN inherit the learned space. Slight cost: introduces a training pipeline and model versioning concerns.
- **composite = 7.0·0.5 + 7.0·0.3 + 8.5·0.2 = 3.5 + 2.1 + 1.7 = 7.30**

## Verdict
**ADVANCE** (composite 7.30 ≥ 7.0). Locks in as second permanent stage, but with a cold-start caveat: gate behind a flag and use LLM-synthesized triples until ≥ ~300 real (intent, accepted, rejected) tuples are collected.

## Gap left
1. **Workflow-edge compositionality.** "Notion→Linear, weekly, Tuesday 4pm" is still a bag-of-fields encoding. Bi-encoder cannot reason across edges.
2. **Compositional reasoning over multiple intent slots.** Matching tools that satisfy `frictions ∩ desired_capabilities ∩ ¬excluded_tools ∩ workflow_edges` requires joint reasoning — single dot-product can't enforce conjunctions.
3. **Cold-start fragility** until enough triples accumulate.

## Next direction
**Cross-encoder reranker with intent context (top-K rerank).** Run iter 1+2+3 to retrieve top-50 candidates, then a Haiku-class cross-encoder takes `(structured intent JSON, tool description)` as a single sequence and scores them jointly with full attention. Attacks gap #1 and #2 directly: cross attention can reason about workflow edges and conjunctions in one forward pass; defers expensive GNN/KG until after rerank proves the compositional signal exists in the data. Cheap infra (per-query cost bounded by K=50), composes cleanly behind contrastive retrieval.
