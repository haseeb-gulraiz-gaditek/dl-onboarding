# Mesh Matching Algorithm — Synthesis (Karpathy-loop final report)

**Loop**: 12 iterations, ~85 minutes elapsed of 120-minute budget. Saturation reached after iter 11. 11 advanced, 1 discarded as standalone (kept as substrate). All raw research and per-iter scoring in `iterations/` and `log.md`.

---

## TL;DR — V1 Final Recommendation

**Pipeline** = `Iter 2 → Iter 5 → Iter 12`

1. **Iter 2 — LLM intent extraction.** Sonnet pre-pass converts raw user signal (workflows, frictions, tool history, counterfactual wishes) into a structured object: `{frictions, desired_capabilities, excluded_tools, workflow_edges, counterfactual_gaps}`.
2. **Iter 5 — ColBERT per-field MaxSim retrieval w/ negative MaxSim hard exclusion.** Each intent slot is a separate vector field; top-50 candidates retrieved with mFAR adaptive weights; `excluded_tools` enforces hard exclusion at retrieval (not rerank).
3. **Iter 12 — Long-context Sonnet (200k) listwise rerank.** Full chat history + iter-2 intent + iter-5 top-50 + iter-6 KG triples (when available) packed into a single prompt; Sonnet returns final ranked top-5 with reasoning trace. Shuffled-bootstrap (3× passes with permuted candidate order) mitigates Lost-in-the-Middle.

**Cost** ~$0.03–0.05/query · **Latency** ~1–2s · **Zero bootstrap data required** · Depth no embedding-only stack reaches.

---

## Why this combination, not the others

The rubric (depth 50% · noise 30% · compose 20%) honestly ranked iter 8 (agentic, 8.45) and iter 12 (in-context, 8.10) at the top — but agentic retrieval costs seconds-per-query and only fires on the ~15% compositional subset. **Iter 12 carries the V1 trunk**; iter 8 stays as the slow path for queries iter 12 can't resolve confidently.

The lower-scoring iters (3, 5, 11) are kept because of **composability** — they're substrate the upstream stages need. Iter 1 (pure semantic) was discarded as standalone but its embeddings power iter 5.

The deepest-on-paper method (iter 9, causal uplift) is **deferred to V2/V3** because Mesh has zero logged outcomes at launch. Honest scoring penalised noise (6.0) and compose (6.5) accordingly.

---

## Versioned roadmap

### V1 (launch, weeks 0–4)
**Active:** iter 2 → iter 5 → iter 12 (the trunk above).
**Why minimal:** zero bootstrap data, deployable in days, depth high enough that the concierge feels personal from day one.
**Catalog:** ~300 manually curated tools (per `basic_idea.md` cold-start plan).

### V1.5 (weeks 4–12, once intent corpus + KG manifests are in place)
**Add:**
- **Iter 4 — Cross-encoder rerank with reasoning trace** as the cost-sensitive fallback path (Haiku-class). Use when budget per query is tight.
- **Iter 6 — KG embeddings (ComplEx/RotatE)** on tool-capability-integration KG bootstrapped from Zapier/Pipedream/native-API manifests. Triple scores fuse into iter-12 prompt as additional evidence.
- **Iter 11 — BetaE / Query2Box neuro-symbolic operators** as the millisecond-fast path for purely compositional queries (∧∨¬∃ over set-typed intent slots). Falls back to iter 12 when box answer set is empty.
- **Iter 8 — Agentic retrieval** as the slow-path for queries that need symbolic reasoning, quantifiers, multi-hop chains, or counterfactual enumeration. Adaptive-RAG classifier routes ~15% of complex queries here.

**Activation thresholds:**
- KG (iter 6): when ≥200 tools have integration manifests scraped → train ComplEx + KEPLER text-init.
- Boxes (iter 11): when ≥1k logged compositional intent objects accumulate → train BetaE.
- Agent (iter 8): immediately if engineering bandwidth allows; high cost-per-query is acceptable on 15% slice.

### V2 (months 3–9, once user-tool interactions accumulate)
**Add:**
- **Iter 3 — Contrastive intent head** trained on ≥300 (intent, accepted, rejected) triples extracted from concierge conversations. Replaces the projection layer above iter-5 retrieval; tightens paradigm-fit.
- **Iter 7 — CompGCN tripartite heterograph** (User × Tool × WorkflowConcept) warm-started from iter-6 weights. Multi-aspect intent + multi-hop reasoning + collaborative filtering emerge naturally. Activates when ≥500 user-tool interaction edges exist.
- **Iter 10 — Epinet/Thompson-sampling exploration** wraps iter-12 ranking output. Epinet gives cheap epistemic uncertainty; samples produce propensity-tagged logs needed for iter 9. ~5–10% of recs become exploratory.

### V3 (months 9–18, ≥5k logged adoptions)
**Add:**
- **Iter 9 — Causal uplift τ(u,t) = P(adopt|rec) − P(adopt|no-rec).** DragonNet or X-learner on iter-7 embeddings; conformal abstention when sparse. Re-ranks iter-12 candidates by counterfactual lift instead of match likelihood. The deepest-possible recommendation criterion: not "matches user" but "would change user's behavior."

---

## Composition graph (text)

```
Raw user signal
   ↓ iter 2: LLM intent extraction
Structured intent {frictions, capabilities, excluded_tools, workflow_edges, counterfactuals}
   ↓ iter 5: ColBERT per-field MaxSim + negative MaxSim (V1.5+: replaces iter 3 single-vector)
   ↓ iter 6 (V1.5): KG triple scoring → fuse via learned gate
   ↓ iter 7 (V2): CompGCN message passing → user/tool embeddings
   ↓ iter 11 (V1.5): box ops fast path (compositional queries only)
top-50 candidates + evidence bundle
   ↓ iter 4 (V1.5 cost-fallback) or iter 12 (V1 trunk): rerank
   ↓ iter 8 (V1.5): agentic slow path for ~15% complex queries
   ↓ iter 10 (V2): Thompson sampling exploration → logs propensity tuples
top-5 ranked + reasoning trace
   ↓ iter 9 (V3): re-rank by causal uplift τ(u,t)
final recommendations to concierge
```

---

## Honest open risks

1. **iter-2 hallucination** — LLM extraction may invent capabilities the user didn't claim. Mitigation: ground extraction prompts; cite raw-text quotes per slot; user can correct in concierge.
2. **iter-5/12 catalog drift** — when tools change descriptions, embeddings stale. Mitigation: nightly re-embed; track description-change deltas.
3. **iter-12 cost at scale** — $0.03–0.05/query × frequent re-recs hurts unit economics. Mitigation: cache by intent fingerprint; iter-4 fallback path; revisit when concierge usage data lands.
4. **iter-9 data prerequisite** — uplift requires explicit randomization (iter 10), not observational data. Skipping iter 10 means iter 9 never activates.
5. **Pipeline complexity at V2+** — 8 active stages = real engineering surface. Stage-by-stage A/B with shadow ranking before promotion.

---

## What was deferred / discarded

- **Iter 1 (pure semantic, 5.85)** — discarded as standalone; kept as embedding substrate for iter 5.
- **Iter 9 (causal uplift, 7.35)** — deferred to V3 (data prerequisite).
- **Not researched, possibly worth a future loop:** GraphRAG, mixture-of-retrievers ensembles, distillation of iter-8 agent into a smaller model, online learning with regret minimisation (full RL not bandit), conformal prediction layer for abstention, federated personalization (privacy-preserving on-device intent embeddings).

---

## Deepest layer reached (vs the user's original bar)

User asked for an algorithm that goes "deeper than basic similarity" with "graph algorithm or graph db or combine a couple of AI/ML algorithms" so that "any noise to relevant feature match" works.

What this loop produced:
- Symbolic reasoning over set-typed intent slots (iter 8, iter 11).
- Typed directed-edge KG with multi-hop composition (iter 6).
- Heterograph message passing for collaborative filtering (iter 7).
- Long-context history-aware personalization (iter 12).
- Counterfactual quantification (iter 9, V3-deferred).
- Bootstrap exploration (iter 10).

The match goes from "tokens overlap" (iter 1) → "structured capability claims overlap" (iter 2+5) → "typed graph triples agree" (iter 6) → "user-similar paths converge" (iter 7) → "symbolic conditions hold" (iter 8/11) → "would change behavior" (iter 9). Six layers of depth, each composed onto the prior.

---

*Loop terminated at iter 12 by saturation signal (iters 8–12 all scored 7.45–8.45). Resumable: bump `budget_seconds` in `state.yaml` and run `/loop` again with a refined direction (e.g. GraphRAG, mixture-of-retrievers, or distillation).*

---

## Resumed-loop addendum (iters 13–16)

User resumed the loop. Four additional control/routing layers added above the iter 1–12 algorithm stack — none change the V1 trunk; all slot into V1.5/V2/V3.

| # | Approach | Composite | Slot |
|---|----------|----------:|------|
| 13 | GraphRAG community retrieval (Leiden + ArchRAG + HippoRAG-2) | 7.35 | V1.5 slow-path complement to iter 11 |
| 14 | Conformal prediction abstention (multi-model min-score + ACI) | 7.50 | V2 honest-concierge primitive (≥500 calibration pairs) |
| 15 | Mixture-of-retrievers (MoR) with learned routing | 7.45 | V2 routing layer (RRF cold-start default) |
| 16 | Contextual bandit (EXP4/Thompson) online routing | 7.60 | V2/V3 closed loop (warm-start via iter-9 IPS replay) |

**Score curve (full 16 iters)**: 5.85 → 7.55 → 7.30 → 7.60 → 7.25 → 7.75 → 7.75 → **8.45** → 7.35 → 7.45 → 7.50 → 8.10 → 7.35 → 7.50 → 7.45 → 7.60.

**Updated V2 stack** (replaces the simpler V2 in the original synthesis):

```
V1 trunk (unchanged):  iter 2 → iter 5 → iter 12
V1.5 adds:             iter 4 (CE rerank cost-fallback)
                       iter 6 (KG embeddings)
                       iter 8 (agentic slow path, ~15% queries)
                       iter 11 (BetaE/Query2Box fast path)
                       iter 13 (GraphRAG slow-path complement)
V2 adds (closed-loop control + learning):
                       iter 3 (contrastive head)
                       iter 7 (CompGCN heterograph)
                       iter 10 (Thompson-sampling exploration → propensity logs)
                       iter 14 (conformal abstention; ≥500 calibration pairs)
                       iter 15 (MoR learned routing supervised by iter-14)
                       iter 16 (EXP4/Thompson contextual bandit; reward = adoption)
V3 adds:               iter 9 (causal uplift τ(u,t); needs ≥5k logged adoptions)
                       federated/on-device personalization (unresearched, next direction)
```

**Why the resumed run did not change V1**: the iter 1–12 trunk already covers the matching-depth axis. Iters 13–16 add control, calibration, routing, and online learning — orthogonal to depth. They make the stack *self-improving and honest*, not deeper. That's why their composite scores cluster at 7.35–7.60 instead of pushing past iter 8's 8.45.

**Open frontier (deferred from this loop)**: federated/on-device per-user personalization with shared prior — the iter-16 agent flagged it as the natural next direction; aligns with Mesh constitution principle "users own their concierge profile." Worth a future loop.

*Resumed loop terminated at iter 16 by user request. State: completed. 16 total iterations, 14 advanced, 1 deferred (iter 9), 1 discarded (iter 1, kept as substrate).*

---

## Iter-1 addendum: post-two-tower successors (genAI era)

A follow-up survey of 2023–2025 advancements that succeed/extend the classic two-tower. **Verdict**: iter-1's dual-encoder substrate is **not obsolete**. The 2025 critique literature confirms generative retrieval (TIGER/OneRec/HSTU) has not universally beaten dense retrieval — and Mesh's 300-tool catalog is well below the scale where it would.

**Upgrade path = composition, not replacement:**
- **V1 add**: KAR-style LLM-augmented features on the tool side (mirrors iter-2 user-side intent extraction). One Sonnet call per tool at index time, cached. No inference-time cost.
- **V1.5 add**: RLMRec-style cross-view contrastive alignment when iter-3 retrains. Pulls collaborative embedding toward LLM-generated text-profile embedding via mutual-information maximization.
- **V2+ defer**: TIGER/LIGER semantic-ID retrieval until catalog ≥3k tools.
- **V3+ defer**: foundation-model thinking (PinFM/HLLM/Netflix FM) when Mesh expands beyond single concierge surface.

With KAR + RLMRec wrappers, iter-1 re-scores **depth 6.5 / noise 7.5 / compose 9.0 = composite 7.20** — would have advanced, not been discarded.

Full 11-paper survey: `scratch/algo-research/iterations/iter-1-addendum-raw.md`. 1-page summary: `iter-1-addendum.md`.
