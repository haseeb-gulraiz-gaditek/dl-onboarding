# specs/

This is where your venture's **canonical knowledge** lives — the constitution (who you are and what you're building) and feature specifications (what the product does today).

## Layout

```
specs/
├── constitution/         # Created by /vkf/init — who you are, what you build, for whom, why
│   ├── index.md
│   ├── mission.md        # Core (required)
│   ├── pmf-thesis.md     # Core (required)
│   ├── principles.md     # Core (required)
│   ├── personas.md       # Extended
│   ├── icps.md           # Extended
│   ├── positioning.md    # Extended
│   └── governance.md     # Extended
└── features/             # Grown by /sdd:complete — current behavior per feature
    └── {feature-slug}/
        └── spec.md
```

## How specs get here

- **Constitution files** are created by `/vkf/init` and edited via `/vkf/constitution` (initial draft) or `/vkf/amend` (any change to a filled-in file). Never edit a filled-in constitution file directly — go through `/vkf/amend` so the tier (C0–C3) is announced and the change is auditable.
- **Feature specs** are created or updated by `/sdd:complete` when a change cycle finishes. The cycle lives in `changes/{slug}/` while in progress; on completion, the `spec-delta.md` is merged into the canonical `specs/features/{feature}/spec.md` and the cycle is moved to `archive/`.

## Governance

| File type        | Governance   | Command           |
|------------------|--------------|-------------------|
| constitution/\*  | Amendment    | `/vkf/amend`      |
| features/\*      | SDD          | `/sdd:start` …    |

See `docs/standards/std-001-spec-driven-development/standard.md` and `docs/standards/std-002-venture-knowledge-foundation/standard.md` for the full standards.
