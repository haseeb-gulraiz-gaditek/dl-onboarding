# Iter 14 — Conformal prediction abstention layer

**Approach**: per-path nonconformity scores (iter 5 dense, iter 11 boxes, iter 13 GraphRAG, iter 8 agent) over held-out (intent, accepted_tool) pairs; multi-model min-score aggregation; ACI-wrapped threshold for distribution shift. `|C|=1` → return; `|C|>1` and small → return as set; `|C|>k` → escalate to agent; `|C|=0` → abstain (clarifying Q).

## Top 3 papers
- **Angelopoulos & Bates 2021 (arXiv 2107.07511)** — gentle introduction; the operational template for any production CP layer.
- **Mitigating LLM Hallucinations via Conformal Abstention (DeepMind 2024, arXiv 2405.01563)** — directly applicable to iter-12 long-context rerank's hallucinated-tool failure mode.
- **Multi-Model Ensemble Conformal Prediction (2024, arXiv 2411.03678)** — literally the multi-retriever-mixture case; tells us how to combine the four paths' nonconformity scores without losing coverage.

Honorable: Vovk foundational, SelectiveNet (selective baseline), Conformal Ranked Retrieval (2024, arXiv 2404.17769), Adaptive CI under distribution shift (Gibbs & Candès 2021), Critical Perspective on Finite-Sample CP (2025) — the honest "needs ≥500 pairs" reality check.

## Scores
- **depth = 7.0** — control layer, not a matching layer; doesn't deepen matching itself. Adds **principled trust** every prior stage lacked: formal coverage, not heuristic confidence. That's its own kind of depth — the meta-layer that says "we don't know, escalate" is structural for honest concierge UX.
- **noise = 8.0** — designed for noise. Prediction sets *quantify* uncertainty rather than masking it; adaptive conformal handles distribution shift as catalog/users evolve. Strongest noise score in the loop.
- **compose = 8.0** — wraps every retriever (iter 5/8/11/13), produces a meaningful gate signal that mixture-of-retrievers can supervise on, and feeds the concierge's "I'm not sure, can you tell me more?" output. Slight cost: needs ≥500 calibration pairs to be useful; shadow-mode until then.
- **composite = 7.0·0.5 + 8.0·0.3 + 8.0·0.2 = 3.5 + 2.4 + 1.6 = 7.50**

## Verdict
**ADVANCE** (composite 7.50 ≥ 7.0). Locks in as the **honest-concierge primitive** — without it, the system can't say "I don't know" with calibration. V2 activation: collect calibration pairs in shadow mode through V1; flip on at ~500 pairs; tighten α as pairs accumulate.

## Gap left
1. **Calibration cold-start.** Useless below ~500 (intent, accepted) pairs; V1 has zero. Shadow-mode logging is the only V1 contribution.
2. **No learned routing.** CP says "this path is uncertain"; doesn't learn *which* path to prefer for which query type. That's a separate model.
3. **Coverage vs efficiency tradeoff** — at small N, sets are wide; tight α means low coverage; users see "I'm not sure" too often.

## Next direction
**Mixture-of-retrievers (MoR) with learned routing supervised by iter-14 conformal-confident-path signal.** Train a small router (intent embedding → softmax over {iter 5, 11, 13, 8}) using iter-14's per-path conformal sets as labels: the path whose `|C|=1` matches the actual accepted tool gets weight 1, others 0. Bootstraps directly off iter-14 telemetry rather than competing with it. Composes: iter-14 produces calibrated gates; MoR consumes them; iter-12 reranks the routed candidates. Direct attack on gap 2; the only unresearched candidate that *piggybacks* on iter-14 rather than running parallel.
