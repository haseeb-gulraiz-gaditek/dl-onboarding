"""Locked 4-question schema for the live-narrowing onboarding flow.

Per spec-delta `live-narrowing-onboarding` F-LIVE-1.

This module is the source of truth for the new flow's question copy,
option tables, and role-conditioning. It is NOT seeded to Mongo; the
existing seed in `app/seed/questions.json` continues to drive the
classic flow at `/onboarding`.

Tunable surfaces (single-line edits, no migration):
  - LIVE_QUESTIONS: copy + structure
  - ROLE_OPTIONS_Q2 / ROLE_OPTIONS_Q3: per-role hand-curated content
  - FALLBACK_OPTIONS_Q2 / FALLBACK_OPTIONS_Q3: generic content for
    unrecognized roles (or job_title="other")
  - ROLE_KEY_MAP: maps Q1 job_title (free-typed or picked from
    suggestion list) to one of the canonical role keys
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---- Models ----

LiveQuestionKind = Literal["dropdowns_3", "multi_select", "single_select"]


class Option(BaseModel):
    value: str
    label: str


class LiveQuestion(BaseModel):
    q_index: int = Field(..., ge=1, le=4)
    key: str
    text: str
    helper: str | None = None
    kind: LiveQuestionKind
    # For dropdowns_3 (Q1) only — three sub-dropdowns share the question.
    sub_dropdowns: dict[str, list[Option]] | None = None
    # For role-agnostic options (Q4 friction).
    options: list[Option] | None = None
    # For role-conditioned questions (Q2 / Q3) only.
    options_per_role: dict[str, list[Option]] | None = None
    fallback_options: list[Option] | None = None


# ---- Q1 — three dropdowns (job title / level / industry) ----

JOB_TITLE_SUGGESTIONS: list[Option] = [
    Option(value="software_engineer", label="Software Engineer"),
    Option(value="data_scientist", label="Data Scientist"),
    Option(value="product_manager", label="Product Manager"),
    Option(value="ux_designer", label="UX / Product Designer"),
    Option(value="accountant", label="Accountant"),
    Option(value="auditor", label="Auditor"),
    Option(value="financial_analyst", label="Financial Analyst"),
    Option(value="doctor", label="Doctor / Physician"),
    Option(value="nurse", label="Nurse"),
    Option(value="pharmacist", label="Pharmacist"),
    Option(value="lawyer", label="Lawyer"),
    Option(value="paralegal", label="Paralegal"),
    Option(value="teacher", label="Teacher / Educator"),
    Option(value="consultant", label="Consultant"),
    Option(value="marketer", label="Marketer"),
    Option(value="sales_rep", label="Sales Rep"),
    Option(value="recruiter", label="Recruiter"),
    Option(value="operations", label="Operations"),
    Option(value="hr", label="HR / People Ops"),
    Option(value="customer_success", label="Customer Success"),
    Option(value="founder_ceo", label="Founder / CEO"),
    Option(value="researcher", label="Researcher"),
    Option(value="student", label="Student"),
    Option(value="other", label="Something else"),
]

LEVEL_OPTIONS: list[Option] = [
    Option(value="junior", label="Junior"),
    Option(value="mid", label="Mid"),
    Option(value="senior", label="Senior"),
    Option(value="lead", label="Lead"),
    Option(value="manager", label="Manager"),
    Option(value="director", label="Director"),
    Option(value="executive", label="Executive"),
    Option(value="freelance", label="Self-employed / Freelance"),
    Option(value="student", label="Student"),
    Option(value="figuring_out", label="Just figuring it out"),
]

INDUSTRY_OPTIONS: list[Option] = [
    Option(value="software_tech", label="Software & Tech"),
    Option(value="finance_accounting", label="Finance & Accounting"),
    Option(value="healthcare", label="Healthcare"),
    Option(value="legal", label="Legal"),
    Option(value="education", label="Education"),
    Option(value="marketing_advertising", label="Marketing / Advertising"),
    Option(value="sales", label="Sales"),
    Option(value="consulting", label="Consulting"),
    Option(value="design_creative", label="Design / Creative"),
    Option(value="operations", label="Operations"),
    Option(value="hr", label="HR / People"),
    Option(value="government", label="Government"),
    Option(value="non_profit", label="Non-profit"),
    Option(value="manufacturing", label="Manufacturing"),
    Option(value="real_estate", label="Real Estate"),
    Option(value="media_content", label="Media / Content"),
    Option(value="retail_ecomm", label="Retail / E-commerce"),
    Option(value="other", label="Something else"),
]


# ---- Role-key normalization ----
# Maps the typed job_title value (from Q1's suggestion list) to one of
# the 13 canonical role keys used by ROLE_OPTIONS_Q2 / ROLE_OPTIONS_Q3.
# Free-typed values that aren't in this map fall through to "other"
# and use FALLBACK_OPTIONS_*.

ROLE_KEY_MAP: dict[str, str] = {
    # software / engineering
    "software_engineer": "software_engineer",
    "data_scientist": "software_engineer",
    "researcher": "software_engineer",
    # product / design
    "product_manager": "product_manager",
    "ux_designer": "designer",
    # finance / audit
    "accountant": "accountant",
    "auditor": "accountant",
    "financial_analyst": "accountant",
    # healthcare
    "doctor": "doctor",
    "nurse": "doctor",
    "pharmacist": "doctor",
    # legal
    "lawyer": "lawyer",
    "paralegal": "lawyer",
    # marketing / sales / cs
    "marketer": "marketer",
    "sales_rep": "sales",
    "recruiter": "sales",
    "customer_success": "customer_success",
    # ops / hr
    "operations": "operations",
    "hr": "operations",
    # founders / consultants
    "founder_ceo": "founder",
    "consultant": "consultant",
    # students / teachers
    "student": "student",
    "teacher": "student",
}


def role_key_for(job_title_value: str) -> str:
    """Map a Q1 job_title value to a canonical role key. Unknown
    values return "other" so the caller can fall back to generic
    options."""
    return ROLE_KEY_MAP.get(job_title_value, "other")


# ---- Q2 — "Which of these do you actually have open most days?" ----
# Per-role hand-curated tool option lists. Multi-select chips. The
# `value` is a slug-friendly identifier; `label` is the human label.

ROLE_OPTIONS_Q2: dict[str, list[Option]] = {
    "software_engineer": [
        Option(value="vscode", label="VS Code / Cursor / IntelliJ"),
        Option(value="terminal", label="Terminal / iTerm"),
        Option(value="github", label="GitHub / GitLab"),
        Option(value="linear", label="Linear / Jira"),
        Option(value="slack", label="Slack"),
        Option(value="db_client", label="Postgres / MongoDB / DB client"),
        Option(value="datadog", label="Datadog / Grafana / Sentry"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="copilot", label="GitHub Copilot / Cursor AI"),
        Option(value="notion", label="Notion / Confluence"),
        Option(value="postman", label="Postman / Insomnia"),
        Option(value="cloud_console", label="AWS / GCP console"),
    ],
    "accountant": [
        Option(value="excel", label="Excel / Google Sheets"),
        Option(value="outlook", label="Outlook / Email"),
        Option(value="sharepoint", label="SharePoint / OneDrive"),
        Option(value="teams", label="Microsoft Teams"),
        Option(value="erp", label="Sage / SAP / Oracle ERP"),
        Option(value="quickbooks", label="QuickBooks / Xero"),
        Option(value="caseware", label="Caseware / Working Papers"),
        Option(value="datasnipper", label="DataSnipper"),
        Option(value="powerbi", label="Tableau / Power BI"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="copilot_excel", label="Microsoft Copilot in Excel"),
    ],
    "doctor": [
        Option(value="epic", label="Epic EHR"),
        Option(value="other_ehr", label="Cerner / Allscripts / Athena"),
        Option(value="uptodate", label="UpToDate / DynaMed"),
        Option(value="mdcalc", label="MDCalc"),
        Option(value="outlook", label="Outlook"),
        Option(value="teams", label="Microsoft Teams"),
        Option(value="dragon", label="Dragon Medical (dictation)"),
        Option(value="ambient_scribe", label="Abridge / Suki / Nuance DAX"),
        Option(value="lab_portal", label="Lab portal"),
        Option(value="whatsapp", label="WhatsApp / SMS for consults"),
        Option(value="pacs", label="PACS imaging viewer"),
    ],
    "marketer": [
        Option(value="google_workspace", label="Google Docs / Sheets"),
        Option(value="slack", label="Slack"),
        Option(value="hubspot", label="HubSpot / Marketo"),
        Option(value="ga", label="Google Analytics"),
        Option(value="figma", label="Figma"),
        Option(value="canva", label="Canva"),
        Option(value="notion", label="Notion / Coda"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="jasper", label="Jasper / Copy.ai"),
        Option(value="ahrefs", label="Ahrefs / Semrush"),
        Option(value="linkedin", label="LinkedIn"),
        Option(value="mailchimp", label="Mailchimp / Klaviyo"),
    ],
    "designer": [
        Option(value="figma", label="Figma"),
        Option(value="sketch", label="Sketch"),
        Option(value="adobe", label="Adobe Creative Cloud"),
        Option(value="notion", label="Notion / Confluence"),
        Option(value="slack", label="Slack"),
        Option(value="linear", label="Linear / Jira"),
        Option(value="miro", label="Miro / FigJam"),
        Option(value="loom", label="Loom"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="midjourney", label="Midjourney / DALL·E"),
        Option(value="framer", label="Framer / Webflow"),
    ],
    "product_manager": [
        Option(value="linear", label="Linear / Jira"),
        Option(value="notion", label="Notion / Confluence"),
        Option(value="figma", label="Figma"),
        Option(value="slack", label="Slack"),
        Option(value="amplitude", label="Amplitude / Mixpanel"),
        Option(value="metabase", label="Metabase / Looker"),
        Option(value="docs", label="Google Docs / Sheets"),
        Option(value="loom", label="Loom"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="productboard", label="Productboard / Aha!"),
        Option(value="zoom", label="Zoom / Google Meet"),
    ],
    "sales": [
        Option(value="salesforce", label="Salesforce / HubSpot CRM"),
        Option(value="outreach", label="Outreach / Salesloft"),
        Option(value="linkedin", label="LinkedIn / Sales Navigator"),
        Option(value="apollo", label="Apollo / ZoomInfo"),
        Option(value="gmail", label="Gmail / Outlook"),
        Option(value="slack", label="Slack"),
        Option(value="zoom", label="Zoom / Google Meet"),
        Option(value="gong", label="Gong / Chorus"),
        Option(value="docusign", label="DocuSign / PandaDoc"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="excel", label="Excel / Sheets"),
    ],
    "founder": [
        Option(value="gmail", label="Gmail"),
        Option(value="slack", label="Slack"),
        Option(value="notion", label="Notion / Coda"),
        Option(value="google_workspace", label="Google Docs / Sheets"),
        Option(value="linear", label="Linear / Jira"),
        Option(value="figma", label="Figma"),
        Option(value="stripe", label="Stripe / Mercury"),
        Option(value="qbo", label="QuickBooks / Xero"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="zoom", label="Zoom / Google Meet"),
        Option(value="linkedin", label="LinkedIn / Twitter"),
    ],
    "student": [
        Option(value="google_docs", label="Google Docs / Sheets"),
        Option(value="word", label="Word / OneNote"),
        Option(value="zotero", label="Zotero / Mendeley"),
        Option(value="overleaf", label="Overleaf / LaTeX"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="notion", label="Notion / Obsidian"),
        Option(value="anki", label="Anki / Quizlet"),
        Option(value="discord", label="Discord / Slack"),
        Option(value="canvas", label="Canvas / Blackboard / Moodle"),
        Option(value="zoom", label="Zoom / Google Meet"),
        Option(value="grammarly", label="Grammarly"),
    ],
    "lawyer": [
        Option(value="word", label="Word / Google Docs"),
        Option(value="outlook", label="Outlook / Gmail"),
        Option(value="lexis", label="LexisNexis / Westlaw"),
        Option(value="ediscovery", label="Relativity / eDiscovery"),
        Option(value="ironclad", label="Ironclad / Juro / DocuSign CLM"),
        Option(value="docusign", label="DocuSign / Adobe Sign"),
        Option(value="practice_mgmt", label="Clio / MyCase / PracticePanther"),
        Option(value="harvey", label="Harvey / Spellbook / CoCounsel"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="excel", label="Excel"),
        Option(value="zoom", label="Zoom / Teams"),
    ],
    "operations": [
        Option(value="excel", label="Excel / Google Sheets"),
        Option(value="slack", label="Slack"),
        Option(value="notion", label="Notion / Confluence"),
        Option(value="zapier", label="Zapier / Make"),
        Option(value="airtable", label="Airtable / SmartSuite"),
        Option(value="asana", label="Asana / ClickUp / Monday"),
        Option(value="metabase", label="Metabase / Looker"),
        Option(value="hr_system", label="BambooHR / Rippling / Workday"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="docusign", label="DocuSign"),
        Option(value="zoom", label="Zoom / Teams"),
    ],
    "customer_success": [
        Option(value="zendesk", label="Zendesk / Intercom / Freshdesk"),
        Option(value="salesforce", label="Salesforce / HubSpot"),
        Option(value="slack", label="Slack"),
        Option(value="gmail", label="Gmail / Outlook"),
        Option(value="loom", label="Loom"),
        Option(value="zoom", label="Zoom / Google Meet"),
        Option(value="notion", label="Notion / Confluence"),
        Option(value="metabase", label="Metabase / Looker"),
        Option(value="gainsight", label="Gainsight / ChurnZero"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="jira", label="Linear / Jira"),
    ],
    "consultant": [
        Option(value="ppt", label="PowerPoint / Google Slides"),
        Option(value="excel", label="Excel / Google Sheets"),
        Option(value="word", label="Word / Google Docs"),
        Option(value="outlook", label="Outlook / Gmail"),
        Option(value="teams", label="Teams / Slack"),
        Option(value="notion", label="Notion / Coda"),
        Option(value="thinkcell", label="think-cell / Mekko"),
        Option(value="chatgpt", label="ChatGPT / Claude"),
        Option(value="research", label="Statista / IBISWorld / Gartner"),
        Option(value="zoom", label="Zoom / Google Meet"),
        Option(value="miro", label="Miro / Mural"),
    ],
}

FALLBACK_OPTIONS_Q2: list[Option] = [
    Option(value="email", label="Email (Gmail / Outlook)"),
    Option(value="slack", label="Slack / Teams"),
    Option(value="docs", label="Google Docs / Word"),
    Option(value="sheets", label="Google Sheets / Excel"),
    Option(value="calendar", label="Calendar"),
    Option(value="zoom", label="Zoom / Google Meet"),
    Option(value="notion", label="Notion / Confluence"),
    Option(value="chatgpt", label="ChatGPT / Claude"),
    Option(value="chrome", label="Browser with too many tabs"),
    Option(value="task_mgr", label="Linear / Asana / Trello"),
    Option(value="drive", label="Google Drive / Dropbox"),
    Option(value="phone", label="Phone / WhatsApp"),
]


# ---- Q3 — "Pick the closest 'big task' you actually finish" ----

ROLE_OPTIONS_Q3: dict[str, list[Option]] = {
    "software_engineer": [
        Option(value="feature_ship", label="Take a feature spec, design, code, test, PR review, ship to prod."),
        Option(value="prod_bug", label="2am page — trace logs, reproduce, root-cause, fix + regression test, deploy."),
        Option(value="refactor", label="Refactor a gnarly legacy module without breaking the 8 things that depend on it."),
        Option(value="internal_tool", label="Build an internal tool from scratch for ops/finance who keep asking the same Slack question."),
        Option(value="reviews_day", label="A day of PR reviews — push back, approve, fix CI."),
    ],
    "accountant": [
        Option(value="quarter_close", label="Close a client's quarterly books — trial balance, reconcile, journals, sign off."),
        Option(value="full_audit", label="Full audit on one client — planning, fieldwork, papers, partner sign-off, final report."),
        Option(value="financial_model", label="Build a financial model from scratch for a board or M&A deal."),
        Option(value="reconcile", label="Reconcile hundreds of transactions across entities and chase the ones that don't tie."),
        Option(value="review_others", label="Review another auditor's work — gaps, review notes, push back, clean up."),
    ],
    "doctor": [
        Option(value="clinic_day", label="Get through clinic — 20 patients, room-to-room, exam, notes, orders, follow-ups."),
        Option(value="rounds", label="Round on hospitalized patients — overnight changes, see each, update plans, notes."),
        Option(value="inbox_clear", label="Clear the inbox — 100+ messages: labs, refills, patient questions, results to route."),
        Option(value="long_case", label="Take a complex case from first visit through diagnosis, treatment, referrals, follow-up over 4–6 weeks."),
        Option(value="care_coord", label="Coordinate care for one patient across 3 specialists, family, social worker, insurance."),
    ],
    "marketer": [
        Option(value="campaign_launch", label="Launch a campaign end-to-end — brief, creative, landing page, ads, measure, iterate."),
        Option(value="brand_content", label="Ship a content piece — research, draft, design, publish, distribute across channels."),
        Option(value="data_review", label="Pull last quarter's metrics into a deck and tell the story to the leadership team."),
        Option(value="lifecycle_email", label="Build a multi-step email sequence — segment, copy, design, set up, A/B."),
        Option(value="event", label="Run an event or webinar — invite list, deck, run-of-show, follow-ups."),
    ],
    "designer": [
        Option(value="feature_design", label="Design a new feature — research, wireframes, high-fi, prototype, hand off, iterate."),
        Option(value="design_review", label="Review and unblock 6 designers' work — critique, decisions, kept-or-killed."),
        Option(value="brand_system", label="Update a design system — tokens, components, docs, migration plan."),
        Option(value="user_research", label="Run a research round — recruit, interview, synthesize, present findings."),
        Option(value="brand_visual", label="Visual / brand piece — illustration, motion, marketing site, packaging."),
    ],
    "product_manager": [
        Option(value="ship_feature", label="Spec, ship, measure a single feature end-to-end."),
        Option(value="quarter_planning", label="Run quarterly planning — gather inputs, set goals, sequence, sell internally."),
        Option(value="discovery", label="Customer-discovery round — interviews, synthesis, opportunity write-up."),
        Option(value="metrics_review", label="Weekly metrics review — pull data, find anomalies, share with the team."),
        Option(value="cross_team", label="Coordinate a cross-team initiative through 3 squads to launch."),
    ],
    "sales": [
        Option(value="full_cycle", label="Take a deal from cold outreach → demo → proposal → close."),
        Option(value="renewal", label="Renew or expand an existing account — review usage, build the case, negotiate."),
        Option(value="prospecting", label="Sourcing day — build lists, write sequences, hit the phone, book meetings."),
        Option(value="proposal", label="Craft a custom proposal / RFP response — pricing, scope, security questions."),
        Option(value="qbr", label="Quarterly business review with a key account — usage, ROI, roadmap, next-quarter plan."),
    ],
    "founder": [
        Option(value="raise", label="Run a fundraising sprint — deck, intros, pitches, follow-ups, term sheet."),
        Option(value="hire", label="Hire one critical role — sourcing, interviews, refs, offer, onboarding."),
        Option(value="ship_v1", label="Ship V1 of the product — spec, build, design, get to first paying user."),
        Option(value="customer_call", label="Run a week of customer calls — listen, synthesize, prioritize what to build."),
        Option(value="ops_setup", label="Set up the ops backbone — payroll, accounting, contracts, vendors."),
    ],
    "student": [
        Option(value="paper", label="Write a research paper — pick topic, sources, draft, revise, submit."),
        Option(value="exam_prep", label="Prep for a major exam — review syllabus, build notes, drill problems, practice."),
        Option(value="thesis_chapter", label="Write a thesis/dissertation chapter — outline, draft, advisor feedback, revise."),
        Option(value="group_project", label="Group project — split work, coordinate, integrate, present."),
        Option(value="job_app", label="Job/grad-school applications — CV, essays, references, interview prep."),
    ],
    "lawyer": [
        Option(value="contract_review", label="Review a contract — redline, negotiate, finalize, get signed."),
        Option(value="brief", label="Draft a legal brief or memo — research, outline, draft, cite-check, file."),
        Option(value="case_management", label="Take a case from intake through discovery, motions, settlement or trial."),
        Option(value="due_diligence", label="Run due diligence on a transaction — review docs, flag risks, write summary."),
        Option(value="advice_call", label="Day of client advice — calls, emails, quick-turn memos, judgment calls."),
    ],
    "operations": [
        Option(value="process_build", label="Build a process from scratch — map, automate, document, train, hand off."),
        Option(value="reporting_pack", label="Build the monthly reporting pack — pull data, format, narrative, send."),
        Option(value="vendor_setup", label="Set up a new vendor / system — contracts, integrations, training, rollout."),
        Option(value="firefighting", label="Day of firefighting — payroll glitch, missing invoice, broken Zapier, locked-out user."),
        Option(value="hr_cycle", label="Run an HR cycle — performance reviews, comp adjustments, doc updates."),
    ],
    "customer_success": [
        Option(value="onboarding", label="Onboard a new customer — kick-off, config, training, first-value milestone."),
        Option(value="qbr", label="QBR with a strategic account — usage data, ROI, expansion conversation."),
        Option(value="escalation", label="Manage a customer escalation — diagnose, mobilize internally, communicate, fix."),
        Option(value="churn_save", label="Save a churning account — root-cause, action plan, weekly check-ins."),
        Option(value="enablement", label="Build an enablement asset — playbook, video, doc that the whole team can reuse."),
    ],
    "consultant": [
        Option(value="full_engagement", label="Run a full client engagement — discovery, analysis, recommendation deck, present."),
        Option(value="market_study", label="Market sizing / landscape study — research, model, deck."),
        Option(value="due_diligence", label="Commercial due diligence — interviews, modeling, risks, deck."),
        Option(value="workshop", label="Run a workshop or strategy offsite — design, facilitate, synthesize, follow-up."),
        Option(value="rfp", label="Pitch / RFP response — qualify, scope, propose, defend pricing."),
    ],
}

FALLBACK_OPTIONS_Q3: list[Option] = [
    Option(value="ship_project", label="Take a project from scope to delivery — plan, execute, hand off."),
    Option(value="weekly_report", label="Pull together a weekly report or update — collect, analyze, share."),
    Option(value="meeting_heavy", label="Run a meeting-heavy day — back-to-back, take notes, follow up on everything."),
    Option(value="customer_call", label="Talk to customers / clients / stakeholders — calls, follow-ups, action items."),
    Option(value="solo_deepwork", label="Solo deep work — write / build / analyze something hard with the door closed."),
]


# ---- Q4 — friction (role-agnostic, single-select) ----

Q4_FRICTION_OPTIONS: list[Option] = [
    Option(value="copy_paste", label="Repetitive copy/paste between apps."),
    Option(value="searching_my_writing", label="Searching for info I already wrote down somewhere."),
    Option(value="redrafting", label="Drafting the same kind of doc / email over and over."),
    Option(value="meeting_catchup", label="Catching up after meetings I missed."),
    Option(value="finding_the_tool", label="Finding the right tool for the thing I need to do."),
    Option(value="data_cleanup", label="Manual data cleanup."),
    Option(value="waiting", label="Waiting on people."),
]


# ---- The 4 locked questions ----

LIVE_QUESTIONS: list[LiveQuestion] = [
    LiveQuestion(
        q_index=1,
        key="role.identity",
        text="Alright, let's start with the basics — who are you for ~8 hours a day?",
        helper="We won't email you. This just helps us not waste your time.",
        kind="dropdowns_3",
        sub_dropdowns={
            "job_title": JOB_TITLE_SUGGESTIONS,
            "level": LEVEL_OPTIONS,
            "industry": INDUSTRY_OPTIONS,
        },
    ),
    LiveQuestion(
        q_index=2,
        key="stack.daily_open",
        text="Which of these do you actually have open most days?",
        helper="Multi-select. We promise we won't recommend any of these — we're checking what your daily reality looks like.",
        kind="multi_select",
        options_per_role=ROLE_OPTIONS_Q2,
        fallback_options=FALLBACK_OPTIONS_Q2,
    ),
    LiveQuestion(
        q_index=3,
        key="task.big_finish",
        text="Pick the one closest to a 'big task' you actually finish at work.",
        helper="Single pick. The boring real one, not the LinkedIn version.",
        kind="single_select",
        options_per_role=ROLE_OPTIONS_Q3,
        fallback_options=FALLBACK_OPTIONS_Q3,
    ),
    LiveQuestion(
        q_index=4,
        key="friction.weekly",
        text="What slows you down most this week?",
        helper="Single pick. It's fine if more than one is true — just the worst one.",
        kind="single_select",
        options=Q4_FRICTION_OPTIONS,
    ),
]


# ---- Lookup helpers ----

def get_question(q_index: int) -> LiveQuestion | None:
    """Return the LiveQuestion for the given 1-based index, or None."""
    if 1 <= q_index <= len(LIVE_QUESTIONS):
        return LIVE_QUESTIONS[q_index - 1]
    return None


def options_for(q_index: int, role_value: str) -> list[Option] | None:
    """Resolve role-conditioned options for Q2 / Q3.

    Returns the per-role list if `role_value` (after normalization)
    has an entry; otherwise the question's fallback list. Returns
    None for non-role-conditioned questions (Q1 / Q4)."""
    question = get_question(q_index)
    if question is None:
        return None
    if question.options_per_role is None:
        # Q1 / Q4 — no role conditioning.
        return None
    role_key = role_key_for(role_value)
    return question.options_per_role.get(role_key, question.fallback_options or [])
