---
name: venture-foundation
description: "Bootstrap and maintain Venture Knowledge Foundation (Disrupt STD-002). Ensures every venture repo has a product constitution, organized specs, freshness tracking, and planning workflows."
user-invocable: true
invocation: "/venture-foundation"
arguments: "[init|validate|constitution|freshness|research|ingest|gaps|amend|transcript|audit|okrs|workflow] [args]"
---

# Venture Knowledge Foundation (STD-002)

## Purpose

Every venture repository MUST have a structured knowledge foundation before adopting higher-level standards like STD-001. This skill bootstraps and maintains that foundation: product constitution, spec structure, freshness tracking, and planning workflows.

## Three-Tier Model

STD-002 uses a tiered adoption model. Each tier builds on the previous one.

| Tier | Name | Audience | Signal to Adopt |
|------|------|----------|-----------------|
| **Core** | Foundation | Every venture | Day one — mission, PMF thesis, principles |
| **Extended** | Growth | Ventures with customers/team | Multiple user types, sales motion, or multiple decision-makers |
| **Advanced** | Operations | Ventures with ongoing knowledge management | Actively ingesting external docs, running planning cycles, managing cross-functional documentation |

**Core files** (always required): `index.md`, `mission.md`, `pmf-thesis.md`, `principles.md`
**Extended files** (adopt when relevant): `personas.md`, `icps.md`, `positioning.md`, `governance.md`
**Advanced capabilities** (fully optional): ingestion, gap analysis, amendments, transcripts, audit, OKRs, workflows
**Knowledge types** (fully optional): When `knowledge_types` is configured in `vkf-state.yaml`, VKF governs the full knowledge base — constitution, architecture, features, UX, and reference documents — with per-type freshness thresholds, ingestion routing, and validation. Without this config, VKF operates on constitution + feature specs only.

Validation: Core = FAIL if missing. Extended = WARN if missing. Advanced = INFO if present, silent if absent. Knowledge types = INFO if configured, silent if absent. A venture passes STD-002 without any Advanced features or knowledge type configuration.

## Invocation

| Command | Behavior |
|---------|----------|
| `/venture-foundation` | Auto-detect: validate if constitution exists, else init |
| `/venture-foundation init` | Bootstrap repo to meet STD-002 |
| `/venture-foundation validate` | Audit repo against all 4 requirements |
| `/venture-foundation constitution` | Interactive constitution drafting |
| `/venture-foundation constitution [section]` | Draft a specific section (e.g., `personas`) |
| `/venture-foundation freshness` | Check spec freshness across repo |
| `/venture-foundation research [topic]` | Exa.ai market research for constitution sections |
| `/venture-foundation ingest [source]` | Classify and place external content through ingestion pipeline |
| `/venture-foundation gaps [scope]` | Scan for knowledge gaps with AI-assisted refinement |
| `/venture-foundation gaps --resolve` | Resolve gaps interactively |
| `/venture-foundation amend [section]` | Tiered amendment process (C0-C3) for constitution |
| `/venture-foundation transcript [source]` | Process meeting transcript through extraction pipeline |
| `/venture-foundation audit [query]` | Query audit logs for content provenance |
| `/venture-foundation okrs [subcommand]` | Manage quarterly objectives and key results |
| `/venture-foundation workflow [subcommand]` | Check documentation lifecycle and pending actions |

## Always

1. Maintain the required directory structure (`specs/constitution/`, `specs/features/`, `changes/`, `archive/`, `.claude/commands/`). If the repo uses non-default paths, check `constitution_root` and `features_root` in `.claude/state/vkf-state.yaml`.
2. Keep all constitution files modular -- one file per section in `specs/constitution/`.
3. Respect the tiered model: Core files (`index.md`, `mission.md`, `pmf-thesis.md`, `principles.md`) are always required. Extended files (`personas.md`, `icps.md`, `positioning.md`, `governance.md`) are adopted when relevant to the venture's stage.
4. Include `Last amended: YYYY-MM-DD` in every constitution file header.
5. Include `Last reviewed: YYYY-MM-DD` in every feature spec header.
6. Validate that no `[REQUIRED]` placeholders remain before marking a section complete.
7. Use commit conventions: `[foundation]`, `[constitution]`, `[spec-review]`, `[validate]`.
8. Update `.claude/state/vkf-state.yaml` after every significant action.
9. Log every ingestion and transcript extraction to `specs/ingestion-log.yaml`.
10. Announce amendment tier (C0-C3) before making any constitution change to active (non-draft) sections.
11. Track "we don't know" as explicit knowledge state (`known_unknown` in state), not as absence.
12. Never overwrite audit log entries — the ingestion log is append-only.

## Ask First

1. Overwriting an existing constitution file that has been filled out -- confirm with user.
2. Marking a spec as reviewed without reading it -- confirm intent.
3. Running exa.ai research that may consume API credits -- confirm scope.
4. Deleting or archiving constitution sections -- requires explicit approval.
5. Applying gap resolution answers that change active constitution content -- routes through `/vkf/amend`.
6. Archiving OKR quarters -- confirm with user before moving to archive.
7. Transitioning documents from Active to Archived in the workflow lifecycle.

## Never

1. Never overwrite filled constitution content with template placeholders.
2. Never mark a `[REQUIRED]` section as complete without content.
3. Never modify `governance.md` without user approval.
4. Never fabricate market data -- use exa.ai or clearly label assumptions.
5. Never skip freshness checks during validation.
6. Never delete gap reports -- they are historical records.
7. Never bypass amendment tiers -- even if the user says "just change it", announce the tier and follow the process.
8. Never auto-resolve gaps without user review of each proposed answer.

## Decision Tree

```
Is specs/constitution/ directory present? (check vkf-state.yaml for alternative path)
├── NO  → Run `init` to bootstrap
└── YES → Are Core files present? (index, mission, pmf-thesis, principles)
    ├── NO  → Report missing Core files, create them
    └── YES → Do Core files contain [REQUIRED] placeholders?
        ├── YES → Run `constitution` to fill them
        └── NO  → Run `validate` for full audit
            ├── PASS → Is Advanced tier adopted?
            │   ├── YES → Check workflow triggers, suggest next action
            │   │   ├── Triggers pending → Run `workflow check`, report pending reviews
            │   │   └── No triggers → Report compliance, suggest `gaps` for quality scan
            │   └── NO → Report compliance, suggest Advanced tier if knowledge management needs detected
            │       └── Signals: ingestion-log.yaml exists, transcripts/ dir exists, user mentions docs to add
            └── WARN/FAIL → List issues with fix suggestions
```

## Commit Convention

| Prefix | Usage |
|--------|-------|
| `[foundation]` | Structure scaffolding (dirs, files) |
| `[constitution]` | Constitution content changes |
| `[spec-review]` | Spec freshness updates |
| `[validate]` | Validation results and fixes |
| `[ingest]` | Knowledge ingestion from external sources |
| `[gaps]` | Gap analysis scans and resolutions |
| `[transcript]` | Meeting transcript processing |
| `[okr]` | OKR drafting, updates, reviews, archiving |
| `[workflow]` | Document lifecycle transitions |

Examples:
```
[foundation] Bootstrap STD-002 directory structure
[constitution] Draft mission and vision
[constitution] Update personas with research findings
[spec-review] Mark auth spec as reviewed
[validate] Fix missing freshness dates
```

## Required Structure

```
project/
  specs/
    constitution/                    # REQUIRED — product governance
      index.md                       # Summary + links to all sections
      mission.md                     # Mission and vision
      pmf-thesis.md                  # Product-market fit thesis
      personas.md                    # User personas
      icps.md                        # Ideal customer profiles
      positioning.md                 # Market positioning
      principles.md                  # Product principles
      governance.md                  # Decision authority + amendments
    features/                        # REQUIRED — feature specifications
      [feature]/
        spec.md                      # Feature specification
        decisions.md                 # (optional) ADRs and design decisions
        [sub-feature]/               # (optional) Sub-feature specs
          spec.md
    architecture.md                  # (optional) System architecture overview
    api-reference.md                 # (optional) API surface documentation
    data-dictionary.md               # (optional) Data models and schemas
    [custom-dir]/                    # (optional) Venture-specific spec dirs
      *.md
    gaps/                          # (Advanced) Gap analysis reports
      {date}-{scope}.md
    meetings/                      # (Advanced) Meeting briefs and register
      INDEX.md                     # Chronological meeting register
      {date}-{title}.md            # Individual meeting briefs
    transcripts/                   # (Advanced) Raw transcripts
      {date}-{title}.md
      templates/                   # Custom extraction templates
        {name}.yaml
    okrs/                          # (Advanced) Quarterly objectives
      current/
        {YYYY}-Q{N}.md
      archive/
        {YYYY}-Q{N}.md
    ingestion-log.yaml             # (Advanced) Audit trail for all ingestions
  changes/                           # Active change proposals
  archive/                           # Completed changes
  .claude/
    commands/
      vkf/
        init.md                      # Bootstrap structure
        validate.md                  # Audit compliance
        constitution.md              # Interactive drafting
        freshness.md                 # Freshness scan
        research.md                  # Exa.ai market research
        ingest.md                    # (Advanced) Knowledge ingestion
        gaps.md                      # (Advanced) Gap analysis
        amend.md                     # (Advanced) Constitutional amendments
        transcript.md                # (Advanced) Transcript processing
        audit.md                     # (Advanced) Audit queries
        okrs.md                      # (Advanced) OKR management
        workflow.md                  # (Advanced) Lifecycle workflows
    state/
      vkf-state.yaml                 # Foundation tracking
```

> Only `specs/constitution/` and `specs/features/` are required (paths configurable via `vkf-state.yaml` if the repo uses a different layout). Project-level docs, multi-file features, and custom directories are venture-specific.

## Advanced Capabilities

### Knowledge Ingestion (`/vkf/ingest`)

Standardized pipeline for ingesting Google Docs exports, Sheets, web pages, local files, and inline text into the constitution and specs. No OAuth — users export to local files or paste inline.

- **9-point classification rubric** maps content to 8 constitution sections + feature specs
- **Confidence scoring**: high (1 clear target), medium (2 possible targets), low (tangential match)
- **Chunking**: sources >5000 words split by heading boundaries
- **Approval gate**: user sees full placement plan before any writes
- **Unclassified handling**: user assigns manually, creates new spec, or discards
- Logs all placements to `specs/ingestion-log.yaml`

### Gap Analysis (`/vkf/gaps`)

Scans knowledge base for missing, thin, or disconnected information. AI proposes answers where possible.

- **7 detection heuristics**: (1) explicit markers `[REQUIRED]`/`[TODO]`, (2) thin sections <50 words, (3) missing cross-references, (4) missing metrics, (5) strategic questions the constitution should answer, (6) stub specs <100 words, (7) market data staleness >90 days
- **Over-flagging safeguards**: allowlist for intentionally brief sections, 14-day recency filter, ingestion awareness, minimum 3-gap threshold, known-unknown skip
- **3 valid resolutions**: Answer (write to target), "We don't know" (tracked as `known_unknown`, resurfaces in 90 days), "Bad question" (suppression entry refines detection)
- Gap reports stored in `specs/gaps/{date}-{scope}.md`

### Constitutional Amendments (`/vkf/amend`)

Tiered change management for active constitution files (files without `[REQUIRED]` placeholders). Files still in draft use `/vkf/constitution` instead.

**4 amendment tiers:**

| Tier | Name | When | Process |
|------|------|------|---------|
| **C0** | Cosmetic | Typos, formatting, date updates | Direct edit, no proposal |
| **C1** | Clarification | Rewording without meaning change | Note in amendment history |
| **C2** | Substantive | Adding/changing/removing actual content | Proposal + constitution-delta + propagation check + approval |
| **C3** | Structural | Changing principles, invalidating PMF, altering governance | Full C2 + principle conflict analysis + rollback plan + impact analysis |

**Auto-detection**: examines what's being touched and whether meaning changes.
**Propagation check (C2+)**: scans feature specs and other constitution files for references to changing content, reports downstream impact.
**Amendment history**: entries added to `governance.md` with date, file, description, author, tier.

### Transcript Processing (`/vkf/transcript`)

Specialized front-end to the ingestion pipeline for conversational content. Produces three artifacts per meeting: raw transcript, meeting brief, and document modifications.

- **Raw storage** in `specs/transcripts/{date}-{title}.md` with metadata header
- **Meeting brief** in `specs/meetings/{date}-{title}.md` — the intermediary analysis artifact containing executive summary, key decisions, action items, learnings with placement targets, open questions, and a document modification table. This is the canonical record of what the meeting produced.
- **Meeting register** at `specs/meetings/INDEX.md` — chronological index of all meetings with one-line outcomes, links to briefs, and ingestion IDs
- **3 built-in extraction templates**:
  - `general` — decisions, action items, product insights, strategic statements, open questions
  - `customer-call` — pain points, feature requests, competitive mentions, buying/churn signals, PMF evidence
  - `strategy-session` — positioning decisions, persona refinements, principle discussions, OKR proposals
- **Custom templates** in `specs/transcripts/templates/{name}.yaml`
- Extractions route through the ingestion classification pipeline (same 9-point rubric)
- Speaker attribution when identifiable
- Cross-meeting linking: when a decision references a prior meeting, the brief links to the earlier brief

### Audit & Provenance (`/vkf/audit`)

Full provenance traceability — every piece of information traceable from source to placement and back. Read-only (no commits).

- **Primary log**: `specs/ingestion-log.yaml` (entries from ingestion, transcripts, gap resolution)
- **5 query modes**:
  - `--trace <section>` — reverse: all sources that contributed to a section
  - `--source <id>` — forward: where content from a source was placed
  - `--stale` — placements whose source may have been updated since placement
  - `--contradictions` — potentially contradictory placements in the same section
  - No args — summary statistics (total ingestions, coverage per section, potential issues)
- **Log immutability**: append-only. Never delete or modify entries. Corrections use `supersedes` field.

### OKR Management (`/vkf/okrs`)

Time-bound objectives linked to constitution sections and feature specs.

- **Directory**: `specs/okrs/current/` (active) and `specs/okrs/archive/` (past)
- **File format**: structured markdown per quarter (`{YYYY}-Q{N}.md`)
- **4 subcommands**: `draft` (interactive creation with constitution links), `update` (progress with auto-status: On Track/At Risk/Behind), `review` (end-of-quarter scoring 0.0-1.0), `archive` (move to archive, create next quarter stub)
- **Gap integration**: gaps in OKR-linked sections get elevated severity in gap reports

### Documentation Workflows (`/vkf/workflow`)

Lifecycle management and orchestration across all documents.

- **5 lifecycle states**: Draft → Review → Active → Review Due → Archived
- **3 trigger types**:
  - Schedule-based: quarterly constitution review, monthly OKR check
  - Event-based: post-ingestion review of modified files, post-amendment propagation check
  - Custom: venture-defined in `specs/workflows.yaml`
- **State tracked centrally** in `vkf-state.yaml` (not in document headers)
- **3 subcommands**: `status` (show all docs by state), `check` (evaluate all triggers), `transition <path> <state>` (manual transition)

## Cross-Capability Interactions

```
External Sources → /vkf/ingest ──→ specs/ingestion-log.yaml ←── /vkf/audit (queries)
                        ↑                    ↑
Meeting Transcripts → /vkf/transcript ───────┤
                        │                    │
                        ├──→ specs/meetings/{brief}.md (intermediary analysis)
                        └──→ specs/meetings/INDEX.md (meeting register)

                        The audit chain:
                        raw transcript → meeting brief → learnings → document modifications
                        (source)         (analysis)      (what)      (where it went)

Knowledge Base ──→ /vkf/gaps ──→ specs/gaps/ ──→ resolution ──→ /vkf/ingest or /vkf/amend
                                                      ↓
                                              "we don't know" → known_unknowns (resurface in 90d)
                                              "bad question"  → suppressed heuristic

Constitution Changes → /vkf/amend (tiered C0-C3) → propagation check → downstream review_due

Time-bound Goals → /vkf/okrs → links to constitution + specs → gap severity elevation

Everything → /vkf/workflow (lifecycle orchestration, schedule + event triggers)
```

## Freshness Thresholds

### Feature Specs

| Status | Condition |
|--------|-----------|
| **CURRENT** | Review date within 90 days AND no code changes since review |
| **STALE** | Code changed since review date, OR review date 30-90 days old |
| **VERY_STALE** | Review date older than 90 days |
| **MISSING** | No `Last reviewed` date found |

### Constitution Files

| Status | Condition |
|--------|-----------|
| **CURRENT** | `Last amended` within 90 days |
| **REVIEW_DUE** | `Last amended` 90-180 days ago |
| **VERY_STALE** | `Last amended` over 180 days ago |
| **MISSING** | No `Last amended` date found |

### Source-Aware (with `--source-aware` flag on `/vkf/freshness`)

| Status | Condition |
|--------|-----------|
| **SOURCE_OK** | Source ingested within 90 days, no hash mismatch |
| **SOURCE_STALE** | Source older than 90 days or hash mismatch detected |
| **SOURCE_UNKNOWN** | No ingestion history for this spec |

## Exa.ai Integration (Optional)

The `research` subcommand uses exa.ai for market research when `EXA_API_KEY` is set. Without the key, the command degrades gracefully with a message explaining how to enable it.

Research supports these constitution sections:
- **Positioning**: Competitor analysis, market landscape
- **ICPs**: Industry trends, company profiles
- **Personas**: Role descriptions, workflow patterns
- **PMF Thesis**: Market validation, customer evidence

## Usage Scenarios

### Scenario 0: Adopting STD-002 with existing documentation

**Situation:** A venture has 200+ files in a docs/ vault and a monolithic Constitution.md. They want to adopt STD-002.

**What happens:**
1. User runs `/venture-foundation init`
2. Init detects existing docs (Constitution.md, numbered folders, feature docs)
3. Offers synthesis mode: "Found existing documentation. Generate constitution files that distill and link back?"
4. User confirms → init reads vault sources, generates 8 constitution files (50-150 lines each) that summarize and link back
5. Each file includes a Sources section with relative paths to the authoritative vault documents
6. `/vkf/validate` confirms compliance; no content duplication

### Scenario 1: Founder shares a strategy deck

**Situation:** The founder exports a Google Slides deck and says "Here are our updated strategy slides."

**What happens:**
1. Claude suggests routing through `/vkf/ingest`
2. Ingestion classifies content → positioning updates (high confidence), PMF evidence (medium), new persona mention (low)
3. User approves high-confidence placements, reassigns the persona mention
4. Since positioning.md is active, Claude notes: "The positioning changes are C2 (substantive). I'll create an amendment proposal."
5. `/vkf/amend` creates the proposal with propagation check
6. Audit log records the full chain

### Scenario 2: Weekly customer call transcript

**Situation:** A team member pastes a Zoom transcript from a key customer call.

**What happens:**
1. Claude suggests `/vkf/transcript` with `customer-call` template
2. Extraction identifies pain points, feature requests, competitive mentions, PMF evidence
3. Meeting brief generated at `specs/meetings/{date}-acme-weekly.md` with executive summary, key decisions, learnings table, and open questions
4. Extractions route through the ingestion classification pipeline
5. Raw transcript stored, meeting register updated, all extractions logged with speaker attribution
6. A team member who missed the call reads the 1-page meeting brief instead of the 45-minute transcript

### Scenario 3: Team discovers a knowledge gap

**Situation:** During OKR drafting, the team realizes they don't know their churn rate.

**What happens:**
1. Claude suggests `/vkf/gaps` on pmf-thesis.md
2. Gap analysis finds the missing metric
3. AI proposes qualitative evidence from transcripts but notes aggregate data is needed
4. Team resolves as "We don't know" — tracked with 90-day resurface
5. Claude suggests making churn tracking an OKR key result

### Scenario 4: Audit trail query

**Situation:** New team member asks "Where did this competitive analysis come from?"

**What happens:**
1. Claude suggests `/vkf/audit --trace specs/constitution/positioning.md`
2. Shows all sources with dates, types, and confidence levels
3. Flags any sources that may be stale
4. Suggests refresh actions where appropriate

## Templates

### Constitution File Header (all files)

```markdown
# [Section Title]

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---
```

### Feature Spec Header

```markdown
# [Feature Name] Specification

**Last reviewed:** YYYY-MM-DD
**Owner:** [Team or person]

---
```

Full templates and writing guidance: see `references/constitution-guide.md`
Freshness validation rules: see `references/freshness-rules.md`
Ingestion classification: see `references/ingestion-rubric.md`
Gap detection heuristics: see `references/gap-heuristics.md`
Audit log schema: see `references/audit-schema.md`

## CLAUDE.md Intelligence Layer

Adopting repos SHOULD include the `CLAUDE.md` template (shipped with the standard) to enable:

1. **Command routing** — maps user intents ("I have a doc to add", "what's missing?") to the right `/vkf/*` command
2. **Auto-detection** — decision tree evaluated before any edit to `specs/` files, routing constitution changes through `/vkf/amend` and external content through `/vkf/ingest`
3. **Passive enforcement** — automatic behaviors like announcing amendment tiers, suggesting gap scans after ingestion, and noting OKR relevance when linked specs change
