# STD-002 Changelog

All notable changes to the Venture Knowledge Foundation standard.

---

## [2.1] - 2026-04-08

### Added

- **§3 Knowledge Architecture (normative taxonomy)** — Promoted from §2.5 (recommended) to a first-class section. Five-type taxonomy (constitution, architecture, features, ux, reference) is now MUST for vocabulary; SHOULD for adoption. Adoption of any specific type beyond Core constitution and at least one feature spec remains optional. The taxonomy itself is normative so that classification, validation, and tooling have a shared vocabulary.

- **§3.1 The litmus test** — Adopted Synapse-derived separation rule: *"If the content would change when a table, function, or config is added/renamed/removed, it belongs below the constitution. Constitution references implementation by linking, never by enumerating."* Resolves the most common boundary disputes between strategic, architectural, and feature-level content.

- **§3.5 Decision Records (ADRs) as a Format** — ADRs colocate with the layer they constrain. No global `adr/` directory. Required fields include "Trigger to revisit" — the part most ADRs miss and what makes them durable. Status discipline (Proposed/Accepted/Superseded/Deprecated) is the source of truth, not folder name. Strategic ADRs → governance.md amendment history; architectural ADRs → `architecture/{domain}/decisions/`; feature ADRs → `features/{feature}/decisions.md`.

- **§3.6 The Operations Layer (Adjacent, Not In Scope)** — `.claude/` (commands, skills, agents), CI configs, deployment scripts named explicitly as adjacent-to but not in scope of VKF. Has its own native governance loop (broken commands fail loudly). `.claude/state/vkf-state.yaml` remains in scope as the knowledge foundation registry. CLAUDE.md files MAY be classified as `type: reference` for frontmatter purposes.

- **§3.7 Configuration** — `knowledge_types` block now activated by default in the template `vkf-state.yaml` with `required` flags and per-type freshness defaults. Ventures override paths via `knowledge_types.{type}.path` to register existing folders without renaming files.

- **`docs_root` configuration** — `vkf-state.yaml` gains `docs_root` field (default: `"specs"` for backward compatibility; recommended new default: `"docs"`).

- **Expanded ingestion rubric** — 3 new classification targets (architecture, UX, reference) for a total of 12, activated when `knowledge_types` is configured. Heuristic signal lists in `skill/references/ingestion-rubric.md`.

- **Knowledge Base Health validation** — `/vkf/validate` step 6 (INFO-level): type coverage, frontmatter coverage, stub detection, cross-reference graph.

- **Per-type freshness thresholds** — Architecture=180d, UX=90d, Reference=365d. Constitution and Features unchanged. Custom overrides via `knowledge_types.{type}.freshness`. See `skill/references/freshness-rules.md` "Knowledge Type Freshness" section.

### Changed

- **§2.5 deleted**, content moved to new §3 with normative language and expanded subsections (3.1–3.7).
- **§4–§11 renumbered** — Spec Currency (was §3 → now §4), Planning Workflows (was §4 → now §5), Advanced Tier Requirements §5–§10 → §6–§11.
- **`vkf-state.yaml` template** — `knowledge_types` block uncommented and defaulted with all 5 types and `required` flags.
- **Standard frontmatter** — `version: "2.1"`, `effective: "2026-04-08"`. `status` remains "Under Review" pending soak period.
- **Component Registry timestamps** — bumped for `vkf-state.yaml` template, `validate.md` command, and `ingestion-rubric.md` / `freshness-rules.md` references (the latter two had been updated with type-aware logic in the unreleased work but never had their registry timestamps refreshed).

### Migration

- **Existing ventures with only constitution + features**: zero impact. The default `knowledge_types` block describes exactly what they have. `docs_root` defaults to `"specs"` so existing paths resolve unchanged.
- **Ventures with mature docs (Synapse pattern)**: configure `knowledge_types.{type}.path` to map existing folders. No file moves required. Optionally add type frontmatter to existing files (use `/vkf/validate` to surface unfrontmatter'd files).
- **Ventures with global ADR directories**: soft migration. The standard says ADRs colocate with their layer; existing global ADRs get moved as part of normal hygiene, not as a v2.1 compliance gate. `/vkf/validate` Knowledge Base Health check flags them as INFO.

### Rejected proposals

- **Operations as a 6th knowledge type.** Considered and rejected for v2.1. Operations has its own native governance loop (broken commands fail loudly, unused skills get pruned) and adding freshness scanning to YAML/prompt content produces noise more than signal. Ventures MAY define `operations` in their own `knowledge_types` block, but the standard provides no built-in support. May be revisited as a future STD-004 governing AI-first execution patterns.
- **`docs_root: "docs"` as the new default.** Considered. Kept `"specs"` as default for backward compatibility. `"docs"` is documented as the recommended new default but not enforced — ventures opt in.
- **Mandatory frontmatter on all knowledge files.** Considered and rejected. Would break adoption for existing venture vaults. Frontmatter remains SHOULD with INFO-level coverage reporting in `/vkf/validate`.

---

## [2.0.1-unreleased] - 2026-04-03

> Pre-release work consolidated into v2.1. The items below were drafted under
> "Unreleased" and shipped as part of v2.1 above. Preserved here for historical
> traceability. The substance is in the v2.1 entry.

### Added

- **Knowledge Architecture** (then section 2.5, now §3) — first draft of the 5-type taxonomy as a *recommended* section. Promoted to normative in v2.1.
- **`knowledge_types` configuration** — first commit to `vkf-state.yaml` template (commented out). Activated by default in v2.1.
- **Expanded ingestion rubric** — 3 new classification targets shipped to `skill/references/ingestion-rubric.md`.
- **Knowledge Base Health validation** — step 6 added to `/vkf/validate`.
- **Per-type freshness thresholds** — added to `skill/references/freshness-rules.md`.

---

## [Previously Added] - 2026-04-02

- **Path flexibility** — Standard now acknowledges that the constitution directory may live at a non-default path (e.g., `docs/constitution/`). Ventures set `constitution_root` and `features_root` in `vkf-state.yaml`. The structural requirement is the modular directory with 8 files, not the literal path.

- **Adoption from Existing Documentation** section — Synthesize-and-Link pattern for ventures with existing docs. Constitution files distill and link back to source documents rather than duplicating content. `/vkf/init` offers synthesis mode when existing docs are detected.

- **Constitution file size guidance** — Target 50-150 lines per file. Prevents both hollow stubs and sprawling essays.

- **Frontmatter flexibility** — Freshness dates may appear in YAML frontmatter or in-body metadata. Validation checks both locations.

- **CHANGELOG.md** — This file.

### Changed

- Effective date updated to April 2026
- `vkf-state.yaml` template includes `constitution_root` and `features_root` fields
- Freshness parsing rules accept both frontmatter and in-body dates
- Constitution guide includes Size and Scope section with synthesize-and-link guidance
- SKILL.md includes vault adoption scenario
- Commands that reference constitution/features paths note the configurable alternative

---

## [2.0-rc] - 2026-02-26

Initial release of the restructured standard with three-tier adoption model.

### Added

- Three-tier model: Core (required), Extended (contextual), Advanced (optional)
- Modular constitution directory with 8 files
- Freshness tracking with git-based drift detection
- Advanced tier: ingestion, gap analysis, amendments, transcripts, audit, OKRs, workflows
- 12 VKF commands in template
- CLAUDE.md intelligence layer template
- Constitution guide, freshness rules, ingestion rubric, gap heuristics, audit schema references
