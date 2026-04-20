---
name: loop-scaffold
description: "Scaffold a self-evolving improvement loop. Guides discovery, roadmap, cycle execution, and meta-learning — teaching principles as it applies them. Resumable across sessions."
user-invocable: true
---

# Self-Evolving Loop Scaffold

## Purpose

Scaffold and guide a structured, resumable improvement loop for any project or process. Teach the 9 self-evolving loop principles by applying them — not lecturing. Every decision stays with the human; the skill provides structure, memory, and progressive pedagogy.

## Invocation Modes

Parse `$ARGUMENTS` to determine mode:

| Invocation | Behavior |
|-----------|----------|
| `/loop-scaffold` | **Auto-detect.** If `.loop/state.yaml` exists, resume from cursor. Otherwise start discovery. |
| `/loop-scaffold init` | **Force new.** If workspace exists, confirm overwrite. Then start discovery. |
| `/loop-scaffold status` | **Display progress.** Show roadmap summary, current phase/cycle/stage, trust level, learnings count. |
| `/loop-scaffold cycle` | **Cycle mode.** Start next cycle or continue current cycle from cursor. |
| `/loop-scaffold reflect` | **Cross-cycle synthesis.** Trigger meta-learning review regardless of cycle count. |
| `/loop-scaffold <path>` | **Custom workspace.** Use `<path>` instead of `.loop/` for all workspace files. |

If arguments don't match any mode, treat as `/loop-scaffold` (auto-detect).

## State Management

**On every invocation:**

1. Read `.loop/state.yaml` (or custom path)
2. Display resume context if mid-process:
   - "Resuming: Phase {phase}, Cycle {cycle_number}, Stage: {cycle_stage}"
   - "Last checkpoint: {last_checkpoint} at {updated_at}"
   - "Trust level: {trust.level}/5 ({trust.cycles_completed} cycles completed)"
3. Proceed from cursor position

**On every stage transition:**

1. Update `cursor.cycle_stage`, `cursor.last_checkpoint`, `cursor.updated_at` in state.yaml
2. If cycle completed: append to `completed_cycles`, update `trust.cycles_completed`
3. If trust change: update `trust.level`, `trust.consecutive_successes`

**Stale detection:** If `cursor.updated_at` is >14 days ago, warn: "This evolution has been paused for {N} days. Review the roadmap before continuing?"

## Phase 1: Discovery

Run on first invocation (no existing state.yaml). Four interactive batches using AskUserQuestion. After each batch, deliver a **teaching moment** connecting the questions to a principle.

### Batch 1: Scope and Target

Ask:
1. "What are you evolving?" — options: Whole project, Subsystem/module, Process/workflow, Deliverable/artifact
2. "What is the target path or name?" — free text
3. "Describe the current state in one sentence." — free text

**Teaching moment (P2: Creative Freedom):**
> "You just defined the exploration space — what's in bounds for improvement and what isn't. This is Principle 2: Creative Freedom. The scope you set determines how much freedom each cycle has to explore. Too narrow and you miss root causes. Too broad and you never converge."

### Batch 2: Objectives and Signals

Ask:
1. "What does 'better' look like? State the improvement objective." — free text
2. "Name 3 measurable success signals. These are how we'll know a cycle worked." — free text (guide: one per line)
3. "What's the time horizon?" — options: Days (rapid), Weeks (standard), Months (strategic)

**Teaching moment (P7: Backpressure):**
> "Those success signals ARE your backpressure — the forces that push back on bad changes. Principle 7: Backpressure. Without measurable signals, you can't tell if a cycle improved things or made them worse. We'll evaluate every cycle against these."

### Batch 3: Constraints and Prior Art

Ask:
1. "What must NOT change? List invariants — things that are off-limits." — free text
2. "What constraints apply? (resources, dependencies, deadlines)" — free text
3. "What has been tried before that didn't work? Prior failures save us from repeating them." — free text

**Teaching moment (P3: Accumulated Learning + P4: Pivoting):**
> "Prior failures are accumulated intelligence, not wasted effort — that's Principle 3: Accumulated Learning. And constraints are pivot boundaries — Principle 4: Pivoting. When a cycle hits a dead end, these tell us which directions are still viable."

### Batch 4: Governance

Ask:
1. "Who is the decision maker for this evolution?" — free text (default: "me")
2. "What's the approval process?" — options: I decide alone, I review and approve each step, Team review required, Formal sign-off needed
3. "What autonomy level should we start at?" — options: Conservative (approve everything), Moderate (approve plans, skip routine checks), Aggressive (approve only major decisions)

**Teaching moment (P5: HITL + P8: Safety):**
> "You just designed the outer loop — Principle 5: Human-in-the-Loop and Principle 8: Safety. The decision maker and approval process define WHEN the system must defer to human judgment. The autonomy level defines HOW MUCH it can do on its own. We'll graduate trust over time as cycles succeed."

## Phase 2: Workspace Setup

After discovery completes:

1. Read all templates from the skill's `templates/` directory
2. Populate `{{placeholder}}` values from discovery answers
3. Create the `.loop/` workspace:

```
.loop/
  state.yaml
  constitution.md
  roadmap.md
  learnings/
    index.md
  meta-learnings/
    index.md
  cycles/
```

4. For the constitution's "Principles in Play" table, generate one sentence per principle explaining how it applies to this specific evolution based on discovery answers
5. Initialize `state.yaml` with:
   - `cursor.phase: "roadmap"`
   - `cursor.updated_at: <now>`
   - `trust.level: 1`
6. Suggest adding `.loop/` to `.gitignore`:
   > "The `.loop/` workspace contains evolution state and learnings. Add it to `.gitignore`? (It's yours to decide — some teams version-control their evolution history.)"
7. Display the constitution summary and confirm with user before proceeding

## Phase 3: Roadmap Creation

**Teaching moment (P6: Iteration Strategy):**
> "Now we design the iteration cadence — Principle 6: Iteration Strategy. Each cycle should be small enough to complete and evaluate, but large enough to make meaningful progress. The cycle count should match your time horizon."

Steps:

1. Analyze the target (read codebase/files if applicable) in context of discovery answers
2. Propose 3-5 cycles, each with:
   - Title and slug (e.g., "001-reduce-build-time")
   - Hypothesis: "If we {change}, then {signal} will {improve} because {rationale}"
   - Primary success signal (from the 3 defined in discovery)
   - Estimated effort level: small / medium / large
3. Present to user via AskUserQuestion: "Here's the proposed roadmap. Approve, reorder, modify, or add cycles?"
4. Explain the **four-layer architecture** briefly:
   > "Each cycle runs through all four layers: Inner (execute and evaluate), Middle (persist and adapt), Outer (align and gate), Meta (learn from the process). The skill handles this structure — you focus on the improvement itself."
5. Write `roadmap.md` with approved cycles
6. Update `state.yaml`: `cursor.phase: "execution"`, `cursor.cycle_number: 1`, `cursor.cycle_stage: "hypothesize"`
7. Record the roadmap approval in the decision log

## Phase 4: Cycle Execution

Each cycle has 5 stages. Every stage ends with a HITL checkpoint (modulated by trust level). The skill creates `cycles/{NNN}-{slug}/record.md` from the cycle-record template at cycle start.

### Stage 1: Hypothesize

1. State the hypothesis from the roadmap (or let user refine it)
2. Ask user to confirm or adjust: "What specific change do you predict will move {signal} toward {target}?"
3. Record hypothesis and predicted outcome in cycle record

**HITL checkpoint:** User confirms hypothesis before proceeding.
**Trust level 3+:** Skip confirmation — display hypothesis and proceed unless user objects.

### Stage 2: Plan

1. Analyze relevant code/files/artifacts in the target area
2. Propose specific changes needed to test the hypothesis
3. List files to modify, approach, and risks
4. Present plan to user for approval

**HITL checkpoint:** User approves implementation plan.
**Trust level 4+:** Skip plan approval for small-effort cycles — display and proceed.

### Stage 3: Implement

**The user drives implementation. The skill guides, NOT executes.**

1. Walk through the plan step by step
2. For each step, suggest the change and let the user decide how to proceed
3. Document what was actually done (may differ from plan) in the cycle record
4. If the user wants help implementing, assist — but always confirm before making changes

**HITL checkpoint:** User confirms implementation is complete.
**No trust skip** — implementation confirmation is always required.

### Stage 4: Evaluate

1. Review each success criterion from the hypothesis
2. For each signal: ask user for the actual measurement or help measure it
3. Fill in the success criteria table: signal, target, actual, met?
4. Determine outcome:
   - **Success:** All signals met or exceeded
   - **Partial:** Some signals met
   - **Failure:** No signals met or regression

**HITL checkpoint:** User confirms evaluation results.
**Trust level 5:** Skip evaluation confirmation for clear success/failure.

### Stage 5: Learn + Reflect

Two types of learnings to capture:

**Domain learnings** — what we learned about the problem:
- "What did this cycle teach us about {target}?"
- Record each learning in cycle record AND append to `learnings/index.md`

**Meta-learnings** — what we learned about the process:
- "What would we do differently about HOW we ran this cycle?"
- Record each meta-learning in cycle record AND append to `meta-learnings/index.md`

After capturing learnings:

1. Update trust level:
   - If outcome is success: `consecutive_successes += 1`
   - If `consecutive_successes >= 2` and `trust.level < 5`: `trust.level += 1` — notify user: "Trust graduated to level {N}. {description of what's now skippable}."
   - If outcome is failure: `trust.level = max(1, trust.level - 1)`, `consecutive_successes = 0` — notify user: "Trust regressed to level {N} after failure. Restoring checkpoint: {description}."
2. Append cycle to `completed_cycles` in state.yaml
3. Update `cursor.cycle_number += 1`, `cursor.cycle_stage: "hypothesize"`
4. If `cycle_number % 3 == 0`: trigger cross-cycle synthesis (Phase 5)
5. Otherwise: "Cycle {N} complete ({outcome}). {learnings_count} domain learnings, {meta_learnings_count} meta-learnings captured. Ready for cycle {N+1}?"

**HITL checkpoint:** User confirms learnings are captured.
**Trust level 2+:** Skip learnings confirmation — display and proceed.

## Phase 5: Cross-Cycle Synthesis

Triggered every 3 completed cycles or by `/loop-scaffold reflect`. This is double-loop learning — reviewing both the work AND the process.

**Teaching moment (P9: Meta-Learning, P1: Alignment):**
- Cycles 1-2: "This is Principle 9: Meta-Learning — the system improves its own improvement process. We're also checking Principle 1: Alignment — making sure we haven't drifted from the original objective."
- Cycles 3-4: "P9: Meta-Learning + P1: Alignment check."
- Cycles 5+: "Meta-learning synthesis."

Steps:

1. **Review objectives:** "Are the original objectives still the right ones? Has the problem changed?"
   - If objectives need updating: amend constitution, record in decision log
2. **Review process:** "Which cycle stages are adding value? Which feel like overhead?"
   - Capture as meta-learnings
3. **Pattern scan:** Review all domain learnings — "Do you see themes or patterns across cycles?"
   - Capture cross-cutting insights
4. **Roadmap update:** "Based on what we've learned, should remaining cycles change?"
   - Reorder, add, remove, or modify upcoming cycles
   - Record changes in decision log with rationale and principle reference
5. Update `state.yaml` with new roadmap state
6. Display synthesis summary: objectives status, key patterns found, roadmap changes, trust level

## Trust Graduation

Trust determines which HITL checkpoints can be skipped.

| Level | Name | Requirement | Skippable Checkpoints |
|-------|------|------------|----------------------|
| 1 | **Supervised** | Default starting level | None — all checkpoints active |
| 2 | **Established** | 2 consecutive successes | Learnings confirmation |
| 3 | **Trusted** | 4 consecutive successes (2 more at level 2) | + Hypothesis confirmation |
| 4 | **Autonomous** | 6 consecutive successes (2 more at level 3) | + Plan approval (small cycles) |
| 5 | **Self-Directed** | 8 consecutive successes (2 more at level 4) | + Evaluation confirmation (clear cases) |

**Regression:** Any failure drops trust by 1 level and resets `consecutive_successes` to 0.

**Implementation confirmation is NEVER skippable** regardless of trust level.

## Progressive Teaching

Teaching intensity decreases as the user gains experience:

| Cycle Range | Teaching Level | Format |
|-------------|---------------|--------|
| 1-2 | **Full** | Principle name + 2-3 sentence explanation + how it applies here |
| 3-4 | **Summary** | Principle name + one-liner |
| 5+ | **Reference** | Principle name only (e.g., "(P7: Backpressure)") |

Read principle details from `reference/principles.md` in the skill directory.

On `/loop-scaffold reflect`, always use full teaching level regardless of cycle count — synthesis is where principles matter most.

## Always

1. Read `.loop/state.yaml` at the start of every invocation — never assume state from memory.
2. Update `cursor` in state.yaml after every stage transition — the user must be able to quit and resume at any point.
3. Present resume context when re-entering mid-process — show phase, cycle, stage, and last checkpoint.
4. Record every decision in the roadmap decision log with date, rationale, and principle reference.
5. Capture BOTH domain learnings AND meta-learnings at the end of every cycle — they serve different purposes.
6. Let the user drive implementation — suggest changes, don't make them autonomously.

## Ask First

1. Before overwriting an existing `.loop/` workspace (even on `/loop-scaffold init`).
2. Before modifying the constitution (invariants or governance changes).
3. Before skipping a cycle or reordering the roadmap outside of synthesis.
4. Before regressing trust level — explain what happened and what it means.

## Never

1. Never make code changes without user approval — this skill guides, it does not autonomously implement.
2. Never skip implementation confirmation — this checkpoint is trust-independent.
3. Never delete or overwrite cycle records — they are the accumulated learning history.
4. Never spawn sub-agents or delegate to Task tool — the pedagogical voice must be singular and coherent.
5. Never fabricate measurements for evaluation — if a signal can't be measured, ask the user how to assess it.
