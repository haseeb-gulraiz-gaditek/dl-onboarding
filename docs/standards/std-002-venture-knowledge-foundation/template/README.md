# VKF Command Template

Starter kit for projects adopting **STD-002 Venture Knowledge Foundation**.

## Quick Setup

Copy the `.claude/` folder to your project root:

```bash
cp -r .claude/ /path/to/your-project/.claude/
```

Then run the init command:

```
/vkf/init
```

This creates all required directories and template files.

## Directory Structure

After setup, your project should have:

```
your-project/
├── .claude/
│   ├── commands/
│   │   └── vkf/
│   │       ├── init.md           # Bootstrap structure
│   │       ├── validate.md       # Audit compliance
│   │       ├── constitution.md   # Interactive drafting
│   │       ├── freshness.md      # Freshness scan
│   │       └── research.md       # Exa.ai market research
│   └── state/
│       └── vkf-state.yaml        # Foundation tracking
├── specs/
│   ├── constitution/
│   │   ├── index.md              # Summary + links
│   │   ├── mission.md            # Mission & vision
│   │   ├── pmf-thesis.md         # PMF thesis
│   │   ├── personas.md           # User personas
│   │   ├── icps.md               # Ideal customer profiles
│   │   ├── positioning.md        # Market positioning
│   │   ├── principles.md         # Product principles
│   │   └── governance.md         # Decision authority
│   └── features/                 # Feature specifications
├── changes/                      # Active change proposals
└── archive/                      # Completed changes
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `/vkf/init` | Scaffold directory structure and template files |
| `/vkf/validate` | Audit repo against all STD-002 requirements |
| `/vkf/constitution` | Interactive constitution section drafting |
| `/vkf/constitution [section]` | Draft a specific section (e.g., `personas`) |
| `/vkf/freshness` | Check spec freshness across repo |
| `/vkf/research [topic]` | Exa.ai market research for constitution sections |

## Workflow

```
/vkf/init
    │
    ▼
Directory structure created with template files
    │
    ▼
/vkf/constitution          # Fill out each section interactively
/vkf/research personas     # Research to inform drafting (optional)
    │
    ▼
/vkf/validate              # Check compliance
    │
    ▼
/vkf/freshness             # Ongoing freshness monitoring
```

## After STD-002

Once all constitution sections are filled and validated, the repo is ready for STD-001 (Spec-Driven Development). Add the SDD commands:

```bash
cp -r /path/to/std-001-template/.claude/commands/sdd/ .claude/commands/sdd/
```

## Exa.ai Integration (Optional)

The `/vkf/research` command uses exa.ai for market research. Set `EXA_API_KEY` in your environment to enable it. Without the key, the command provides guidance for manual research instead.

## Reference

See [STD-002 Venture Knowledge Foundation](../standard.md) for the full standard.
