# Iter 3 — Contrastive / triplet head on (intent, accepted, rejected) for Mesh

Goal: learn a Mesh-specific projection on top of frozen E5/BGE so accepted tools beat rejected tools in cosine, even when rejected has higher raw capability cosine (the paradigm-fit gap iter-2 left open).

## Papers

1. **FaceNet: Triplet loss for face embeddings (Schroff et al., 2015)** — Foundational triplet objective: pull anchor toward positive, push past negative by a margin. Tells us: with curated hard negatives a small projection can carve depth that raw similarity misses — exactly the paradigm-fit shape.
2. **BPR: Bayesian Personalized Ranking from Implicit Feedback (Rendle et al., 2009)** — The canonical "user prefers i over j" pairwise objective; treats not-clicked as negative. Maps directly onto Mesh's (adopted > tried-and-bounced) signal — bounced is a *stronger* negative than uniform random.
3. **SimCSE: Simple Contrastive Learning of Sentence Embeddings (Gao et al., EMNLP 2021)** — Dropout-as-augmentation + InfoNCE; supervised variant uses NLI contradictions as hard negatives. Tells us: a tiny contrastive head on frozen encoders can move STS by 4+ points — encouraging for Mesh's small projection plan; also flags representation collapse if augmentation is too weak.
4. **ANCE: Approximate Nearest Neighbor Negative Contrastive Learning (Xiong et al., ICLR 2021)** — Periodically refresh an ANN index and mine global hard negatives; in-batch negatives have vanishing gradients. Tells us: Mesh needs to escalate from `excluded_tools` to *currently top-ranked-but-wrong* negatives once the head starts learning, or training stalls on uninformative pairs.
5. **RocketQA (Qu et al., NAACL 2021)** — Cross-batch negatives + denoised hard negatives (cross-encoder filters false negatives) + data augmentation. Directly relevant: Mesh's "rejected" set is noisy (user might bounce for a non-paradigm reason — pricing, bug, mood). Denoising is mandatory.
6. **Contrastive Self-Supervised Learning in Recommender Systems: A Survey (Yu et al., TOIS 2023)** — Taxonomy of view-generation, contrastive task, objective; documents that CL helps sparsity/cold-start but adds false-negative + popularity-bias risk. The "what can go wrong" reference for this iteration.
7. **Few-Shot Representation Learning for Cold-Start Users and Items (Hao et al., APWeb 2020) + CLCRec (Wei et al., MM 2021)** — Meta-learn / contrastively align content features so cold users/items get usable embeddings from <100 interactions. Directly addresses Mesh's week-1 reality: a triplet head trained from scratch on 50 triples will overfit; pre-train on synthetic intent↔tool pairs from descriptions, then fine-tune on real adoptions.
8. **Understanding Hard Negatives & Feature Collapse (e.g., Robinson et al., ICLR 2021 "Contrastive Learning with Hard Negative Samples"; Huang et al., ICML 2023 "Model-Aware CL")** — Too-hard negatives induce dimensional collapse; too-easy negatives give zero gradient. Mesh needs a curriculum: start with random in-batch + `excluded_tools`, escalate to model-mined hard negatives only after the head stabilizes.

## Synthesis — Mesh pipeline shape

**Architecture.** Frozen E5/BGE encodes both the intent object's `desired_capabilities` text (and optionally a serialized intent blob) and tool descriptions. A small MLP projection head φ (2 layers, ~256→128) trained on Mesh data sits on top of *both* sides (or just the tool side, with intent passed through identity). Score = cos(φ(intent), φ(tool)).

**Loss.** Triplet with margin, or InfoNCE with one positive (adopted tool) + K negatives:
- K1: in-batch negatives (cheap, lots of gradient early)
- K2: `excluded_tools` from the intent object — already labeled hard negatives, free
- K3: the user's *tried-and-bounced* tool — the paradigm-fit signal we actually care about, weighted highest
- K4 (later): ANCE-style mined hard negatives — currently top-ranked tools that no one in the same intent cluster adopted

**What new depth this reaches.** Paradigm fit becomes learnable because the gradient explicitly says "Reflect cosine should *drop* relative to Obsidian for this intent, even though both have note-taking capability." Specific friction match improves too: if "database-first felt overwhelming" recurs in bounced-Notion triples, the head learns to push DB-paradigm tools away from intents that mention friction with structure.

**Noise it handles.** Capability-cosine ties between near-paradigm twins; user vocabulary drift (E5 already absorbs that, head sharpens it); multi-reason rejections (with denoising à la RocketQA — use Claude as a cross-encoder to label whether a bounce is paradigm-driven vs. accidental).

**Gap that REMAINS.** Two:
1. **Workflow-edge / composition signals** (intent.workflow_edges) are still flattened into bag-of-capabilities. The head can't learn "tool A only fits when it pipes into tool B" from a projection over a single embedding.
2. **Cold-start honesty.** With <100 users in week 1, a triplet head trained from scratch will memorize noise. Mitigation: bootstrap with synthetic triples (LLM generates (intent, plausible_match, plausible_mismatch) from the tool catalog + paradigm tags), then fine-tune on real adoptions as they arrive — meta-learning / CLCRec-style. Without this bootstrap, hold the projection head behind a feature flag until ~300 real triples exist; until then, ship raw E5/BGE + `excluded_tools` filter and log adoptions.

## Suggested next iteration

**Cross-encoder reranker with intent context (top-K rerank stage).** Pick this over GNN/KG/ColBERT because:

- The remaining gap is *compositional reasoning over the intent object* (workflow_edges, counterfactual_gaps, frictions interacting), not graph topology or token-level matching. A cross-encoder gets the full structured intent JSON + full tool description in one forward pass and can attend across them — exactly where bi-encoders (even with a learned head) lose information.
- It is the cheapest depth jump: no new infra (Claude Haiku as the cross-encoder works), no graph to maintain, no new training data beyond the same triples (use them as rerank labels).
- It composes cleanly: contrastive head produces top-20 candidates → cross-encoder rerank to top-5. The bi-encoder + head handles paradigm fit at scale; the cross-encoder handles workflow/compositional fit on the short list.
- GNN, KG, and ColBERT all require infrastructure or labeled graphs Mesh does not have in week 1; agentic retrieval is the *next* step after the reranker proves the compositional signal exists.

Order of operations: ship contrastive head (this iter) → cross-encoder rerank (iter 4) → revisit graph/agentic only if rerank still misses a measurable class of failures.
