# SDD Command Template

Starter kit for projects adopting **STD-001 Spec-Driven Development**.

## Quick Setup

Copy the `.claude/` folder to your project root:

```bash
cp -r .claude/ /path/to/your-project/.claude/
```

Then create the required project directories:

```bash
mkdir -p specs/features changes archive
```

## Directory Structure

After setup, your project should have:

```
your-project/
├── .claude/
│   ├── commands/
│   │   └── sdd/
│   │       ├── start.md      # Begin change cycle
│   │       ├── status.md     # Show progress
│   │       ├── implement.md  # Execute tasks
│   │       └── complete.md   # Merge & archive
│   └── state/
│       └── sdd-state.yaml    # Cycle tracking
├── specs/
│   └── features/             # Canonical specifications
├── changes/                  # Active change cycles
└── archive/                  # Completed changes
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `/sdd/start [slug]` | Scaffold `changes/[slug]/` with templates |
| `/sdd/status` | Show cycle state and task progress |
| `/sdd/implement` | Execute task(s) following spec |
| `/sdd/complete` | Merge spec-delta and archive change |

## Workflow

```
/sdd/start add-dark-mode
    │
    ▼
Fill out proposal.md, spec-delta.md, tasks.md
    │
    ▼
/sdd/status          # Check progress
/sdd/implement       # Execute tasks (repeat)
    │
    ▼
/sdd/complete        # Merge to specs/, archive
```

## Extension Points

Teams commonly add:

- `/sdd/next` - Task briefing with full context
- `/sdd/validate` - Run validation gates
- `/sdd/baseline` - Brownfield adoption helper
- `/sdd/backlog` - Manage backlog items

## Reference

See [STD-001 Spec-Driven Development](../standard.md) for the full methodology.
