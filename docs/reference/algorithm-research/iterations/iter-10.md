# Iter 10 — Epinet / Thompson-sampling exploration above iter-8 candidates

**Approach**: control layer above iter-8 agent. Agent generates K candidates; Epinet provides cheap epistemic-uncertainty samples over per-candidate τ; sample one (or top-K with calibrated propensities) instead of pure argmax. Logs (user_embed, tool_embed, action_taken, propensity, outcome) — exactly the schema iter 9 needs.

## Top 3 papers
- **Epistemic Neural Networks / Epinet (Osband NeurIPS 2023, arXiv 2107.08924)** — cheap posterior samples without full ensembles; one MLP head learns the epistemic uncertainty signal. Practical Thompson sampling at production scale.
- **Epinet for Content Cold Start (Jeon 2024, arXiv 2412.04484)** — Facebook Reels bootstrap via Epinet; direct precedent for Mesh's <100-user phase. Ships propensity-logged data into a downstream uplift model (mirrors Mesh iter 9).
- **Calibrated Recommendations with Contextual Bandits (Spotify 2025, arXiv 2509.05460)** — production calibration of propensities under exploration; addresses the off-policy-eval correctness Mesh's iter 9 will depend on.

Honorable: Russo/Van Roy 2018 TS tutorial, Li 2010 LinUCB Yahoo, Bootstrapped DQN (Osband 2016), NeuralUCB/TS (Zhou 2020), Approximate TS via ENN (Osband UAI 2023), IDS (Russo & Van Roy 2014), Feel-Good TS (Zhang 2021).

## Scores
- **depth = 7.0** — generator more than scorer; doesn't deepen *matching* but escapes greedy-ranking self-fulfilling-prophecy trap. Adds the "exploration is its own form of depth" capability — without it, popular tools dominate forever and iter 9 never has data to learn τ. Without exploration, the deeper later iters cannot exist.
- **noise = 7.5** — regret-bounded exploration handles noisy reward signals; Epinet's epistemic uncertainty separates "I haven't seen this user-tool pair" from "this pair is genuinely bad." Calibrated propensities preserve off-policy validity.
- **compose = 8.5** — sits cleanly above iter 8; output (logged tuples) feeds iter 9 as designed. Required bridge between V1 (matching) and V2/V3 (uplift). Slight cost: user-satisfaction tax (~5-10% exploratory recs may underperform — visible at <100-user scale).
- **composite = 7.0·0.5 + 7.5·0.3 + 8.5·0.2 = 3.5 + 2.25 + 1.7 = 7.45**

## Verdict
**ADVANCE** (composite 7.45 ≥ 7.0). Locks in as the V1.5 control layer that activates the iter 9 V2/V3 uplift path. Without iter 10, iter 9 is unreachable from launch.

## Gap left
1. **Set-level / quantifier reasoning still LLM-only.** Iter 8 handles "any CRM the user already uses" via Sonnet calls. A pure-vector substrate for set operations (intersection, union, "exists at least one") would close the latency-and-cost gap iter 8 has on the slow path.
2. **No in-context personalization at retrieval time.** Long-context models (Sonnet 1M) could dynamically include the user's full chat history as context — different from training-time personalization.
3. **Saturation signal.** The pipeline now spans semantic → structured → graph → symbolic-LLM → causal → exploration. Marginal value-per-iteration is dropping.

## Next direction
**Query2Box / Concept2Box neuro-symbolic operators** for set-and-quantifier reasoning in vector space. Box embeddings represent *sets of entities* rather than points; intersection, union, negation become geometric operations on boxes. Mesh queries like "tools matching frictions A AND capabilities (B OR C) AND NOT excluded" become box compositions, computed in ~ms vs the agent's seconds. Composes with iter 5 (boxes ≈ multi-vector regions), iter 6 (entities = box centers), iter 8 (agent calls box solver as a tool primitive). One more iteration before synthesis if value-per-iter stays positive.
