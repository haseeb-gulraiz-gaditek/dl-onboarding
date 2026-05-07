# Iter 11 — Box / Cone / Beta Embeddings as a Set-Reasoning Substrate

## Per-paper takeaways

1. **Query2Box (Ren, Hu, Leskovec — ICLR 2020)** — Embeds entities as points and queries as axis-aligned boxes; ∧ = box intersection, ∃/projection = learned translation, ∨ handled by DNF rewrite. Proves union-of-boxes-is-not-a-box theorem (forces DNF), and that disjunction without DNF needs dimensionality ∝ |entities|. **No native negation**. +25% over prior SOTA on FB15k/NELL. Foundational substrate for set-level KG queries. ([arxiv](https://arxiv.org/abs/2002.05969))

2. **BetaE (Ren & Leskovec — NeurIPS 2020)** — Replaces boxes with Beta distributions on each dimension; the bounded support gives a principled complement (1−p), so negation is **native** without DNF gymnastics. First geometric/probabilistic QE model handling the **full FOL set {∧, ∨, ¬, ∃}**. +25.4% relative over conjunctive-only baselines. The right pick if Mesh queries include "NOT excluded_tools". ([arxiv](https://arxiv.org/abs/2010.11465))

3. **ConE (Zhang et al. — NeurIPS 2021)** — Entities/queries as Cartesian products of 2-D sectors (cones); intersection, union, AND complement are all geometric (the complement of a sector is still a sector, unlike a box). First geometry-based QE handling all FOL operators. Comparable accuracy to BetaE with cleaner geometric semantics — strong fallback if Beta training is unstable on small KGs. ([arxiv](https://arxiv.org/abs/2110.13715))

4. **Concept2Box (Huang et al. — ACL Findings 2023)** — Joint two-view embedding: high-level **concepts as boxes** (volume = granularity, overlap = subsumption), fine-grained **entities as vectors**, with a learned vector-to-box distance bridging them. Built on Amazon's product KG. **Directly maps to Mesh's friction/capability hierarchy**: capabilities/frictions are concept boxes, individual tools are points scored by box-membership. ([arxiv](https://arxiv.org/abs/2307.01933))

5. **GNN-QE (Zhu et al. — ICML 2022)** — Drops the geometric prior entirely: decomposes any FOL query into 4 fuzzy-set ops (relation projection, intersection, union, negation) and **executes them with a GNN over the actual KG**, not in an opaque embedding space. Beats BetaE on most FB15k/NELL splits, and intermediate sets are **interpretable** (you can read off the answer entities at every step). Relevant because Mesh's KG is small enough that GNN execution stays cheap. ([proceedings.mlr.press](https://proceedings.mlr.press/v162/zhu22c/zhu22c.pdf))

6. **LMPNN (Wang et al. — ICLR 2023)** — Treats each atomic edge of the query graph as a one-hop link-prediction problem solved by a pretrained KGE (e.g. ComplEx), and combines them via message passing on the **query graph**. Decouples link prediction from logical composition — composition cost compounds far less, and you reuse whatever KGE you already trained for iter-3. Strong fit for "bolt logic onto an existing point-embedding stack". ([openreview](https://openreview.net/forum?id=SoyOsp7i_l))

7. **CLMPT — Conditional Logical Message Passing Transformer (Zhang et al. — KDD 2024)** — Distinguishes constant vs. variable nodes during message passing and uses transformer self-attention to weight logical dependencies. Current SOTA on standard CQA benchmarks. Confirms the field is still squeezing accuracy out of better aggregation, not better geometry — a signal that V1 doesn't need bleeding-edge here. ([arxiv](https://arxiv.org/abs/2402.12954))

8. **Neural-Symbolic Reasoning over KGs: A Survey from a Query Perspective (2024)** — Taxonomy across geometric (Q2B, ConE), probabilistic (BetaE), neural (kgTransformer, SQE), and neural-symbolic (GNN-QE, LMPNN). Documents two consistent failure modes across all families: **(i) closed-world** — every entity/relation must be seen at training; **(ii) deep-nesting error compounding** — accuracy drops sharply past depth ~3 logical ops. ([arxiv](https://arxiv.org/abs/2412.10390))

## Synthesis — fitting box/Beta into Mesh

**Pipeline shape.** Iter-2 intent JSON already gives a logical tree: `AND(friction:A, OR(capability:B, capability:C), NOT(tool:X))`. Add a Phase-2.5 between intent extraction and ColBERT:

1. **Train BetaE (or Concept2Box if hierarchies dominate) on the Mesh KG** — frictions, capabilities, tools, and the typed relations between them. ~500–5K entities is at the small end but tractable; ConE is the safer fallback if Beta gradients misbehave.
2. **Compose the query embedding directly from the intent tree** — no LLM call. Each leaf is an entity/concept embedding; each internal node is a learned operator (intersection, complement, projection). Output is a single distribution / box / cone over candidate tools.
3. **Score**: tools by membership probability inside the result region, then re-rank ColBERT/GNN candidates by a convex combination with that score.

**Depth gained.** Native ∧/∨/¬/∃ at vector-op latency (single-digit ms), replacing iter-8's multi-second Sonnet call for *common* compositional queries. The agent path stays for genuinely novel reasoning (multi-turn clarifications, ambiguous quantifier scope) — box layer is the **fast path**, agent is the **fallback**.

**Noise tolerance.** Boxes/Beta dists are inherently set-valued, so single mislabeled entities barely move the region's centre — composition averages over many entities. Far more robust than point-embedding intersection, which is brittle to single-vector noise.

**Gap that remains — be honest:**
- **Closed-world.** Boxes only know entities/relations seen at training. New tools added post-training need either KEPLER-style text-init proxies (init box from tool description embedding) or periodic re-training. This is the dominant V1 risk for Mesh's catalog growth.
- **Composition error compounding.** Past depth ~3 nested ops, all QE families degrade. Mesh queries with deep nesting still need iter-8 escalation — keep the agent path warm.
- **Small-KG training cost.** Standard QE training assumes FB15k-scale (~15K entities, 500K edges). On a 1–5K-entity Mesh KG with sparse edges, expect to need synthetic query generation (same as Q2B/BetaE training pipelines) and KGE warm-start (ComplEx → LMPNN-style) rather than from-scratch box training.
- **Disjunction headache survives.** Q2B's DNF rewrite blows up combinatorially on deep disjunctions; BetaE/ConE handle ∨ natively but at probabilistic-fuzzy-OR precision (not crisp).

## Suggested next direction — STOP. Write the synthesis.

**Recommendation: option (b).** Marginal value-per-iter has visibly flattened: iters 8–11 each added a viable retrieval substrate, and we now have a **stack of overlapping options** (ColBERT + KGE + GNN + agent + Epinet/TS + box-QE) without a deployment plan distinguishing them. Picking another algorithm (long-context recsys, GraphRAG, MoR) trades against a real V1 risk: that we ship nothing because we can't pick.

The higher-leverage work now is the **V1/V1.5/V2/V3 deployment synthesis** — for each iter, the gating threshold (latency budget, KG size, query complexity tier) that triggers it; the fallback graph (box-QE fast path → agent slow path → epinet exploration); and the cost/latency budget per request. Box-QE belongs in V1.5 as the agent's fast path for compositional queries; without the synthesis to anchor that decision, this iter is just one more option on the pile.

**One sentence: stop researching, write the deployment plan.**
