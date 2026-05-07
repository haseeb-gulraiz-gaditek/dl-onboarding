# Iter 2 — LLM intent / friction extraction layer

**Approach**: pre-encode LLM pass converts raw user signal → `{frictions, desired_capabilities, excluded_tools, workflow_edges, counterfactual_gaps}`; embed structured fields against tool descriptions; `excluded_tools` becomes a hard filter.

## Top 3 papers
- **HyDE (Gao 2022, arXiv 2212.10496)** — generate a hypothetical answer doc from the query, embed *that* and retrieve. Closes layperson↔vendor language gap; directly applicable to "I wish a tool existed that did X" counterfactuals.
- **Query2Doc (Wang 2023, arXiv 2303.07678)** — LLM-generated pseudo-doc concatenated with query before encoding; consistent BEIR/MS-MARCO gains; cheap, drop-in upgrade to dense retrieval.
- **Negation rewriting in product search (Guo, COLING 2025)** — explicit slot for excluded entities outperforms learned negation; validates Mesh's `excluded_tools` hard-filter design.

Honorable mentions: ILLUMINER (zero-shot LLM slot filling), Sun SIGIR 2024 (LLM intent-driven session rec), Yoon 2025 (HyDE knowledge-leakage caveat — gains may inflate on memorized corpora; Mesh's small obscure catalog reduces this risk but warrants own eval).

## Scores
- **depth = 7.0** — moves from topical to capability-claim depth. Structured fields capture workflow edges (Notion→Linear, weekly cadence) and counterfactual wishes as first-class signals. Still bag-of-fields cosine; doesn't capture paradigm/fit ("daily-note paradigm felt heavy") — that's qualitative.
- **noise = 7.5** — absorbs paraphrase of frictions, multi-entity workflows, hypotheticals, and negation. Structuring acts as denoiser. Residual: hallucinated capability claims if Sonnet over-extrapolates from sparse user input — needs grounded extraction prompts.
- **compose = 9.0** — pre-encoding sits cleanly under every downstream method. Rerankers, contrastive learning, GNNs, RAG all inherit the structured intent for free.
- **composite = 7.0·0.5 + 7.5·0.3 + 9.0·0.2 = 3.5 + 2.25 + 1.8 = 7.55**

## Verdict
**ADVANCE** (composite 7.55 ≥ 7.0). First substantive step beyond surface similarity. Locks in as a permanent stage in the pipeline.

## Gap left
**Paradigm/fit qualitative signal.** Tools fail users not because capability lists mismatch but because *paradigm* mismatches — Reflect's daily-note model, Notion's database-first model, Linear's keyboard-first model. Bag-of-fields cosine cannot represent "this user bounces off opinionated daily-note tools." Also: the structured fields cannot cleanly express *contrastive preferences* — what the user accepts vs rejects relative to siblings.

## Next direction
**Contrastive intent learning on `(user_intent, accepted_tool, rejected_tool)` triples.** Train a small projection head on top of frozen E5/BGE embeddings using triplet loss where positives are tools the user adopted and negatives are sibling tools they tried-and-bounced. This directly attacks the paradigm-fit gap because the negative is a *near-neighbor in capability space but rejected for paradigm reasons* — exactly the signal capability cosine cannot see. Fed by `excluded_tools` slots from iter 2 (negative signal is free). No click-volume or graph required. Composes additively on top of iter 2 without rework.
