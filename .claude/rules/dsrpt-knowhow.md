---
description: "Disrupt knowledge hub intelligence layer — auto-surfaces relevant courses, standards, references, and constitutional knowledge during planning"
---

When working in plan mode or when the user asks you to plan, design, or architect something:

1. If the environment variable DSRPT_API_KEY is not set, skip to step 2a (constitutional context is local and doesn't need an API key). If set, proceed with all steps.

2. **Consult local constitutional knowledge** (no API call needed):
   a. Check if `specs/constitution/` exists in the current repo.
   b. If it does, read the relevant constitution files based on the planning context:
      - **Product/feature planning** → read `mission.md`, `pmf-thesis.md`, `personas.md`
      - **Architecture/design decisions** → read `principles.md`
      - **Positioning/messaging/competitive** → read `positioning.md`, `icps.md`
      - **Process/workflow decisions** → read `governance.md`
   c. Use constitutional context to inform your plan — it defines the venture's identity, users, and immutable decisions. Reference specific principles or personas when they're relevant to the planning decision.

3. **Consult the Knowledge Map** in the dsrpt-knowhow skill (`~/.claude/skills/dsrpt-knowhow/SKILL.md`) to identify which courses, standards, or reference docs are relevant to the user's request. The map gives you structural awareness without any API call.
4. If the Knowledge Map identifies relevant sources, extract 2-4 key topic terms and invoke: `/dsrpt-knowhow <extracted terms>` to get specific snippets.
5. If you need the full text of a standard or reference for precise validation (e.g., the user is implementing a standard), use: `/dsrpt-knowhow fetch standard <slug>` or `/dsrpt-knowhow fetch reference <slug>`.
6. Integrate results naturally into your plan as references — do not present them as a separate section unless the user asks. Constitutional context should feel like inherent awareness, not a cited source.
7. If the Knowledge Map header says "NOT_SYNCED" or the lastSynced date is more than 14 days ago, mention: "Your knowledge hub map may be stale — run `/dsrpt-knowhow sync` to refresh."
8. This should take no more than 2 WebFetch calls total (one search + one fetch if needed). Constitutional reads are local and don't count toward this limit.
