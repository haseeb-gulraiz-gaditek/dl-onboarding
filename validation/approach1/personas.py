"""The 3 locked personas from validation/onboarding-v1-locked.md,
expressed as progressive UserVectors at each step (post-Q1, post-Q2,
post-Q3, post-Q4).

The doc's "→ Algorithm" notes per pick tell us exactly what each answer
implies about the user's feature vector — those notes are encoded here.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

from validation.approach1.feature_scorer import UserVector


# ---- Persona A — ACCA (Senior Audit Manager, Finance) -------------------

ACCA_Q1 = UserVector(
    industry="finance_accounting",
    role="senior audit manager",
    setup_tolerance="around_10min",  # Senior + AI-curious-but-naive
    maturity="low",  # ChatGPT for curiosity, not workflow
)

ACCA_Q2 = deepcopy(ACCA_Q1)
ACCA_Q2.stack = ["Excel", "Outlook", "Sharepoint", "Teams", "SAP", "ChatGPT"]

ACCA_Q3 = deepcopy(ACCA_Q2)
# pick #2: full audit cycle -> long-cycle, multi-stage, producer + reviewer
ACCA_Q3.task_shape = ["long_cycle", "multi_stage", "producer", "reviewer"]

ACCA_Q4 = deepcopy(ACCA_Q3)
# pick #4: heavy numbers AM, meetings PM, EOD cleanup
ACCA_Q4.paradigm = ["morning_deep", "afternoon_coord"]


# ---- Persona B — SWE (Senior Backend, Software & Tech) ------------------

SWE_Q1 = UserVector(
    industry="software_tech",
    role="senior backend engineer",
    setup_tolerance="willing_to_customize",  # Senior + AI-mature
    maturity="medium",
)

SWE_Q2 = deepcopy(SWE_Q1)
SWE_Q2.stack = [
    "VS Code", "Cursor", "Terminal", "GitHub", "Linear", "Slack",
    "Chrome", "Postgres", "Datadog", "ChatGPT", "Copilot", "Notion",
]

SWE_Q3 = deepcopy(SWE_Q2)
# pick #1: spec -> code -> review -> ship
SWE_Q3.task_shape = ["long_cycle", "producer", "multi_stage", "deep_work"]

SWE_Q4 = deepcopy(SWE_Q3)
# pick #1: standup -> deep code AM -> reviews PM -> ship at 6
SWE_Q4.paradigm = ["morning_deep", "in_flow", "afternoon_coord", "ai_mature"]


# ---- Persona C — Doctor (Family Med Attending, Healthcare) --------------

DOC_Q1 = UserVector(
    industry="healthcare",
    role="family medicine physician",
    setup_tolerance="under_2min",  # Senior + AI-naive + Epic-locked
    maturity="low",
)

DOC_Q2 = deepcopy(DOC_Q1)
DOC_Q2.stack = ["Epic", "UpToDate", "Outlook", "Teams", "Lab portal", "WhatsApp"]

DOC_Q3 = deepcopy(DOC_Q2)
# pick #1: clinic day, 20 patients, charting between visits.
# Charting between visits = the workflow's defining task = capture.
DOC_Q3.task_shape = ["short_cycle", "high_throughput", "capture", "reactive"]

DOC_Q4 = deepcopy(DOC_Q3)
# pick #1: outpatient day with EOD charting -- "pajama-time" friction.
# Doc's own algorithm note: "ambient scribe + EHR-native automation +
# inbox triage." So paradigm is ambient (scribe) + in_flow (during
# patient visits) + async (EOD catch-up).
DOC_Q4.paradigm = ["ambient", "in_flow", "async"]


PERSONAS = {
    "ACCA — Senior Audit Manager (Finance)": [
        ("Q1", ACCA_Q1),
        ("Q2", ACCA_Q2),
        ("Q3", ACCA_Q3),
        ("Q4", ACCA_Q4),
    ],
    "SWE — Senior Backend Engineer (Software)": [
        ("Q1", SWE_Q1),
        ("Q2", SWE_Q2),
        ("Q3", SWE_Q3),
        ("Q4", SWE_Q4),
    ],
    "Doctor — Family Medicine Attending (Healthcare)": [
        ("Q1", DOC_Q1),
        ("Q2", DOC_Q2),
        ("Q3", DOC_Q3),
        ("Q4", DOC_Q4),
    ],
}


def vec_summary(v: UserVector) -> dict:
    return asdict(v)
