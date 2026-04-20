# Gap Detection Heuristics

7 heuristics for scanning the knowledge base for missing, thin, or disconnected information. Each heuristic targets a specific failure mode in constitution and spec completeness.

---

## Heuristic 1: Explicit Markers

Detect placeholder markers that should have been replaced with real content.

### Detection Method

Scan all `.md` files in `specs/constitution/` and `specs/features/` for the following markers (case-insensitive):

```
[REQUIRED]
[TODO]
[TBD]
[PLACEHOLDER]
[FILL IN]
[INSERT]
[PENDING]
```

### Example Findings

```
GAP: specs/constitution/positioning.md:14 — [REQUIRED: Fill in the formula below]
GAP: specs/constitution/icps.md:22 — [TBD: awaiting sales data]
GAP: specs/features/export/spec.md:8 — [TODO: define file format options]
```

### Tuning Guidance

- Match markers inside square brackets only -- don't flag the word "required" in prose (e.g., "SSL is required for all endpoints" is not a gap)
- Include markers in code blocks only if they appear in template sections, not in example code
- Markers in `archive/` directories are excluded

---

## Heuristic 2: Thin Sections

Detect sections with insufficient substantive content.

### Detection Method

For each H2 section in constitution files:
1. Count words excluding headers, template text, and blank lines
2. Flag sections with fewer than 50 words of substantive content
3. Template text is identified by `[REQUIRED:`, `>Template:`, or content inside `[square brackets]`

### Example Findings

```
GAP: specs/constitution/governance.md ## Decision Authority — 12 words (threshold: 50)
GAP: specs/constitution/personas.md ## Persona: CTO — 38 words (threshold: 50)
```

### Tuning Guidance

- The 50-word threshold applies to constitution files. Feature specs use the stub spec heuristic (Heuristic 6) with a 100-word threshold instead.
- Tables count their cell content toward word count -- a well-populated table satisfies the threshold.
- Do not count frontmatter (`Last amended:`, blockquotes linking to parent constitution) toward the word count.

---

## Heuristic 3: Missing Cross-References

Detect concepts referenced in one section but not defined in the expected section.

### Detection Method

1. Extract named entities from each constitution file: persona names, ICP segment names, competitor names, principle names
2. Cross-check: if personas.md mentions "Enterprise CTO" but pmf-thesis.md references "CTO buyer" without linking to personas.md, flag the disconnect
3. Check for orphaned references: concepts mentioned in 2+ sections but not having a canonical definition in the expected section

### Reference Expectations

| Concept | Expected definition | Common reference locations |
|---------|-------------------|---------------------------|
| Persona names | personas.md | pmf-thesis.md, icps.md, feature specs |
| ICP segments | icps.md | pmf-thesis.md, positioning.md, feature specs |
| Competitor names | positioning.md | pmf-thesis.md, principles.md |
| Product principles | principles.md | feature specs, governance.md |

### Example Findings

```
GAP: "Enterprise segment" referenced in pmf-thesis.md:34 but no matching ICP in icps.md
GAP: "Acme Corp" named as competitor in pmf-thesis.md:12 but absent from positioning.md competitive landscape
GAP: personas.md defines "DevOps Lead" but feature specs reference "Platform Engineer" — possible alias?
```

### Tuning Guidance

- Use fuzzy matching for names (e.g., "DevOps Lead" and "DevOps Engineer" should be flagged as potential aliases, not separate gaps)
- Only flag cross-reference gaps when the concept appears in 2+ files -- a single mention doesn't warrant a gap
- Exclude generic terms like "user", "customer", "team" from cross-reference checks

---

## Heuristic 4: Missing Metrics

Detect claims that lack quantitative backing.

### Detection Method

Scan for qualitative assertions that should be supported by numbers:
1. Look for vague quantifiers: "strong", "high", "significant", "growing", "most", "many", "low", "few"
2. Check if the sentence or surrounding paragraph contains a number, percentage, date, or citation
3. Flag when a qualitative claim appears without quantitative evidence within the same section

### Target Sections

| Section | What needs metrics |
|---------|-------------------|
| pmf-thesis.md | Retention rates, NPS scores, churn percentages, cohort data, growth numbers |
| positioning.md | Market size, competitor revenue/funding, win rates, market share |
| personas.md | Frequency data, time-spent estimates, team sizes |
| icps.md | Budget ranges, company size ranges, deal sizes |

### Example Findings

```
GAP: pmf-thesis.md:23 — "strong retention" without specific retention percentage
GAP: positioning.md:45 — "growing market" without market size or growth rate
GAP: icps.md:18 — "large enterprises" without employee count or revenue range
```

### Tuning Guidance

- Not every qualitative word is a gap. "We always prioritize simplicity" in principles.md is prescriptive, not a claim needing evidence.
- Only flag missing metrics in sections where quantitative backing is expected (see target sections table above)
- Principles.md and governance.md are exempt from this heuristic -- they are prescriptive, not evidential

---

## Heuristic 5: Strategic Questions

Detect common strategic questions the constitution should answer but doesn't.

### Detection Method

Maintain a checklist of fundamental strategic questions. For each question, check whether the relevant constitution section provides an answer.

### Question Checklist

| Question | Expected Section | Detection |
|----------|-----------------|-----------|
| Who is our primary customer? | pmf-thesis.md, personas.md | Look for a named persona or customer description |
| What problem do we solve? | pmf-thesis.md | Look for a "Problem" section with substantive content |
| Who are our competitors? | positioning.md | Look for a populated competitive landscape table |
| What is our primary differentiator? | positioning.md | Look for differentiator in positioning statement or moat section |
| What is our PMF status? | pmf-thesis.md | Look for "Current stage:" with a value (Pre-PMF, Approaching, Post-PMF) |
| What are our product principles? | principles.md | Look for at least 2 items in "We Always" or "We Prioritize" |
| Who has decision authority? | governance.md | Look for a populated decision authority table |
| What is our ideal customer profile? | icps.md | Look for at least 1 ICP with qualification criteria |
| How do we amend the constitution? | governance.md | Look for amendment process section with at least 2 steps |

### Example Findings

```
GAP: "Who is our primary competitor?" — positioning.md has no competitive landscape table
GAP: "What is our PMF status?" — pmf-thesis.md has no "Current stage:" field
GAP: "Who has decision authority?" — governance.md decision authority table is empty
```

### Tuning Guidance

- This heuristic fires broadly on fresh constitutions. That's expected -- a new constitution will have many strategic questions unanswered.
- Weight the questions: customer, problem, and competitor questions are higher priority than governance questions for early-stage ventures.
- If a question is answered across multiple sections (spread out), don't flag it as missing -- flag it under Heuristic 3 (missing cross-references) instead.

---

## Heuristic 6: Stub Specs

Detect feature specs that exist structurally but lack substantive content.

### Detection Method

For each `.md` file in `specs/features/*/`:
1. Count total words excluding frontmatter, headers, and template markers
2. Flag specs with fewer than 100 words of substantive content
3. Additionally flag specs where every section is a template placeholder (all content is inside `[square brackets]`)

### Example Findings

```
GAP: specs/features/export/spec.md — 42 words (threshold: 100), 3 of 4 sections are template-only
GAP: specs/features/notifications/spec.md — 0 words, file contains only headers
GAP: specs/features/billing/decisions.md — 15 words, appears to be a stub
```

### Tuning Guidance

- The 100-word threshold is deliberately low. The goal is to catch truly empty stubs, not to enforce thoroughness.
- Companion files like `decisions.md` or `changelog.md` are expected to start thin -- only flag them if the parent `spec.md` is also a stub.
- Newly created specs (created within the last 7 days per git history) get a grace period: flag as `STUB_NEW` instead of `STUB` to indicate they may be in progress.

---

## Heuristic 7: Market Data Staleness

Detect positioning or competitive data that may be outdated.

### Detection Method

1. Scan positioning.md and pmf-thesis.md for date references (explicit dates, "as of Q1 2025", "last updated")
2. Check if any referenced data is older than 90 days from the current date
3. Look for research citations or source references without dates -- these are flagged as `UNDATED`
4. Cross-reference with ingestion-log.yaml: if the source that contributed positioning data was ingested more than 90 days ago, flag the placement

### Example Findings

```
GAP: positioning.md:28 — competitor data "as of Q3 2025" is 180+ days old
GAP: pmf-thesis.md:45 — "NPS score of 72" has no date reference (UNDATED)
GAP: positioning.md:52 — source ING-012 (market report) ingested 120 days ago, may be outdated
```

### Tuning Guidance

- The 90-day threshold aligns with the freshness rules in freshness-rules.md. Adjust if the venture's market moves faster or slower.
- PMF evidence dates are critical -- stale PMF data leads to false confidence. Weight these flags higher than stale competitive data.
- Industry reports and market size data are acceptable at 180-day thresholds (markets don't shift that fast). Apply the 90-day rule strictly to competitor-specific data.

---

## Over-Flagging Safeguards

These safeguards prevent the gap analysis from generating noise. Apply them after all 7 heuristics have run.

### Allowlist

Sections that are intentionally brief should not be flagged as thin:
- A solo founder's governance.md may legitimately have minimal decision authority content (one person decides everything)
- Early-stage ventures may have a single ICP -- an icps.md with one well-described segment is not a gap
- Document allowlist entries in `vkf-state.yaml` under `gap_allowlist`:

```yaml
gap_allowlist:
  - section: "specs/constitution/governance.md"
    heuristic: "thin-sections"
    reason: "Solo founder; governance is minimal by design"
    created_at: "2026-03-04"
```

### Recency Filter

Do not flag sections that were amended in the last 14 days. Recent amendments indicate active work -- flagging them creates friction during active editing cycles.

Check `Last amended:` date in the file header. If within 14 days of the current date, suppress all gap flags for that file.

### Ingestion Awareness

Do not flag gaps that were addressed by a recent ingestion. Cross-reference gap targets with `ingestion-log.yaml` timestamps:
- If the target section received an extraction within the last 7 days, suppress the gap
- This prevents the pattern: ingest content, run gap analysis, see gaps that were just filled

### Minimum Threshold

Require at least 3 gaps before generating a report. If fewer than 3 gaps are found across all heuristics and safeguards:
- Log the findings internally but do not surface a gap report to the user
- Display: "Knowledge base health check: no significant gaps detected."

### Known Unknowns

Items tracked as `known_unknown` in vkf-state.yaml are intentionally unanswered questions. Do not re-flag them unless their 90-day resurface timer has elapsed.

```yaml
known_unknowns:
  - question: "What is our month-6 retention rate?"
    heuristic: "missing-metrics"
    section: "specs/constitution/pmf-thesis.md"
    created_at: "2026-01-15"
    resurface_at: "2026-04-15"  # created_at + 90 days
```

If `resurface_at` has passed, re-flag the item and prompt: "This question was parked 90 days ago. Is it answerable now?"

---

## Resolution Workflow

Every detected gap must resolve to one of 3 outcomes:

### 1. Answer

Proposed content is written to the target section.

- If the target is an active constitution file, the answer routes through `/vkf/amend` for proper amendment tracking
- If the target is a feature spec, content is written directly
- The gap entry is removed from the active gap list and logged as resolved in ingestion-log.yaml

### 2. "We Don't Know"

The question is valid but currently unanswerable.

- Tracked as `known_unknown` in vkf-state.yaml
- Resurface date set to `created_at + 90 days`
- AI may suggest a `/vkf/research` query to help answer the question later

```yaml
known_unknowns:
  - question: "Who is our primary competitor in the SMB segment?"
    heuristic: "strategic-questions"
    section: "specs/constitution/positioning.md"
    created_at: "2026-03-04"
    resurface_at: "2026-06-02"
```

### 3. "Bad Question"

The heuristic fired incorrectly -- the gap is not a real gap.

- Create a suppression entry to prevent the same pattern from firing again
- Stored in vkf-state.yaml under `gap_suppressions`

---

## Suppression Schema

```yaml
gap_suppressions:
  - heuristic: "thin-sections"
    pattern: "specs/constitution/governance.md ## Amendment Process"
    reason: "Solo founder; amendment process is intentionally simple"
    created_at: "2026-03-04"
  - heuristic: "missing-metrics"
    pattern: "positioning.md:market-size"
    reason: "Pre-revenue; market sizing is premature"
    created_at: "2026-03-04"
  - heuristic: "strategic-questions"
    pattern: "Who are our competitors?"
    reason: "Category-creating product; no direct competitors exist"
    created_at: "2026-03-04"
```

### Suppression Fields

| Field | Required | Description |
|-------|----------|-------------|
| `heuristic` | Yes | Which heuristic generated the gap |
| `pattern` | Yes | Specific pattern to suppress (file path, section name, or question text) |
| `reason` | Yes | Why this gap is suppressed -- must be a human-written justification |
| `created_at` | Yes | ISO date when suppression was created |

Suppressions do not expire. They remain active until manually removed. This is deliberate -- unlike known unknowns, a suppressed gap means the heuristic is wrong for this venture, not that the answer is unknown.

---

## AI-Assisted Refinement

For each detected gap, the AI assistant should attempt one of three responses:

1. **Propose an answer** -- If existing knowledge elsewhere in the constitution or ingestion log contains enough information to draft an answer, propose it with citation. Example: "Based on ING-007 (board deck), your primary competitor appears to be Acme Corp. Shall I add this to positioning.md?"

2. **Declare unanswerable** -- If the gap requires information not present in the knowledge base, tag it as a knowledge request. Example: "No retention data found in any ingested source. This requires primary data collection."

3. **Suggest a research query** -- If the gap could be resolved with external research, propose a `/vkf/research` command. Example: "To fill the competitive landscape gap, I can run: `/vkf/research competitive analysis for [venture category]`"
