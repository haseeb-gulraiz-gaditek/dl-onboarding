# Iter 16 — Contextual bandits / EXP4 / Thompson sampling for online retriever routing

Bridging iter-10 propensity-logged adoption rewards into iter-15 routing without waiting for supervised labels.

## Papers

1. **The Nonstochastic Multiarmed Bandit Problem** (Auer, Cesa-Bianchi, Freund, Schapire, 2002) — Foundational EXP4: exponential-weights over N "experts" each emitting a probability over K arms, achieves O(sqrt(KT log N)) regret with no stochastic assumptions on rewards. Directly applicable: treat MoR weights, RRF, uniform, and per-retriever specialists as experts; bandit hedges over them adversarially. https://cesa-bianchi.di.unimi.it/Pubblicazioni/J18.pdf

2. **EXP4.P: Contextual Bandit Algorithms with Supervised Learning Guarantees** (Beygelzimer, Langford, Li, Reyzin, Schapire, 2011) — Tightens EXP4 to a *high-probability* regret bound O(sqrt(KT ln(N/delta))). Critical for Mesh: production routing needs anytime tail guarantees, not just expected regret, before exploration cost is acceptable to ship. https://arxiv.org/abs/1002.4058

3. **A Contextual-Bandit Approach to Personalized News Article Recommendation** (Li, Chu, Langford, Schapire, 2010) — LinUCB; per-arm ridge regression over context, picks argmax of mean + alpha * uncertainty. Yahoo! deployment, +12.5% CTR vs context-free. The realistic blueprint for Mesh's first online cut: cheap, interpretable, no neural net needed, and the iter-14 nonconformity score plugs directly into the confidence term. https://arxiv.org/abs/1003.0146

4. **Thompson Sampling for Contextual Bandits with Linear Payoffs** (Agrawal, Goyal, 2013) — Posterior-sampling alternative with Õ(d^{3/2} sqrt(T)) regret, empirically matches/beats LinUCB and is parameter-free (no alpha to tune). For Mesh: TS naturally ties to iter-10's epinet posterior — sampled draw -> arm pick -> observed adoption -> Bayesian update. Cleanest fit if we're already maintaining posteriors upstream. https://arxiv.org/abs/1209.3352

5. **Cascading Bandits: Learning to Rank in the Cascade Model** (Kveton, Szepesvari, Wen, Ashkan, 2015) — Online L2R where reward = position of first click; CascadeUCB/CascadeKL-UCB achieve gap-dependent O(log T) regret. Relevant because Mesh users scan ranked tool lists top-down — adoption is the cascading-click signal, not full-list relevance. Position bias is built into the model rather than estimated post-hoc. https://arxiv.org/pdf/1502.02763

6. **Adapting to Non-Stationary Environments: MAB-Enhanced RAG on Knowledge Graphs** (Tang, Li, Du, Xie, AAAI 2025) — Closest published analogue to Mesh's iter-16: multi-objective MAB picks among retrieval methods per query, rewards from real-time feedback, beats static neural routers (which need full labels) under drift. Validates the architecture; their gap-shaped result (bandit > supervised router when label coverage is partial) is exactly Mesh's situation. https://arxiv.org/abs/2412.07618

7. **PAK-UCB: Online Learning Approach to Prompt-Aware Selection of Generative Models and LLMs** (Hu, Leung, Farnia, ICML 2025) — Kernel-UCB over prompt embeddings to pick best generator per prompt; random-Fourier features keep it scalable. The retriever-routing analogue: same template (context = embedding, arms = models, reward = quality), production-grade, and shows kernel-UCB beats deep contextual bandits at modest scale — useful warm-start before going neural. https://openreview.net/forum?id=mqDgNdiTai

8. **Mostly Exploration-Free Algorithms for Contextual Bandits** (Bastani, Bayati, Khosravi, 2021) — Critical counter-result: under context diversity assumptions, greedy (exploit-only) is rate-optimal; explicit exploration can hurt. For Mesh: if iter-14 conformal abstention already inflates uncertainty correctly and iter-10 propensities give natural exploration noise, an aggressive epsilon=0 LinTS might dominate. Tells us *not* to over-engineer exploration. https://hamsabastani.github.io/greedybandit.pdf

## Synthesis

**Pipeline integration.** Per query q: build context x_q = [intent_embed; conformal_nonconformity(iter-14); query_features]. Bandit policy pi(a|x_q) over arms {dense, boxes, GraphRAG, agent, RRF} returns retriever a_q with logged propensity p_q. Iter-12 reranks, top-k surfaced. User accept/click/dwell -> reward r_q in [0,1] (iter-10's adoption signal). Update: LinUCB updates per-arm A_a, b_a; Thompson updates posterior; EXP4 updates expert weights using importance-weighted reward. MoR (iter-15) becomes one of the EXP4 experts rather than the only router — bandit *hedges* over MoR/RRF/uniform/per-retriever specialists, so cold-start defaults to RRF with provable convergence to whichever expert is best in hindsight. Off-policy replay against iter-9 IPS lets us pre-train weights before any live exploration.

**New depth.** (a) No supervised label required — adoption *is* the reward, closing iter-15's coverage gap. (b) Provably sublinear regret (sqrt-T or log-T cascading) — first formal guarantee in the stack. (c) Online adaptation to drift (new tools, shifting intent mix) without retraining. (d) Hedging across MoR + RRF + uniform means iter-15 can't underperform the safe baseline by much, which de-risks deployment.

**Noise absorbed.** Delayed rewards via reward attribution windows; partial feedback is native (only chosen arm observed); position bias handled by cascading model; non-stationarity by Tang et al.'s sliding-window or discounted variants.

**Gap that REMAINS.** Cold-start regret is O(sqrt(KT)) — the *first thousand users* pay the exploration tax. User-satisfaction tax is real and not fully mitigated by hedging if the uniform/RRF expert itself is mediocre. Bandits are query-level only; they don't personalize per user without per-user posteriors (state explosion). Reward shaping is fragile — adoption ≠ true utility (clickbait tools, novelty bias). Bastani warns we may be over-exploring; LinUCB alpha needs tuning we can't do offline.

## Suggested next direction

**Federated / on-device personalization (per-user contextual bandit with shared prior).** Strongest gap-filler: iter-16 routes per *query*, but Mesh's value is per-*founder* tool fit. Federated bandits (per-user posteriors, shared kernel/prior across users) close the personalization gap that EXP4 explicitly punts on, and on-device computation sidesteps the privacy/latency tax of logging everything centrally. Agent distillation overlaps too much with iter-8; multi-task instruction-tuned retrievers overlap with iter-5/11.

**Saturation check.** Value-per-iter trend (subjective): iter-13 GraphRAG ~9, iter-14 conformal ~8.5, iter-15 MoR ~8, iter-16 bandits ~8 (closes a real gap, but architecturally adjacent to 10/15). Not yet below 7.5 for 3 consecutive iters — *do not stop yet*. If iter-17 (federated personalization) lands below 7.5, then iter-18 should be the V2 SYNTHESIS rather than a new mechanism.

## Sources

- [The Nonstochastic Multiarmed Bandit Problem (Auer et al. 2002)](https://cesa-bianchi.di.unimi.it/Pubblicazioni/J18.pdf)
- [EXP4.P / Contextual Bandit with Supervised Learning Guarantees (Beygelzimer et al. 2011)](https://arxiv.org/abs/1002.4058)
- [LinUCB / Personalized News Recommendation (Li et al. 2010)](https://arxiv.org/abs/1003.0146)
- [Thompson Sampling for Linear Contextual Bandits (Agrawal & Goyal 2013)](https://arxiv.org/abs/1209.3352)
- [Cascading Bandits (Kveton et al. 2015)](https://arxiv.org/pdf/1502.02763)
- [MAB-Enhanced RAG on Knowledge Graphs (Tang et al. AAAI 2025)](https://arxiv.org/abs/2412.07618)
- [PAK-UCB (Hu, Leung, Farnia ICML 2025)](https://openreview.net/forum?id=mqDgNdiTai)
- [Mostly Exploration-Free Contextual Bandits (Bastani, Bayati, Khosravi 2021)](https://hamsabastani.github.io/greedybandit.pdf)
