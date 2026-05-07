# Iter 16 — Contextual bandit (EXP4 / Thompson) online retrieval routing

**Approach**: contextual bandit with arms = `{iter 5, iter 11, iter 13, iter 8, RRF}`; context = `[intent_embed; iter-14 nonconformity; user_features]`; reward = downstream adoption from iter-10-logged outcomes. EXP4 hedges across experts (MoR weights, RRF, uniform) for sublinear regret. Iter-9 IPS used as warm-start via offline replay before live exploration.

## Top 3 papers
- **EXP4 / EXP4.P (Auer 2002 + Beygelzimer 2011)** — foundational expert-mixing bandit; high-probability regret bound that gives a *formal quality cliff guarantee* on top of iter 15's MoR.
- **LinUCB (Li 2010, arXiv 1003.0146)** — production-scale contextual bandit at Yahoo; closest deployed analog. Linear context model is enough for Mesh's intent-vector dimensionality.
- **MAB-Enhanced RAG on KGs (Tang AAAI 2025, arXiv 2412.07618)** — most direct precedent: bandit selects retrieval strategy per query in a RAG pipeline; shows bandit beats static fusion at production scale.

Honorable: Thompson Sampling for Linear Contextual Bandits (Agrawal-Goyal 2013), Cascading Bandits (Kveton 2015), PAK-UCB (Hu ICML 2025) — kernel-UCB model selection, Bastani 2021 (greedy-bandit critique: when ε-greedy suffices).

## Scores
- **depth = 7.0** — adds *online adaptation* and regret-bounded routing depth; doesn't deepen matching itself but turns retrieval routing into a learnable closed loop. Cap: bandit picks among existing retrievers; cannot create new depth beyond the constituent arms.
- **noise = 8.0** — designed for noisy delayed rewards; partial feedback handled natively; EXP4's hedge guarantees competitive performance even when constituent experts (MoR, RRF) disagree noisily.
- **compose = 8.5** — wraps iter 15 (MoR becomes one expert, not the sole router); consumes iter 10 rewards; respects iter 14 gates; outputs feed iter 12 rerank. Strongest compose: turns the entire stack into a closed-loop learner.
- **composite = 7.0·0.5 + 8.0·0.3 + 8.5·0.2 = 3.5 + 2.4 + 1.7 = 7.60**

## Verdict
**ADVANCE** (composite 7.60 ≥ 7.0). V2/V3 lock-in: closes the loop between retrieval choice and adoption outcomes with formal regret guarantees. Iter 9 IPS-replay warm-starts the bandit before live exploration to keep cold-start regret manageable.

## Gap left
1. **Cold-start regret tax** — early queries pay an exploration cost. Warm-start via iter-9 IPS replay helps but doesn't eliminate it.
2. **No per-user personalization in the routing policy itself.** Bandit context includes user features but treats them as features, not as separate sub-policies. Heavy users vs new users get the same router.
3. **Reward shaping is fragile.** Adoption ≠ utility; users may adopt and abandon, recommend a tool to others, etc. Single scalar reward hides this.

## Next direction
**Federated / on-device per-user personalization with shared prior.** Each user gets a small local model that fine-tunes routing weights on their own conversation history; gradients (not raw conversations) optionally aggregate to a global model. Closes gap 2 (per-user policy), respects Mesh's data-ownership constitution principle ("users own their concierge profile"), and composes with iter 16 (federated layer sits above bandit, modulating routing weights). This is the natural V3 direction — privacy-preserving deep personalization.
