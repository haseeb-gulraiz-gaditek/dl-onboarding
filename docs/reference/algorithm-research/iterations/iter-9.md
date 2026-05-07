# Iter 9 — Causal uplift modeling τ(u,t) = P(adopt|rec) − P(adopt|no-rec)

**Approach**: rerank iter-8 agent candidates by uplift instead of match score. Train τ(u,t) on (user_embed, tool_embed) → adoption outcomes using DragonNet / X-learner / IPS-weighted BPR. Conformal-prediction abstention when data is sparse. **Critical caveat**: structurally V2/V3 — Mesh at <100 users has no propensity-logged outcomes; uplift requires explicit randomization or strong ignorability that observational data won't satisfy.

## Top 3 papers
- **Causal Forests (Wager & Athey 2015, arXiv 1510.04342)** — honest splitting + nearest-neighbor weights for HTE estimation; the foundational uplift method for tabular contexts. Limit: needs ~10⁴+ observations for stable estimates.
- **DragonNet (Shi 2019, arXiv 1906.02120)** — joint propensity + outcome head sharing a representation; fits our setup of having user/tool embeddings already and wanting τ on top. Practical neural HTE baseline.
- **Counterfactual Risk Minimization (Swaminathan & Joachims 2015, arXiv 1502.02362)** — IPS-weighted training directly from logged bandit data; the principled path from agent traces to learned ranker without on-policy A/B testing.

Honorable: Künzel meta-learners (S/T/X), TARNet, BanditNet, Gao 2022 causal-recsys survey, Raja & Vats 2025 (IPS-BPR for recsys), Jeon 2024 Epinet (cold-start exploration).

## Scores
- **depth = 8.5** — deepest possible recommendation criterion: not "matches user" but "would change user's behavior." Match-quality ceiling broken. Cap: ceiling is data-bound, not algorithm-bound.
- **noise = 6.0** — uplift estimation is brutally noise-sensitive at low N. With <1k logged outcomes, treatment-effect variance dominates signal. Conformal abstention helps but bounds coverage. Score reflects honesty: this stage *amplifies* noise unless data volume is there.
- **compose = 6.5** — composes with iter 7/8 outputs as features, but requires new infra: logging, randomization, propensity tracking, IPS reweighting. Hard data prerequisite. Less plug-and-play than every prior advanced iteration.
- **composite = 8.5·0.5 + 6.0·0.3 + 6.5·0.2 = 4.25 + 1.8 + 1.3 = 7.35**

## Verdict
**ADVANCE** (composite 7.35 ≥ 7.0) — but explicitly **deferred to V2/V3** with a hard data prerequisite (~5k logged adoptions before training τ). Until then, stage 9 is a placeholder; iter-8 agent + iter-4 rerank produce the V1 final ranking.

## Gap left
1. **No logged data at launch.** Without propensity-logged outcomes, uplift cannot be trained — observational data with confounding will systematically bias τ.
2. **Exploration absent.** Without a generator that intentionally varies recommendations across similar users, the data needed for uplift never arrives.
3. **No online learning loop.** Static models can't adapt as user/tool catalog evolves.

## Next direction
**Epinet / Thompson-sampling exploration layer wrapped around iter-8 agent candidates.** This is the *generator* that produces propensity-logged tuples needed by iter 9 (and every later causal method). At each rec, sample from a posterior over τ predictions; log (user_embed, tool_embed, action_taken, propensity, outcome). Epinet provides cheap epistemic uncertainty for Thompson sampling without ensembles. Without this, iter 9 has nothing to train on. Composes as a control layer above iter 8: agent produces candidate set, exploration layer selects with calibrated randomness, logs everything for iter 9. Direct attack on gap 2 (no exploration) and prerequisite for gap 1 (no data).
