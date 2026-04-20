---
description: Start or continue a deep investigation before an SDD cycle
version: "1.4"
---

## Arguments

- **$ARGUMENTS**: Investigation slug (e.g., "rag-migration", "self-learning-features")

## Actions

### If `wip/{slug}/` does not exist — Start new investigation

1. **Create folder and overview**
   - Create `wip/{slug}/00-overview.md` with:

   ```markdown
   # {Title derived from slug}

   **Date:** {YYYY-MM-DD} | **Status:** Investigation in progress

   ## Problem
   {Problem statement from user's description}

   ## Documents

   | # | Document | What It Covers |
   |---|----------|---------------|
   | 00 | This file | Overview and reading guide |
   ```

   - Do NOT create other files yet — they emerge from the conversation

2. **Load context**
   - Read `specs/constitution/` if present — especially `principles.md`, `personas.md`, `positioning.md`
   - Read existing specs in `specs/features/` for the affected area
   - Scan the codebase for relevant files, patterns, and conventions
   - If a WIP report exists in a related folder, read its overview

3. **Initial analysis**
   - Based on context, give the user an honest initial assessment:
     - What you understand about the problem
     - What the codebase tells you (relevant patterns, existing infrastructure)
     - Tensions with constitutional principles or existing specs
     - What you don't yet know
   - Ask the user what aspect they want to investigate first

4. **Investigate iteratively**
   - As the conversation develops, create numbered files for each subject that emerges. Common patterns:
     - **Gap analysis** — map current code against desired capabilities
     - **Architecture options** — 2-3 approaches with trade-off comparison matrices
     - **Root cause analysis** — ranked failure modes, research findings
     - **Corner cases** — numbered edge cases with analysis
     - **Production patterns** — what other systems do (with research)
     - **Trade-offs** — comparison matrices, what each approach gains and loses
     - **Strategic recommendations** — sequenced moves, honest assessment, with reasoning
   - Name files descriptively: `01-root-cause-analysis.md`, `02-architecture-options.md`, etc.
   - Each file should be a focused investigation of one subject — dense, data-driven, opinionated
   - Use real data: line counts, error rates, timelines, trade-off matrices
   - Update `00-overview.md` document table as files are created
   - After writing each file, surface what it implies: tensions with the constitution, scope larger than expected, technology forks that need deciding

### If `wip/{slug}/` exists — Continue investigation

1. **Read the existing folder**
   - Read `00-overview.md` for current state
   - Skim all numbered files to understand what's been covered

2. **Summarize and continue**
   - Show: "Here's where we left off — {N} documents covering {topics}. What do you want to investigate next?"
   - The user may be in a new conversation — do not assume prior context

### When the user is ready to implement

- Offer: "Ready to start an SDD cycle from this investigation? Run `/sdd/start {slug}` — it will read this folder and pre-fill the proposal."
- Do NOT auto-start the cycle — the user decides when

## Output

### New investigation
```
═══════════════════════════════════════════════════════════════
  EXPLORE — {slug}
═══════════════════════════════════════════════════════════════

Created: wip/{slug}/00-overview.md

Context loaded:
  • Constitution: {relevant principles found, or "not present"}
  • Existing specs: {relevant specs, or "none in affected area"}
  • Codebase: {key files/patterns in affected area}

{Initial analysis}

What aspect do you want to investigate first?
═══════════════════════════════════════════════════════════════
```

### Continuing investigation
```
═══════════════════════════════════════════════════════════════
  EXPLORE — {slug} (continuing)
═══════════════════════════════════════════════════════════════

Documents so far:
  00 Overview
  01 {title} — {one-line summary}
  02 {title} — {one-line summary}
  ...

Status: {status from overview}

{Summary of what's been covered and what's still open}
═══════════════════════════════════════════════════════════════
```

## Notes

- Do NOT create numbered files upfront — they emerge from the conversation
- Each file should be genuinely useful analysis, not template filler
- Be honest and opinionated — "this is 12 months away" is more useful than hedging
- The WIP folder may never become an SDD cycle — some investigations conclude with "don't build this" or "needs more market research"
- Do not commit WIP files automatically — the user decides when to commit