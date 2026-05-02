# Governance

> Part of the Mesh Product Constitution
> **Tier:** Extended — adopted to make solo authority and the explicit "amend on first hire" trigger an on-the-record decision rather than implicit.

**Last amended:** 2026-04-27

---

## Decision Authority

| Decision Type | Authority | Process |
|---------------|-----------|---------|
| All product decisions (features, scope, sequencing) | Haseeb Gulraiz (sole founder) | Sole discretion until first co-founder or hire |
| Constitution amendments (C0–C3 per STD-002 §8) | Haseeb Gulraiz | Tier-aware (see Amendment Process below) |
| Feature spec-delta approvals (per STD-001) | Haseeb Gulraiz | Sole discretion via `/sdd:start` → `/sdd:complete` |
| Public launch, pricing, monetization changes | Haseeb Gulraiz | Sole discretion |
| Hiring / team expansion | Haseeb Gulraiz (when budget exists) | n/a — when this triggers, this document is amended (C2) |

## Amendment Process

Tier definitions follow STD-002 §8 verbatim:

- **C0 (Cosmetic)** — Direct edit for typos, formatting, dates. Commit with `[constitution]` prefix; no further process.
- **C1 (Clarification)** — History entry for rewording without meaning change. Direct edit OR `/vkf/amend`; row added to Amendment History below.
- **C2 (Substantive)** — Proposal + propagation check for content changes. `/vkf/amend` required; check that other constitution files (and any feature specs that reference the changed section) stay coherent; bump `Last amended` date on the file.
- **C3 (Structural)** — Full C2 process + principle conflict analysis + rollback plan. `/vkf/amend` required.

**Mesh-specific addition to C3:** pause ≥24 hours between drafting a C3 amendment and committing it. C3 changes alter the load-bearing identity of the venture (mission, primary customer definition, a "We Always" / "We Never" principle). The pause forces a second-pass reflection before the change is committed.

**Trigger for amending this document:** when a co-founder or first hire joins, this section is amended (C2) to add their authority and to introduce a 2-person review for C2 / C3 changes (sole-amender ceases at headcount = 2).

## Amendment History

| Date | File | Change | Author |
|------|------|--------|--------|
| 2026-04-27 | governance.md | Initial draft — solo authority, STD-002 tier alignment, explicit amend-on-first-hire trigger, +24h pause for C3 | Haseeb Gulraiz |
| 2026-05-02 | principles.md | C2 — We Always #3: allow well-matched launches to appear alongside organic recs in a distinct `launches` slot, gated by the same match-quality threshold as the concierge nudge. Storage and ranking pipelines stay separate. | Haseeb Gulraiz |
