# Iter 6 — KG embeddings (RotatE / ComplEx / TransE-family) for typed-edge reasoning

## 1. Per-paper takeaways

1. **TransE — Translating Embeddings for Modeling Multi-relational Data (Bordes et al., NeurIPS 2013)** — Models relations as translations `h + r ≈ t` in a single real space. Cheap, ~O(|E|d) params, trains on tens of thousands of triples; perfect for a 300-tool/few-thousand-edge bootstrap. Caveat: cannot encode symmetric or 1-to-N relations, which matters for `syncs_with` (symmetric) and `integrates_with` (many-to-many). [arxiv](https://papers.nips.cc/paper/5071-translating-embeddings-for-modeling-multi-relational-data)

2. **ComplEx — Complex Embeddings for Simple Link Prediction (Trouillon et al., ICML 2016)** — Uses complex-valued embeddings + Hermitian dot product so asymmetric and symmetric relations are both representable. Linear in time/space, robust on small KGs. Strong default for Mesh's mix of `exports_to` (asymmetric) and `syncs_with` (symmetric). [arxiv:1606.06357](https://arxiv.org/abs/1606.06357)

3. **RotatE — Knowledge Graph Embedding by Relational Rotation in Complex Space (Sun et al., ICLR 2019)** — Each relation = rotation in C^d; uniquely captures symmetry, antisymmetry, inversion, *and composition* (`A exports_to B ∧ B imports_from C ⇒ A → C`) with self-adversarial negatives. Composition is the killer feature for multi-hop workflow chains. [arxiv:1902.10197](https://arxiv.org/abs/1902.10197)

4. **QuatE — Quaternion Knowledge Graph Embeddings (Zhang et al., NeurIPS 2019)** — Generalizes ComplEx/RotatE to quaternions (two rotation planes), more expressive on entangled relations but ~4x params; overkill for ~3k edges and risks overfitting our regime. Useful as ablation ceiling. [arxiv:1904.10281](https://arxiv.org/abs/1904.10281)

5. **KEPLER — Unified KE + Pretrained LM (Wang et al., TACL 2021)** — Encodes entity *text descriptions* with a PLM, then trains the KE objective on top. This is the bridge from pure-KG to Mesh's text catalog: tool descriptions become entity priors, giving inductive lift on the long-tail of cold tools where structural edges are sparse. [arxiv:1911.06136](https://arxiv.org/abs/1911.06136)

6. **StarE — Hyper-Relational KG Embedding (Galkin et al., EMNLP 2020)** — Generalizes triples to `(h, r, t, qualifiers)` so `(Notion, exports_to, Linear, weekly)` is a first-class fact, not three side-tables. Reports up to +25 MRR vs triple-only on Wikidata-style data. Direct match for our temporal/frequency qualifiers on `workflow_edges`. [semanticscholar](https://www.semanticscholar.org/paper/Beyond-Triplets:-Hyper-Relational-Knowledge-Graph-Rosso-Yang/f4e39a4f8fd8f8453372b74fda17047b9860d870)

7. **TNTComplEx — Tensor Decompositions for Temporal KB Completion (Lacroix et al., ICLR 2020)** — Decomposes a 4-way tensor (h, r, t, time) and separates temporal vs non-temporal predicates. Maps cleanly to "weekly/daily/one-off" qualifiers; gives a principled fallback if StarE is too heavy to train at our scale. [arxiv:2004.04926](https://arxiv.org/pdf/2004.04926)

8. **Query2box — Reasoning over KGs with Box Embeddings (Ren et al., ICLR 2020)** — Embeds *queries* (conjunction/disjunction/existential) as boxes, so user intent like "tool that exports_to Linear AND imports_from Slack" becomes a box-intersection operation, not a triple lookup. This is the crucial bridge from "score a triple" to "answer a multi-aspect intent." [arxiv:2002.05969](https://arxiv.org/abs/2002.05969)

(Optional adjacent reads, not core: KGAT 2019 — KG-flavored CF, useful only for the rec-side; CompGCN 2020 — sets up the next-iter GNN move.)

## 2. Synthesis — how a small RotatE/ComplEx KG fits Mesh

**Bootstrap.** Crawl Zapier/Pipedream/native-API integration manifests → ~300 tool nodes, ~50 capability nodes, ~30 data-type nodes, ~3–8k typed edges across {`integrates_with`, `exports_to`, `imports_from`, `syncs_with`, `replaces`, `requires`}. Use ComplEx as default (handles symmetric `syncs_with` + asymmetric `exports_to` cleanly, linear, well-behaved at this scale); RotatE as a parallel run we keep if its composition test wins on held-out 2-hop chains. Add KEPLER-style text init from tool descriptions to handle cold tools and the long tail, since 300 nodes / 3k edges is borderline for pure-structural training.

**Query-time.** LLM-extracted `workflow_edges` from iter-2 become candidate triples `(t1, exports_to, t2)`. Score each with the trained KGE: `f(h, r, t)` ∈ R becomes a *typed-edge plausibility score*. Hybridize with iter-5 ColBERT MaxSim text scores via a small learned linear (or gated) fusion head — same pattern as iter-3's contrastive head, just with a new feature column. Multi-hop intents ("something that exports_to Linear and is replaced_by Notion") get scored by composing relation rotations (RotatE) or by a poor-man's Query2box approximation: intersect candidate sets per relation.

**New depth reached.** Yes — `(Notion, exports_to, Linear)` is now a typed, directional, learned fact, not bag-of-tokens co-occurrence. Symmetric `syncs_with` is no longer confused with directional `exports_to`. Composition gives free 2-hop reasoning: if Notion→Linear and Linear→Slack, the model scores Notion→Slack high even with zero training examples for that pair. **KG completion** implicitly handles missing manifest edges — we predict plausible but undocumented integrations rather than treating absence as no.

**Noise handled.** Manifest noise (broken/deprecated integrations) is smoothed by the low-rank embedding bottleneck; LLM-extracted edges that contradict the KG get pushed down by the fusion score; cold tools borrow signal from text descriptions via KEPLER-init.

**Gap that REMAINS.** Three honest ones. (a) **Triple scoring ≠ user-intent matching.** A user query is multi-aspect — frictions + capabilities + workflow_edges + counterfactuals — but KGE only scores one triple at a time. Query2box mitigates partly but assumes pure logical queries, not noisy LLM output. (b) **Closed-world assumption.** Missing edge = false during training; this hurts us because integration manifests are radically incomplete (most real integrations are undocumented), so negatives are polluted. (c) **No tripartite user↔tool↔workflow message passing.** KGE has no mechanism to propagate signal across the user side of the graph; it only knows the catalog graph.

## 3. Suggested next direction

**Pick: GNN over a multi-relational tripartite graph (CompGCN or R-GCN, with RotatE/ComplEx composition operator).**

Why this and not the others: the *biggest* remaining gap is (c) — KGE is single-triple, but Mesh's recommendation is a tripartite reasoning problem (user-profile node ↔ tool nodes ↔ workflow/capability nodes) where we need 2–3 hop message passing from "user mentioned exports_to Linear" through "Linear imports_from {X, Y, Z}" to candidate tools. CompGCN composes node and *relation* embeddings in each layer using exactly the TransE/ComplEx/RotatE composition functions we'd already have trained — so it's a natural extension that reuses iter-6 weights as warm-start, not a from-scratch reroll. Agentic retrieval and RAG-with-reasoning solve a different problem (LLM tool-use loops), and Query2box/concept2box are valuable but solve gap (a) which is downstream of fixing the structural reasoning. Causal matching is premature without more interaction data. Ensemble fusion is what iter-7 *output* should feed into iter-3's head — not a research direction itself.

Iter 7 = R-GCN/CompGCN over the (user, tool, capability, data-type) heterograph, warm-started from iter-6 ComplEx/RotatE entity/relation vectors.
