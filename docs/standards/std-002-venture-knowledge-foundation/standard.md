---
id: "STD-002"
title: "Venture Knowledge Foundation"
description: "Every venture repository must have a product constitution, a normative knowledge architecture (5 types), organized specs, freshness tracking, planning workflows, and (optionally) advanced knowledge operations before adopting higher-level standards."
status: "Under Review"
version: "2.1"
effective: "2026-04-08"
prerequisite-for: "STD-001"
---

# STD-002: Venture Knowledge Foundation

**Status:** Under Review | **Version:** 2.1 | **Effective:** April 2026

---

## Summary

Every venture repository MUST have a structured knowledge foundation: a product constitution, organized specification directories, freshness tracking on all documents, and planning workflows. This standard is a strict prerequisite for STD-001 (Spec-Driven Development) -- you cannot manage change to specs that don't exist yet.

---

## Requirements

### 1. Repository Structure

Every venture repository MUST have:

```
project/
├── specs/
│   ├── constitution/                  # REQUIRED — product governance
│   │   ├── index.md                   # Summary + links to all sections
│   │   ├── mission.md                 # ★ Core — Mission and vision
│   │   ├── pmf-thesis.md              # ★ Core — Product-market fit thesis
│   │   ├── principles.md              # ★ Core — Product principles
│   │   ├── personas.md                #   Extended — User personas
│   │   ├── icps.md                    #   Extended — Ideal customer profiles
│   │   ├── positioning.md             #   Extended — Market positioning
│   │   └── governance.md              #   Extended — Decision authority
│   ├── features/                      # REQUIRED — feature specifications
│   │   └── [feature]/
│   │       ├── spec.md                # Feature specification
│   │       ├── decisions.md           # (optional) ADRs and design decisions
│   │       └── [sub-feature]/         # (optional) Sub-feature specs
│   │           └── spec.md
│   ├── architecture.md                # (optional) System architecture overview
│   ├── api-reference.md               # (optional) API surface documentation
│   ├── data-dictionary.md             # (optional) Data models and schemas
│   └── [custom-dir]/                  # (optional) Venture-specific spec dirs
│       └── *.md                       #   e.g., specs/schemas/, specs/apis/
├── changes/                           # Active change proposals (STD-001)
├── archive/                           # Completed changes (STD-001)
└── .claude/
    └── commands/                      # Planning workflows
```

> **Required vs flexible:** Only `specs/constitution/` and `specs/features/` are structurally required. Project-level docs at the `specs/` root (architecture, API reference, data dictionary, style guides), multi-file feature directories, and custom spec directories are all encouraged but venture-specific. A new venture may only have `constitution/` and `features/auth/spec.md`. A mature venture might have architecture docs, API references, and 17-file feature directories. Both are valid.

> **Path flexibility:** The tree above shows default paths. Ventures with a different documentation layout (e.g., `docs/constitution/` or `docs/specs/constitution/`) MAY use alternative roots — the structural requirement is the modular directory with 8 files, not the literal path `specs/constitution/`. When using non-default paths, configure `constitution_root`, `features_root`, and `docs_root` in `.claude/state/vkf-state.yaml` so VKF commands resolve correctly. See section 2.5 (Knowledge Architecture) for the recommended `docs/` layout.

### 2. Product Constitution

The `specs/constitution/` directory MUST contain modular governance documents. Each file is standalone, covering one aspect of product governance.

Not every venture needs every file on day one. The constitution uses a **tiered model** -- Core files are always required, Extended files are adopted when the venture reaches the stage where they matter.

#### Core Tier (always required)

These files capture the minimum viable product knowledge. Every venture has a mission, knows what it's building, and has opinions about how it builds. Without these, even a solo founder is flying blind.

| File | Purpose | Why Core |
|------|---------|----------|
| `index.md` | Summary + links to all sections | Navigation; shows what exists and what's missing |
| `mission.md` | Mission (one sentence) and vision (one sentence) | If you can't say what you're building in one sentence, you can't spec it |
| `pmf-thesis.md` | Customer, problem, solution, evidence, PMF status | The hypothesis the entire product is testing |
| `principles.md` | Product principles: always/never/prioritize | Resolves debates before they happen; guides every tradeoff |

#### Extended Tier (adopt when relevant)

These files become important as the venture matures -- when you're selling to companies, competing for market position, or growing beyond a single decision-maker. A pre-revenue solo project doesn't need ICPs. A venture with paying customers does.

| File | Purpose | When to Adopt |
|------|---------|---------------|
| `personas.md` | User personas with goals, pain points, workflows | When you have distinct user types with different needs |
| `icps.md` | Ideal customer profiles with qualification criteria | When you're selling to companies (B2B) or segmenting users |
| `positioning.md` | Positioning statement, competitive landscape, moat | When competitors exist and you need to articulate differentiation |
| `governance.md` | Decision authority table, amendment process | When more than one person makes product decisions |

**Validation behavior:** `/vkf/validate` checks Core files as REQUIRED (FAIL if missing) and Extended files as RECOMMENDED (WARN if missing, with a note on when to adopt). A venture passes STD-002 with Core tier complete. Extended files are tracked but don't block STD-001 adoption.

**Size guidance:** Constitution files should be concise governance summaries, not exhaustive documentation. Target **50-150 lines** per file. Files under 30 lines likely lack substance; files over 200 lines should be reviewed for content that belongs in feature specs, vault docs, or other artifacts. `governance.md` may grow beyond this range as amendment history accumulates -- this is expected.

#### Advanced Tier (adopt when relevant)

These capabilities support ventures with active knowledge management needs — regularly ingesting external documents, running planning cycles, and managing cross-functional documentation. They are fully optional and never affect Core/Extended compliance.

| Capability | Command | Purpose | When to Adopt |
|-----------|---------|---------|---------------|
| Knowledge Ingestion | `/vkf/ingest` | Classify and place external content into constitution and specs | When you regularly receive docs, decks, or research to incorporate |
| Gap Analysis | `/vkf/gaps` | Scan for missing, thin, or disconnected information | When you want systematic knowledge quality checks |
| Constitutional Amendments | `/vkf/amend` | Tiered change management (C0-C3) for constitution files | When constitution sections are active and changes need governance |
| Transcript Processing | `/vkf/transcript` | Extract insights from meeting transcripts | When you have regular customer calls or strategy sessions |
| Audit Logs | `/vkf/audit` | Query content provenance and trace sources to placements | When traceability matters (investors, compliance, team onboarding) |
| OKR Management | `/vkf/okrs` | Time-bound objectives linked to constitution and specs | When you run quarterly planning cycles |
| Documentation Workflows | `/vkf/workflow` | Lifecycle management with schedule and event triggers | When you need systematic document review cadences |

**Validation behavior:** `/vkf/validate` checks Advanced features as INFO (present) or silent (absent). They never produce WARN or FAIL. A venture passes STD-002 without any Advanced features.

**Note on technical sections:** STD-001's technical constitution (stack, architecture, coding standards) becomes `specs/constitution/technical.md` -- another file in the same directory, following the same pattern. STD-002 covers the product layer; STD-001 layers the technical layer on top.

### 3. Knowledge Architecture

**The repo is the source of truth.** All venture knowledge — strategy, architecture, features, UX, reference material — MUST live in the repository as structured markdown. No Notion, no Google Docs, no external wikis. This makes knowledge versioned, agent-readable, reviewable, and portable.

Every venture knowledge base MUST be organized around a fixed taxonomy of five knowledge types. **The taxonomy itself is normative**: ventures use these names so that classification, validation, and tooling have a shared vocabulary. **Adoption of any specific type is optional**: ventures populate types as they grow. A solo founder with constitution + one feature spec passes STD-002.

#### 3.1 The Five Knowledge Types

| Type | Question it answers | Volatility | Governance | The litmus test |
|---|---|---|---|---|
| **Constitution** | Who are we, what are we building, for whom, why? | Very low | Amendment (C0–C3) | "Would this change if we rebranded or repositioned?" |
| **Architecture** | How is the system built? What are the load-bearing structural choices? | Low–medium | Freshness + ADRs | "Would this change if we replaced a database, framework, or major subsystem?" |
| **Features** | What does the product do for the user? | Medium–high | SDD (STD-001) manages change; VKF tracks freshness | "Would a user notice if this changed?" |
| **UX** | How does the user experience the product? | High | Freshness | "Would this change if we restyled an onboarding flow without changing capabilities?" |
| **Reference** | Shared vocabulary, mock data, glossaries, external context | Low | Light | "Is this background knowledge that supports the others?" |

**The separation rule:**

> If the content would change when a table, function, or config is added/renamed/removed, it belongs *below* the constitution. Constitution references implementation by linking, never by enumerating. Each layer enumerates its own concerns and links upward — never duplicating the layer above.

This rule resolves the most common boundary disputes. A "We use ClickHouse for analytics" sentence belongs in `constitution/technical.md` because it's a strategic commitment. The actual table DDL belongs in `architecture/`. The user-facing dashboard built on those tables belongs in `features/`. Each layer enumerates its own concerns and links to the others — duplication is the failure mode.

#### 3.2 Required vs Optional Population

| Type | Required | When to populate |
|---|---|---|
| Constitution | YES (Core tier — see §2) | Always |
| Features | YES (at least one feature spec) | As soon as you ship anything observable |
| Architecture | NO (recommended once stack stabilizes) | When more than one engineer needs the same answer twice |
| UX | NO (recommended once you have users) | When happy paths and edge states drift between devs and designers |
| Reference | NO (recommended once you share vocabulary) | When new contributors keep asking what a term means |

**Validation behavior:** `/vkf/validate` reports per-type *coverage* (which types have any content) as INFO. Missing optional types never produce WARN/FAIL. Constitution Core tier remains the only structural REQUIRED — see §2 for details.

#### 3.3 Recommended Directory Layout

```
project/
├── docs/                            # The venture knowledge base (configurable via docs_root)
│   ├── constitution/                # Strategic identity (REQUIRED — see §2)
│   │   ├── index.md
│   │   ├── mission.md
│   │   ├── pmf-thesis.md
│   │   ├── principles.md
│   │   ├── personas.md              # Extended
│   │   ├── icps.md                  # Extended
│   │   ├── positioning.md           # Extended
│   │   ├── governance.md            # Extended
│   │   └── technical.md             # Added by STD-001
│   ├── architecture/                # System design (optional, recommended)
│   │   └── {domain}/                # e.g., data/, api/, infrastructure/, agents/
│   │       ├── *.md
│   │       └── decisions/           # Architectural ADRs (see §3.5)
│   │           └── ADR-NNN-{slug}.md
│   ├── features/                    # Product capabilities (REQUIRED — at least one)
│   │   └── {feature}/
│   │       ├── spec.md
│   │       ├── decisions.md         # Feature-level ADRs (see §3.5)
│   │       └── {sub-feature}/
│   ├── ux/                          # Interaction design (optional, recommended)
│   │   └── {flow-or-stage}/
│   └── reference/                   # Shared knowledge (optional, recommended)
│       ├── glossary.md
│       └── {topic}/
├── changes/                         # Active change proposals (STD-001)
├── archive/                         # Completed changes (STD-001)
└── .claude/
    ├── state/
    │   └── vkf-state.yaml           # Knowledge foundation registry
    ├── commands/
    │   └── vkf/                     # Knowledge commands
    └── skills/
```

**Path flexibility is preserved.** Ventures with existing layouts (e.g., numbered folders like `2-Architecture/`, `3-Features/`) map their paths via `knowledge_types.{type}.path` in `vkf-state.yaml`. The directory names above are default convention; the *type* is metadata. A venture does not need to rename a single file to adopt this architecture — only register what already exists.

**`docs_root` vs `specs/`:** STD-002 historically used `specs/` as the default root. Both are valid. `docs/` is the recommended new default because the knowledge base is broader than feature specifications. Set `docs_root` in `vkf-state.yaml` to your chosen root (defaults to `specs` for backward compatibility).

#### 3.4 Frontmatter Convention

Every document in the knowledge base SHOULD include structured frontmatter so agents can discover and classify content:

```yaml
---
title: "Document Title"
type: constitution | architecture | feature | ux | reference
status: draft | active | review-due | archived
last-amended: YYYY-MM-DD            # constitution
last-reviewed: YYYY-MM-DD           # everything else
tags: [relevant, keywords]
---
```

Frontmatter is not required for STD-002 compliance (would break adoption for existing venture vaults), but is **strongly recommended**. `/vkf/validate` reports frontmatter coverage as INFO and flags individual files without frontmatter so they can be progressively added.

#### 3.5 Decision Records (ADRs) as a Format

Decision records (ADRs) capture the *why* behind irreversible or hard-to-reverse choices. They are a **format**, not a knowledge type. ADRs colocate with the layer whose decisions they constrain:

| Decision scope | Where it lives | Format |
|---|---|---|
| **Strategic** (changes constitution meaning) | `docs/constitution/governance.md` amendment history | C2/C3 amendment record (see §6 — Constitutional Amendment Process) |
| **Architectural** (stack, data model, infrastructure) | `docs/architecture/{domain}/decisions/ADR-NNN-{slug}.md` | Full ADR template (Context / Decision / Consequences / Alternatives / Trigger to revisit) |
| **Feature** (scope, behavior tradeoffs within a feature) | `docs/features/{feature}/decisions.md` | Numbered decision log within the file |

**There is no global `adr/` directory.** Decisions live next to the thing they constrain so they are discovered by anyone reading that thing. A global graveyard becomes a place where decisions go to be forgotten.

**Required ADR fields** (for architectural and feature ADRs):

| Field | Purpose |
|---|---|
| **Status** | Proposed, Accepted, Superseded by ADR-NNN, or Deprecated |
| **Date** | YYYY-MM-DD when the decision was made |
| **Context** | What problem is being solved, what forces are at play |
| **Decision** | What was chosen, in plain language |
| **Consequences** | What this implies — both positive and negative |
| **Alternatives considered** | Real alternatives evaluated, not strawmen |
| **Trigger to revisit** | Conditions under which this decision should be re-evaluated |

The "Trigger to revisit" field is what most ADRs miss and what makes them durable. A decision without a revisit trigger calcifies into received wisdom; one with a trigger remains a *current* decision because everyone knows when it expires.

**Status discipline:** A decision with status "Accepted" is not a "future consideration." A decision with status "Proposed" is not yet binding. The status field is the source of truth — folder names are not. Misclassified ADRs (e.g., an Accepted ADR in a folder called "Future Considerations") should be moved to the appropriate decisions directory.

**Naming:** `ADR-NNN-{kebab-case-slug}.md`. NNN is zero-padded and unique per scope (architecture-wide or per-feature, never global).

#### 3.6 The Operations Layer (Adjacent, Not In Scope)

Beyond the five knowledge types lives the **operations layer**: the executable institutional knowledge in `.claude/` (commands, skills, agent definitions) and adjacent operational artifacts (CI configs, deployment scripts, runbooks). This layer is *adjacent to* the knowledge base — it acts on knowledge — but it is not itself a knowledge type for the purposes of this standard.

**Why it's not a knowledge type:**

- It has its own native governance loop. A broken command fails on invocation. An unused skill gets deleted in cleanup. Health is measurable through usage, not through review dates.
- Its content is largely structural (YAML frontmatter, command bodies, agent prompts), not narrative. Freshness scanning produces noise more than signal.
- It is an ongoing concern of execution-focused standards, not knowledge governance.

**What VKF still cares about:**

- **`.claude/state/vkf-state.yaml`** is part of the knowledge foundation. It is the registry of what knowledge exists, where, and at what freshness. It is operational *and* knowledge.
- **`CLAUDE.md` files** at the repo root and in subdirectories are procedural reference. Ventures MAY classify them as `type: reference` for frontmatter purposes; this is optional.
- **Documentation about commands and skills** (e.g., a README explaining when to use `/vkf/ingest`) is reference, not operations. The thing being documented is operations; the documentation is reference.

**What VKF stays out of:**

- The contents of command bodies, agent prompts, and skill SKILL.md files
- CI/CD pipeline configuration
- Deployment scripts and infrastructure-as-code

Ventures that want to formally govern these as a sixth knowledge type MAY define `operations` in `knowledge_types`. The standard does not provide built-in support, validators, or freshness rules for it.

#### 3.7 Configuration

Knowledge architecture is configured via `.claude/state/vkf-state.yaml`:

```yaml
docs_root: "docs"                    # Where the knowledge base lives (default: "specs")

knowledge_types:
  constitution:
    path: "constitution"             # Relative to docs_root
    freshness: 90
    governance: amendment
    required: true
  features:
    path: "features"
    freshness: 90
    governance: sdd
    required: true
  architecture:
    path: "architecture"
    freshness: 180
    governance: review
    required: false
  ux:
    path: "ux"
    freshness: 90
    governance: review
    required: false
  reference:
    path: "reference"
    freshness: 365
    governance: none
    required: false
```

When `knowledge_types` is absent, VKF operates on constitution + feature specs only — current default behavior, full backward compatibility. When present, VKF activates type-aware freshness scanning, ingestion routing across all 12 classification targets, and the Knowledge Base Health check in `/vkf/validate`.

---

### 4. Spec Currency

All specification documents MUST include freshness metadata:

- **Feature specs** (`specs/features/`): MUST have `Last reviewed: YYYY-MM-DD` in the document header. All `.md` files in a feature directory are scanned, not just `spec.md`.
- **Constitution files** (`specs/constitution/`): MUST have `Last amended: YYYY-MM-DD` in the document header, with quarterly review recommended
- **Project-level specs** (`specs/*.md`): MUST have `Last reviewed: YYYY-MM-DD` in the document header. Assessed by date only (no code path mapping).

> **Metadata location:** Freshness dates MAY appear as in-body metadata (e.g., `**Last amended:** YYYY-MM-DD`) or in YAML frontmatter (e.g., `updated: YYYY-MM-DD`). Validation tools MUST check both locations -- frontmatter first, then in-body. Ventures MAY add additional frontmatter fields (e.g., `status`, `owner`, `tags`) to support their tooling; these are not required by STD-002 but are encouraged for traceability.

A spec is considered:

| Status | Condition |
|--------|-----------|
| **CURRENT** | Review date is within 90 days and no code changes since review |
| **STALE** | Code has changed since the review date, OR review date is 30-90 days old with no code changes |
| **VERY_STALE** | Review date is older than 90 days |
| **MISSING** | No review date present in the document |

Freshness is validated by cross-referencing `Last reviewed` dates with `git log` on corresponding code paths.

### 5. Planning Workflows

The repository MUST contain Claude Code commands or skills for planning new work:

- `.claude/commands/` MUST exist with at least one planning command
- Commands SHOULD support: initializing structure, validating compliance, drafting constitution sections, and checking freshness

### Advanced Tier Requirements

The following requirements apply only to ventures that adopt the Advanced tier. They are validated as INFO (informational) and never block STD-002 compliance.

#### 6. Knowledge Ingestion Pipeline

Ventures with active knowledge management SHOULD have:

- A standardized ingestion process using `/vkf/ingest` for external content
- Content classification against the 9-point rubric (8 constitution sections + feature specs)
- Confidence scoring (high/medium/low) with user approval gates
- An append-only audit log at `specs/ingestion-log.yaml`

#### 7. Gap Analysis

Ventures SHOULD periodically scan their knowledge base:

- 7 detection heuristics covering markers, thin sections, cross-references, metrics, strategic questions, stub specs, and data staleness
- Over-flagging safeguards (allowlist, recency filter, ingestion awareness, minimum threshold)
- Three valid gap resolutions: Answer, "We don't know" (tracked), "Bad question" (suppressed)
- Gap reports stored in `specs/gaps/`

#### 8. Constitutional Amendment Process

Ventures with active (non-draft) constitution sections SHOULD use tiered change management:

- **C0 (Cosmetic):** Direct edit for typos, formatting, dates
- **C1 (Clarification):** History entry for rewording without meaning change
- **C2 (Substantive):** Proposal + propagation check for content changes
- **C3 (Structural):** Full C2 + principle conflict analysis + rollback plan

Amendment history tracked in `governance.md`.

#### 9. Meeting Transcript Processing

Ventures with regular meetings SHOULD have:

- A standardized extraction pipeline using `/vkf/transcript`
- Built-in templates: `general`, `customer-call`, `strategy-session`
- Custom template support in `specs/transcripts/templates/`
- Raw transcript storage in `specs/transcripts/`
- Extractions routed through the ingestion classification pipeline

##### 9.1 Meeting Briefs (Intermediary Artifacts)

Each processed transcript MUST produce a **meeting brief** — a standalone analysis document stored at `specs/meetings/{date}-{title}.md`. The meeting brief is the intermediary layer between a raw transcript and the document modifications it produces. It captures what was learned, decided, and left open, with explicit links to both the source transcript and every document modification.

Meeting briefs MUST contain:

| Section | Purpose | Required |
|---------|---------|----------|
| **Executive Summary** | 2-3 sentence synopsis of what happened and what matters | Yes |
| **Key Decisions** | What was decided, context, who was involved | Yes |
| **Action Items** | Task, owner, deadline, status (open/done) | Yes |
| **Learnings** | Insights extracted with category and placement target | Yes |
| **Open Questions** | Unresolved topics, deferred decisions, things to research | Yes |
| **Document Modifications** | Every knowledge base file changed as a result, with section, change description, and confidence | Yes |

Meeting briefs serve three purposes:

1. **Auditable context**: The ingestion log records WHAT changed WHERE. The meeting brief records WHY — the analysis, the discussion, the reasoning that led to the change.
2. **Standalone review**: A team member who missed the meeting reads the brief, not the 8,000-word transcript. The brief is the canonical record of what the meeting produced.
3. **Cross-meeting continuity**: When a decision from Meeting A is revisited in Meeting B, the Meeting B brief links to Meeting A's brief, creating a decision chain that is navigable without re-reading transcripts.

##### 9.2 Meeting Register

A meeting register at `specs/meetings/INDEX.md` MUST be maintained as a chronological index of all processed meetings. Each entry records:

- Date, title, template used
- Participants
- One-line key outcome
- Link to meeting brief
- Ingestion ID (linking to the audit log)

The register is the discovery layer — it answers "what meetings have we had, and what did each one produce?" without opening individual briefs.

#### 10. Audit & Provenance

Ventures that ingest external content SHOULD maintain:

- An append-only ingestion log at `specs/ingestion-log.yaml`
- Queryable provenance: trace sections to sources, sources to placements
- Staleness detection and contradiction scanning
- Integration with freshness tracking (`--source-aware` flag)

#### 11. Objectives & Documentation Lifecycle

Ventures running planning cycles SHOULD have:

- Quarterly OKRs in `specs/okrs/` linked to constitution sections and feature specs
- Document lifecycle tracking (Draft → Review → Active → Review Due → Archived)
- Schedule-based and event-based review triggers
- Workflow orchestration via `/vkf/workflow`

---

## Why

Most venture repositories start with code and add documentation as an afterthought. By the time a team wants structured change management (STD-001), there's nothing to manage -- no specs, no constitution, no governance. This standard fills the foundation gap:

- **Constitution as directory, not monolith**: Each section is its own file because (a) teams can update personas without touching positioning, (b) a missing file = a missing section -- easy to validate, (c) PRs touch only the relevant section, (d) STD-001's tech sections become just another file in the same directory.
- **Freshness as discipline**: Explicit review dates are the authority; git log catches when discipline lapses. Together they form a practical system that degrades gracefully.
- **Structure before process**: You can't do spec-driven development without specs. STD-002 creates the knowledge layer; STD-001 layers change management on top.

---

## Adoption from Existing Documentation

Many ventures already have substantial documentation before adopting STD-002 -- a Notion wiki, Google Docs, a Venture Vault, or a monolithic constitution file. The constitution is a **structured interface** to existing knowledge, not a replacement for it.

### Synthesize-and-Link Pattern

When a venture has existing docs, constitution files SHOULD:

1. **Distill**: Summarize key facts from existing sources (target 50-150 lines per file)
2. **Link**: Include relative-path links back to the authoritative source documents
3. **Not duplicate**: The constitution captures the structured summary; the source retains the depth

Each constitution file MAY include a **Sources** section at the bottom listing the vault documents it synthesizes:

```markdown
## Sources

- [Problem Statement](../01-Concept/Problem.md)
- [Solution Overview](../01-Concept/Solution.md)
- [Market Landscape](../01-Concept/Market-Landscape.md)
```

### `/vkf/init` with Existing Docs

When initializing in a repo with existing documentation, `/vkf/init` SHOULD:

1. Scan for common documentation patterns (monolithic constitution file, numbered doc folders, feature directories)
2. Map discovered content to the 8 constitution file targets
3. Offer **synthesis mode**: generate distilled constitution files that summarize and link back to sources, rather than empty `[REQUIRED]` templates
4. Report which source documents were consumed and which constitution files were generated

The user always has the option to choose greenfield mode (empty templates) even when existing docs are detected.

---

## Relationship to STD-001

STD-002 is a **strict prerequisite** for STD-001:

| Concern | STD-002 | STD-001 |
|---------|---------|---------|
| Product governance | `specs/constitution/` (mission, personas, positioning...) | `specs/constitution/technical.md` (stack, architecture) |
| Specs | Creates `specs/features/` structure | Manages changes to specs via proposals |
| Freshness | Establishes review dates | Maintains them through change cycles |
| Workflows | Planning commands (`/vkf/*`) | Change commands (`/sdd/*`) |
| Knowledge ops | Advanced tier: ingestion, gaps, amendments, audit, OKRs, workflows | N/A (STD-002 scope) |

STD-001 currently references `specs/constitution.md` (single file). Repos adopting STD-002 use `specs/constitution/` (directory). STD-001's skill/template should eventually be updated to expect the directory -- this is a separate follow-up.

---

## Resources

- [VKF Command Template](/resources/std-002-venture-knowledge-foundation-template) -- starter kit with `/vkf/init`, `/vkf/validate`, `/vkf/constitution`, `/vkf/freshness`, `/vkf/research` commands
- [CLAUDE.md Intelligence Layer](/resources/std-002-claude-md-template) -- routing table, auto-detection, passive enforcement rules for Claude Code

---

## Component Registry

| Component | Type | Last Updated |
|-----------|------|--------------|
| [`venture-foundation`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/SKILL.md) | Skill | 19/Mar/26 05:02 PM PKT |
| [`skill/references/constitution-guide.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/references/constitution-guide.md) | Skill Reference | 26/Feb/26 02:47 PM PKT |
| [`skill/references/ingestion-rubric.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/references/ingestion-rubric.md) | Skill Reference | 8/Apr/26 12:00 PM PKT |
| [`skill/references/gap-heuristics.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/references/gap-heuristics.md) | Skill Reference | 4/Mar/26 10:17 PM PKT |
| [`skill/references/audit-schema.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/references/audit-schema.md) | Skill Reference | 19/Mar/26 05:02 PM PKT |
| [`skill/references/freshness-rules.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/skill/references/freshness-rules.md) | Skill Reference | 8/Apr/26 12:00 PM PKT |
| [`/vkf/init`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/init.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/constitution`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/constitution.md) | Command | 26/Feb/26 02:47 PM PKT |
| [`/vkf/validate`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/validate.md) | Command | 8/Apr/26 12:00 PM PKT |
| [`/vkf/amend`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/amend.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/gaps`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/gaps.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/workflow`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/workflow.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/audit`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/audit.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/research`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/research.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/transcript`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/transcript.md) | Command | 19/Mar/26 05:02 PM PKT |
| [`/vkf/freshness`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/freshness.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/ingest`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/ingest.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`/vkf/okrs`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/commands/vkf/okrs.md) | Command | 4/Mar/26 10:17 PM PKT |
| [`vkf-state.yaml`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-002-venture-knowledge-foundation/template/.claude/state/vkf-state.yaml) | State | 8/Apr/26 12:00 PM PKT |
