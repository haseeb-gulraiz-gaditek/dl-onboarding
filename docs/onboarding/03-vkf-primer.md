# 03 — VKF Primer

Just enough VKF to bootstrap your venture's foundation. For the full spec see [`docs/standards/std-002-venture-knowledge-foundation/standard.md`](../standards/std-002-venture-knowledge-foundation/standard.md).

**Time:** ~15 minutes.

---

## The one-sentence version

> Every venture has a constitution — who we are, what we build, for whom, and why — and an organized specs layout, both governed by an amendment process, because knowledge is code and must be versioned and reviewed like code.

---

## The 5-type knowledge taxonomy

Everything your venture will ever write down fits into one of five buckets. Knowing which bucket something belongs in tells you where to put it and how to govern it.

| Type | Question it answers | Volatility | Governance | Example |
|---|---|---|---|---|
| **Constitution** | Who are we? What do we build? For whom? Why? | Very low | Amendment (C0–C3) | "We serve Series A–B SaaS companies." |
| **Architecture** | How is it built? What structural choices? | Low–medium | Review + ADRs | "We use Postgres as the source of truth." |
| **Features** | What does the product do? | Medium–high | SDD | "Users can export results as CSV." |
| **UX** | How does the user experience it? | High | Light review | "The export button is bottom-right of the results table." |
| **Reference** | Shared vocab, mock data, glossaries | Low | None | "`user.plan` values: `free`, `pro`, `team`, `enterprise`." |

A litmus test you can apply: *would this change if we rebranded?* Constitution: yes. Features: no. *Would this change if we swapped the database?* Architecture: yes. Features: no. Using the litmus tests forces clarity about what kind of knowledge you're looking at.

---

## The constitution

Eight files. Four required (Core), four optional-but-recommended (Extended).

### Core — required

| File | Purpose |
|---|---|
| `mission.md` | One sentence on what you do. Plus vision and why this exists. |
| `pmf-thesis.md` | Who the customer is, what problem, what solution, what evidence. "We don't know yet" is a legitimate answer — but it must be explicit. |
| `principles.md` | Immutable product decisions. 3–8 items. Each is a deliberate choice, not a platitude. |
| `index.md` | Summary + links to every section, with status. |

### Extended — adopt when relevant

| File | Adopt when |
|---|---|
| `personas.md` | You have more than one distinct user type |
| `icps.md` | You have a B2B motion (companies are the target, not just individuals) |
| `positioning.md` | You have identifiable competitors |
| `governance.md` | > 1 person will make decisions on the constitution |

**Rule:** Don't fill these in preemptively. A `positioning.md` written before you have competitors is creative writing. Wait until it's real.

---

## The amendment tiers: C0–C3

Every change to a *filled-in* constitution file goes through an amendment process proportional to its impact.

| Tier | Name | What it is | Process |
|---|---|---|---|
| **C0** | Cosmetic | Whitespace, typos, dates, formatting | Direct edit + update `Last amended:` |
| **C1** | Clarification | Rewording that doesn't change meaning | Log amendment history entry |
| **C2** | Substantive | Adds / changes / removes content | Full proposal + delta + propagation check |
| **C3** | Structural | Changes principles, invalidates PMF, alters governance | C2 + conflict analysis + rollback plan |

**Why tiers?** Because "let me just fix the wording" and "let me change our ICP from mid-market to enterprise" should not cost the same amount of ceremony. The tiers are proportionality — serious changes get serious review, trivial changes get out of the way.

**Never bypass the tier.** Even if the user types *"just change it,"* Claude Code is instructed to announce the tier. That's not bureaucracy — it's auditability. When you look back in six months at why your positioning shifted, the amendment log is how you find the answer.

---

## Knowledge operations beyond amendments

VKF's "Advanced tier" adds five capabilities. You don't need them on day one, but you should know they exist.

| Capability | Command | What it does |
|---|---|---|
| Ingestion | `/vkf/ingest` | Someone pastes a doc / sheet / link. It gets classified against the 9-point rubric and routed to the right constitution section (or logged as feature-relevant). No more "I'll file this later" docs. |
| Gap analysis | `/vkf/gaps` | Scans the constitution for thin spots and proposes answers you can accept, reject, or mark as known unknowns. |
| Transcripts | `/vkf/transcript` | Meeting recording → structured meeting brief → decisions captured, action items surfaced. |
| OKRs | `/vkf/okrs` | Quarterly objectives linked back to the constitution, so progress is measurable against mission. |
| Workflow | `/vkf/workflow` | Lifecycle state on every document: Draft / Review / Active / Review Due / Archived. |

---

## Freshness

The constitution isn't a stone tablet. Knowledge goes stale; markets shift; personas evolve. Each knowledge type has a **freshness threshold**:

- Constitution: 90 days
- Architecture: 180 days
- Features: 90 days
- Reference: 365 days

`/vkf/freshness` scans for documents past their review threshold and flags them. A stale document isn't broken; it's *due for review*. Review doesn't mean amend — it means "look at this, decide if it's still true, bump the `Last reviewed:` if yes, open an amendment if no."

---

## The two hardest disciplines

Most of VKF is mechanical. Two things are hard, because they are habits:

1. **"I don't know" is explicit knowledge.** When your `pmf-thesis.md` says *"We haven't validated churn numbers yet — tracked as KU-003"*, that is more valuable than a plausible-looking fabricated number. The whole team can see what's known and what isn't. Resist the urge to plug every hole with a guess.
2. **Everything external goes through `/vkf/ingest`.** Research, customer interviews, competitor analysis, strategy docs — they all have a home somewhere in the constitution or specs. When you route them through ingestion, the classification is deliberate and logged. When you don't, they sit in Slack or your local notes and decay.

---

**Next:** [04 — Bootstrap your venture](04-bootstrap-your-venture.md)
