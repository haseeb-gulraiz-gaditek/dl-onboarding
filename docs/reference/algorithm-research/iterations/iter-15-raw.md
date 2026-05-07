# Iter-15 raw: Mixture-of-Retrievers / learned routing for Mesh

## Per-paper takeaways

1. **MoR: Mixture of Sparse, Dense, and Human Retrievers (2025, arXiv 2506.15862)** — zero-shot weighted combination of heterogeneous retrievers (BM25 + dense + "human" sources); routing depth is shallow (per-retriever trustworthiness scalars, no per-query gating), but the +10.8% over best single retriever at 0.8B params validates the *fusion-with-weights* shape we want. Small-data viable because zero-shot; weakness — not query-conditional, so it leaves the per-query-type gain on the table that Mesh actually wants.

2. **RouterRetriever (Lee et al., AAAI 2025, arXiv 2409.02685)** — per-query routing over a mixture of LoRA-adapted expert embedding models using a pilot-embedding nearest-domain rule; +2.1 nDCG@10 over MS-MARCO single-task and +3.2 over multi-task on BEIR. Routing depth is genuine query-conditional (one expert per query), training is parameter-light (LoRA gates ~0.5%/expert), and experts can be added/removed without retraining — the closest published analogue to what iter-15 needs.

3. **LTRR: Learning To Rank Retrievers for LLMs (Kim et al., SIGIR 2025 LiveRAG, arXiv 2506.13743)** — frames routing as learning-to-rank over retrievers with downstream-answer-correctness as the supervision signal; XGBoost pairwise ranker is the winner. Directly relevant: their AC-objective is conceptually identical to our iter-14 "accepted with |C|=1" tuples, and their feature engineering shows routing works with a few thousand labeled queries — i.e., small-data viable.

4. **Adaptive-RAG (Jeong et al., NAACL 2024, arXiv 2403.14403)** — T5-Large complexity classifier routes among no-retrieval / single-hop / multi-hop strategies, labels auto-derived from which strategy actually answered correctly. Routing depth is strategy-level not retriever-level, but the auto-label trick (use *outcome* as the route label) is exactly the trick we need to bootstrap from iter-14 telemetry without hand-labeling.

5. **Self-Route / RAG-vs-Long-Context (Li et al., 2024, arXiv 2407.16833)** — LLM self-reflects on whether retrieved chunks suffice, falls back to long-context if not; cuts cost ~40-65% with no quality loss because RAG and LC agree on >60% of queries. Routing depth is binary (RAG vs LC) and uses model self-confidence as the gate — same philosophy as our conformal gate but uncalibrated; reinforces that calibrated uncertainty (iter-14) beats self-reported confidence.

6. **Reciprocal Rank Fusion (Cormack et al., SIGIR 2009)** — parameter-free rank aggregation `score(d) = Σ 1/(k+rank_i(d))`; the canonical baseline that "almost invariably" beats the best individual retriever. Critical for Mesh: this is the cold-start fallback when the learned router has no data, and the floor every learned MoR variant must beat to justify itself.

7. **Inter-Cascade / Cascade-aware deferral (2025, arXiv 2509.22984; survey 2307.02764)** — confidence-based deferral cascades and the formal "learning to defer to expert" framework; shows confidence-based deferral suffices only when the confidence is calibrated, otherwise deferral degrades to random. Direct critique of any uncalibrated router — and direct support for putting iter-14 conformal scores into the router input rather than the router's own softmax.

## Synthesis: how iter-15 MoR slots into Mesh

**Architecture.** Router input vector = `[intent_embedding (from iter-7 clarifier) || conformal_nonconformity_per_path (4 dims: ColBERT/BetaE/GraphRAG/agentic from iter-14) || query-type one-hot (from iter-9 classifier)]`. Output = softmax over 4 retriever paths. Train with cross-entropy where the target is the path that produced the iter-14 |C|=1 confident set *and* whose top-k ended up in the final accepted recommendation. Weighted candidate fusion happens at the score level (not rank), then iter-14 conformal still gates final output, then iter-12 cross-encoder reranks the surviving candidates. So the router never *replaces* conformal — it just allocates compute and shapes the candidate pool.

**New depth reached.** Per-query-type best-retriever selection without manual rules: e.g., the router learns "comparison-style intents → up-weight BetaE boxes" or "multi-hop tool-chain queries → up-weight GraphRAG community" purely from telemetry. This is the LTRR + RouterRetriever capability we currently lack.

**Noise it handles.** Router learns to down-weight a path that is chronically high-nonconformity for a given query type (e.g., agentic on simple lookups), reducing wasted reranker budget and reducing iter-14 abstain rate.

**Gaps that remain — be honest.** (a) Labeled (intent → best-retriever) data is scarce; iter-14 telemetry gives us positives only when |C|=1 *and* the rec was accepted, which is a small fraction of traffic. (b) Oracle MoR (best path picked retroactively) vs learned MoR is a known real gap — LTRR shows ~30-40% of the oracle's gain is typically left on the table. (c) Cold-start: until ~5K labeled tuples accumulate, the router will underperform RRF, so we must default to RRF and gate switchover on a held-out win-rate threshold. (d) Distribution shift: as the catalog grows, the router stales faster than the retrievers themselves — needs a freshness signal.

## Suggested next direction

**Online learning with regret minimization** (specifically: contextual bandit / EXP4-style aggregation over the 4 retriever paths, with iter-14 conformal acceptance as the reward signal). Why this and not the others:

- **Addresses the MoR gap directly.** The training-data scarcity above is *the* binding constraint on learned MoR. A bandit treats the router as an online policy that updates from every accepted/rejected recommendation, so we don't wait for a labeled batch — every iter-14 |C|=1 acceptance is a reward sample.
- **Closes the oracle-vs-learned gap.** Regret bounds give us a formal guarantee that as t→∞ we approach oracle MoR; offline supervised routers can't promise this.
- **Cold-start clean.** EXP4 with RRF-as-an-expert means the bandit *starts* at RRF performance and only deviates when evidence accumulates — exactly the safety property iter-15 needs.
- **Beats the alternatives for our case.** Agent distillation needs a strong teacher we don't have; federated/on-device personalization is premature pre-launch; multi-task instruction-tuned retriever is a path-level upgrade, not a routing upgrade.

Value-per-iter is *not* dropping — iter-14 unlocked calibrated signals and iter-15 turns them into a learned policy; iter-16 (online bandit) closes the loop. Continue.

## Sources

- [MoR (arXiv 2506.15862)](https://arxiv.org/abs/2506.15862)
- [RouterRetriever (arXiv 2409.02685)](https://arxiv.org/abs/2409.02685)
- [LTRR (arXiv 2506.13743)](https://arxiv.org/abs/2506.13743)
- [Adaptive-RAG (arXiv 2403.14403)](https://arxiv.org/abs/2403.14403)
- [Self-Route / RAG vs LC (arXiv 2407.16833)](https://arxiv.org/abs/2407.16833)
- [Reciprocal Rank Fusion (Cormack et al. SIGIR 2009)](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- [Inter-Cascade / online cascade deferral (arXiv 2509.22984)](https://arxiv.org/abs/2509.22984)
- [When Does Confidence-Based Cascade Deferral Suffice? (arXiv 2307.02764)](https://arxiv.org/abs/2307.02764)
