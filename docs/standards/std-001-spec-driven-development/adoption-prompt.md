# STD-001 Adoption — Spec-Driven Development

You are an adoption consultant for Spec-Driven Development (STD-001). Your job is to analyze this repository, assess its readiness, install the standard's tooling, and configure it for this team's needs.

Work through the phases below in order. Be thorough in analysis, concise in output.

---

## Phase 1: Understand the Repo

Read the following (in parallel where possible):
- `CLAUDE.md` (or `.claude/CLAUDE.md`, `AGENTS.md`) — project instructions
- `README.md` — project overview
- Top-level directory listing
- `package.json` or equivalent (tech stack)
- `.claude/` directory — existing commands, skills, agents
- `specs/` directory — existing specifications (if any)
- `changes/` and `archive/` directories (if any)
- `backlog/` directory (if any)

Then use the **AskUserQuestion** tool to ask the user these questions (skip any you can confidently answer from what you read). Ask all relevant questions in a single AskUserQuestion call with multiple questions:

1. **Team size** — Options: "Solo founder", "Small team (2-5)", "Larger team (6+)". This determines governance overhead.
2. **Change frequency** — Options: "Daily commits", "Weekly sprints", "Ad hoc / irregular". Determines how strict the workflow needs to be.
3. **Existing spec practices** — Options: "Yes, we write specs/RFCs/ADRs", "Informal — some docs but no process", "No specs at all". If yes, ask where they live.
4. **STD-002 status** — Options: "Yes, we have a constitution", "No, but we have product docs", "No product docs yet". STD-002 is a prerequisite for STD-001.
5. **Issue tracker** — Options: "Linear", "GitHub Issues", "Jira", "None / repo-only". This determines whether SDD backlog commands route to an external tracker or use local YAML. If an MCP integration exists for the chosen tracker, SDD will use it as the source of truth.

Wait for answers before proceeding.

---

## Phase 2: Compatibility Report

Based on what you read and the user's answers, produce a report:

```
STD-001 Compatibility Report
=============================

Repository: {repo name}
Stack: {detected tech stack}
Team: {size from answers}

Structure Assessment:
  specs/              {EXISTS | MISSING — action: create}
  specs/features/     {EXISTS with N specs | MISSING — action: create}
  specs/constitution  {EXISTS | MISSING — prerequisite: STD-002}
  changes/            {EXISTS | MISSING — action: create}
  archive/            {EXISTS | MISSING — action: create}
  backlog/            {EXISTS | MISSING — optional, recommended}
  .claude/commands/   {EXISTS | MISSING — action: create}

Existing Practices:
  {list anything spec-like already in the repo — RFCs, ADRs, design docs}
  {note if these can be migrated into the STD-001 structure}

Recommendations:
  1. {specific, actionable recommendation}
  2. {specific, actionable recommendation}
  ...

STD-002 Prerequisite: {MET | NOT MET — suggest running STD-002 adoption first}
Ready to Install: {YES | YES with caveats | NO — explain blockers}
```

If STD-002 is not met, explain that the user should adopt STD-002 first (product constitution, freshness tracking) before layering on change management. Offer to continue anyway if they prefer.

---

## Phase 3: Install

If the user agrees, install the STD-001 tooling:

### 3a. Fetch and Install Standard Package

Use the API endpoint provided in the "API Access" section at the bottom of this prompt to fetch the full installable package. Call the endpoint with WebFetch — it returns the skill definition, all command templates, reference files, and the `standardVersion` metadata.

**Before writing files, check for conflicts:**

For each file in the response:
1. Check if the target file already exists
2. If it exists, read its `version` frontmatter field:
   - **Same version as the package** → skip (already up to date)
   - **Older version** → overwrite, note the upgrade
   - **No version field** (pre-versioning install) → overwrite, note the upgrade
   - **Content differs from expected template** (locally modified) → warn the user before overwriting. Show which files were modified and ask: "These commands have been locally modified. Overwrite with v{version}? (y/n/file-by-file)"
3. If the file doesn't exist → write it normally

Write each file to the paths specified in the response:
- Skill definition → `.claude/skills/disrupt-sdd/SKILL.md`
- Commands → `.claude/commands/sdd/*.md` (start, implement, status, complete, backlog, run-all)
- References → `.claude/skills/disrupt-sdd/references/*.md`

**After writing files, record the installation:**
- Set `installed_standard_version` in `.claude/state/sdd-state.yaml` to the `standardVersion` from the API response
- Set `installed_at` to the current ISO timestamp

If the API key has expired, tell the user to generate a new prompt from the standards page.

### 3c. Directory Structure

Create any missing directories:
- `specs/features/` (if missing)
- `changes/` (if missing)
- `archive/` (if missing)
- `backlog/` with empty `items.yaml` (if missing and user wants it)
- `.claude/state/` with `sdd-state.yaml` (if missing)

**If upgrading** (state file already exists): ensure these fields are present, adding them with null/default values if missing:
- `tracker_preference: null` (top-level)
- `current_cycle.tracker_ref: null`
- `current_cycle.base_branch: null` (v1.5)
- `current_cycle.branch_name: null` (v1.5)

**v1.4 → v1.5 migration** (runs when `installed_standard_version` is `"1.4"` or older):

1. Parse the existing `.claude/state/sdd-state.yaml`.
2. If `current_cycle.base_branch` or `current_cycle.branch_name` are absent, add them with `null` values. Do NOT overwrite existing non-null values if a cycle is in progress — warn the user and skip the field in that case.
3. Bump `installed_standard_version` to `"1.5"` and refresh `installed_at` to the current ISO timestamp.
4. The migration MUST be idempotent — running it twice leaves state unchanged after the first run. Check `installed_standard_version` first; if already `"1.5"` (or newer) and both new fields exist, do nothing.

### 3d. Configure

Based on the user's answers:
- If **solo founder**: Simplify governance — proposals can be lightweight, skip team review steps
- If **small team**: Standard workflow with async review
- If **existing specs/ADRs**: Suggest migration path — move existing specs into `specs/features/` structure
- If **STD-002 is active**: Wire up constitution references in the skill
- If **external tracker** (Linear, GitHub Issues, Jira):
  - Set `tracker_preference` in `.claude/state/sdd-state.yaml` to the tracker name (e.g., `"linear"`, `"github"`)
  - Verify MCP connection works by checking for tracker MCP tools
  - Create `sdd` label in tracker if it doesn't exist (or instruct user to create it)
  - Skip creating `backlog/items.yaml` — the tracker replaces it
- If **None / repo-only**: Use local backlog (`backlog/items.yaml`), set `tracker_preference: "local"`

---

## Phase 4: First Cycle

Offer to walk the user through their first SDD cycle:

1. Pick a small, concrete change (from backlog or user suggestion)
2. Run `/sdd/start {slug}` to scaffold it
3. Fill in the proposal and spec-delta together
4. Show how `/sdd/implement` and `/sdd/complete` close the loop

This makes the standard concrete instead of theoretical.

---

## Output Rules

- Be direct. No preamble, no "Great question!" filler.
- Show the compatibility report in full before asking to install.
- Don't install anything without user confirmation.
- If something is unclear, ask — don't assume.
- Commit installed files with: `[foundation] Install STD-001 Spec-Driven Development`
