---
name: dsrpt-knowhow
description: "Disrupt AI engineering intelligence layer — structural awareness, semantic search, full content access, and standard installation for the knowledge hub."
user-invocable: true
argument-hint: "[search query | sync | fetch <type> <path> | install <standard-slug> | map]"
---

# Disrupt Knowledge Hub — Intelligence Layer

## Purpose

Multi-mode intelligence layer for the Disrupt AI engineering knowledge hub. Provides structural awareness of all courses, standards, and reference docs — plus semantic search, full content retrieval, and standard installation into any repo.

## Authentication

Read the `DSRPT_API_KEY` environment variable. If not set, tell the user:
"Set up your API key: add `DSRPT_API_KEY` to the `env` section of `~/.claude/settings.json`. Get a key at https://disrupt-knowhow.firebaseapp.com/intelligence-layer"

**Base URL**: `https://disrupt-knowhow.firebaseapp.com/api/content`

## Command Routing

Parse `$ARGUMENTS` and route to the appropriate mode:

| Arguments | Mode | Description |
|-----------|------|-------------|
| `sync` | Sync | Check version, refresh knowledge map |
| `fetch <type> <path>` | Fetch | Retrieve full content |
| `install <standard-slug>` | Install | Fetch standard package, write to repo |
| `map` | Map | Display the embedded knowledge map |
| *(anything else or empty)* | Search | Semantic search (default) |

---

## Mode: Search (default)

When arguments are plain text (not a subcommand):

1. If no arguments were provided (invoked by plan-mode rule), extract 2-4 key topic terms from the current conversation context
2. **Before searching, consult the Knowledge Map below** to identify which courses, standards, or references are likely relevant. This avoids blind searches and lets you give the user targeted context even if the search API returns imprecise results.
3. Use WebFetch to call: `GET <Base URL>/search?q=<query>&key=<DSRPT_API_KEY>&limit=5`
4. Parse the JSON response
5. For each result, format as:
   - **[Title]** (type) — snippet
   - Link: url
6. Present results under a "Knowledge Hub References" heading

## Mode: Sync

When arguments are `sync`:

1. Call `GET <Base URL>/meta?key=<DSRPT_API_KEY>` — returns `{ buildSha, buildDate, coursesCount, standardsCount, referencesCount, agentsCount }`
2. Compare `buildSha` with the value in the Knowledge Map header below
3. If they match: report "Knowledge map is up to date (build <sha>, <date>)"
4. If they differ:
   a. Call `GET <Base URL>/manifest?key=<DSRPT_API_KEY>` — returns full catalog
   b. Rebuild the "Knowledge Map" section of THIS file (`~/.claude/skills/dsrpt-knowhow/SKILL.md`) using the manifest data. Preserve the table format exactly. Update the build SHA and date in the header.
   c. Report what changed: new/removed courses, updated standards, etc.
5. If buildSha matches but lastSynced is very old, update the lastSynced date

## Mode: Fetch

When arguments start with `fetch`:

Parse: `fetch <type> <path>` where type is one of: `module`, `standard`, `reference`, `agent`

| Type | API Call | Example path |
|------|----------|-------------|
| module | `GET <Base URL>/course/<dir>/<section>/<module>?key=...` | `03-agentic-memory/modules/01-memory-fundamentals` |
| standard | `GET <Base URL>/standard/<slug>?key=...` | `std-002-venture-knowledge-foundation` |
| reference | `GET <Base URL>/reference/<slug>?key=...` | `production-patterns` |
| agent | `GET <Base URL>/agents?key=...` then filter by name | `revision-validator` |

Present the full content to the conversation. This is useful for:
- Validating implementations against authoritative source material
- Answering detailed questions that need more than a snippet
- Comparing local code against standard requirements

## Mode: Install

When arguments start with `install`:

Parse: `install <standard-slug>`

The slug can be a short form (`std-002`) or full slug (`std-002-venture-knowledge-foundation`). Match against the Knowledge Map to resolve.

1. Call `GET <Base URL>/standard/<full-slug>/installable?key=<DSRPT_API_KEY>`
2. The response contains:
   ```json
   {
     "standard": { "slug", "id", "title", "status", "content" },
     "skill": { "path": "skill/SKILL.md", "content": "..." } | null,
     "references": [{ "path": "...", "content": "..." }],
     "templates": [{ "path": "...", "content": "..." }]
   }
   ```
3. For each file in `templates`, write it to the current repo at the path specified. Template paths are relative to the repo root (e.g., `.claude/commands/vkf/init.md`).
4. If a `skill` is included, write the skill definition to `.claude/skills/<skill-name>/SKILL.md` in the current repo. Extract the skill name from the SKILL.md frontmatter.
5. If `references` are included, write them alongside the skill definition at `.claude/skills/<skill-name>/references/`.
6. Report what was installed: list all files written, organized by type (commands, skill, references, templates).
7. Remind the user to add any required CLAUDE.md content if a template CLAUDE.md was included.

## Mode: Map

When arguments are `map`:

Display the Knowledge Map section below, formatted cleanly. This is useful when the user wants to see what the knowledge hub contains without making any API call.

---

## Knowledge Map (build 2d9c1fd | 2026-04-06)

### Courses

| Directory | Title | Category | Key Topics |
|-----------|-------|----------|------------|
| 01-claude-code-mastery | Claude Code Mastery | foundations | CLAUDE.md, hooks, MCP servers, custom slash commands, skills, agents, permissions |
| 10-information-engineering | Information Engineering | foundations | knowledge architecture, RAG evolution, context engineering, MCP protocol |
| 04-ai-first-development | AI-First Development | foundations | team transformation, AI-native workflows, organizational adoption |
| 07-sdd-context-engineering | SDD & Context Engineering | core | spec-driven development, context engineering, spec-deltas, change proposals |
| 08-context-engineering-intelligence-layers | Context Engineering Intelligence Layers | core | intelligence layers, knowledge systems, production patterns |
| 06-llm-observability | LLM Observability | core | evaluation strategies, monitoring, observability platforms, metrics |
| 02-agentic-frameworks | Agentic Frameworks | advanced | LangGraph, CrewAI, multi-agent orchestration, tool use, agent patterns |
| 03-agentic-memory | Agentic Memory | advanced | RAG, vector stores, memory architectures, retrieval patterns |
| 09-self-evolving-agentic-loops | Self-Evolving Agentic Loops | advanced | autonomous loops, meta-learning, evaluation-driven development, constitutional governance |
| 05-cloud-native-ai | Cloud-Native AI | advanced | Kubernetes, model serving, GPU orchestration, production deployment |

### Standards

| ID | Slug | Title | Status | Commands |
|----|------|-------|--------|----------|
| STD-001 | std-001-spec-driven-development | Spec-Driven Development | Adopted | /sdd/* |
| STD-002 | std-002-venture-knowledge-foundation | Venture Knowledge Foundation | Adopted | /vkf/* |
| STD-003 | std-003-venture-metrics | Venture Metrics | Under Review | /metrics/* |

### Reference Docs

| Slug | Title | Category |
|------|-------|----------|
| production-patterns | Production AI Patterns | engineering |
| storage-comparison | Storage Comparison Matrix | engineering |
| mcp-interoperability | MCP Interoperability Guide | engineering |
| decision-frameworks | Decision Frameworks | engineering |
| glossary | AI Engineering Glossary | reference |

### Constitutional Knowledge

If the current repo has a `specs/constitution/` directory (STD-002 adopted), these files define the venture's identity and should inform planning decisions:

| File | Purpose | When to consult |
|------|---------|----------------|
| mission.md | Why this venture exists | Any strategic or product planning |
| pmf-thesis.md | Who the users are, why they care | Feature planning, prioritization |
| personas.md | User archetypes and their needs | UX decisions, content targeting |
| icps.md | Ideal customer profiles | Go-to-market, segmentation decisions |
| positioning.md | How the venture differentiates | Messaging, competitive decisions |
| principles.md | Immutable product decisions | Any design or architecture choice |
| governance.md | How decisions get made | Process and workflow planning |

**Note:** Constitutional files are local (not served via API). Read them directly from `specs/constitution/` when the directory exists.

---

## Always

- Consult the Knowledge Map before making API calls — use structural awareness to guide searches
- Show source links for every search result
- Keep search output concise (max ~1500 chars)
- For `fetch` and `install`, present full content without truncation
- After `install`, list every file written

## Never

- Block or slow down the user's workflow
- Make more than 2 WebFetch calls per invocation (1 for search/fetch, 1 for sync meta check)
- Show results if the API returns an error — continue silently
- Overwrite existing files during `install` without confirming with the user first
