# Knowledge Ingestion Classification Rubric

The rubric maps ingested content to classification targets. When `knowledge_types` is configured in `vkf-state.yaml`, ingestion routes content across all registered types (up to 12 targets). Without `knowledge_types`, the default 9 targets apply (8 constitution sections + feature specs).

---

## Classification Targets

### 1. `mission.md` -- Mission & Vision

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "mission", "vision", "purpose", "why we exist", "what we do", "our goal", "north star", "reason for being" |
| **Content types** | Mission statements, vision statements, purpose declarations, founding narratives, elevator pitches |
| **Example match** | "Our mission is to help small teams ship faster by removing infrastructure overhead." |
| **Confidence boost** | Content explicitly uses "mission" or "vision" framing; describes the product's reason for existing in one to three sentences |
| **Confidence drop** | Content describes how the product works (likely feature spec) rather than why it exists |

### 2. `pmf-thesis.md` -- Product-Market Fit Thesis

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "retention", "churn", "NPS", "product-market fit", "PMF", "validation", "assumption", "evidence", "hypothesis", "cohort", "activation" |
| **Content types** | Customer evidence, retention data, churn analysis, PMF assessments, market validation experiments, key assumptions, invalidation criteria |
| **Example match** | "Month-2 retention is 68% across our first 3 cohorts, up from 45% in Q1." |
| **Confidence boost** | Contains quantitative evidence (numbers, percentages, dates); references customer behavior data |
| **Confidence drop** | Describes individual user workflows (likely personas) rather than aggregate market signals |

### 3. `personas.md` -- User Personas

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "user", "persona", "role", "workflow", "pain point", "day in the life", "use case", "frustration", "frequency of use", "technical comfort" |
| **Content types** | User descriptions, role-based workflows, pain point inventories, user research findings, day-in-life scenarios, interview transcripts about user behavior |
| **Example match** | "Sarah is a DevOps lead at a 50-person startup. She spends 3 hours daily on deploy pipeline issues." |
| **Confidence boost** | Describes a specific person or role archetype with goals, pain points, and context |
| **Confidence drop** | Describes a company (likely ICP) rather than an individual user |

### 4. `icps.md` -- Ideal Customer Profiles

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "ICP", "ideal customer", "segment", "company size", "industry", "buying trigger", "deal", "qualification", "disqualifier", "budget", "decision maker" |
| **Content types** | Company profiles, buying criteria, deal qualification frameworks, segment definitions, disqualification rules, sales playbook notes |
| **Example match** | "Our best-fit customers are Series A-B SaaS companies with 20-100 engineers and no dedicated platform team." |
| **Confidence boost** | Describes company-level attributes (size, industry, budget) rather than individual user attributes |
| **Confidence drop** | Describes an individual's workflow (likely personas) or a competitor (likely positioning) |

### 5. `positioning.md` -- Market Positioning

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "competitor", "competitive", "differentiator", "moat", "market", "landscape", "category", "positioning", "versus", "alternative", "compared to" |
| **Content types** | Competitive analysis, market landscape reviews, differentiation claims, moat assessments, category definitions, battlecards |
| **Example match** | "Unlike Terraform, we handle state management automatically -- no backend configuration required." |
| **Confidence boost** | Names specific competitors or alternative solutions; makes explicit comparison claims |
| **Confidence drop** | Describes internal product values (likely principles) rather than external market position |

### 6. `principles.md` -- Product Principles

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "principle", "tenet", "value", "always", "never", "prioritize", "over", "tradeoff", "design philosophy", "non-negotiable" |
| **Content types** | Product values, design tenets, prioritization rules, always/never declarations, tradeoff frameworks |
| **Example match** | "We always prioritize correctness over speed. A slow correct answer beats a fast wrong one." |
| **Confidence boost** | Uses prescriptive language ("we always", "we never", "X over Y"); defines tradeoff resolutions |
| **Confidence drop** | Describes what the product does (likely mission) rather than how decisions are made |

### 7. `governance.md` -- Governance

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "decision", "authority", "process", "amendment", "approval", "review", "team structure", "RACI", "escalation", "owner" |
| **Content types** | Decision authority matrices, process change proposals, team structure definitions, amendment processes, escalation paths |
| **Example match** | "Breaking API changes require sign-off from the CTO and a 48-hour review window." |
| **Confidence boost** | Defines who decides, how decisions are made, or how the constitution itself is changed |
| **Confidence drop** | Describes product behavior (likely feature spec) rather than organizational process |

### 8. `index.md` -- Constitution Index

| Attribute | Detail |
|-----------|--------|
| **Signal words** | N/A -- rarely targeted directly |
| **Content types** | Cross-cutting summaries that span multiple constitution sections without belonging to any single one |
| **Example match** | "Here's a one-page overview of our product strategy covering mission, market, and team." |
| **Confidence boost** | Content is explicitly a summary or overview touching 3+ constitution sections |
| **Confidence drop** | Content has a clear primary section -- route there instead |
| **Note** | Default to a more specific section whenever possible. Only classify to index.md when content is genuinely cross-cutting and cannot be decomposed |

### 9. `specs/features/` -- Feature Specs

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "feature", "requirement", "user story", "acceptance criteria", "endpoint", "API", "implementation", "spec", "as a user I want", "RFC", "technical design" |
| **Content types** | Feature requests, technical requirements, user stories, implementation details, API designs, RFC documents, technical design docs |
| **Example match** | "Users should be able to export dashboards as PDF with configurable page sizes and headers." |
| **Confidence boost** | Describes specific product functionality, technical implementation, or user-facing behavior changes |
| **Confidence drop** | Describes strategy or values (likely constitution content) rather than what to build |

### 10. `architecture/` -- Architecture Documents

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "stack", "database", "schema", "API", "infrastructure", "architecture", "data model", "state machine", "CI/CD", "deployment", "observability", "agent orchestration" |
| **Content types** | Stack decisions, data architecture docs, API contracts, infrastructure design, system diagrams, agent orchestration patterns, state management design |
| **Example match** | "We use ClickHouse Cloud for analytics and Supabase for operational data, connected via Inngest event pipelines." |
| **Confidence boost** | Describes system internals, technology choices, or data flows; answers "how does X work?" |
| **Confidence drop** | Describes what the product does for users (likely feature spec) rather than how it's built |
| **Requires** | `knowledge_types.architecture` configured in `vkf-state.yaml` |

### 11. `ux/` -- User Experience Documents

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "onboarding", "flow", "journey", "happy path", "user story", "wireframe", "interaction", "workflow", "error state", "edge case", "graduation", "stage" |
| **Content types** | Onboarding flows, user journeys, happy paths, error handling UX, stage transitions, interaction patterns, workflow diagrams |
| **Example match** | "New users complete a 5-step onboarding: connect data source → configure dashboard → invite team → set first goal → review insights." |
| **Confidence boost** | Describes step-by-step user interactions, stage transitions, or end-to-end flows |
| **Confidence drop** | Describes technical implementation (likely architecture) or product strategy (likely constitution) |
| **Requires** | `knowledge_types.ux` configured in `vkf-state.yaml` |

### 12. `reference/` -- Reference Documents

| Attribute | Detail |
|-----------|--------|
| **Signal words** | "glossary", "definition", "template", "process", "guide", "reference", "standard", "convention", "terminology", "concept model" |
| **Content types** | Glossaries, concept models, process guides, templates, external reference summaries, naming conventions, mental models |
| **Example match** | "War Stack: The venture's complete operational toolkit — the combination of intelligence, strategy, and execution tools deployed at each lifecycle stage." |
| **Confidence boost** | Defines terms, explains concepts, or provides reusable reference material |
| **Confidence drop** | Contains actionable requirements (likely feature spec) or decisions (likely constitution) |
| **Requires** | `knowledge_types.reference` configured in `vkf-state.yaml` |

---

## Confidence Scoring

| Level | Definition | Example |
|-------|-----------|---------|
| **High** | Content explicitly matches section purpose; 1 clear target | "Our mission is to..." maps to mission.md |
| **Medium** | Content relates but could plausibly fit 2 sections | Customer complaint could be personas.md or pmf-thesis.md |
| **Low** | Tangential match; needs user decision to place correctly | General industry trend -- positioning.md? research? discard? |

### Scoring Guidelines

- **High confidence**: Proceed with placement. Log the extraction in ingestion-log.yaml.
- **Medium confidence**: Present both candidate targets to the user. Show the excerpt and explain the ambiguity. Let the user choose.
- **Low confidence**: Flag as unclassified. Present the content with suggested targets but do not auto-place.

---

## Chunking Rules

Sources longer than 5000 words should be chunked before classification.

### Chunking Method

1. **Primary split**: Break at heading boundaries (H1, H2, H3)
2. **Secondary split**: If a section exceeds 2000 words with no sub-headings, split at topic shifts (paragraph clusters with distinct subjects)
3. **Minimum chunk size**: 100 words. Fragments shorter than this should be merged with the preceding chunk.
4. **Context preservation**: Each chunk retains the document title and parent heading as metadata for classification context.

### Independent Classification

Each chunk is classified independently. A single source document may produce extractions to 3+ different targets. This is expected and correct -- a board deck often contains mission context, PMF data, and feature requests in different sections.

---

## Unclassified Content Handling

When content cannot be confidently classified (Low confidence, no user override), there are 3 valid outcomes:

| Outcome | When to Use | Action |
|---------|-------------|--------|
| **User assigns manually** | Content is valuable but ambiguous | Present to user with candidate targets; user picks placement |
| **Create new feature spec** | Content describes functionality not yet tracked | Create `specs/features/[name]/spec.md` with the content as seed |
| **Discard with reason** | Content is irrelevant, duplicate, or out of scope | Log in ingestion-log.yaml under `skipped` with reason |

Never silently discard content. Every piece of ingested content must be either placed or explicitly logged as skipped.

---

## Multi-Target Content

Content that matches multiple sections is presented once with all candidate targets listed. The user selects the primary placement.

### Rules

1. Show the excerpt once, not duplicated per target
2. List targets in descending confidence order
3. User selects primary placement; content is written there
4. If content genuinely serves two sections (e.g., a persona description that also contains PMF evidence), the user may choose to split: place persona details in personas.md and PMF evidence in pmf-thesis.md
5. Never auto-duplicate content across multiple constitution sections -- this creates maintenance burden and staleness risk

---

## Edge Cases

- **Meeting notes**: Route to `/vkf/transcript` command instead of direct classification. Transcripts have their own extraction pipeline with speaker attribution and structured parsing.
- **Code snippets**: Not constitution content. If the code illustrates a feature, extract the feature description and classify that. Discard the code itself with reason `code-snippet`.
- **Images and diagrams**: Log a reference entry (filename, description) in the ingestion log but do not place into constitution files. Constitution files are markdown text only.
- **Spreadsheets and CSVs**: Extract row-level insights and classify the narrative content. Raw data tables are not placed directly -- summarize or extract key findings first.
- **Duplicate sources**: If a source's content hash matches a previously ingested source, flag as duplicate. Present to user: "This content was previously ingested as ING-XXX. Re-ingest anyway?"
- **Empty or near-empty sources**: Sources with fewer than 50 words of substantive content (excluding boilerplate, headers, signatures) are flagged as `too-short` and require user confirmation before processing.
