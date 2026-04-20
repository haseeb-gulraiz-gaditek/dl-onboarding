# STD-001 Changelog

All changes to the Spec-Driven Development standard are documented here. Standard changes are held to a higher bar than regular code — each entry records the rationale and what was evaluated but rejected.

---

## 2026-04-17 — v1.5: Auto-Branching and Auto-PR for SDD Cycles

**Origin:** Dogfooding on this repo. Two failure modes made cycle boundaries implicit rather than enforced:

1. **Main accumulated stale `current_cycle` state.** The `standard-template-versioning` cycle was started 2026-04-03, its work shipped via the STD-001 v1.3 and v1.4 commits, but `/sdd:complete` was never run. `sdd-state.yaml` on `main` stayed non-null for 11 days until a retroactive manual archive on 2026-04-17. Any new branch off main inherited the phantom state, and `/sdd:start` refused until it was cleared.
2. **Branching was manual and uncoordinated.** The v1.4 `/sdd:start` did not touch git branches. Contributors either ran it on `main` (committing `[spec]` directly to main) or remembered to `git checkout -b` first. Branch naming was ad hoc; two contributors using the same slug would collide.

Both were rooted in the same cause: cycle boundary (who owns this work, on what branch, for how long) was implicit in convention rather than enforced by the commands.

### Changes Made

#### 1. `/sdd:start` owns branch creation (`template/.claude/commands/sdd/start.md`, active + template)

**Before:** `/sdd:start` scaffolded `changes/{slug}/` and committed `[spec]` without touching git branches. Base branch choice was up to the contributor.

**After:** Before scaffolding, `/sdd:start` now:
- Refuses on a dirty working tree (lists uncommitted paths).
- Captures `base_branch = git symbolic-ref --short HEAD` (or the short SHA on detached HEAD) so Work Forest worktrees and feature-branch workflows are preserved.
- Resolves a collision-safe branch name: `{slug}`, or `001-{slug}` ... `999-{slug}` on collision (checks both local refs and `git ls-remote --heads origin`). Refuses if all 1000 candidates are taken.
- Runs `git switch -c {branch_name}` before any file I/O, so all cycle commits land on the new branch.
- Records `base_branch` and `branch_name` in `current_cycle` alongside the existing fields.

**Why this earns its place:** Branch creation is a 100% mechanical step that the user previously had to remember. Forgetting it means `[spec]` commits land directly on main — the worst case. Making `/sdd:start` own it removes the failure mode and provides a clean cycle boundary by construction. Base-branch capture (not hardcoding `main`) keeps the Work Forest pattern intact.

#### 2. `/sdd:complete` clears state atomically and opens a PR (`template/.claude/commands/sdd/complete.md`, active + template)

**Before:** Step 11 ("Clear State") updated state in memory and added to history. No explicit commit was required for the clear. No push. No PR. The user was expected to push and open a PR manually.

**After:**
- Step 10 ("Clear State and Commit Archive") clears all `current_cycle` fields including the new `base_branch` and `branch_name`, and bundles the clear into the `[archive]` commit so state-clear is atomic with archival. Revised commit message: `[archive] Archive {slug} and clear cycle state`.
- New step 11 ("Push and PR") reads the captured `base_branch` and `branch_name`, pushes `git push -u origin {branch_name}`, detects the platform from `origin` (`github.com` → `gh`, `gitlab.com` or `*gitlab*` → `glab`), checks CLI availability (`command -v` + `auth status`), and either creates the PR or falls back to printing a compare URL. Pre-v1.5 cycles (no `base_branch`) warn and exit successfully.

**Why this earns its place:** The 11-day phantom-state incident was the trigger. Bundling the state-clear into the `[archive]` commit makes it impossible for main to carry non-null active-cycle state after a cycle completes — the clear is guaranteed because `/sdd:complete` is what writes the commit. The auto-PR step removes a manual step that contributors routinely skip (or skip correctly but forget to link to the archive), and the compare-URL fallback means the command never silently fails on environments without `gh`/`glab`.

#### 3. State schema additions (`template/.claude/state/sdd-state.yaml`)

Added two fields to `current_cycle`: `base_branch` (branch `/sdd:start` was invoked from) and `branch_name` (actual cycle branch, which may differ from slug on collision). Both default to `null`. Commands MUST treat missing fields on old installs as `null` — no deserialization crash.

#### 4. New Always rules 11 and 12 in `skill/SKILL.md`

- 11: `/sdd:start` MUST create the cycle's branch from current HEAD and refuse on a dirty working tree.
- 12: `/sdd:complete` MUST clear `current_cycle` (including new fields) in a committed step BEFORE pushing or opening a PR.

Also added a Cycle State section to `SKILL.md` documenting the full `sdd-state.yaml` schema — previously only documented in the template file.

#### 5. Standard §10 — Cycle Branching (new section in `standard.md`)

Codifies the cycle-branch rule, naming convention, dirty-tree refusal, and the state-clear-before-PR ordering as a normative requirement. §10 is what makes the `/sdd:*` command behavior part of the standard rather than just a convenience of the template.

#### 6. Adoption-prompt migration (`adoption-prompt.md`)

Added an idempotent v1.4 → v1.5 migration step: null-initialize `base_branch` and `branch_name` on existing installs, bump `installed_standard_version` to `"1.5"`, refresh `installed_at`. Running it twice is a no-op.

#### 7. Status display (`/sdd/status.md`, active + template)

Added a `Branch: {branch_name} (from {base_branch})` line to the Active Cycle output. Omitted for pre-v1.5 cycles where `branch_name` is null.

### Design Decisions

- **Collision prefix is `NNN-{slug}`, not `{slug}-NNN`.** Prefix sorts deterministically in branch listings (`001-foo`, `002-foo` group together) and preserves the slug's prefix-search behavior (`git branch | grep ^foo` still finds the original).
- **State-clear bundled into `[archive]` commit, not a separate commit.** One commit means the clear can never be forgotten — the archival and state-clear ship together or neither ships. A separate commit could be skipped on error.
- **Push-then-PR, not PR-then-push.** `gh pr create` needs the branch to exist on the remote. We push first, then try to open the PR. If the PR tool fails, push still succeeded — the user gets a compare URL fallback and the cycle still counts as completed.
- **Pre-v1.5 cycle warning, not refusal.** The migration may not have run yet when someone completes an in-flight cycle. Refusing would block work; warning lets them complete and push manually, preserving the standard's intent (cycle completes) while sacrificing the automation (manual PR).

### Evaluated and Rejected

| Capability | Reason for Rejection |
|---|---|
| **Auto-rebase on base branch before PR** | Merge conflicts are a human decision. SDD doesn't own conflict resolution policy — the contributor does. Auto-rebasing would surprise users who prefer merge commits or who have policy reasons for the linear history they already have. |
| **Draft vs. ready PR distinction** | Draft-by-default would require another flag and a convention. Users who want draft PRs can open one manually or convert with `gh pr ready --undo`. Always-ready keeps the command surface narrow. |
| **PR templates beyond spec-delta summary** | Projects have their own PR template requirements (security review, test plan, screenshots). Generating a generic body would either conflict with repo `.github/PULL_REQUEST_TEMPLATE.md` or duplicate it. We write a minimal body summarizing the spec-delta and link to the archive; the repo's own template handles the rest. |
| **`sdd` label auto-applied to PR** | Labels are repo-specific and require the label to exist. The `sdd` label already applies to tracker issues when the tracker is configured; propagating to PRs requires more coupling than it's worth. |
| **Force-retry push on failure** | If push fails, the state is already cleared — we can't rewind. But force-retrying hides the underlying problem (auth expired, branch protection, network). Better to exit nonzero with the git error so the user sees it. The state-cleared commit is already safe on the local branch; re-pushing is a one-liner. |
| **Separate `/sdd:push` and `/sdd:pr` commands** | Splitting the step creates two commands users have to remember and sequence. The whole point of auto-PR is to close the loop inside `/sdd:complete`. If the CLI is missing, the compare-URL fallback handles it cleanly. |
| **Cap collisions at `099-{slug}` instead of `999-`** | Harmless to go higher. The real bottleneck is slug hygiene — if you've used `fix-bug` 100 times, that's the problem, not the counter. `999-` is a soft ceiling; anyone hitting it is doing something wrong regardless. |
| **Dirty-tree auto-stash** | Silently stashing and popping on failure is a good way to lose uncommitted work. Refusing with a clear message is safer and nudges the user toward intentional stashing or committing. |

### Files Changed

- `standard.md` — Version bump to 1.5, Last Updated 17/Apr/26, added §10 Cycle Branching, Component Registry dates refreshed.
- `skill/SKILL.md` — Added Always rules 11 and 12, added Cycle State section with full state schema, version schema documented.
- `template/.claude/commands/sdd/start.md` — New Branch Setup step (step 2), state update records `base_branch`/`branch_name`, Error Handling extended with dirty-tree/not-a-repo/collision-exhausted cases, version bump to 1.5.
- `template/.claude/commands/sdd/complete.md` — Step 6 captures locals before clearing, step 10 clears state and commits atomically with archive, new step 11 Push and PR with platform detection and compare-URL fallback, version bump to 1.5.
- `template/.claude/commands/sdd/status.md` — Active Cycle output adds `Branch: {name} (from {base})` line, version bump to 1.5.
- `template/.claude/state/sdd-state.yaml` — Added `base_branch` and `branch_name` fields under `current_cycle` with inline NEW in v1.5 comments.
- `adoption-prompt.md` — Added idempotent v1.4 → v1.5 migration step.
- `.claude/commands/sdd/start.md`, `complete.md`, `status.md` — Mirrored changes in the active commands for this repo (dogfooding).
- `.claude/state/sdd-state.yaml` — Added new fields (populated with real values during the self-hosting cycle).
- `content/courses/07-sdd-context-engineering/modules/04-sdd-process.md` — Updated to teach auto-branching and auto-PR; Work Forest section notes base-branch capture honors current HEAD.
- `specs/constitution/governance.md` — STD-001 version row bumped from 1.2 (stale) to 1.5.
- `content/changelog/` — Site-wide entry dated 2026-04-17 with `type: standard-update`, `standards: [STD-001]`.

---

## 2026-04-06 — v1.4: Surface Tensions & Deep Investigation

**Origin:** TenDemo venture feedback (Munam Tariq, Walid Daniel). During the 11 Labs migration, `/sdd/start` scaffolded templates without surfacing any of the architectural decisions, technology forks, or constitutional tensions the agent could see — leading to wrong implementation choices discovered only during testing. Research of Agent OS (`shape-spec` command), GStack (`plan-ceo-review`, `office-hours` skills), and Addy Osmani's spec writing framework informed the design.

### Changes Made

#### 1. Surface Tensions step added to `/sdd/start` (`template/.claude/commands/sdd/start.md`, `skill/SKILL.md`)

**Before:** `/sdd/start` immediately scaffolded `changes/{slug}/` with `[REQUIRED]` templates and committed. It never read the codebase, constitution, or existing specs before scaffolding.

**After:** Before scaffolding, `/sdd/start` reads the relevant codebase context, existing feature specs, and constitutional principles (if STD-002 is active). It flags four specific types of findings: constitutional tensions, existing spec conflicts, technology forks with meaningful trade-offs, and hidden scope. If nothing is found, scaffolding proceeds immediately (identical to prior behavior). If findings exist, they're presented to the user, and decisions are incorporated into the scaffold.

**Why this earns its place:** The standard's core rule is "spec before code." A spec built on unexamined assumptions is worse than no spec — it gives false confidence. Surface Tensions is the agent doing due diligence on what it already knows before the user commits to a spec. The constitutional integration (STD-002) is where the real leverage is: the agent holds the team's stated principles in context and checks new proposals against them. This is not a questioning protocol or a mandatory brainstorming session — the agent flags what it finds, sometimes that's nothing.

#### 2. `/sdd/explore` command added (`template/.claude/commands/sdd/explore.md`, `skill/SKILL.md`)

**Before:** No pre-SDD investigation workflow existed. Users who wanted deep analysis before a cycle did it ad hoc in conversation (ephemeral) or manually created files.

**After:** `/sdd/explore {slug}` creates a `wip/{slug}/` folder for deep investigation. It starts with `00-overview.md` as an index, loads constitutional and codebase context, and supports iterative investigation where numbered files emerge organically per subject (gap analyses, architecture options, trade-off matrices, corner cases, strategic recommendations). `/sdd/start {slug}` detects existing WIP folders and pre-fills the cycle from the investigation.

**Why this earns its place:** Surface Tensions catches what the agent knows. But for complex features, architecture migrations, or new product directions, the user needs to build their case through back-and-forth exploration — challenge assumptions, compare approaches, investigate corner cases. This is a different activity than spec scaffolding: it produces a research artifact (`wip/` folder) that may or may not become an SDD cycle. The command provides consistent folder structure, automatic context loading, and a clean handoff to `/sdd/start`.

#### 3. Ambiguity resolution requirement added (`standard.md` §2.3)

**Before:** The standard required proposals but said nothing about examining existing specs for conflicts during the proposal phase.

**After:** New requirement §2.3 — "The proposal phase SHOULD include review of existing specs and project principles for tensions with the proposed change. Conflicts with existing specified behavior MUST be acknowledged as MODIFIED sections in the spec-delta, not silently overridden."

**Why this earns its place:** The second sentence is a correctness fix, not a feature. If you're changing existing specified behavior, that's by definition a MODIFIED section — the standard already requires it (§4, §5). This makes it explicit at the proposal stage rather than catching it at implementation.

### Evaluated and Rejected

| Capability | Reason for Rejection |
|---|---|
| **Formal complexity classification** (trivial / standard / complex) | The agent already knows when something is ambiguous. A classification system adds a meta-decision that wastes cycles without improving the actual flagging. |
| **Question quotas** (3-8 questions scaled to complexity) | Quotas create filler. If there are 2 real tensions, asking 3-5 means inventing noise. If there are 6, a cap of 5 suppresses signal. Flag what you find. |
| **Question dimension framework** (Architecture / Product / Edge Cases / Trade-offs) | Forces the agent to think in categories rather than naturally identifying what's unclear. Results in covering all four dimensions even when only one matters. |
| **Separate `/sdd/plan` command** | Fragments the workflow. Surfacing tensions is part of start, not a separate phase users must learn. |
| **`--quick` flag to skip tensions** | Implies the default is slow. The default should already be fast for simple changes (nothing to flag → proceed immediately). If the user says "just scaffold it," the agent respects that without needing a flag. |
| **Product critic persona** (GStack-style CEO review) | SDD's job is "spec before code," not "challenge your product vision." Product exploration belongs in `/sdd/explore`, not `/sdd/start`. Conflating the two makes every cycle pay the cost of product review. |
| **Persisted Q&A file** (`decisions.md`) | Decisions should be woven into proposal.md and spec-delta.md where they're actionable. A separate Q&A log is dead weight after the cycle starts. |
| **Mandatory questioning before every proposal** | Previously rejected in v1.2 for the same reason: adds overhead to simple changes. Surface Tensions is signal-driven (flag what you find), not protocol-driven (ask N questions). |

### Files Changed

- `template/.claude/commands/sdd/start.md` — Added Surface Tensions step (step 2), WIP detection in source resolution step (step 3), version bump to 1.4
- `template/.claude/commands/sdd/explore.md` — New command
- `skill/SKILL.md` — Added Always rule 10, `/sdd/explore` to commands table, cycle flow diagram updated, Deep Investigation section added
- `standard.md` — Version bump to 1.4, added §2.2 (Deep Investigation) and §2.3 (Ambiguity Resolution)

---

## 2026-04-06 — v1.3: External Issue Tracker Integration

**Origin:** TenDemo venture feedback (Walid Daniel, Munam Tariq). Teams using Linear (or GitHub Issues, Jira) as their operational hub face split-brain problems when the SDD backlog is a local YAML file. Ilian's directive: "if we use Linear as the backlog, I would not keep also a copy — just have the SDD commands work with Linear through the MCP integration."

### Changes Made

#### 1. Tracker-as-source-of-truth for backlog (`standard.md` §2.1, all commands)

**Before:** The backlog was exclusively a local `backlog/items.yaml` file. Teams using external trackers had to manually keep both in sync, leading to status drift and split-brain state.

**After:** The backlog supports two backends: an external issue tracker via MCP (Linear, GitHub Issues) or local YAML. When a tracker is configured, it becomes the single source of truth — no local copy is maintained. Detection is zero-config: install the tracker's MCP server and SDD auto-detects it, with a one-time confirmation prompt. The preference is stored in `sdd-state.yaml` as `tracker_preference`.

**Why this earns its place:** The standard's backlog tier was designed for solo founders and small teams without trackers. Real ventures use Linear/GitHub Issues as their operational brain — for GTM, stakeholders, weekly reporting, not just dev tickets. Forcing them to maintain a parallel YAML file is the exact dual-state problem SDD exists to solve. This change makes the backlog tier usable for teams with existing workflows.

#### 2. `--from` flag for `/sdd/start` (`template/.claude/commands/sdd/start.md`)

**Before:** `/sdd/start {slug}` created a blank scaffold. There was no way to pull context from an existing tracker issue or backlog item.

**After:** `/sdd/start {slug} --from {ref}` accepts a tracker issue ID (e.g., `TEND-42`) or local backlog reference (`backlog:3`). When provided, the proposal is pre-filled from the issue title, description, and comments. Sections with source context are marked `[REVIEW]` instead of `[REQUIRED]`.

**Why this earns its place:** Most real work starts from a tracker issue, not a blank scaffold. Pre-filling reduces friction and preserves context that would otherwise be lost in the handoff from "someone filed an issue" to "someone started implementing."

#### 3. Tracker status propagation (`template/.claude/commands/sdd/start.md`, `complete.md`)

**Before:** Starting or completing a cycle had no effect on external tracker state. Users had to manually update issue status in their tracker.

**After:** `/sdd/start` marks the tracker issue as In Progress. `/sdd/complete` marks it as Done and adds a comment linking to the archive. The tracker reference is stored in `current_cycle.tracker_ref` and cleared on completion.

**Why this earns its place:** Without automatic propagation, the tracker and repo state drift apart within hours. The whole point of tracker integration is that the tracker reflects reality — not that users have to update two systems.

#### 4. Tracker status in `/sdd/status` (`template/.claude/commands/sdd/status.md`)

**Before:** Status display showed standard version, cycle info, and task progress.

**After:** Now also shows tracker connection status (e.g., "Linear (connected)"), the tracker reference for the active cycle, and queued item count from the tracker when no cycle is active.

#### 5. Adoption prompt tracker question (`adoption-prompt.md`)

**Before:** Phase 1 asked about team size, change frequency, existing specs, and STD-002 status.

**After:** New question 5 asks about issue tracker preference. Phase 3d configures `tracker_preference`, verifies MCP connection, and creates the `sdd` label in the tracker.

### Design Decisions

1. **Tracker as source of truth, not bidirectional sync.** The tracker OR local YAML is authoritative, never both simultaneously. Sync engines are complexity traps that create merge conflicts and stale state.

2. **No git commits for status changes.** Tracker status updates (In Progress, Done) are tracker state, not repo state. The only git artifacts are the SDD cycle files. This addresses Walid's explicit concern.

3. **Tracker-agnostic interface.** Commands say "tracker" not "Linear." Detection checks for available MCP tools, which is inherently tracker-agnostic. Required capabilities: create issue, update status, query by label/status, fetch by ID.

4. **`sdd` label for filtering.** Every SDD-created issue gets an `sdd` label so commands can distinguish SDD items from GTM tasks, customer support tickets, and other issues in the same tracker.

5. **No migration of existing items.** Connecting a tracker does not auto-migrate `backlog/items.yaml` items. Users create them manually in the tracker if they want. Migration is a one-time task that doesn't justify the complexity.

6. **No tracker credentials stored.** The MCP integration handles auth. SDD stores only the preference and per-cycle reference. No API keys, OAuth tokens, or token management.

### Evaluated and Rejected

| Capability | Reason for Rejection |
|---|---|
| **Bidirectional sync** between tracker and local YAML | Complexity bomb. The whole point is to eliminate dual state, not manage it more carefully. Merge conflicts on YAML, stale state, debugging nightmares. |
| **Auto-migration** of existing `backlog/items.yaml` to tracker on first connect | One-time convenience with disproportionate complexity. Users can manually create the few items they care about. |
| **Sub-issue creation** for tasks.md items | Over-engineering. The tracker issue represents the cycle, not individual tasks. Tasks live in `tasks.md`. |
| **URL parsing** for `--from` (e.g., `--from https://linear.app/...`) | Convenience feature, not core. Parse the URL to extract issue ID. Can be added later without breaking changes. |
| **Learnings posted as tracker comments** | Nice-to-have but mixes concerns. Learnings are for the engineering team; tracker issues are for stakeholders. Low priority. |

### Files Changed

- `standard.md` — Updated §2.1 (Backlog Tier) with tracker backend options, version bump to 1.3
- `skill/SKILL.md` — Updated Backlog Tier section, decision tree, commands table, cycle flow diagram, required structure
- `template/.claude/commands/sdd/backlog.md` — Added tracker detection (step 1), branched add/confirm steps for tracker vs. local
- `template/.claude/commands/sdd/start.md` — Added `--from` argument, source resolution step, tracker update step, `tracker_ref` in state
- `template/.claude/commands/sdd/complete.md` — Added tracker update step (step 10), clear `tracker_ref` in state
- `template/.claude/commands/sdd/run-all.md` — Updated Phase 1 to read from tracker, updated Step B/D for tracker status
- `template/.claude/commands/sdd/status.md` — Added tracker status line, tracker ref for active cycles, queued count
- `template/.claude/commands/sdd/implement.md` — Version bump to 1.3
- `template/.claude/state/sdd-state.yaml` — Added `tracker_preference` and `current_cycle.tracker_ref` fields
- `adoption-prompt.md` — Added issue tracker question (Phase 1 Q5), tracker config in Phase 3d

---

## 2026-03-26 — v1.2: Red Flag Rationalization Enumeration

**Origin:** Knowledge extraction from obra/superpowers (93k+ GitHub stars, #1 Claude Code marketplace plugin). Jesse Vincent's core innovation: agents rationalize bypassing structured workflows, and explicitly naming those rationalizations in skill text prevents bypass. Validated by Dan Shapiro's research on persuasion principles applied to LLMs.

### Changes Made

#### 1. Red flag rationalization section added (`skill/SKILL.md`)

**Before:** The skill had Always/Ask First/Never rules defining what to do and not do, but did not address the specific rationalizations agents use to justify bypassing spec-before-code.

**After:** New "Red Flag Rationalizations" section between "Never" and "Decision" enumerates the six most common excuses agents generate to skip proposals: perceived simplicity, post-hoc spec writing, user pressure, misclassified bug fixes, false confidence, and scope minimization.

**Why this earns its place:** The standard's core rule is "spec before code." The v1.1 readiness gate fixed enforcement at the implementation boundary. This fixes enforcement at the decision boundary — the moment the agent decides whether a proposal is needed. These are complementary: the readiness gate catches proposals with placeholders; red flag enumeration prevents skipping the proposal entirely. This is not a new requirement — it is the existing requirement, enforced at the point where it most commonly fails.

### Evaluated and Rejected

| Capability | Reason for Rejection |
|---|---|
| **Two-stage verification** (spec compliance + code quality as separate passes) | STD-001 v1.1 deliberately chose the verification *principle* ("THAT you verify"), not the method ("HOW you verify"). Mandating two-stage review crosses into prescribing method. Note as best practice in course materials instead. |
| **Proposal self-review checklist** | Useful but belongs in command templates, not the standard or skill. The readiness gate already catches `[REQUIRED]` placeholders. Softer quality checks (vague language, missing evidence) are subjective and project-specific. |
| **Instruction hierarchy** (user > skills > defaults) | The SDD skill is passive (not user-invocable). Priority conflicts between user instructions and SDD rules are already handled by the Ask First section. An explicit hierarchy adds complexity without solving a real enforcement gap. |
| **Brainstorming phase before proposal** | `/sdd/design-review` was already rejected in v1.1 as UI-specific. A mandatory brainstorming phase before every proposal adds overhead to simple changes. The standard says "proposal before code," not "brainstorm before proposal." |
| **Placeholder-free plan requirements for tasks.md** | STD-001's tasks.md is an implementation tracking checklist, not a subagent dispatch plan. Superpowers' detailed plan format serves a different purpose (autonomous execution by fresh subagents with zero codebase context). Different tools for different jobs. |

### Files Changed

- `skill/SKILL.md` — Added "Red Flag Rationalizations" section after "Never"

---

## 2026-03-17 — v1.1: Readiness Gate & Verification Principle

**Origin:** Cross-pollination analysis between STD-001 (standard template) and MainStreet's production SDD implementation. MainStreet evolved 9 capabilities beyond the standard template through real-world use. Each was evaluated for inclusion in the standard.

### Changes Made

#### 1. Readiness gate strengthened (`template/.claude/commands/sdd/implement.md`)

**Before:** `/sdd/implement` only checked `spec-delta.md` for `[REQUIRED]` placeholders.

**After:** Checks ALL files in `changes/{slug}/` — proposal.md, spec-delta.md, and tasks.md. Lists which files still have unfilled placeholders.

**Why this earns its place:** The standard's core rule is "spec before code." A readiness gate that only checks one of three spec files is the standard failing to enforce its own principle. This is a correctness fix, not a feature.

#### 2. Spec verification requirement added (`standard.md` §9, `skill/SKILL.md` §Always.9, `template/.claude/commands/sdd/complete.md`)

**Before:** The standard defined Given/When/Then format but never required verifying scenarios against implementation. Specs could be written, committed, and archived without anyone confirming they actually hold.

**After:** New requirement §9 — "Spec scenarios MUST be verified before a cycle is marked complete. The verification method is project-specific." The `/sdd/complete` command now verifies scenarios before merging and shows unverified scenarios as a blocking error (overridable with `--force`).

**Why this earns its place:** A spec format without a verification expectation is a test framework with no test runner. The standard already mandates spec-before-code and archive-on-merge — verification closes the loop. Critically, the standard does NOT prescribe HOW to verify (that's project-specific), only THAT verification must happen.

### Evaluated and Rejected

The following capabilities from MainStreet's implementation were evaluated and intentionally excluded from the standard:

| Capability | Reason for Rejection |
|---|---|
| **Shipping agents** (spec-evaluator, progress-tracker, etc.) | Agents are inherently project-specific. A spec-evaluator depends on tech stack; a product-designer encodes brand guidelines. Standards define workflow, not instruments. |
| **Ledger system** (learnings, blockers, cycle logs) | Operational infrastructure for high-velocity projects. Overhead-to-value ratio is wrong for a universal standard. Ventures add this when they need it. |
| **`/sdd/backlog` command** | Task management isn't the standard's job. Teams already have Linear, GitHub Issues, etc. The standard owns "spec before code," not where work items come from. |
| **`/sdd/run-all` batching** | Workflow optimization for high-volume queues. Assumes backlog (rejected above) and a particular automation style. |
| **`/sdd/run-specs` runner** | A universal spec runner is impossible — verification is inherently project-specific. The fix was the verification *principle*, not a command. |
| **`/sdd/design-review`** | Only applies to UI projects. API ventures, CLIs, and data pipelines don't need Chrome screenshots. |
| **Subtask decomposition** | Prescribes how Claude manages task execution. The standard should say "implement following the spec," not dictate agent orchestration. |
| **Richer state tracking** | More fields = more maintenance = more drift. Minimal state (`slug`, `phase`, `started_at`) tracks exactly enough. |

### Files Changed

- `standard.md` — Added §9 (Spec Verification)
- `skill/SKILL.md` — Added Always rule 9
- `template/.claude/commands/sdd/implement.md` — Broadened readiness gate to all three files
- `template/.claude/commands/sdd/complete.md` — Added verification step (step 2), renumbered subsequent steps, added unverified scenarios error case, updated force-complete behavior
