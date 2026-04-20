---
description: Scan knowledge base for missing, thin, or disconnected information with AI-proposed answers and resolution workflow
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Optional scope for the scan
  - `constitution`: scan only `specs/constitution/` files
  - `features`: scan only `specs/features/` directories
  - `all`: scan everything (default)
  - Specific file path: scan a single file (e.g., `specs/constitution/positioning.md`)
  - `--resolve`: append to any scope to enter interactive resolution mode after the report

## Actions

1. **Determine Scope**
   - Parse `$ARGUMENTS` to set scan scope
   - If empty or `all`: scan constitution files, feature specs, and project-level specs
   - If `constitution`: scan only `specs/constitution/*.md` (or the configured `constitution_root`)
   - If `features`: scan only `specs/features/**/*.md` (or the configured `features_root`)
   - If a file path: scan that single file
   - Strip `--resolve` flag and store for step 9

2. **Load Safeguards**
   - Read `.claude/state/vkf-state.yaml` for:
     - `known_unknowns` list: skip matching gaps unless 90-day resurface timer has elapsed
     - `gap_suppressions` list: skip matching heuristic+pattern combinations permanently
     - Recent ingestion timestamps: skip sections amended in the last 14 days (recently touched = not stale)

3. **Run 7 Heuristics**

   - **H1: Explicit Markers** — scan for `[REQUIRED]`, `[TODO]`, `[TBD]`, `[PLACEHOLDER]` tags
   - **H2: Thin Sections** — identify sections with <50 words of substantive content (excluding headers, tables, boilerplate)
   - **H3: Missing Cross-References** — check for constitution files that reference concepts defined in other files but lack explicit links (e.g., personas mentioned in PMF thesis but not linked)
   - **H4: Missing Metrics** — flag claims like "strong retention", "high growth", "significant traction" that lack quantitative data
   - **H5: Strategic Questions** — detect unanswered strategic questions (sections that pose questions without answers, or TODO items phrased as questions)
   - **H6: Stub Specs** — feature specs with only a title or <100 words total
   - **H7: Market Data Staleness** — competitor data, market size, or pricing information older than 6 months (cross-reference dates in content with current date)

4. **Apply Safeguards**
   - Filter results through safeguard rules from step 2
   - Remove gaps matching active suppressions
   - Remove gaps in sections amended within the last 14 days
   - Remove known unknowns whose 90-day resurface timer has not elapsed
   - Log how many gaps were filtered and why

5. **Threshold Check**
   - If fewer than 3 gaps found after filtering:
     - Report "knowledge base is in good shape"
     - Show any remaining findings as informational (not actionable)
     - Skip AI refinement and report generation
     - Still update state with scan timestamp

6. **AI-Assisted Refinement**
   - For each gap:
     - Attempt to propose an answer using existing knowledge in the specs (cite source files)
     - If a reasonable answer can be constructed: present it as a proposal
     - If unanswerable from existing knowledge: tag as `knowledge_request`
     - If researchable via web: suggest a specific `/vkf/research` query

7. **Generate Report**
   - Write report to `specs/gaps/{date}-{scope}.md` with:
     - Scan metadata (scope, date, safeguard summary)
     - Each gap with: ID, heuristic, file, section, finding, AI proposal, severity
   - Severity classification:
     - **High**: core constitution file, explicit marker, or missing critical data
     - **Medium**: thin section, missing metrics, or cross-reference gap
     - **Low**: informational, market staleness, or stub spec

8. **Update State**
   - Record gap scan in `.claude/state/vkf-state.yaml`:
     ```yaml
     last_gap_scan: "{current ISO timestamp}"
     last_gap_scope: "{scope}"
     gaps_found: {N}
     gaps_filtered: {M}
     ```

When `--resolve` flag is present, continue with steps 9-10:

9. **Interactive Resolution**
   - Walk through each gap in severity order (High first):
     - Present the gap with AI's proposed answer (if any)
     - User chooses one of three actions:
       - **Answer**: accept or edit the proposed content, then apply it
         - If target is an active constitution file: route through `/vkf/amend`
         - If target is a draft file or feature spec: apply directly
       - **"We don't know"**: track as known unknown in state with 90-day resurface date
       - **"Bad question"**: add heuristic+pattern to `gap_suppressions` in state

10. **Commit**
    - `[gaps] Scan {scope} — {N} gaps found, {M} resolved`

## Output Format

```
Gap Analysis Report
===================
Scope: all | Generated: 2026-03-04
Safeguards: 2 known unknowns skipped, 1 suppression active, 3 recent sections excluded

Gaps Found: 5

GAP-001 [H4: Missing Metrics] pmf-thesis.md > Evidence
  Finding: "Strong retention" claimed without quantitative data
  AI Proposal: Based on ingestion ING-003, Acme renewed without prompting.
               Suggest: "Acme Corp renewed (Feb 2026) — qualitative retention signal"
  Severity: Medium

GAP-002 [H2: Thin Section] positioning.md > Moat / Defensibility
  Finding: Section has 23 words, below 50-word threshold
  AI Proposal: Cannot propose — insufficient existing knowledge
  Suggested: /vkf/research positioning (competitive landscape)
  Severity: Medium

GAP-003 [H1: Explicit Marker] personas.md > Pain Points
  Finding: [REQUIRED] placeholder still present
  AI Proposal: Based on ING-005 transcript, users report: export latency,
               missing date filters, no bulk operations
  Severity: High

GAP-004 [H5: Strategic Question] principles.md > Trade-offs
  Finding: "Should we prioritize speed or accuracy?" — unanswered
  AI Proposal: Cannot propose — this is a strategic decision requiring founder input
  Severity: High

GAP-005 [H7: Market Data Staleness] positioning.md > Competitive Landscape
  Finding: Competitor pricing data from 2025-06-15 (264 days old)
  AI Proposal: Cannot propose — requires fresh research
  Suggested: /vkf/research competitors
  Severity: Low

Report saved: specs/gaps/2026-03-04-all.md
Resolution: Run /vkf/gaps --resolve to address each gap interactively
```

## Error Handling

- **No specs directory**: Suggest `/vkf/init`
- **No gaps directory**: Create `specs/gaps/` automatically
- **State file missing safeguard fields**: Initialize them with empty defaults:
  ```yaml
  known_unknowns: []
  gap_suppressions: []
  ```
- **Invalid scope argument**: List valid options (`constitution`, `features`, `all`, or a file path)
- **Single file not found**: Report "file not found at {path}", list available constitution files
