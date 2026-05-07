# Iter 10 — Thompson Sampling / Epinet / Bayesian Bandits as Bootstrap Exploration Layer

**Goal:** Above iter-8 agentic candidates, sit a posterior-sample selector that turns the cold-start problem into a propensity-logged data factory for iter-9 (causal uplift).

---

## Per-paper takeaways

1. **A Tutorial on Thompson Sampling — Russo, Van Roy, Kazerouni, Osband, Wen (2018)** [arxiv 1707.02038](https://arxiv.org/abs/1707.02038)
   The canonical reference. Posterior-sample-then-greedy is provably near-optimal across Bernoulli, linear, and structured bandits. *Cold-start signal:* TS is the right default when priors are reasonable; it requires sampling from posterior, which is the bottleneck Mesh must solve cheaply.

2. **A Contextual-Bandit Approach to Personalized News (LinUCB) — Li, Chu, Langford, Schapire (2010)** [arxiv 1003.0146](https://arxiv.org/abs/1003.0146)
   Yahoo Front Page, 33M events, +12.5% CTR over context-free bandits — and gains *grow as data gets sparser*. Establishes that linear contextual bandits work in true cold-start with content churn. *Feasibility check:* a LinTS baseline over (user_embed ⊕ tool_embed) is genuinely viable at <100 users.

3. **Deep Exploration via Bootstrapped DQN — Osband, Blundell, Pritzel, Van Roy (2016)** [arxiv 1602.04621](https://arxiv.org/abs/1602.04621)
   K-head bootstrap ensemble approximates posterior sampling in deep nets; demonstrates that *temporally-coherent* exploration beats epsilon-greedy by orders of magnitude in sparse-reward MDPs. *Mesh implication:* dithering (eps-greedy on the iter-8 ranker) leaves money on the table; sampling a coherent posterior across a session matters.

4. **Neural Contextual Bandits with UCB-based Exploration (NeuralUCB) — Zhou, Li, Gu (2020)** [arxiv 1911.04462](https://arxiv.org/abs/1911.04462)
   First Õ(√T) regret bound for neural-net contextual bandits via NTK-derived confidence widths. Companion *NeuralTS* (Zhang et al.) is the Thompson variant. *Caveat:* NTK confidence is expensive (gradient-based covariance); not a fit for live serving but useful as an offline yardstick.

5. **Epistemic Neural Networks (Epinet) — Osband, Wen, Asghari, Dwaracherla, Ibrahimi, Lu, Van Roy (NeurIPS 2023)** [arxiv 2107.08924](https://arxiv.org/abs/2107.08924)
   The epinet is a small additive head with an *index input* z ~ p(z); a single forward pass with a fresh z gives a posterior sample. Matches 100+ ensemble particles at ~1% the compute. Critical insight: *joint predictive accuracy* (not marginal calibration) is what TS needs. **This is the algorithmic core for Mesh.**

6. **Approximate Thompson Sampling via Epistemic Neural Networks — Osband et al. (UAI 2023)** [PMLR v216](https://proceedings.mlr.press/v216/osband23a/osband23a.pdf)
   Operationalises Epinet inside Thompson sampling; shows graceful scaling to neural-scale environments. Confirms the recipe: *one forward pass per posterior sample*, no ensemble, no Laplace.

7. **Epinet for Content Cold Start — Jeon, Liu, Li, Lyu, Song, Liu, Wu, Zhu (WebConf 2025)** [arxiv 2412.04484](https://arxiv.org/abs/2412.04484)
   First production deployment of epinet for online recsys: Facebook Reels, statistically significant lifts in both traffic and engagement-efficiency. *Cold-start signal:* this is the closest analog to Mesh's situation — a constantly-refreshing item catalog and a need for cheap per-impression posterior samples. Existence proof that the approach ships.

8. **Calibrated Recommendations with Contextual Bandits — Spotify Research (2025)** [arxiv 2509.05460](https://arxiv.org/abs/2509.05460)
   Neural contextual bandit chooses content-type *distribution* per slate; eps-greedy exploration; reward = binarised stream time, optionally co-clustered. Production wins on impressions, homepage activity, total minutes. *Honesty check:* Spotify ships eps-greedy, not TS — a reminder that exploration *quality* often loses to exploration *operability*.

9. **Learning to Optimize via Information-Directed Sampling — Russo, Van Roy (2014/2018)** [arxiv 1403.5556](https://arxiv.org/abs/1403.5556)
   IDS picks actions minimizing (regret²)/(information-gain). Strictly dominates TS on problems with structured information leakage (e.g., one query reveals about many tools). *Mesh angle:* a future upgrade once we have a KG/embedding structure to exploit; not V1.

10. **Feel-Good Thompson Sampling — Zhang (2021)** [arxiv 2110.00871](https://arxiv.org/abs/2110.00871)
    Fixes a known TS pathology: under model misspecification (non-realizable reward function) standard TS can suffer linear regret. Adds an optimism bonus to the posterior. *Why it matters:* Mesh's reward model *will* be misspecified in V1 — Feel-Good TS gives a robustness knob.

---

## Synthesis — How this layer slots into Mesh

**Architecture in one paragraph:** iter-8 agent emits K (≈10–20) candidate tools per query. A two-tower model φ(user) · ψ(tool) + epinet head produces, per candidate, an *adoption-probability posterior* parameterized by an index z. At serve time we sample one z, score all K candidates, then either argmax (top-1 surface) or softmax-with-temperature (top-K slate). The action, the K-wide candidate set, the sampled z (or equivalently the implied propensity p(action | context, z)), and the eventual outcome (click / install / kept-after-7d) are logged. Once volume hits ~5k logged tuples with non-degenerate propensities, iter-9's doubly-robust uplift estimator τ̂(u, t) becomes trainable; until then, the epinet posterior *is* the policy.

**Depth reached now:** *better data*, not better policy. The win is propensity-logged exploration that breaks the popularity feedback loop and makes counterfactual estimation possible. **Depth reached later:** once iter-9 trains, the epinet posterior conditions on τ̂ (sample uplift, not raw adoption) — exploration concentrates on candidates with *uncertain treatment effect*, not just uncertain reward.

**Noise tolerance:** sublinear regret bounds (NeuralUCB / NeuralTS / Feel-Good TS) absorb stochastic reward noise; bootstrap/epinet randomization absorbs model-class noise; logged propensities absorb selection-bias noise downstream via IPW/DR.

**Gaps that remain.** (a) **User-satisfaction tax is real:** at K=15 with 5–10% exploration mass, ≈1 in 10 sessions surfaces a deliberately suboptimal recommendation — visible to users at <100-user scale. (b) **Prior elicitation:** epinet needs a sensible prior; with zero history we either bootstrap from synthetic rollouts (LLM-generated user simulations) or accept a uniform-ish prior and pay a few hundred sessions of high regret. (c) **Top-K vs top-1:** Mesh shows slates, but most TS theory is single-arm; combinatorial pure-exploration results (Chen et al. 2014 etc.) apply but are loose in practice. (d) **Non-stationarity:** tool catalog drifts; the posterior must forget. None of these are blockers — all are tunable.

**Honest caveat.** Exploration is a *bootstrap mechanism* whose job is to commit suicide gracefully: it should be replaced (or heavily down-weighted) the moment iter-9's uplift model has signal. A 6–12 month deprecation arc is the realistic plan.

---

## Suggested next direction — **STOP. Start the synthesis.**

We are 10 iterations deep. We have: 7 active stages (iters 2–8), 1 deferred to V2/V3 (iter 9), 1 generator above the stack (iter 10). Marginal value-per-iteration of the *next* algorithm idea (Query2Box, GraphRAG, mixture-of-retrievers, in-context recsys with long-context Sonnet) is now strictly less than the marginal value of writing down **which subset ships in V1 / V1.5 / V2 / V3 with thresholds and tradeoffs.** The research-vs-deploy frontier has tipped.

**Concrete iter-11 deliverable:** a deployment plan that (i) maps each of iters 2–10 to a release, (ii) gives each an *activation threshold* (data volume, latency budget, eng-weeks), (iii) lists the *fallback* if the iter underperforms, and (iv) names the metric that triggers promotion to the next tier. Without this synthesis, iters 2–10 stay a bag of papers; with it, they become a roadmap. Pick synthesis. Ship the plan.
