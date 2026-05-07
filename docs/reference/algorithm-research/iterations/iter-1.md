# Iter 1 — Baseline semantic matching

**Approach**: two-tower dense embedding (E5/BGE/GTE) + cosine NN over ~300-tool catalog.

## Top 3 papers
- **DPR (Karpukhin 2020)** — asymmetric dual encoder, in-batch negatives; validates short-noisy-user / longer-tool-doc shape.
- **E5 (Wang 2022)** — `query:` / `passage:` prefix; first OSS embedding to beat BM25 zero-shot on BEIR. Best off-the-shelf v1 candidate.
- **YouTube two-tower w/ sampling correction (Yi 2019)** — same shape as Mesh; flags popularity collapse failure mode unless frequency-corrected.

## Scores
- **depth = 4.5** — reaches topical/capability vocabulary only. Flattens 3-entity time-conditioned workflows into a single centroid. No intent vs description bridge.
- **noise = 6** — strong on lexical noise (synonyms, paraphrase, typos). Weak on semantic noise (frictions vs features) and unable to honor `tried-and-bounced` negatives.
- **compose = 9** — every subsequent approach (rerank, graph, intent layer, GNN) sits on top of an embedding base. Foundational scaffolding.
- **composite = 4.5·0.5 + 6·0.3 + 9·0.2 = 5.85**

## Verdict
**Discard as standalone** (composite 5.85 < 7.0). Keep as the retrieval substrate that later approaches compose with.

## Gap left
1. Intent-vs-description gap — users describe friction, vendors describe features.
2. Workflow compositionality — multi-entity, time-conditioned signals collapse.
3. Negative signals (tried-and-bounced) cannot be excluded via cosine.
4. Counterfactual wishes look like descriptions of existing tools.
5. Popularity collapse without sampling correction.

## Next direction
**LLM-driven intent / friction extraction layer.** Pre-encode pass converts raw user signal into structured `{frictions, desired_capabilities, excluded_tools, workflow_edges}` object; embed the capabilities field, not raw text. Addresses gap #1 directly (the biggest), composes cleanly with everything downstream, cheap to run (one cached Sonnet call per profile).
