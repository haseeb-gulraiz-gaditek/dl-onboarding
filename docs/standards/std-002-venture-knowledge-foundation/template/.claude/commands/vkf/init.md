---
description: Bootstrap STD-002 directory structure with constitution templates, spec directories, and planning workflows. Use --advanced to scaffold Advanced tier directories.
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS** (optional): `--advanced` to scaffold Advanced tier directories and files in addition to Core/Extended structure

## Actions

1. **Check Current State**
   - Read `.claude/state/vkf-state.yaml` if it exists
   - If already initialized, show current state and ask user if they want to re-initialize

2. **Create Directory Structure**
   - Create the constitution root directory (if not exists)
   - Create the features root directory (if not exists)
   - Create `changes/` (if not exists)
   - Create `archive/` (if not exists)
   - Create `.claude/commands/` (if not exists)

3. **Detect Existing Documentation**

   Before creating templates, check if the repo already has documentation that could be synthesized into constitution files (e.g., a monolithic `Constitution.md`, a `docs/` folder with product/strategy content).

   If existing docs are found, offer the user a choice:
   - **Synthesis mode**: Generate constitution files that distill existing sources (50-150 lines each) and link back to them via a Sources section
   - **Greenfield mode**: Create empty `[REQUIRED]` templates as normal

4. **Create Constitution Files**

   Create each file in `specs/constitution/` (or the configured `constitution_root`).

   **In greenfield mode:** create files with `[REQUIRED]` placeholders.
   **In synthesis mode:** create files that distill existing sources (50-150 lines each, with a Sources section linking back).

   **Core Tier** (always created -- these are required for STD-002 compliance):
   - `index.md`, `mission.md`, `pmf-thesis.md`, `principles.md`

   **Extended Tier** (also created as templates, but marked optional -- adopt when relevant):
   - `personas.md`, `icps.md`, `positioning.md`, `governance.md`

   All 8 files are scaffolded so they're ready when needed. Extended files include a note at the top explaining when to adopt them.

   **specs/constitution/index.md**
   ```markdown
   # [REQUIRED: Venture Name] Product Constitution

   **Established:** [REQUIRED: YYYY-MM-DD]
   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## Sections

   | Section | Summary | Status |
   |---------|---------|--------|
   | [Mission](mission.md) | [REQUIRED] | Draft |
   | [PMF Thesis](pmf-thesis.md) | [REQUIRED] | Draft |
   | [Personas](personas.md) | [REQUIRED] | Draft |
   | [ICPs](icps.md) | [REQUIRED] | Draft |
   | [Positioning](positioning.md) | [REQUIRED] | Draft |
   | [Principles](principles.md) | [REQUIRED] | Draft |
   | [Governance](governance.md) | [REQUIRED] | Draft |
   ```

   **specs/constitution/mission.md**
   ```markdown
   # Mission & Vision

   > Part of the [REQUIRED: Venture Name] Product Constitution

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## Mission

   [REQUIRED: One sentence. What does this product do, and for whom?]

   ## Vision

   [REQUIRED: One sentence. Where is this heading in 3-5 years?]

   ## Context

   [REQUIRED: 2-3 sentences. Why does this matter now?]
   ```

   **specs/constitution/pmf-thesis.md**
   ```markdown
   # Product-Market Fit Thesis

   > Part of the [REQUIRED: Venture Name] Product Constitution

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## PMF Status

   **Current stage:** [REQUIRED: Pre-PMF | Approaching PMF | Post-PMF]

   ## Customer

   [REQUIRED: Who is the primary customer?]

   ## Problem

   [REQUIRED: What problem are they experiencing?]

   ## Solution

   [REQUIRED: How does the product solve this?]

   ## Evidence

   [REQUIRED: What evidence supports this thesis?]

   ## Key Assumptions

   [REQUIRED: What must be true for this thesis to hold?]

   ## Invalidation Criteria

   [REQUIRED: What would prove this thesis wrong?]
   ```

   **specs/constitution/personas.md** *(Extended -- adopt when you have distinct user types)*
   ```markdown
   # User Personas

   > Part of the [REQUIRED: Venture Name] Product Constitution
   > **Tier:** Extended -- adopt when you have distinct user types with different needs. OK to leave as template until then.

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## Persona: [REQUIRED: Name / Role]

   | Attribute | Detail |
   |-----------|--------|
   | **Role** | [REQUIRED] |
   | **Goals** | [REQUIRED] |
   | **Pain Points** | [REQUIRED] |
   | **Current Workflow** | [REQUIRED] |
   | **Success Metric** | [REQUIRED] |
   | **Technical Comfort** | [REQUIRED: Low / Medium / High] |
   | **Frequency of Use** | [REQUIRED: Daily / Weekly / Monthly] |

   ### Scenarios

   1. [REQUIRED: A day-in-the-life scenario]
   ```

   **specs/constitution/icps.md** *(Extended -- adopt when selling to companies or segmenting users)*
   ```markdown
   # Ideal Customer Profiles

   > Part of the [REQUIRED: Venture Name] Product Constitution
   > **Tier:** Extended -- adopt when you're selling to companies (B2B) or segmenting users. OK to leave as template until then.

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## ICP: [REQUIRED: Segment Name]

   | Attribute | Detail |
   |-----------|--------|
   | **Company Size** | [REQUIRED] |
   | **Industry** | [REQUIRED] |
   | **Tech Maturity** | [REQUIRED: Early adopter / Mainstream / Laggard] |
   | **Annual Budget** | [REQUIRED] |
   | **Buying Trigger** | [REQUIRED] |
   | **Decision Maker** | [REQUIRED] |
   | **Champion** | [REQUIRED] |

   ### Qualification Criteria

   Must have:
   - [REQUIRED]

   ### Disqualifiers

   - [REQUIRED]
   ```

   **specs/constitution/positioning.md** *(Extended -- adopt when competitors exist and differentiation matters)*
   ```markdown
   # Market Positioning

   > Part of the [REQUIRED: Venture Name] Product Constitution
   > **Tier:** Extended -- adopt when competitors exist and you need to articulate differentiation. OK to leave as template until then.

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## Positioning Statement

   > For **[REQUIRED: target customer]** who **[REQUIRED: statement of need]**, **[REQUIRED: product name]** is a **[REQUIRED: product category]** that **[REQUIRED: key benefit]**. Unlike **[REQUIRED: primary competitor]**, we **[REQUIRED: primary differentiator]**.

   ## Competitive Landscape

   | Competitor | Category | Strengths | Weaknesses | Our Advantage |
   |-----------|----------|-----------|------------|---------------|
   | [REQUIRED] | | | | |

   ## Moat / Defensibility

   [REQUIRED: What makes this hard to copy?]

   ## Category

   [REQUIRED: What category does this product create or belong to?]
   ```

   **specs/constitution/principles.md**
   ```markdown
   # Product Principles

   > Part of the [REQUIRED: Venture Name] Product Constitution

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## We Always

   1. [REQUIRED]: [Explanation]

   ## We Never

   1. [REQUIRED]: [Explanation]

   ## We Prioritize (Ordered)

   1. [REQUIRED] over [REQUIRED]

   ## Design Tenets

   1. **[REQUIRED]**: [Description]
   ```

   **specs/constitution/governance.md** *(Extended -- adopt when more than one person makes product decisions)*
   ```markdown
   # Governance

   > Part of the [REQUIRED: Venture Name] Product Constitution
   > **Tier:** Extended -- adopt when more than one person makes product decisions. OK to leave as template until then.

   **Last amended:** [REQUIRED: YYYY-MM-DD]

   ---

   ## Decision Authority

   | Decision Type | Authority | Process |
   |--------------|-----------|---------|
   | [REQUIRED] | [Who decides] | [Process] |

   ## Amendment Process

   [REQUIRED: How are constitution changes proposed, reviewed, and approved?]

   ## Amendment History

   | Date | File | Change | Author |
   |------|------|--------|--------|
   | [REQUIRED] | | | |
   ```

4. **Create Advanced Tier Structure** (only if `--advanced` flag present)

   Create directories and template files for Advanced capabilities:

   - Create `specs/gaps/` (gap analysis reports)
   - Create `specs/transcripts/` (raw transcripts)
   - Create `specs/transcripts/templates/` (custom extraction templates)
   - Create `specs/okrs/current/` (active quarter OKRs)
   - Create `specs/okrs/archive/` (past quarter OKRs)
   - Create `specs/ingestion-log.yaml` with header:
     ```yaml
     # VKF Ingestion Log - Audit trail for all knowledge ingestions
     # Location: specs/ingestion-log.yaml
     # Managed by /vkf/ingest and /vkf/transcript commands
     # This file is append-only. Never delete or modify existing entries.

     entries: []
     ```
   - Create `specs/workflows.yaml` with header:
     ```yaml
     # VKF Workflow Triggers - Custom review triggers
     # Location: specs/workflows.yaml
     # Used by /vkf/workflow check

     triggers: []
       # - name: "Monthly competitive review"
       #   target: "specs/constitution/positioning.md"
       #   schedule: "30d"
       #   action: "Review competitive landscape is current"
     ```

5. **Initialize State**
   - Create or update `.claude/state/vkf-state.yaml`:
     ```yaml
     initialized_at: "{current ISO timestamp}"
     advanced_tier: true   # or false if --advanced not used
     last_validation: null
     last_constitution_review: null
     ```

6. **Commit**
   - Stage all new files
   - Commit with message: `[foundation] Bootstrap STD-002 directory structure`

## Output

Display:
```
Initialized Venture Knowledge Foundation (STD-002)

  specs/
  ├── constitution/
  │   ├── index.md              # Summary + links
  │   ├── mission.md            # ★ Core — Mission & vision
  │   ├── pmf-thesis.md         # ★ Core — PMF thesis
  │   ├── principles.md         # ★ Core — Product principles
  │   ├── personas.md           #   Extended — when you have distinct user types
  │   ├── icps.md               #   Extended — when selling to companies
  │   ├── positioning.md        #   Extended — when competitors matter
  │   └── governance.md         #   Extended — when multiple decision-makers
  └── features/                 # Feature specs go here
  changes/                      # Change proposals (STD-001)
  archive/                      # Completed changes

★ Core files are required for STD-002 compliance.
  Extended files are scaffolded and ready — adopt them when relevant.

Next steps:
1. Run /vkf/constitution to fill out Core sections first
2. Run /vkf/validate to check compliance
3. Adopt STD-001 when Core constitution is complete
4. Run /vkf/ingest to bring in existing documents
5. Run /vkf/gaps to identify what's missing

Advanced Tier (scaffolded with --advanced):
  specs/
  ├── gaps/                    # Gap analysis reports
  ├── transcripts/             # Raw transcripts
  │   └── templates/           # Custom extraction templates
  ├── okrs/
  │   ├── current/             # Active quarter OKRs
  │   └── archive/             # Past quarter OKRs
  ├── ingestion-log.yaml       # Audit trail (append-only)
  └── workflows.yaml           # Custom review triggers
```

## Error Handling

- **Already initialized**: Show state, ask to re-initialize or skip
- **Partial structure exists**: Create only missing pieces, report what was skipped
- **Files already have content**: Never overwrite non-placeholder content
