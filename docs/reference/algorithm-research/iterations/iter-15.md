# Iter 15 — Mixture-of-retrievers (MoR) with learned routing

**Approach**: small router takes `[intent_embed || per-path conformal nonconformity (iter-14) || query-type one-hot]` → softmax over `{iter 5, 11, 13, 8}` → score-level fusion of weighted candidates → iter-14 final gate → iter-12 rerank. Cold-start default: RRF. Trained on (intent, |C|=1 path matching accepted) tuples from iter-14 telemetry.

## Top 3 papers
- **MoR 2025 (arXiv 2506.15862)** — first explicit "mixture of sparse, dense, and human retrievers" paper; query-conditional routing beats best single retriever and RRF baselines.
- **RouterRetriever (AAAI 2025, arXiv 2409.02685)** — softmax routing over expert embedding models; close architectural template for Mesh's per-retriever routing.
- **LTRR (SIGIR 2025, arXiv 2506.13743)** — learning-to-rank-retrievers; supervised on per-query best-retriever labels — exactly what iter-14 produces.

Honorable: Adaptive-RAG (complexity-aware routing), Self-Route (RAG-vs-LC routing), RRF (foundational cold-start fallback), cascade deferral critiques (when does routing actually help).

## Scores
- **depth = 7.0** — doesn't deepen matching directly; enables the right *combination* of depths the upstream retrievers provide. Per-query-type best-retriever selection without manual rules. Cap: oracle MoR vs learned MoR has a measured gap (~30-40% of theoretical gain typically lost to label scarcity); router cannot exceed the best constituent retriever's depth.
- **noise = 7.5** — router learns to down-weight noisy retrievers per query type; iter-14 conformal gate still bounds final coverage. Path diversity acts as noise filter. Slight risk: router itself can be noisy at low N.
- **compose = 8.5** — natively wraps every retriever (iter 5/8/11/13); supervised by iter-14; gates upstream of iter-12 rerank. Plug-and-play. Slight cost: training pipeline + telemetry capture.
- **composite = 7.0·0.5 + 7.5·0.3 + 8.5·0.2 = 3.5 + 2.25 + 1.7 = 7.45**

## Verdict
**ADVANCE** (composite 7.45 ≥ 7.0). Locks in as **V2 routing layer**. Cold-start = RRF until ≥5k labeled (intent, accepted) tuples; learned router activates with monotonic weight transition. Iters 13–15 all scored 7.35–7.50 — saturation plateau confirmed.

## Gap left
1. **Label scarcity for supervised MoR.** Only |C|=1 conformal-confident matches produce clean labels; most queries don't yield supervised signal.
2. **Oracle vs learned router gap.** Even with abundant labels, the upper bound is the oracle (always picks best retriever). Production MoR captures 60–70% of that lift.
3. **Cold-start router** must default to RRF; learned router activation needs a "weight ramp" to avoid a quality cliff.

## Next direction
**Contextual bandit (EXP4 / Thompson) online learning with regret minimization, RRF as starting expert.** Treat retriever choice as bandit-arm; receive reward = downstream adoption (iter-10 logs). EXP4-style algorithm hedges across MoR weights and RRF, provably converging to oracle policy with sublinear regret. Directly addresses gap 1 (labels emerge from online play, not requiring conformal-confident matches) and gap 3 (RRF is the safe expert; learned router is the exploring expert; regret bound = quality cliff guarantee). Composes with iter 10 (Thompson exploration generates the rewards) and iter 14 (conformal gate still enforces honesty). Continue, do not synthesize yet — value-per-iter still positive on routing/uncertainty stack.
