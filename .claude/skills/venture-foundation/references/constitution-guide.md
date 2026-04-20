# Constitution Guide

Full templates and writing guidance for each constitution file in `specs/constitution/`.

## Size and Scope

Constitution files are **structured governance summaries**, not exhaustive documentation. They serve as the agent-readable interface to product knowledge -- concise enough to scan quickly, detailed enough to resolve ambiguity.

**Target: 50-150 lines per file.** Under 30 lines likely lacks substance. Over 200 lines should be reviewed for content that belongs elsewhere (feature specs, vault docs, or reference material).

Exception: `governance.md` naturally grows as amendment history accumulates. This is expected and acceptable.

When a venture has existing deep documentation (a "vault"), constitution files should **distill and link** rather than duplicate:
- Summarize the key facts (structured for quick reference)
- Include relative-path links back to authoritative source documents
- Optionally include a "Sources" section listing the vault documents each file synthesizes

---

## index.md

The index ties all constitution sections together with one-line summaries and links.

```markdown
# [Venture Name] Product Constitution

**Established:** YYYY-MM-DD
**Last amended:** YYYY-MM-DD

---

## Sections

| Section | Summary | Status |
|---------|---------|--------|
| [Mission](mission.md) | [One-line summary] | Active |
| [PMF Thesis](pmf-thesis.md) | [One-line summary] | Active |
| [Personas](personas.md) | [One-line summary] | Active |
| [ICPs](icps.md) | [One-line summary] | Active |
| [Positioning](positioning.md) | [One-line summary] | Active |
| [Principles](principles.md) | [One-line summary] | Active |
| [Governance](governance.md) | [One-line summary] | Active |

## Related

- `technical.md` -- Technical constitution (STD-001): stack, architecture, coding standards
```

---

## mission.md

Mission (one sentence: what we do, for whom) and Vision (one sentence: where we're heading).

```markdown
# Mission & Vision

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## Mission

[REQUIRED: One sentence. What does this product do, and for whom?]

> Template: "[Product] helps [audience] [achieve outcome] by [mechanism]."

## Vision

[REQUIRED: One sentence. Where is this heading in 3-5 years?]

> Template: "A world where [aspirational future state]."

## Context

[REQUIRED: 2-3 sentences. Why does this matter now? What market shift or pain point makes this urgent?]
```

### Writing Guidance

- Mission should be testable: can you verify the product does what the mission claims?
- Vision should be ambitious but not absurd -- something you could plausibly achieve.
- Context grounds the mission in reality. Why this, why now?

---

## pmf-thesis.md

The product-market fit thesis: who's the customer, what's the problem, what's the solution, what's the evidence.

```markdown
# Product-Market Fit Thesis

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## PMF Status

**Current stage:** [REQUIRED: Pre-PMF | Approaching PMF | Post-PMF]

## Customer

[REQUIRED: Who is the primary customer? Be specific -- job title, company size, context.]

## Problem

[REQUIRED: What problem are they experiencing? Describe the pain in their words.]

## Solution

[REQUIRED: How does the product solve this? Focus on the mechanism, not features.]

## Evidence

[REQUIRED: What evidence supports this thesis? Include qualitative and quantitative signals.]

| Signal | Type | Strength |
|--------|------|----------|
| [e.g., "5 customers renewed without being asked"] | Retention | Strong |
| [e.g., "NPS score of 72"] | Satisfaction | Moderate |
| [e.g., "3 inbound referrals this month"] | Word of mouth | Strong |

## Key Assumptions

[REQUIRED: What must be true for this thesis to hold? List the riskiest assumptions first.]

1. [Assumption 1]
2. [Assumption 2]
3. [Assumption 3]

## Invalidation Criteria

[REQUIRED: What would prove this thesis wrong?]

- If [condition], then [conclusion about PMF]
```

### Writing Guidance

- PMF status should be honest. Most early ventures are Pre-PMF. That's fine.
- Evidence should be specific and dated. "Users love it" is not evidence.
- Invalidation criteria prevent the team from clinging to a failing thesis.

---

## personas.md

User personas: who uses the product, what they care about, how they work.

```markdown
# User Personas

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## Persona: [REQUIRED: Name / Role]

| Attribute | Detail |
|-----------|--------|
| **Role** | [REQUIRED: Job title and context] |
| **Goals** | [REQUIRED: What they're trying to achieve] |
| **Pain Points** | [REQUIRED: What frustrates them today] |
| **Current Workflow** | [REQUIRED: How they solve this without the product] |
| **Success Metric** | [REQUIRED: How they measure success] |
| **Technical Comfort** | [REQUIRED: Low / Medium / High] |
| **Frequency of Use** | [REQUIRED: Daily / Weekly / Monthly / Occasional] |

### Scenarios

1. [REQUIRED: A day-in-the-life scenario showing how this persona uses the product]

---

## Persona: [REQUIRED: Name / Role]

[Repeat table and scenarios for each persona]
```

### Writing Guidance

- Start with 2-3 personas maximum. More than 5 means you haven't prioritized.
- Each persona should be distinguishable -- if two personas have the same goals and pain points, merge them.
- Scenarios should be concrete, not hypothetical. Base them on real user behavior where possible.
- Include at least one "non-user" persona (e.g., the buyer who doesn't use the product daily) if relevant.

---

## icps.md

Ideal Customer Profiles: what companies are the best fit for the product.

```markdown
# Ideal Customer Profiles

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## ICP: [REQUIRED: Segment Name]

| Attribute | Detail |
|-----------|--------|
| **Company Size** | [REQUIRED: Employee count range] |
| **Industry** | [REQUIRED: Primary industries] |
| **Tech Maturity** | [REQUIRED: Early adopter / Mainstream / Laggard] |
| **Annual Budget** | [REQUIRED: Budget range for this category] |
| **Buying Trigger** | [REQUIRED: What event causes them to seek a solution] |
| **Decision Maker** | [REQUIRED: Title of the person who signs] |
| **Champion** | [REQUIRED: Title of the person who advocates internally] |

### Qualification Criteria

Must have:
- [REQUIRED: Hard requirements that define this ICP]

Nice to have:
- [REQUIRED: Signals that strengthen fit]

### Disqualifiers

- [REQUIRED: Red flags that indicate poor fit]

---

## ICP: [REQUIRED: Segment Name]

[Repeat for each ICP segment]
```

### Writing Guidance

- Start with 1-2 ICPs. If you serve everyone, you serve no one.
- Buying trigger is the most important field -- it tells you when to reach out.
- Disqualifiers save more time than qualification criteria. Be specific about who is NOT a fit.
- Keep ICPs and personas aligned: each ICP should map to at least one persona.

---

## positioning.md

Market positioning: how the product is different, who it competes with, what's defensible.

```markdown
# Market Positioning

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## Positioning Statement

[REQUIRED: Fill in the formula below]

> For **[target customer]** who **[statement of need]**, **[product name]** is a **[product category]** that **[key benefit]**. Unlike **[primary competitor]**, we **[primary differentiator]**.

## Competitive Landscape

| Competitor | Category | Strengths | Weaknesses | Our Advantage |
|-----------|----------|-----------|------------|---------------|
| [REQUIRED] | [Category] | [Their strengths] | [Their gaps] | [Why we win] |
| [REQUIRED] | [Category] | [Their strengths] | [Their gaps] | [Why we win] |

## Moat / Defensibility

[REQUIRED: What makes this hard to copy? Choose applicable moats:]

- [ ] Network effects
- [ ] Data advantage
- [ ] Switching costs
- [ ] Brand / trust
- [ ] Technical complexity
- [ ] Regulatory / compliance
- [ ] Distribution advantage

**Explanation:** [REQUIRED: Why the selected moats apply to this venture]

## Category

[REQUIRED: What category does this product create or belong to? Is the goal to win an existing category or create a new one?]
```

### Writing Guidance

- The positioning statement formula is from April Dunford's "Obviously Awesome." Fill it in literally.
- Competitive landscape should include at least 2 competitors, even if they're indirect (spreadsheets, manual processes).
- Be honest about moats. Most early-stage ventures have weak moats. That's a signal, not a failure.
- Category is strategic: creating a new category is powerful but expensive. Most startups should position within an existing one.

---

## principles.md

Product principles: the immutable decisions that guide every tradeoff.

```markdown
# Product Principles

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## We Always

[REQUIRED: Things the product will always do, regardless of pressure]

1. [Principle]: [Explanation]
2. [Principle]: [Explanation]
3. [Principle]: [Explanation]

## We Never

[REQUIRED: Hard lines the product will not cross]

1. [Principle]: [Explanation]
2. [Principle]: [Explanation]
3. [Principle]: [Explanation]

## We Prioritize (Ordered)

[REQUIRED: When two good things conflict, which wins? List in priority order.]

1. [Highest priority value] over [lower priority value]
2. [Next priority] over [next lower]
3. [Next priority] over [next lower]

> Example: "Correctness over speed", "User privacy over engagement metrics", "Simplicity over configurability"

## Design Tenets

[REQUIRED: 3-5 principles that guide product and UX decisions]

1. **[Tenet name]**: [One-sentence description]
2. **[Tenet name]**: [One-sentence description]
3. **[Tenet name]**: [One-sentence description]
```

### Writing Guidance

- Principles that never cause tension are useless. "We care about quality" is not a principle. "We ship less but ship correctly" is.
- The ordered prioritization list is the most valuable section. It resolves debates before they happen.
- Aim for 3-5 items per section. More than that dilutes their power.

---

## governance.md

Decision authority: who decides what, how to change the constitution, amendment history.

```markdown
# Governance

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## Decision Authority

| Decision Type | Authority | Process |
|--------------|-----------|---------|
| [REQUIRED: e.g., "New feature"] | [Who decides] | [How: async review, meeting, etc.] |
| [REQUIRED: e.g., "Breaking change"] | [Who decides] | [Process] |
| [REQUIRED: e.g., "Constitution amendment"] | [Who decides] | [Process] |
| [REQUIRED: e.g., "Pricing change"] | [Who decides] | [Process] |
| [REQUIRED: e.g., "Deprecation"] | [Who decides] | [Process] |

## Amendment Process

Changes to any constitution file require:

1. [REQUIRED: What triggers an amendment?]
2. [REQUIRED: Who must review?]
3. [REQUIRED: What approval is needed?]
4. [REQUIRED: How is it documented?]

## Amendment History

| Date | File | Change | Author |
|------|------|--------|--------|
| [YYYY-MM-DD] | [File changed] | [What changed] | [Who] |
```

### Writing Guidance

- Decision authority should cover the 5-7 most common decision types. Don't try to cover everything.
- The amendment process should be lightweight for a small team, more formal as the team grows.
- Amendment history creates accountability. Every constitution change should be traceable.

---

## Technical Constitution (STD-001 Addition)

When STD-001 is adopted, `specs/constitution/technical.md` is added to the same directory:

```markdown
# Technical Constitution

> Part of the [Venture Name] Product Constitution

**Last amended:** YYYY-MM-DD

---

## Stack

[Tech stack decisions]

## Architecture

[Architecture decisions and patterns]

## Coding Standards

[Code style, conventions, patterns]

## Security Invariants

[Security rules that must never be violated]
```

This follows the same pattern as all other constitution files -- modular, standalone, trackable.
