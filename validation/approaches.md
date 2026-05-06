# Two recommendation approaches — refined spec

Both approaches share the same input (4-question onboarding) and same output (live-narrowing tool set: 300 → 150 → 100 → 50 → 10). They differ in **how they store and query relations between tools.**

---

## Shared structure

### Pipeline (both approaches)

```
Q1 answered  →  derive feature set 1  →  filter 300 → 150
Q2 answered  →  + feature set 2       →  filter 150 → 100
Q3 answered  →  + feature set 3       →  filter 100 →  50
Q4 answered  →  + feature set 4       →  filter  50 →  10
```

Each filter step is **soft** (re-score every tool, take top-K) — not hard cuts. A tool that drops out of top-150 after Q1 can come back if Q2 strongly favors it.

### Live update mechanics

After each question:
1. Append derived features to user profile
2. Re-score all 300 tools
3. Sort, take top-K for current step
4. Push to UI: "Here are the 150 tools matching what we know so far"

### Feature taxonomy (both approaches use this)

Six feature dimensions — each tool has a tagged value, each user gets one inferred from answers:

| Dim | Source question | Example values |
|---|---|---|
| `industry` | Q1 industry | Finance · Software · Healthcare · ... |
| `role` | Q1 title + level | "Senior Audit Manager", "Backend Eng L5", "Family Med Attending" |
| `stack` | Q2 tools | {Excel, Outlook, ...} → integration constraints |
| `task_shape` | Q3 scenario | long-cycle vs short-cycle · producer vs reviewer · multi-stage vs reactive |
| `paradigm` | Q4 day-shape + Q2 absence/presence of AI | in-flow vs async · morning-deep vs reactive · AI-mature vs AI-naive |
| `setup_tolerance` | derived from level + AI maturity | <2 min · ~10 min · willing to customize |

Each tool in the 300-tool catalog gets a **feature record**:

```yaml
tool: Granola
industry: [software, marketing, sales, consulting, generic]
role: [PM, founder, sales, anyone-with-meetings]
stack_integrations: [Linear, Notion, Slack, Jira]
task_shape: short-cycle, capture-then-export
paradigm: ambient, in-meeting
setup_tolerance: <2 min
capabilities: [meeting-transcription, task-extraction, export-to-PM-tool]
excluded_paradigms: [daily-note, manual-tagging]
maturity_required: low
```

### Score per tool

```
score(user, tool) = w_industry * sim(user.industry, tool.industry)
                  + w_role     * sim(user.role,     tool.role)
                  + w_stack    * jaccard(user.stack, tool.stack)
                  + w_task     * sim(user.task_shape, tool.task_shape)
                  + w_paradigm * sim(user.paradigm, tool.paradigm)
                  + w_setup    * fit(user.setup_tolerance, tool.setup_tolerance)
```

Weights start equal, get tuned on validation.

---

## Approach 1 — Pure feature-driven (no graph)

### Architecture

```
[Onboarding answers]
        ↓
[Feature extractor]   ← rules + LLM fallback
        ↓
[User feature vector]
        ↓
[Tool feature matrix] (pre-computed, ~300 × 6 dims)
        ↓
[Weighted similarity scorer]
        ↓
[Top-K live narrowing]
```

### What's stored
- **Postgres table**: `tools(id, name, description, feature_json)` — the 300 tools
- **In-memory matrix**: `tool_features` (300 × N) — re-computed nightly when catalog updates
- **Per-session Redis**: `user_features` accumulating as questions answered

### What's good
- **Interpretable** — every score has a reason ("matched on industry + stack, weak on paradigm")
- **Fast** — single matrix mul; sub-100ms re-rank for any K
- **No training data needed** — runs from day one with hand-tagged features
- **Easy to debug** — when a wrong tool ranks #1, you see which feature drove it

### What's missed
- **No relational signal** — "Granola integrates with Linear" is just a tag, not a graph edge. Can't ask "tools that integrate with anything in user's stack" via traversal.
- **No multi-hop** — "tool X feeds tool Y feeds tool Z" requires manual tagging on every transitive edge.
- **No co-use signal** — can't naturally express "users who use Notion also tend to like Mem."
- **Feature drift** — when a new tool integrates with 5 things, you re-tag manually.

### Cost to build (rough)
- Feature schema: 1 day
- Tool catalog tagging (300 tools × 6 dims): ~2 days hand + LLM-assisted
- Scorer: half a day
- UI live-update wiring: ~1 day
- **Total: ~4–5 days**

---

## Approach 2 — Feature-driven + Neo4j graph

### Architecture

```
[Onboarding answers]
        ↓
[Feature extractor]                        [Neo4j graph DB]
        ↓                                          ↑
[User feature vector]  ──→  [Cypher query]  ──→  [Graph score]
        ↓                                          ↓
[Tool feature score]                       [Combined score]
                  ↘                       ↙
                   [Top-K live narrowing]
```

### Graph schema (proposed)

**Nodes**:
- `(:Tool {id, name, desc, feature_json})`
- `(:Capability {name})` — e.g. "task-extraction", "meeting-transcription"
- `(:Industry {name})` — Finance, Software, ...
- `(:Role {name})` — Auditor, SWE, Physician, ...
- `(:User {session_id, profile_json})`

**Edges**:
- `(:Tool)-[:HAS_CAPABILITY]->(:Capability)`
- `(:Tool)-[:INTEGRATES_WITH]->(:Tool)` (directed, e.g. Granola → Linear)
- `(:Tool)-[:REPLACES]->(:Tool)` (Cursor replaces VSCode + Copilot for some)
- `(:Tool)-[:USED_BY_ROLE {weight}]->(:Role)`
- `(:Tool)-[:FITS_INDUSTRY {weight}]->(:Industry)`
- `(:User)-[:USES]->(:Tool)`
- `(:User)-[:REJECTED]->(:Tool)`

### Query examples (post Q1)

After Q1 (Audit Manager / Senior / Finance):
```cypher
MATCH (r:Role {name: "Audit Manager"})<-[ub:USED_BY_ROLE]-(t:Tool)
MATCH (i:Industry {name: "Finance"})<-[fi:FITS_INDUSTRY]-(t)
RETURN t, ub.weight + fi.weight AS graph_score
ORDER BY graph_score DESC LIMIT 150
```

After Q2 (user picks Excel + Outlook + Sharepoint + ERP):
```cypher
MATCH (t:Tool)
MATCH (s:Tool) WHERE s.name IN ["Excel","Outlook","Sharepoint","SAP"]
OPTIONAL MATCH (t)-[i:INTEGRATES_WITH]->(s)
WITH t, count(i) AS integration_score
RETURN t, integration_score
ORDER BY integration_score DESC LIMIT 100
```

After Q3 (task = "full audit cycle"):
```cypher
MATCH (cap:Capability) WHERE cap.name IN
  ["sample-testing","working-papers","reconciliation","report-generation"]
MATCH (cap)<-[:HAS_CAPABILITY]-(t:Tool)
RETURN t, count(cap) AS capability_score
ORDER BY capability_score DESC LIMIT 50
```

After Q4 (day = "AM deep, PM meetings"):
- Apply paradigm filter from feature score
- Combine: `final_score = α * feature_score + (1-α) * graph_score`

### What's good
- **Multi-hop natural** — "tools that integrate with anything in user's Q2 stack" = single Cypher query, no manual transitive tagging
- **Co-use signal** — once `(:User)-[:USES]->(:Tool)` data accumulates, `MATCH (u1:User)-[:USES]->(:Tool {name:"Notion"}), (u1)-[:USES]->(t:Tool)` returns "tools commonly used alongside Notion"
- **Industry/role embedding for free** — `(:Tool)-[:USED_BY_ROLE]->(:Role)` weighted edges give a learnable signal
- **Easy to extend** — add new edge types (REPLACES, COMPETES_WITH, UPSTREAM_OF) without schema migration

### What's missed (vs Approach 1)
- **Cold-start severity** — at launch, USES/REJECTED edges are empty; graph score is just feature score with extra steps
- **Maintenance overhead** — graph has to stay synced with the catalog; integration edges need to be scraped/curated
- **Cypher query complexity** — debugging a wrong-rank tool is harder than reading a feature score breakdown
- **Two systems** — Postgres + Neo4j to keep in sync

### Cost to build (rough)
- Everything in Approach 1 (4–5 days)
- + Neo4j setup + schema: 1 day
- + Edge ingestion (integrations from Zapier/Pipedream/manual): 2 days
- + Cypher queries + scoring fusion: 2 days
- **Total: ~9–10 days**

---

## My recommendation: build Approach 1 first, A/B against Approach 2

### Why
- **Approach 1 is the floor** — you need feature scoring anyway. Approach 2 adds graph *on top of* features, not instead.
- **A1 ships in a week**; A2 in two. Faster validation cycle.
- **A1 is the honest baseline** — if A2 doesn't beat it by a meaningful margin (>10% recall@10), the graph is overhead.
- **Most graph wins (USES, REJECTED edges) are V2** — they need user data we don't have yet. A2's V1 advantages are mostly catalog-side (integration edges, capability hierarchy) which can also be encoded as features in A1.

### Concrete plan

1. **Build A1** with the 6-dim feature scorer.
2. **Run A1 against the 3 personas** (ACCA, SWE, Doctor) — record narrowing at each step (300/150/100/50/10).
3. **Hand-rank gold top-10 per persona** — your judgment as founder.
4. **Compute A1 metrics**: recall@K, precision@K, NDCG@K, paradigm-match.
5. **If A1 < 70% recall@10**: build A2 to see if graph closes the gap.
6. **If A1 ≥ 70% recall@10**: ship A1, defer A2 to V1.5 when user data starts feeding USES edges.

---

## Prerequisites before either runs

These are blockers — call them out explicitly:

1. **Tool catalog** — we have zero tools in a database. Need to seed ~50–100 to start (target 300 by V1 launch).
2. **Feature tagging** — the 6-dim feature record per tool. Hybrid: 70% LLM-tagged from descriptions, 30% manual review.
3. **Gold-rank ground truth** — for the 3 personas, you (founder) rank the top-10 tools you'd recommend. This is the validator.
4. **Q2/Q3/Q4 option templates per role** — the answer-set for each role. Start with the 3 personas (we already have these).

---

## Open questions for you

1. **Catalog seed size for first run**: 50 tools or jump to 300?
2. **Who tags features**: hand + LLM, or pure LLM?
3. **Gold ranking**: you do all 3 personas? Or invite domain experts (an actual ACCA, SWE, doctor) to rank?
4. **Integration data source**: scrape Zapier/Pipedream API directories? Or hand-curate top-50 integration edges?
5. **Live-narrowing UI**: just numbers ("150 → 100"), or do we show actual tool cards updating? UI affects what we need to render.

Lock these and I'll start building.
