# Iter 1 — Addendum: post-two-tower successors (genAI era, 2023–2025)

**Question revisited**: now that we're in the LLM era, is iter-1's dual-encoder substrate obsolete? **No.** The 2025 critique literature (Zhang et al. arXiv 2509.22116) confirms generative retrieval has *not* universally beaten dense retrieval. Mesh's 300-tool catalog is well below the scale where TIGER/OneRec start paying off. Upgrade path = **composition, not replacement**.

## 5-category taxonomy of successors

| Category | Defining move | Strongest 2024–25 candidate | Mesh fit |
|---|---|---|---|
| **Generative retrieval (semantic IDs)** | Items become RQ-VAE codeword tuples; retrieval = beam search over learned codebook | **TIGER** (NeurIPS 2023) → **OneRec** (Kuaishou 2025) | Defer — codebooks need ≥3k items to learn meaningful hierarchies |
| **Decoder-only single-model** | One transformer ingests user-action stream, generates next item; no encoders | **HSTU** (Meta ICML 2024) | Skip — Mesh has intake form, not behavior stream |
| **Foundation models** | Shared backbone over user activity, fine-tuned per surface | **PinFM** (2025) / **HLLM** (ByteDance 2024) / **Netflix FM** (2025) | Right philosophy, V3+ when surfaces multiply |
| **LLM-augmented dual encoder** | Keep tower, enrich inputs with LLM-distilled features | **KAR** (+7% online at Huawei) / **RLMRec** (WWW 2024) | **Highest leverage today** — composes with iter 1+2+3 |
| **Hybrid / critique** | Combine paradigms; question generative dominance | **LIGER** / Zhang 2025 | Validates keeping iter-1 as substrate |

## Top 3 architectures Mesh should consider

### 1. KAR-style LLM-augmented dual encoder (recommended primary)
Keep E5/BGE. Add offline Sonnet pass (cached per tool) generating structured factual knowledge — capabilities, integration partners, frictions-this-solves, ICP fit, tried-and-bounced reasons. Hybrid-expert MLP adapter projects LLM features into tower input space. **Closes iter-1 gap #1 (intent-vs-description) structurally** — vendor features get rewritten as frictions before embedding. Composes with iter 2 (user side already has this), iter 3 (contrastive head), iter 4/5/6. Cost: ~$0.50 one-time per 300 tools, no inference-time LLM call.

### 2. RLMRec-style cross-view contrastive alignment (recommended for iter-3 retraining)
When iter-3 retrains, add second contrastive loss pulling the collaborative embedding toward an LLM-generated text-profile embedding for the same tool/user. MI maximization between views, no inference-time LLM. Smooths cold-start manifold; pushes embedding geometry toward semantic coherence vs co-occurrence. Cost: ~2× contrastive training compute. Risk: noisy LLM profiles can drag the space — needs ablation gate.

### 3. Semantic-ID hybrid (LIGER-style) — defer
RQ-VAE tool-IDs (3-tuple coarse→fine) for hierarchical taxonomy + beam-search candidates reranked by dense retrieval. Native cold-start, automatically-learned taxonomy the concierge could name ("you're in cluster X"). **Defer until catalog ≥3k tools.** At 300 tools the codebook collapses to trivial buckets.

## Score (revisits iter 1 with addendum lens)

| Axis | Original | With KAR+RLMRec | Why |
|---|---:|---:|---|
| depth | 4.5 | **6.5** | LLM-distilled features bridge friction↔feature; alignment regularizes for semantic coherence |
| noise | 6.0 | **7.5** | Cross-view alignment denoises embedding space; LLM-generated capability claims absorb paraphrase noise |
| compose | 9.0 | **9.0** | unchanged — substrate role |
| **composite** | **5.85** | **7.20** | crosses advance threshold |

## Verdict update
**Iter 1 is not obsolete.** With KAR+RLMRec wrappers, the dual-encoder substrate scores 7.20 — would have *advanced* not discarded. Pure generative retrieval (TIGER/OneRec/HSTU) deferred to V2+ when scale/behavior justify it.

## Slot in Mesh roadmap

- **V1**: keep iter-1 baseline as iter-5's substrate; layer **KAR-style LLM-augmented features** as a tool-side enrichment pass (mirrors iter-2 user-side intent extraction). Costs ~$0.50 one-time per refresh, no serving cost.
- **V1.5**: when iter-3 trains, add **RLMRec cross-view alignment** as a regularizer.
- **V2+**: monitor catalog growth; revisit **TIGER/LIGER** when Mesh crosses ~3k tools.
- **V3+**: foundation-model thinking when Mesh expands beyond single concierge surface (alerts, swap-recs, founder-side discovery).

Raw research with all 11 papers + sources: `iter-1-addendum-raw.md`.
