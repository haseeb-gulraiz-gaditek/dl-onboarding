# Self-Evolving Loop Principles — Quick Reference

Use this cheatsheet during teaching moments. Cycle 1-2: full explanation. Cycle 3-4: name + core question. Cycle 5+: name only.

## The Nine Principles

| # | Principle | Core Question | Layer |
|---|-----------|--------------|-------|
| 1 | **Alignment** | How do you prevent goal drift in long-running systems? | 3 (Outer) |
| 2 | **Creative Freedom** | How do you balance exploration with exploitation? | 1 (Inner) |
| 3 | **Accumulated Learning** | How does intelligence compound across iterations? | 2 (Middle) |
| 4 | **Pivoting and Adaptation** | How does the system detect dead ends and change direction? | 2 (Middle) |
| 5 | **Human-in-the-Loop** | When should the system defer to human judgment? | 3 (Outer) |
| 6 | **Iteration Strategy** | What loop cadence matches the problem? | 2 (Middle) |
| 7 | **Backpressure** | What forces push back on bad output? | 1 (Inner) |
| 8 | **Safety and Sandboxing** | How do you contain the blast radius? | 3 (Outer) |
| 9 | **Meta-Learning** | How does the system improve its own improvement process? | 4 (Meta) |

## Four-Layer Architecture

| Layer | Name | Principles | Timescale | Key Mechanism |
|-------|------|-----------|-----------|---------------|
| 1 | **Inner Loop** | 2 (Creative Freedom), 7 (Backpressure) | Seconds-minutes | Execute, evaluate, iterate. Backpressure steers; freedom explores. |
| 2 | **Middle Loop** | 3 (Learning), 4 (Pivoting), 6 (Iteration) | Minutes-hours | Persist state, detect dead ends, manage cost. |
| 3 | **Outer Loop** | 1 (Alignment), 5 (HITL), 8 (Safety) | Hours-days | Prevent goal drift, gate decisions, contain blast radius. |
| 4 | **Meta Loop** | 9 (Meta-Learning) | Weeks-months | Reflect on process, accumulate patterns, tune loops below. |

## Composition Rule

Start at Layer 1. Add layers as the use case demands. Over-engineering a bounded task with four layers is waste. Under-engineering a long-running system with one layer is dangerous.

## Principle Pairings for Teaching Moments

| Discovery Question | Principle(s) | Why It Applies |
|-------------------|-------------|----------------|
| Scope + target + current state | P2 Creative Freedom | Defining the exploration space — what's in bounds, what's not |
| Objectives + success signals + time horizon | P7 Backpressure | Success signals ARE the backpressure — they push back on bad changes |
| Invariants + constraints + prior failures | P3 Accumulated Learning, P4 Pivoting | Prior failures are accumulated intelligence; constraints prevent known dead ends |
| Decision maker + approval process + autonomy | P5 HITL, P8 Safety | Governance defines the outer loop — who decides, when to gate, what to protect |
| Roadmap creation | P6 Iteration Strategy | Cycle cadence and scope must match the problem's timescale |
| Cross-cycle synthesis | P9 Meta-Learning | Double-loop learning — improving the improvement process itself |
| Trust graduation | P1 Alignment, P5 HITL | Earned autonomy prevents goal drift; graduated trust replaces binary on/off |
