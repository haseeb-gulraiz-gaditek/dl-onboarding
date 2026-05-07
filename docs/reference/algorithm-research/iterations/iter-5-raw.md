# Iter 5 — ColBERT-style multi-vector late interaction with per-field encoding

## 1. Papers

1. **ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT (Khattab & Zaharia, SIGIR 2020)** — Introduces MaxSim: query and doc are encoded as token-vector sets, scored by sum-of-max cosine. Tells us the foundational shape — fine-grained matching survives independent encoding, so per-token (or per-slot) signal is preserved without paying cross-encoder cost. ([arxiv](https://arxiv.org/abs/2004.12832))

2. **ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction (Santhanam et al., NAACL 2022)** — Adds denoised distillation (cross-encoder teacher cleans label noise) and residual compression (256B → 20–36B per vector, 6–10x footprint cut). For Mesh: noisy-user training data is exactly the regime where denoised supervision matters; compression makes per-slot indexing affordable. ([arxiv](https://arxiv.org/abs/2112.01488))

3. **PLAID: An Efficient Engine for Late Interaction Retrieval (Santhanam et al., CIKM 2022)** — Centroid-interaction + centroid pruning eliminates low-scoring candidates before MaxSim; 7x GPU / 45x CPU latency cut over ColBERTv2 at 140M passages. Tells us per-field MaxSim over a small tool catalog (10³–10⁴ items) is essentially free. ([arxiv](https://arxiv.org/abs/2205.09707))

4. **COIL: Revisit Exact Lexical Match with Contextualized Inverted List (Gao, Dai, Callan, NAACL 2021)** — Late interaction restricted to overlapping tokens via inverted lists. For Mesh: when intent slots contain canonical tokens (tool names like "Notion", "Linear"), contextualized exact match gives both interpretability and a natural index for excluded_tools. ([arxiv](https://arxiv.org/abs/2104.07186))

5. **Multi-View Document Representation Learning for Open-Domain Dense Retrieval — MVR (Zhang et al., ACL 2022)** — Multiple "viewer" tokens generate K embeddings per doc with global-local contrastive loss to prevent collapse. Closest to what we want: each viewer ≈ a slot (frictions, capabilities, edges). Tells us anti-collapse regularization is non-trivial — naive per-field encoders converge. ([arxiv](https://arxiv.org/abs/2203.08372))

6. **ColBERTer: Neural Bag of Whole-Words with Enhanced Reduction (Hofstätter et al., 2022)** — Fuses single-vector retrieval + multi-vector refinement, BOW2 whole-word aggregation, learned contextualized stopwords. 2.5x vector-count reduction at constant top-10. For Mesh: BOW2-style aggregation is what turns sub-word noise into stable per-slot signal. ([arxiv](https://arxiv.org/abs/2203.13088))

7. **Multi-Field Adaptive Retrieval — mFAR (Microsoft, ICLR 2025)** — Decomposes documents into independently-indexed fields (dense + lexical) and learns query-conditioned field-importance weights. SOTA on STaRK structured retrieval. This is the most direct template for Mesh: per-slot intent → per-field tool index → adaptive weighting per query. ([arxiv](https://arxiv.org/abs/2410.20056))

8. **XTR: Rethinking the Role of Token Retrieval in Multi-Vector Retrieval (Lee et al., NeurIPS 2023)** — Trains the model to retrieve only the *important* tokens; scores candidates with retrieved tokens only, killing the gather stage. +2.8 nDCG@10 on BEIR, scoring ~1000x cheaper than ColBERT. For Mesh: most intent slots will have a few decisive tokens ("Tuesday", "Notion→Linear"); XTR's importance-weighted retrieval matches that sparsity. ([arxiv](https://arxiv.org/abs/2304.01982))

## 2. Synthesis — how this lands in Mesh

**Pipeline shape.** Replace the flat single-vector intent embedding with a per-slot multi-vector. At index time: each tool description is tokenized and encoded once into a fielded multi-vector (description-tokens, capability-tokens, paradigm-tokens, integration-tokens) and stored compressed (ColBERTv2 residuals + PLAID centroids). At query time: each intent slot {frictions, desired_capabilities, workflow_edges, excluded_tools, counterfactual_gaps} is encoded into its own token-vector set. Score = weighted sum of per-slot MaxSim against the tool's matching field (mFAR-style adaptive weights conditioned on the structured intent), plus a **negative MaxSim** term over excluded_tools that subtracts the max similarity any excluded-tool token has to any tool-name token — turning soft exclusion into a hard penalty at retrieval, before the cross-encoder sees the candidate.

**New depth gained.**
- Per-slot interpretability: we can show "matched on capability=async-comm (0.81), missed on workflow_edge (0.12)" — the cross-encoder reasoning trace from iter 4 now has retrieval-side evidence to anchor on.
- Robustness to slot noise: missing a slot just zeros that term (or mFAR re-weights), instead of polluting one flat vector.
- Hard exclusion at recall time: negative MaxSim on excluded_tools acts as a true filter, not a re-rank nudge.

**Honest limit — workflow_edges.** Late interaction still treats `workflow_edges = ["Notion→Linear", "weekly", "Tuesday"]` as a *bag of contextualized tokens*. MaxSim will match "Notion" to Notion-mentioning tools and "Linear" to Linear-mentioning tools, but it does **not** represent the typed directed edge `(Notion, exports_to, Linear)` as a first-class object. A tool that mentions both Notion and Linear in unrelated contexts will score the same as one that actually bridges them. This is a representation-class limit, not a training limit — no amount of multi-vector training fixes it.

**Noise absorbed.** Tokenizer noise, slot-omission, paraphrase variation, sub-word splits (via BOW2-style aggregation). Compression makes per-slot indexing cheap enough to ship.

**Gap remaining.** Typed, directed, n-ary structure. Workflow edges are graph data masquerading as text.

## 3. Next direction — Knowledge-graph-augmented retrieval (KG-RAG with TransE/RotatE-style edge embeddings)

Pick: **typed-edge KG embeddings (RotatE-family) on a tool–capability–integration graph, hybridized with the late-interaction retriever.** Build a small KG where nodes = tools, capabilities, data-objects (Notion-doc, Linear-issue, Slack-message) and edges are typed (`integrates_with`, `exports_to`, `triggered_by`, `replaces`). Embed with RotatE (handles symmetry/antisymmetry/composition — exactly what `exports_to` vs `imports_from` vs `syncs_with` need). At query time, parse `workflow_edges` into candidate triples `(Notion, exports_to, Linear)` via entity-linking against the KG, then score tools by KG-side compatibility (does this tool sit on the path?) and combine with the per-slot MaxSim score.

**Why this and not the alternatives.** GNNs on a tripartite graph capture typed edges but require enough interaction data to train end-to-end — Mesh doesn't have it yet. Agentic retrieval is overkill for a representation problem. Causal/counterfactual matching addresses `counterfactual_gaps` but not edges. RotatE-style KG embeddings are the smallest, most direct fix for the *exact* gap: representing typed directed edges as algebraic objects rather than token bags. The KG can be bootstrapped from tool integration manifests (we already have them) and grows with usage. It composes cleanly with iter 5: late-interaction retrieves on text, KG scores on structure, cross-encoder reranks both.

---
**Sources:**
- [ColBERT (Khattab & Zaharia, 2020)](https://arxiv.org/abs/2004.12832)
- [ColBERTv2 (Santhanam et al., 2022)](https://arxiv.org/abs/2112.01488)
- [PLAID (Santhanam et al., 2022)](https://arxiv.org/abs/2205.09707)
- [COIL (Gao et al., 2021)](https://arxiv.org/abs/2104.07186)
- [MVR (Zhang et al., 2022)](https://arxiv.org/abs/2203.08372)
- [ColBERTer (Hofstätter et al., 2022)](https://arxiv.org/abs/2203.13088)
- [Multi-Field Adaptive Retrieval (Microsoft, ICLR 2025)](https://arxiv.org/abs/2410.20056)
- [XTR (Lee et al., NeurIPS 2023)](https://arxiv.org/abs/2304.01982)
- [RotatE (Sun et al., ICLR 2019)](https://arxiv.org/abs/1902.10197)
- [PARADE (Li et al., 2020)](https://arxiv.org/abs/2008.09093)
