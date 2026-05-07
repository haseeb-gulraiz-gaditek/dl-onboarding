# Architecture

System-level design decisions and the load-bearing structural choices that would change if we replaced a database, framework, or major subsystem.

## Contents

- **[system-design.md](system-design.md)** — v0.1 system design lock. Tech stack, data model, deploy targets, V1 scope. Source of truth for the venture's structural decisions; CLAUDE.md routes architecture questions here.

## When to add a doc here

- A change crosses subsystems (frontend ↔ backend ↔ vector DB ↔ Mongo).
- A choice that future contributors would re-litigate without a written record (Mongo vs Postgres, REST vs GraphQL, FastAPI vs Next.js API routes).
- An ADR-shaped decision that doesn't belong inside a single feature spec.

## Freshness

Architecture knowledge has medium decay. Review on every major cycle that touches a subsystem boundary; otherwise a quarterly skim is enough.
