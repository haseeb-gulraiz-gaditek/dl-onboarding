# Iter 12 — In-Context Recommendation with Long-Context LLMs

**Question:** at ~300 tools, can we throw the entire catalog + the user's full chat history into a 1M-context Sonnet prompt and get a ranking in one pass — collapsing iters 2–11 into a single LLM call?

## Papers

1. **Lost in the Middle: How Language Models Use Long Contexts** (Liu et al., TACL 2024). U-shaped recall curve: items at the start/end of long prompts are recalled reliably, items in the middle are forgotten. Direct hit on a 300-tool prompt — middle-of-list tools will be systematically under-ranked unless we shuffle/bootstrap.

2. **Can Long-Context LMs Subsume Retrieval, RAG, SQL, and More? (LOFT)** (Lee et al., 2024, arXiv 2406.13121). DeepMind benchmark up to 1M tokens; finds LCLMs rival dedicated retrievers and RAG pipelines on retrieval/RAG tasks but degrade on compositional reasoning. Strongly supports the "skip the pipeline" hypothesis at our catalog size, but warns that multi-hop logic (paradigm-aware filtering, conditional reasoning) is where LCLMs still trail.

3. **Long Context vs. RAG for LLMs: An Evaluation and Revisits** (Li et al., 2025, arXiv 2501.01880). LC beats RAG on Wikipedia QA; chunk-RAG underperforms; summarization-style retrieval is comparable. Suggests for Mesh's V1.5, "retrieve top-k then long-context rerank" is a sweet spot rather than pure-LC or pure-RAG.

4. **Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach (Self-Route)** (Li & Qiu et al., 2024, arXiv 2407.16833). Quantifies the cost gap: LC wins on quality when "resourced sufficiently" but RAG is dramatically cheaper. Proposes routing easy queries to RAG and hard ones to LC — a useful pattern for Mesh given that most queries probably don't need 1M tokens.

5. **LongBench / LongBench v2** (Bai et al., ACL 2024, arXiv 2308.14508). Multi-task long-context benchmark; even strong commercial models degrade on truly long inputs and on tasks requiring deep reasoning. Tells us that 1M-token Sonnet won't match its short-context quality — degradation is real even when "needle" recall is near-perfect.

6. **Gemini 1.5 Technical Report** (Reid et al., 2024, arXiv 2403.05530). >99.7% needle recall up to 1M tokens, holding to 10M in text. Provides the optimistic ceiling: at 300 tools (~50–100k tokens), recall is essentially saturated. Caveat: NIAH is a single-fact retrieval task, not a 300-way ranking with personalization.

7. **Large Language Models are Zero-Shot Rankers for Recommender Systems** (Hou et al., 2023, arXiv 2305.08845). LLMs rank well zero-shot but (a) struggle to use the *order* of user history, (b) are biased by item popularity and position in the prompt. Mitigation: bootstrap by shuffling candidate order and aggregating. Direct V1 implementation guide for our long-context ranker.

8. **LlamaRec: Two-Stage Recommendation using LLMs for Ranking** (Yue et al., PGAI@CIKM 2023, arXiv 2311.02089). Small sequential retriever → LLM verbalizer-based reranker over candidates. Empirically validates the "retrieve-then-LLM-rerank" pattern that maps to our V1.5 hybrid (iter-5 retrieves top-50, Sonnet reranks).

9. **Real-Time Personalization for LLM-based Recommendation with Customized ICL (RecICL)** (Hu et al., 2024, arXiv 2410.23136). Shows recommendation tuning *destroys* a model's ICL ability unless the tuning is structured as ICL examples. Argument for staying with vanilla Sonnet (no fine-tune) for V1 — we keep ICL strength for free.

10. **RankGPT: Zero-Shot Listwise Document Reranking with a LLM** (Sun et al., EMNLP 2023, arXiv 2305.02156). Listwise prompting + sliding-window strategy beats pointwise. With 300 tools we may not need the sliding window, but listwise reasoning is the prompt format of choice.

## Synthesis — what in-context Sonnet would do for Mesh

**V1 minimal:** stuff the system prompt with all ~300 tool cards (title + 1-line description + tags ≈ 150 tok each → ~45k tokens, well inside Sonnet's 200k window, no need for 1M); inject the user's structured intent (iter 2) plus the last ~30 chat turns; ask for a listwise ranking with reasoning. No retrieval, no embeddings, no GNN. Re-personalizes at every query for free because history is in-prompt.

**V1.5 hybrid:** ColBERT (iter 5) retrieves top-50; Sonnet reranks with full chat history + KG triples (iter 6) + box-op constraints (iter 11) attached. This matches LlamaRec / Self-Route patterns and respects Lost-in-the-Middle (50 items < 300, all near prompt edges).

**Depth reached:** history-aware (full chat is in-context), paradigm-aware (Sonnet reads tone/jargon directly), conditional ("if pricing matters, prefer X"). LLM can self-filter hallucinations because the catalog is *grounded* in the prompt — it cannot invent a tool not listed. This is qualitatively beyond iter 8 (agentic with tool calls): one round-trip, no tool-call planning loop.

**Honest gaps:** (a) Cost — at 200k tokens / query × $3/M-input, ≈ $0.6/query for V1 minimal, NOT $0.01–0.05 as initially hoped (prompt caching brings repeated runs to ~$0.06, still 10× iter 5). V1.5 hybrid (top-50, ~10k tokens) lands at ~$0.03–0.05. (b) Latency — 5–15s for full-catalog prompt; ~1–2s for top-50 rerank. (c) Lost-in-the-Middle — Hou 2023 confirms position bias is real for recommendation specifically; mitigate by shuffled-bootstrap (3 passes, aggregate) but that triples cost. (d) No collaborative signal — pure in-context can't learn "users like you also picked Y" without that signal embedded in the prompt; we'd need iter 7 GNN signals as side-input or warm-start once usage data exists.

## Final recommendation — V1 minimal viable algorithm

**Iter 2 (intent extraction) → Iter 5 (ColBERT top-50) → Iter 12 (Sonnet long-context listwise rerank with full chat history + KG triples).**

Rationale: iter 2 turns chat into structured intent so the retriever has clean queries; iter 5 keeps cost/latency tractable (top-50 ≈ $0.03–0.05 and 1–2s, vs. $0.6 and 10s for full catalog); iter 12 delivers the personalization depth (full history, paradigm-aware, conditional reasoning) that no embedding-only stack can match — and it works from day one with zero bootstrap data, unlike iter 7 (GNN, needs interaction graph) or iter 9 (CE rerank, needs labeled pairs). Iters 6/11 (KG, neuro-symbolic) attach as prompt context once the KG is populated; iters 4/8/10 are deferred to V2 when usage telemetry justifies them.

## Sources

- [Lost in the Middle (arXiv 2307.03172)](https://arxiv.org/abs/2307.03172)
- [LOFT — Can LCLMs Subsume Retrieval, RAG, SQL? (arXiv 2406.13121)](https://arxiv.org/abs/2406.13121)
- [Long Context vs. RAG for LLMs (arXiv 2501.01880)](https://arxiv.org/abs/2501.01880)
- [RAG or Long-Context LLMs? Self-Route (arXiv 2407.16833)](https://arxiv.org/abs/2407.16833)
- [LongBench (arXiv 2308.14508)](https://arxiv.org/abs/2308.14508)
- [Gemini 1.5 Technical Report (arXiv 2403.05530)](https://arxiv.org/abs/2403.05530)
- [LLMs are Zero-Shot Rankers for RecSys — Hou 2023 (arXiv 2305.08845)](https://arxiv.org/abs/2305.08845)
- [LlamaRec (arXiv 2311.02089)](https://arxiv.org/abs/2311.02089)
- [RecICL — Real-Time Personalization with ICL (arXiv 2410.23136)](https://arxiv.org/abs/2410.23136)
- [RankGPT (arXiv 2305.02156)](https://arxiv.org/abs/2305.02156)
- [P5: Recommendation as Language Processing (arXiv 2203.13366)](https://arxiv.org/abs/2203.13366)
- [Evaluating Position Bias in LLM Recommendations (arXiv 2508.02020)](https://arxiv.org/abs/2508.02020)
