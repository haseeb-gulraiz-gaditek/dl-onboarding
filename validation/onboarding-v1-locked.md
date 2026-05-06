# Onboarding V1 — locked 4-question set

Tone: casual, slightly self-aware, no condescension. Tap-and-go where possible. Q2/Q3/Q4 options are **dynamically templated** based on the role from Q1.

---

## Q1 — "Alright, let's start with the basics — who are you for ~8 hours a day?"

Three quick dropdowns:

**Job title** (typeable + suggestions)
- Suggestion list scrolls: Software Engineer, Data Scientist, Product Manager, UX Designer, Accountant, Auditor, Financial Analyst, Doctor, Nurse, Pharmacist, Lawyer, Paralegal, Teacher, Consultant, Marketer, Sales Rep, Recruiter, Operations, HR, Founder/CEO, Researcher, Student, Other...

**Level**
- Junior · Mid · Senior · Lead · Manager · Director · Executive · Self-employed/Freelance · Student · "Just figuring it out"

**Industry**
- Software & Tech · Finance & Accounting · Healthcare · Legal · Education · Marketing/Advertising · Sales · Consulting · Design/Creative · Operations · HR · Government · Non-profit · Manufacturing · Real Estate · Media/Content · Retail/E-comm · Other...

> *Tiny copy under the dropdowns:* "We won't email you. This just helps us not waste your time."

---

## Q2 — "Which of these do you actually have open most days?"

> *Tiny copy:* "Multi-select. We promise we won't recommend any of these — we're checking what your daily reality looks like."

**Options are role-dependent** (Q1 → Q2 templating). Show ~12-15 most-relevant tools, plus an "Other" chip.

---

## Q3 — "Pick the one that sounds closest to a 'big task' you actually finish at work."

> *Tiny copy:* "Single pick. The boring real one, not the LinkedIn version."

5 role-relevant scenarios written in plain language.

---

## Q4 — "Which of these is closest to your average Tuesday?"

> *Tiny copy:* "Single pick. Pick the closest, even if it's annoying that none fit perfectly."

4-5 day-shape narratives (not bullet lists — short paragraphs that read like a friend describing their day).

---

# Walkthroughs — 3 personas

---

## Persona A — ACCA (Senior Audit Manager, Finance & Accounting)

### Q1
- **Job title**: Audit Manager
- **Level**: Senior
- **Industry**: Finance & Accounting

### Q2 — "Which of these do you actually have open most days?"

ACCA-relevant options:
- ☑ **Excel / Google Sheets**
- ☑ **Outlook / Email**
- ☑ **Sharepoint / OneDrive**
- ☑ **Microsoft Teams**
- ☐ Slack
- ☐ QuickBooks / Xero
- ☑ **Sage / SAP / Oracle ERP** (client systems)
- ☐ Caseware / Working Papers software
- ☐ DataSnipper (PDF→Excel audit AI)
- ☐ MindBridge (anomaly-detection AI)
- ☐ Tableau / Power BI
- ☑ **ChatGPT / Claude** (curiosity, not work)
- ☐ Microsoft Copilot in Excel
- ☐ Numerous.ai / Rows AI
- ☐ Other

**Picks (5)**: Excel, Outlook, Sharepoint, Teams, ERP, ChatGPT
**→ What this tells the algorithm**: Excel is home base; communication is email/Teams (not Slack); audit/financial-system fluent; AI curiosity but not workflow-integrated yet.

### Q3 — "Pick the one that sounds closest to a 'big task' you actually finish."

Options for Audit/Finance role:
1. *Closing a client's quarterly books — pulling trial balance, reconciling, reviewing journal entries, signing off, sending the package.*
2. *Running a full audit on one client — planning, fieldwork at their office, working papers, review notes, partner sign-off, final report.*
3. *Building a financial model from scratch for a board or M&A deal.*
4. *Reconciling a few hundred transactions across multiple entities and chasing down the ones that don't tie out.*
5. *Reviewing another auditor's work — finding the gaps, writing review notes, pushing it back, getting it cleaned up.*

**Pick**: #2 — full audit cycle.
**→ Tells algorithm**: long-cycle deliverable, multi-stage workflow, document-heavy, reviewer + producer hybrid role.

### Q4 — "Closest to your average Tuesday?"

Options:
1. *Inbox first thing → couple hours deep in Excel on a model or workpaper → team huddle → call with client about an issue → afternoon reviewing junior staff's work → late-day cleanup emails.*
2. *Mostly back-to-back meetings — internal reviews, client calls, partner check-ins. I barely touch Excel. I'm coordinating, not building.*
3. *On-site at a client all day — fieldwork, sample testing, asking the controller for documents, writing up findings between meetings.*
4. *Heavy numbers in the morning when my brain works → meetings stack up after lunch → I clean up the day's emails and prep tomorrow's work between 5–7.*
5. *Reactive — whatever blew up overnight. Manager pings, client questions, fires. I rarely finish what I started.*

**Pick**: #4 — heavy numbers AM, meetings PM.
**→ Tells algorithm**: morning deep-work paradigm, afternoon coordination, end-of-day catch-up — recommend morning-flow tools (Excel-native AI, model-builder helpers) and evening summarization tools (inbox triage, Teams catch-up).

---

## Persona B — SWE (Senior Backend Engineer, Software & Tech)

### Q1
- **Job title**: Software Engineer (Backend)
- **Level**: Senior
- **Industry**: Software & Tech

### Q2 — "Which of these do you actually have open most days?"

SWE-relevant options:
- ☑ **VS Code / Cursor / IntelliJ**
- ☑ **Terminal / iTerm**
- ☑ **GitHub / GitLab**
- ☑ **Linear / Jira**
- ☑ **Slack**
- ☑ **Chrome (with 30+ tabs)**
- ☐ Discord
- ☑ **Postgres / MongoDB / DB client**
- ☑ **Datadog / Grafana / Sentry**
- ☑ **ChatGPT / Claude**
- ☑ **GitHub Copilot / Cursor AI**
- ☑ **Notion / Confluence**
- ☐ Postman / Insomnia
- ☐ Figma (read-only)
- ☐ AWS / GCP console
- ☐ Other

**Picks (11)**: VS Code, Terminal, GitHub, Linear, Slack, Chrome, Postgres, Datadog, ChatGPT, Copilot, Notion
**→ Algorithm**: high tool-density, AI-native (Copilot already in flow), observability-aware, multi-app workflow. Existing AI usage = *already past the "tried and didn't stick" stage*.

### Q3 — "Pick the one closest to a 'big task' you actually finish."

Options for SWE role:
1. *Take a feature spec, design it out, write the code, test it, open a PR, get reviews, address feedback, ship to prod.*
2. *Get paged at 2am about a production bug — trace logs, reproduce locally, find the root cause, write the fix + a regression test, deploy.*
3. *Refactor a gnarly legacy module without breaking the 8 things that depend on it.*
4. *Build an internal tool from scratch for the ops/finance team because they keep asking the same Slack question.*
5. *Spend a day on PR reviews — push back on 2, approve 3, fix CI on the one that's been broken for a week.*

**Pick**: #1 — feature spec → ship.
**→ Algorithm**: producer mode dominant, full-cycle ownership, integrates code/review/deploy. Recommend tools that span the cycle (spec → code → review → test → ship), not point-tools.

### Q4 — "Closest to your average Tuesday?"

Options:
1. *Standup at 10 → deep coding for 3 hours → lunch → afternoon code reviews and Slack threads → I push the day's work around 6 and call it.*
2. *Mostly meetings and design docs. I'm coordinating across teams; I haven't merged code in a week and I'm a little sad about it.*
3. *Reactive day — production issues, oncall pings. Mostly Slack, dashboards, and `kubectl logs`.*
4. *Standup → some coding → 1–2 design discussions → some reviews → write up notes → ship something small.*
5. *Half deep work, half on calls. By Friday my brain is fried from context-switching.*

**Pick**: #1 — coding morning, reviews afternoon.
**→ Algorithm**: paradigm = "in-flow during deep work, async/light in afternoon." Recommend IDE-integrated tools for AM, async PR-context tools for PM.

---

## Persona C — Doctor (Attending, Family Medicine, Healthcare)

### Q1
- **Job title**: Physician (Family Medicine)
- **Level**: Senior (Attending)
- **Industry**: Healthcare

### Q2 — "Which of these do you actually have open most days?"

Doctor-relevant options:
- ☑ **Epic EHR**
- ☐ Cerner / Allscripts / Athena (other EHR)
- ☑ **UpToDate / DynaMed** (clinical reference)
- ☐ MDCalc
- ☑ **Outlook**
- ☑ **Microsoft Teams** (system-mandated)
- ☐ Doximity / Doximity GPT
- ☐ Dragon Medical (dictation)
- ☐ Abridge / Suki / Nuance DAX (ambient scribe)
- ☐ ChatGPT / Claude
- ☐ PACS imaging viewer
- ☑ **Lab portal**
- ☑ **WhatsApp / SMS** (colleague consults)
- ☐ Practice management software
- ☐ Other

**Picks (6)**: Epic, UpToDate, Outlook, Teams, Lab portal, WhatsApp
**→ Algorithm**: locked into Epic, no AI in workflow yet, asynchronous colleague-consult via WhatsApp = informal info channel. Strong filter: don't recommend anything that doesn't integrate with Epic or doesn't work fully offline.

### Q3 — "Pick the one closest to a 'big task' you actually finish."

Options for physician role:
1. *Get through a clinic day — 20 patients, room-to-room, exam, write notes, place orders, set follow-ups, between-patient charting.*
2. *Round on hospitalized patients — review overnight changes, see each one, update plans, write progress notes, coordinate with consultants.*
3. *Clear the inbox — 100+ messages: lab results, refill requests, patient questions, results to review and route.*
4. *Take a complex case from first visit through diagnosis, treatment plan, specialist referrals, and follow-up over 4–6 weeks.*
5. *Coordinate care for one patient across 3 specialists, the patient's family, social worker, and insurance — get everyone on the same page.*

**Pick**: #1 — clinic day with 20 patients.
**→ Algorithm**: short-cycle high-throughput workflow, charting bottleneck, between-patient micro-tasks. Top fit = ambient scribe (Abridge/Suki) — not productivity tools.

### Q4 — "Closest to your average Tuesday?"

Options:
1. *7am rounds (if inpatient day) → 9am clinic starts → patient after patient, 15-min slots, charting between → quick lunch → more clinic → 5pm I'm catching up on notes and inbox → I finish charting at home around 9pm.*
2. *Pure clinic day. 20+ patients, no break, charting backlog grows, I'm doing notes between visits and finishing them at home.*
3. *Inpatient day — rounds in the morning, consults, family meetings, attending notes, nothing is a procedure but everything is communication.*
4. *Mix — half clinic, half admin/meetings. Quality committee, peer review, residents.*
5. *Procedure days — different rhythm. Block of procedures back-to-back, between-case notes, faster turn-arounds.*

**Pick**: #1 — outpatient clinic + inpatient rounds + EOD charting at home.
**→ Algorithm**: "pajama-time charting" is the universal physician friction. Recommendation MUST attack this: ambient scribe + EHR-native automation + inbox triage. Anything else gets de-prioritized.

---

## What the algorithm now has after 4 questions

For each persona it has:
- **Industry + role + seniority** (drives recommendation domain)
- **Stack fingerprint** (what tools the person already uses → integration constraints)
- **Task-shape** (long-cycle vs short-cycle, producer vs reviewer, multi-stage vs reactive)
- **Day rhythm** (when deep work happens, when coordination happens, where the EOD friction is)

This is 4 picks worth of data. The next 8 questions (post-V1, contextual) will go deeper on:
- Tools tried-and-bounced (exclusion)
- Counterfactual wishes
- Trust/accuracy paradigm
- Setup tolerance
- Integration must-haves

---

## Note on Q1 → Q2/Q3/Q4 templating

The tool/scenario/day-flow options must be **role-conditioned**. Implementation:
- Maintain a `role_templates.yaml` mapping `{job_title × industry → option_sets}`
- LLM fallback: for unrecognized roles, generate the option set on the fly (cached per role)
- Coverage: ~30 most common roles hand-curated; rest LLM-generated

This is the V1 trade-off: hand-curated for top roles (sharp signal), LLM-fallback for long tail (good-enough signal).
