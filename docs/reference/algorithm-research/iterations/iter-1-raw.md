# Iteration 1 — Baseline Semantic Matching for Mesh

_Scope: pure embedding + cosine similarity. No rerankers, no hybrid, no graphs._

## Papers

1. **Sentence-BERT (Reimers & Gurevych, 2019)** — Siamese fine-tuning of BERT produces fixed-size sentence vectors comparable by cosine, collapsing 65-hour pair scoring to ~5s. Establishes the *core mechanic* Mesh would use, but trained on NLI/STS — generic semantic similarity, not workflow-friction-to-tool-capability matching. Noise tolerance is purely whatever BERT learned; no retrieval-grade discrimination.
   https://arxiv.org/abs/1908.10084

2. **DPR — Dense Passage Retrieval (Karpukhin et al., EMNLP 2020)** — Two-tower BERT dual encoders, separately encoding short queries and longer passages, beat BM25 by 9–19% top-20 accuracy on open-domain QA. Validates the *asymmetric two-tower* shape Mesh needs (short noisy user signal vs. longer tool description) and shows in-batch negatives suffice to learn discriminative spaces — but only when the training distribution matches the test distribution.
   https://arxiv.org/abs/2004.04906

3. **E5 — Text Embeddings by Weakly-Supervised Contrastive Pre-training (Wang et al., 2022)** — First open embedding to beat BM25 zero-shot on BEIR; trained on web pairs (Reddit post→comment, SE Q→A, Wikipedia, scientific). The asymmetric `query:` / `passage:` prefix encodes the same "short request → longer artifact" structure Mesh has. Strongest off-the-shelf candidate for v1, but its training pairs are *expository* (questions, comments) — not "I copy between Notion and Linear at 4pm."
   https://arxiv.org/abs/2212.03533

4. **GTE — General Text Embeddings via Multi-stage Contrastive Learning (Li et al., 2023)** — 110M-param model beating OpenAI's text-embedding API on MTEB by combining unsupervised pretraining over diverse pair sources with supervised fine-tuning. Confirms small dense models can be production-grade for symmetric *and* asymmetric tasks. Tells us Mesh doesn't need a giant model — it needs *the right pairs*.
   https://arxiv.org/abs/2308.03281

5. **C-Pack / BGE (Xiao et al., SIGIR 2024)** — Releases the BGE family plus C-MTP training corpus and C-MTEB benchmark; BGE-large tops MTEB English at release. Practical takeaway for Mesh: BGE / E5 / GTE are interchangeable for v1 baseline; differentiation comes from domain fine-tuning, not base model selection.
   https://arxiv.org/abs/2309.07597

6. **Sampling-Bias-Corrected Two-Tower for YouTube (Yi et al., RecSys 2019)** — Production two-tower retrieval over tens of millions of items; introduces frequency-correction for in-batch softmax to avoid popular items dominating. Most relevant *recommender* paper here: same shape as Mesh (user tower vs. item tower, cosine retrieval), and it surfaces a noise mode we will hit — popular tools (Notion, ChatGPT) will swallow the neighborhood unless we correct sampling.
   https://research.google/pubs/sampling-bias-corrected-neural-modeling-for-large-corpus-item-recommendations/

7. **MTEB (Muennighoff et al., EACL 2023)** — Benchmarks 33 embedding models across 58 datasets / 8 tasks; headline finding: *no single embedding wins everywhere.* STS-strong models can be retrieval-weak. For Mesh this means: we cannot pick an embedding by leaderboard rank alone — we need our own eval set of (user-profile, correct-tool) pairs.
   https://arxiv.org/abs/2210.07316

## Synthesis — what pure semantic matching buys Mesh, and what it doesn't

A two-tower setup (E5 or BGE on the user side and tool side, cosine-NN over ~300 tools) gets us to **topical / capability-level matching** cheaply. If a user writes "I take messy meeting notes and need to turn them into Jira tickets," cosine similarity will reliably surface tools whose descriptions contain "meeting transcription," "task extraction," or "Jira integration." It absorbs **lexical noise well** (synonyms, paraphrase, casing, misspellings) and **handles short user signals** that BM25 would tokenize into nothing. With 300 tools the index is trivial — a single matrix multiply per query.

What it does **not** reach is the depth Mesh actually promises. Five concrete failure modes:

- **Intent-vs-description gap.** Tool pages describe *features* ("AI-powered note-taking with smart summaries"); users describe *frictions* ("I lose track of what I promised in standup"). Embeddings match surface vocabulary, not the implied capability bridge. A tool whose page never says "standup" loses, even if it solves the friction.
- **Workflow compositionality.** "Notion → Linear every Tuesday at 4pm" is a 3-entity, time-conditioned, multi-hop request. A single dense vector flattens this into a topical centroid; the time signal and the directional Notion→Linear edge are gone.
- **Tried-and-bounced negatives.** "I tried Reflect, didn't stick because the daily-note paradigm felt heavy" is *negative* signal embedded inside positive-looking text. Cosine has no native way to *exclude* tools resembling Reflect — they will rank highly because the user wrote about them.
- **Counterfactual wishes.** "I wish a tool existed that did X" looks superficially like a description of a tool that does X — embeddings will return the closest existing tool with no signal that the user's hypothesis is *that no such tool exists yet.*
- **Popularity collapse.** Per Yi et al., two-tower nearest-neighbor over a skewed catalog (Notion, ChatGPT, Linear are over-described in the corpus) drifts toward the popular center unless sampling-corrected.

Net: baseline semantic matching reaches **surface/topical depth at workflow vocabulary**, absorbs **lexical noise**, but cannot disentangle intent from description, cannot honor exclusions, and cannot reason over multi-entity workflows.

## Suggested next direction

**Add an LLM-driven intent / friction extraction layer between the user's raw signal and the embedding tower.** Before encoding, run a Claude/Sonnet pass that converts the messy user profile into a structured object: `{frictions: [...], desired_capabilities: [...], excluded_tools: [...], workflow_edges: [(Notion, Linear, weekly), ...]}`. Embed the *capabilities* field (not the raw text) against tool descriptions; use the `excluded_tools` field as a hard filter; surface `workflow_edges` to a future hybrid layer.

Why this over a cross-encoder rerank or hybrid sparse+dense: the bottleneck for Mesh is **not retrieval precision over a 300-item catalog** — top-20 recall will already be fine. The bottleneck is **the gap between layperson friction-language and vendor capability-language**. A reranker sharpens an already-relevant list; intent extraction *changes what we embed*, which is the actual root cause. It's also cheap (one LLM call per profile, cached) and composes cleanly with whatever we add next (rerankers, graphs, KGs).
