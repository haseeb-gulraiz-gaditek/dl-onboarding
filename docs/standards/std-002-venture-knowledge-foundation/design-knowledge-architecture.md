# Design: VKF as Venture Knowledge Architecture

**Status:** Design proposal | **Date:** 2026-04-03 | **Scope:** STD-002 evolution

## The Principle

**The repo is the source of truth.** No Notion, no Google Docs, no external wikis. All venture knowledge — strategy, architecture, features, UX, operations — lives in the repository as structured markdown. This makes it:

- Versioned (git history IS the audit trail)
- Agent-readable (LLMs can navigate, search, classify, and update it)
- Reviewable (knowledge changes go through the same PR process as code)
- Portable (clone the repo, you have the entire venture brain)

STD-002 currently prescribes the strategic layer (constitution). This design extends it to prescribe the **full information architecture** — what types of knowledge a venture needs, how each type is structured, and how AI agents discover and operate on it.

---

## Knowledge Types

Every venture produces the same categories of knowledge. STD-002 should be directive about what these are and how they're organized.

### 1. Constitution (Strategic Identity)

**What:** Who we are, what we're building, for whom, and why.
**Files:** 8 modular files (mission, PMF thesis, personas, ICPs, positioning, principles, governance, technical)
**Governance:** Amendment process (C0-C3). Highest governance level — changes here ripple everywhere.
**Already in STD-002:** Yes, fully specified.

### 2. Architecture (System Design)

**What:** How the system is built — stack decisions, data models, API contracts, infrastructure, agent orchestration.
**Structure:** One folder per architectural domain. Each document answers "how does X work?" with enough detail for an AI agent to implement against it.
**Governance:** Freshness tracking. Architecture docs should be current within 180 days. Changes to architecture docs don't need constitutional amendments — they need code review.
**Not currently in STD-002.**

### 3. Features (Product Capabilities)

**What:** What the product does — feature specs with Given/When/Then scenarios, acceptance criteria, edge cases.
**Structure:** One folder per feature domain. Specs are buildable — an agent should be able to implement from the spec alone.
**Governance:** SDD (STD-001) manages changes. VKF tracks freshness and completeness.
**Partially in STD-002:** `specs/features/` exists but is SDD territory. VKF tracks freshness.

### 4. User Experience (Interaction Design)

**What:** How users interact with the product — onboarding flows, workflows, happy paths, edge cases, error states.
**Structure:** Organized by user journey stage or flow type.
**Governance:** Freshness tracking. UX docs drift fast as the product ships — 90-day freshness is appropriate.
**Not currently in STD-002.**

### 5. Reference (Shared Knowledge)

**What:** Glossaries, external references, process docs, templates, mock data, concept models.
**Structure:** Flexible — reference material organized by purpose.
**Governance:** Light. Freshness at 365 days. No amendment process. Updated as needed.
**Not currently in STD-002.**

### 6. Operations (How We Work)

**What:** Agent commands, audit rubrics, stream contracts, workflow definitions, project plans.
**Structure:** Lives in `.claude/` (commands, skills, agents) and operational docs.
**Governance:** Self-governing through usage — broken commands get fixed, unused ones get pruned.
**Not in scope for STD-002** — this is tooling, not knowledge.

---

## Proposed Structure

STD-002 prescribes this as the **recommended** knowledge architecture. Ventures don't need all of it on day one — same tiered adoption as today.

```
project/
  docs/                              # The venture knowledge base
    constitution/                    # Strategic identity (STD-002 Core)
      index.md
      mission.md
      pmf-thesis.md
      principles.md
      personas.md
      icps.md
      positioning.md
      governance.md
      technical.md
    architecture/                    # System design
      {domain}/                      # e.g., data/, api/, infrastructure/, agents/
        *.md
    features/                        # Product capabilities
      {feature}/
        spec.md
        decisions.md
    ux/                              # Interaction design
      {flow-or-stage}/
        *.md
    reference/                       # Shared knowledge
      glossary.md
      {topic}/
        *.md
    _ingestion-log.yaml              # Audit trail (Advanced)
    _gaps/                           # Gap analysis reports (Advanced)
    _transcripts/                    # Meeting transcripts (Advanced)
    _okrs/                           # Quarterly objectives (Advanced)
  specs/                             # Technical contracts (optional, for API/schema YAML)
    apis/
    schemas/
  changes/                           # Active change proposals (STD-001)
  archive/                           # Completed changes
  .claude/
    state/
      vkf-state.yaml                # Knowledge foundation state
    commands/
      vkf/                          # Knowledge commands
    skills/
```

**Key decisions:**
- `docs/` is the knowledge root, not `specs/`. Knowledge is broader than specifications.
- Constitution stays at `docs/constitution/` (matches project-gtm).
- Feature specs can live in `docs/features/` OR `specs/features/` — both are valid. `specs/` is for technical contracts (YAML APIs, JSON schemas).
- The path flexibility already in STD-002 (via `constitution_root`, `features_root`) extends naturally — add `docs_root` for the whole knowledge base.

---

## Document Frontmatter Convention

Every document in the knowledge base SHOULD include structured frontmatter so agents can discover and classify content:

```yaml
---
title: "Document Title"
type: constitution | architecture | feature | ux | reference
status: draft | active | review-due | archived
last-amended: 2026-04-03        # or last-reviewed
tags: [relevant, keywords]
---
```

This is not mandatory for STD-002 compliance (would break adoption), but is **strongly recommended** and unlocked by the `validate` command which can flag files missing frontmatter.

---

## What Changes in the Standard

### New Section: "Knowledge Architecture" (after Constitution, before Spec Currency)

Describes the 5 knowledge types, their purpose, and recommended directory structure. Uses SHOULD language (not MUST) for types beyond constitution — ventures adopt as they grow.

### Expanded Validation

`/vkf/validate` currently checks 4 things: structure, constitution, freshness, workflows.

Add a 5th (optional, INFO-level): **Knowledge Base Health**
- Which knowledge types exist?
- Are there documents without frontmatter?
- Are there stubs (<50 words)?
- Cross-reference completeness (do feature specs reference constitution principles? do architecture docs reference the technical constitution?)

### Expanded Ingestion Rubric

Currently 9 targets (8 constitution files + feature specs). Expand to include:
- Architecture docs (signal: "stack", "database", "API", "schema", "infrastructure")
- UX docs (signal: "onboarding", "flow", "journey", "user story", "happy path")
- Reference docs (signal: "glossary", "template", "process", "guide")

The ingestion pipeline already has the machinery — it just needs more targets.

### Freshness Thresholds by Type

| Type | Current | Review Due | Very Stale |
|------|---------|------------|------------|
| Constitution | 90d | 180d | 365d |
| Architecture | 90d | 180d | 365d |
| Features | 90d (+ git drift) | - | 90d |
| UX | 90d | 180d | 365d |
| Reference | 180d | 365d | 730d |

### vkf-state.yaml Extension

```yaml
# Knowledge Base Configuration
docs_root: "docs"                    # Where the knowledge base lives
knowledge_types:
  constitution:
    path: "constitution"             # Relative to docs_root
    freshness: 90
    governance: amendment             # Uses C0-C3 amendment process
  architecture:
    path: "architecture"
    freshness: 180
    governance: review               # Freshness tracking only
  features:
    path: "features"
    freshness: 90
    governance: sdd                  # Managed by STD-001
  ux:
    path: "ux"
    freshness: 90
    governance: review
  reference:
    path: "reference"
    freshness: 365
    governance: none                 # No formal governance
```

Ventures configure which types they use. Absent types are ignored. The default (no `knowledge_types` key) behaves exactly as STD-002 does today — constitution + feature specs only.

---

## What Does NOT Change

- **Constitution tiers** (Core/Extended) — unchanged
- **Amendment process** (C0-C3) — still constitution-only
- **SDD integration** — feature specs still managed by STD-001
- **Compliance requirements** — passing STD-002 still means constitution + freshness + workflows
- **Advanced tier** — ingestion, gaps, transcripts, OKRs, audit — unchanged in mechanics

---

## AI-Forward Compatibility Checklist

What makes a knowledge base AI-agent-compatible:

1. **Everything in the repo** — no external dependencies for knowledge
2. **Structured frontmatter** — agents can parse metadata without reading full content
3. **Consistent directory hierarchy** — agents navigate by convention, not discovery
4. **Cross-references** — documents link to each other (agents can follow the graph)
5. **Freshness dates** — agents know what's current and what's stale
6. **Machine-readable registry** — vkf-state.yaml tells agents what exists and where
7. **Standard document types** — agents know what sections to expect in each type
8. **Ingestion pipeline** — new information gets classified and placed, not dumped randomly
9. **Gap detection** — agents can identify what's missing, not just what's wrong

STD-002 already delivers 5-9. This design adds 1-4 explicitly.

---

## Mapping to project-gtm

| project-gtm current | Proposed standard |
|---------------------|-------------------|
| `docs/constitution/` (9 files) | `docs/constitution/` — unchanged |
| `docs/2-Architecture/` (30+ files) | `docs/architecture/` — numbered prefix optional |
| `docs/3-Features/` (110+ files) | `docs/features/` — SDD-managed specs |
| `docs/4-User-Experience/` (20+ files) | `docs/ux/` — journey and flow docs |
| `docs/1-Concept/`, `docs/5-Knowledge/` | `docs/reference/` — concept models, glossary |
| `docs/CLAUDE.md`, `docs/AGENTS.md` | Stays in `docs/` or `.claude/` — operational, not knowledge |
| `docs/_ingestion-log.yaml`, `_gaps/`, etc. | Stays as VKF Advanced tier system files |

project-gtm doesn't need to rename anything. The numbered folders are a valid convention. The standard recommends a structure; ventures can map their existing layout via `knowledge_types` paths.

---

## Next Steps (when ready to implement)

1. Add "Knowledge Architecture" section to `standard.md`
2. Extend `vkf-state.yaml` template with `docs_root` and `knowledge_types`
3. Expand ingestion rubric with architecture/UX/reference targets
4. Add Knowledge Base Health check to `/vkf/validate`
5. Update freshness-rules.md with per-type thresholds
6. Update SKILL.md with knowledge type awareness
7. Update adoption-prompt.md to ask about knowledge types during setup
8. Configure project-gtm's vkf-state.yaml with its knowledge types mapping
