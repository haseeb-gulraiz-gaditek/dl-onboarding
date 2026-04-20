# Venture Knowledge Foundation (STD-002)

This repository follows the Venture Knowledge Foundation standard. The sections below guide Claude Code on when and how to use each VKF command.

## Knowledge Operations

### Command Routing Table

When the user asks about or attempts something, consult this table and suggest the right command:

| User says / situation | Command | What it does |
|----------------------|---------|-------------|
| "I have a doc/sheet/notes to add" | `/vkf/ingest` | Classify and place external content (12 targets when `knowledge_types` configured) |
| "Where do architecture/UX/reference docs go?" | See STD-002 §3 | 5-type taxonomy: constitution, architecture, features, ux, reference |
| "Where do ADRs/decisions go?" | See STD-002 §3.5 | Colocate with the layer they constrain — never a global `adr/` directory |
| "Here's a meeting recording/transcript" | `/vkf/transcript` | Extract insights, generate meeting brief, update register |
| "What meetings have we had?" / "Meeting history" | Read `specs/meetings/INDEX.md` | Show meeting register with outcomes and brief links |
| "What did we decide in the [X] meeting?" | Read `specs/meetings/{date}-{title}.md` | Show meeting brief with decisions, learnings, and modifications |
| "What's missing?" / "What don't we know?" | `/vkf/gaps` | Scan for knowledge gaps with AI-proposed answers |
| "We need to change our positioning/mission/..." | `/vkf/amend` | Tiered amendment process for constitution |
| "Where did this info come from?" | `/vkf/audit --trace` | Trace any section back to its sources |
| "Are our docs up to date?" | `/vkf/freshness` | Check freshness + source staleness |
| "What are our goals this quarter?" | `/vkf/okrs` | View/update quarterly objectives |
| "What needs attention?" | `/vkf/workflow status` | Show document lifecycle and pending actions |
| Pasting content in chat without context | Suggest `/vkf/ingest --inline` | Route pasted content through proper ingestion |
| Editing constitution files directly | Suggest `/vkf/amend` | Ensure proper change governance |
| "Initialize" / "Set up VKF" | `/vkf/init` | Bootstrap STD-002 structure |
| "Are we compliant?" / "Check everything" | `/vkf/validate` | Full STD-002 audit |
| "Draft the mission/personas/..." | `/vkf/constitution` | Interactive constitution drafting |
| "Research competitors/market/..." | `/vkf/research` | Market research for constitution sections |

### Path Resolution

All VKF commands resolve paths from `.claude/state/vkf-state.yaml`:
- `constitution_root` (default: `specs/constitution`) — where constitution files live
- `features_root` (default: `specs/features`) — where feature specs live

References to `specs/constitution/` and `specs/features/` below use defaults. Substitute configured values.

### Before Modifying Knowledge Base Files

Before editing any file in the specs tree, evaluate this decision tree:

1. **Is this a constitution file?** (any `.md` in the configured constitution root)
   - YES → Is the file still in Draft state (has `[REQUIRED]` placeholders)?
     - YES → Use `/vkf/constitution` for initial drafting
     - NO → Use `/vkf/amend` — announce: "This is an active constitution section. I'll use the amendment process."
   - NO → Continue normally (feature specs follow SDD if STD-001 is adopted)

2. **Is the user providing external content?** (pasting text, sharing a file reference, referencing a doc)
   - YES → Announce: "I'll route this through `/vkf/ingest` to classify and place it properly."
   - NO → Continue normally

3. **Is the user sharing a meeting transcript or recording notes?**
   - YES → Announce: "I'll use `/vkf/transcript` to extract and classify insights."
   - NO → Continue normally

### Passive Behaviors

Things to do automatically without being asked:

- **After any ingestion or constitution change:** Remind the user that `/vkf/gaps` can identify what's still missing
- **When freshness scan shows STALE specs:** Suggest specific actions (re-review, ingest new data, or run gap analysis)
- **When editing constitution files:** Always check amendment tier and announce it — "This is a C2 (substantive) change because it alters the meaning of the positioning statement."
- **When OKRs exist and a related spec changes:** Note: "This change relates to OKR [objective]. Consider updating progress."
- **After completing a gap resolution cycle:** Suggest running `/vkf/workflow check` to see if any review triggers fired
- **When the user asks a question the constitution should answer but doesn't:** Note: "The constitution doesn't address this yet. Want me to run `/vkf/gaps` to surface this formally?"

### Always

- Log every ingestion and transcript extraction to `specs/ingestion-log.yaml`
- Announce amendment tier before making constitution changes
- Track "we don't know" as explicit knowledge state, not as absence
- Update `Last amended` / `Last reviewed` dates on every document change
- Update `.claude/state/vkf-state.yaml` after significant operations
- Follow commit conventions: `[ingest]`, `[gaps]`, `[constitution]`, `[transcript]`, `[okr]`, `[workflow]`, `[foundation]`, `[spec-review]`, `[validate]`

### Ask First

- Applying gap resolution answers that change active constitution content (routes through amend)
- Archiving OKR quarters
- Transitioning documents from Active to Archived
- Overwriting an existing constitution file that has been filled out
- Marking a spec as reviewed without reading it
- Running exa.ai research that may consume API credits

### Never

- Never overwrite audit log entries (append-only)
- Never delete gap reports (they are historical records)
- Never bypass amendment tiers — even if the user says "just change it", announce the tier
- Never auto-resolve gaps without user review
- Never overwrite filled constitution content with template placeholders
- Never mark a `[REQUIRED]` section as complete without content
- Never fabricate market data — use exa.ai/research or clearly label assumptions
