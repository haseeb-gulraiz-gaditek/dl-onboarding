# Iter 6 — Knowledge Graph embeddings (RotatE / ComplEx) on tool-capability-integration KG

**Approach**: build small KG (~300 tools, ~50 capabilities, ~30 data types, few-thousand typed edges from Zapier/Pipedream/native API manifests). Train ComplEx primary, RotatE parallel. KEPLER-style text-init from tool descriptions to compensate for small-KG regime. LLM-extracted `workflow_edges` become query-time triples scored against KG embeddings; fuse with iter 5 text MaxSim via learned gate.

## Top 3 papers
- **RotatE (Sun 2019, arXiv 1902.10197)** — relations as complex rotations; uniquely captures symmetry / antisymmetry / composition simultaneously. `exports_to` (antisymmetric) + `syncs_with` (symmetric) + chain composition (Slack→Notion→Linear) are exactly its strengths.
- **ComplEx (Trouillon 2016, arXiv 1606.06357)** — complex bilinear scoring; SOTA-equivalent on small KGs with 1/2 the parameters of RotatE; default starting point for ~3k-edge regime.
- **KEPLER (Wang 2021, arXiv 1911.06136)** — joint text-language-model and KG embedding training; entity vectors initialized from descriptions. Critical for Mesh's small KG: text init carries 80%+ of zero-shot signal; pure KG training would underfit at this scale.

Honorable: TransE (foundational), QuatE (quaternion variant), TNTComplEx (temporal extension — could capture "weekly Tuesday 4pm"), StarE (N-ary facts for `(Notion, exports_to, Linear, format=CSV, cadence=weekly)`), Query2box (complex KG queries with intersection/union — mid-term option), GreaseLM (KG+LM fusion).

## Scores
- **depth = 8.0** — first stage to natively represent typed directed edges. `(Notion, exports_to, Linear)` is a first-class learned triple, not co-occurrence. RotatE composition handles multi-hop chains (Slack→Notion→Linear). Highest depth lift in the loop so far. Honest cap: triples are single-aspect — user intent is multi-aspect (frictions × capabilities × workflow); KG embedding doesn't natively reason across aspects without extra plumbing.
- **noise = 7.5** — KG completion implicitly imputes missing edges via embedding manifold; KEPLER text-init absorbs lexical noise from descriptions. Closed-world assumption is the real risk: integration manifests are radically incomplete, so absent edges become spurious negatives during training. Mitigation: PU-learning loss or treat unobserved as "unknown" with reduced gradient weight.
- **compose = 7.5** — fuses with iter 5 via learned scalar gate. **Critical compose property**: CompGCN's composition operator IS the TransE/ComplEx/RotatE function — so iter 6 weights warm-start iter 7's GNN, no rework. Slight cost: KG ingestion + refresh pipeline (when tools change integrations).
- **composite = 8.0·0.5 + 7.5·0.3 + 7.5·0.2 = 4.0 + 2.25 + 1.5 = 7.75**

## Verdict
**ADVANCE** (composite 7.75 ≥ 7.0) — highest depth score in the loop. Locks in as fifth stage. Triple-scoring head fuses with iter 5 retrieval; iter 4 CE rerank can ingest top KG triples as additional context.

## Gap left
1. **Multi-aspect user intent.** Triple scoring is single-aspect (one (s,r,o) at a time). User intent has multiple slots that need joint reasoning over the graph, not independent triple lookups.
2. **Closed-world assumption.** Missing edges in manifests = false negatives during training; biases the embedding space.
3. **No user-side message passing.** Users themselves should be nodes in a graph (user→friction→tool→capability→tool), enabling collaborative-filtering-style propagation that current scheme can't do.

## Next direction
**CompGCN / R-GCN over a tripartite heterograph (user, tool, workflow_concept) warm-started from iter 6 weights.** CompGCN's composition operator is exactly TransE/ComplEx/RotatE, so iter 6 weights initialize iter 7 — research is reusable, not redone. Multi-aspect intent flows via message passing across user→friction→tool→capability paths; collaborative filtering emerges from user-tool edges; multi-hop reasoning is depth-of-network. Composes with iter 5 (text features inject as node features) and iter 4 (rerank uses GNN-augmented embeddings).
