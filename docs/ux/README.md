# UX

User-experience knowledge — visual design, interaction patterns, and the design briefs that informed the implementation.

## Contents

- **[design-brief.md](design-brief.md)** — Mesh's UX language brief: tap-and-go question flow, dual-pane onboarding shell, OKLCH color tokens, ToolGraph canvas. Informed cycles #13 (frontend-core) and #15 (live-narrowing).

## When to add a doc here

- A new surface gets a visual or interaction pattern that other surfaces should mirror (dual-pane onboarding shell, header-bell pill, score-band layer chips).
- Design tokens or motion grammar evolve enough to need documenting (OKLCH palette tweaks, animation cadence changes).
- Cross-page UX invariants emerge from cycles (e.g., "every tool slug must be a clickable Link to /p/{slug}").

## Freshness

UX knowledge has medium decay — patterns change as features ship. A short note when a pattern is broken or evolved beats keeping the brief perfectly synced.
