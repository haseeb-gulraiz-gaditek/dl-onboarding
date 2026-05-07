"""Seed ~26 realistic user profiles so concierge scans have real
candidates to match against.

Each seeded user gets:
  - users row (role_type=user, password='seeded123')
  - profiles row + a 1536-dim embedding from OpenAI
  - live_answers rows for Q1..Q4 (mirrors the live-onboarding flow)
  - ProfileEmbedding row in Weaviate (so similarity_search finds them)

Run: python -m app.seed.seed_users
Idempotent: existing emails are skipped.
"""
import asyncio
import sys
from typing import Any

from dotenv import load_dotenv

from app.auth.passwords import hash_password
from app.db.live_answers import upsert_live_answer
from app.db.mongo import close_mongo, init_mongo
from app.db.profiles import get_or_create_profile
from app.db.users import find_user_by_email, insert_user
from app.embeddings.lifecycle import ensure_profile_embedding
from app.embeddings.vector_store import close_weaviate_client


# ---- Persona definitions ----
# Each entry: (display_name, role canonical_key for live questions,
# Q1 dropdowns, Q2 stack picks, Q3 task, Q4 friction)

PERSONAS: list[dict[str, Any]] = [
    # ---- Software engineering ----
    {"name": "Aanya SWE Senior", "q1": ("software_engineer", "senior", "software_tech"),
     "q2": ["vscode", "github", "linear", "slack", "db_client", "copilot"],
     "q3": "feature_ship", "q4": "searching_my_writing"},
    {"name": "Bilal SWE Lead", "q1": ("software_engineer", "lead", "software_tech"),
     "q2": ["vscode", "terminal", "github", "datadog", "chatgpt", "copilot", "notion"],
     "q3": "refactor", "q4": "meeting_catchup"},
    {"name": "Carla DataSci", "q1": ("data_scientist", "mid", "software_tech"),
     "q2": ["vscode", "github", "db_client", "chatgpt", "notion"],
     "q3": "internal_tool", "q4": "data_cleanup"},
    {"name": "Dmitri Junior Dev", "q1": ("software_engineer", "junior", "software_tech"),
     "q2": ["vscode", "github", "slack", "chatgpt", "copilot"],
     "q3": "reviews_day", "q4": "finding_the_tool"},

    # ---- Marketing ----
    {"name": "Elena Growth Marketer", "q1": ("marketer", "senior", "marketing_advertising"),
     "q2": ["hubspot", "ga", "figma", "canva", "jasper", "ahrefs", "linkedin"],
     "q3": "campaign_launch", "q4": "redrafting"},
    {"name": "Fatima Content Marketer", "q1": ("marketer", "mid", "media_content"),
     "q2": ["google_workspace", "notion", "canva", "chatgpt", "jasper", "linkedin"],
     "q3": "brand_content", "q4": "redrafting"},
    {"name": "Greg Brand Lead", "q1": ("marketer", "lead", "marketing_advertising"),
     "q2": ["figma", "canva", "notion", "slack", "ga", "ahrefs"],
     "q3": "data_review", "q4": "meeting_catchup"},

    # ---- Healthcare ----
    {"name": "Hina Family Doctor", "q1": ("doctor", "senior", "healthcare"),
     "q2": ["epic", "uptodate", "outlook", "teams", "lab_portal", "whatsapp"],
     "q3": "clinic_day", "q4": "meeting_catchup"},
    {"name": "Imran Hospitalist", "q1": ("doctor", "senior", "healthcare"),
     "q2": ["epic", "uptodate", "outlook", "teams", "ambient_scribe", "whatsapp"],
     "q3": "rounds", "q4": "redrafting"},

    # ---- Sales ----
    {"name": "Jamal Sales Rep", "q1": ("sales_rep", "mid", "sales"),
     "q2": ["salesforce", "outreach", "linkedin", "apollo", "gmail", "zoom"],
     "q3": "full_cycle", "q4": "redrafting"},
    {"name": "Kira AE Senior", "q1": ("sales_rep", "senior", "sales"),
     "q2": ["salesforce", "outreach", "linkedin", "gong", "gmail", "zoom", "docusign"],
     "q3": "renewal", "q4": "meeting_catchup"},

    # ---- Designers ----
    {"name": "Liam Product Designer", "q1": ("ux_designer", "senior", "design_creative"),
     "q2": ["figma", "notion", "slack", "linear", "miro", "loom", "chatgpt"],
     "q3": "feature_design", "q4": "redrafting"},
    {"name": "Maya UX Lead", "q1": ("ux_designer", "lead", "design_creative"),
     "q2": ["figma", "miro", "notion", "linear", "loom"],
     "q3": "brand_system", "q4": "finding_the_tool"},

    # ---- Product Managers ----
    {"name": "Naoki PM", "q1": ("product_manager", "senior", "software_tech"),
     "q2": ["linear", "notion", "figma", "slack", "amplitude", "docs", "chatgpt"],
     "q3": "ship_feature", "q4": "meeting_catchup"},
    {"name": "Olga PM Lead", "q1": ("product_manager", "lead", "software_tech"),
     "q2": ["linear", "notion", "figma", "slack", "metabase", "loom"],
     "q3": "quarter_planning", "q4": "data_cleanup"},

    # ---- Founders ----
    {"name": "Priya Founder", "q1": ("founder_ceo", "executive", "software_tech"),
     "q2": ["gmail", "slack", "notion", "linear", "stripe", "chatgpt", "linkedin"],
     "q3": "raise", "q4": "waiting"},
    {"name": "Quinn Solo Founder", "q1": ("founder_ceo", "freelance", "software_tech"),
     "q2": ["gmail", "notion", "linear", "stripe", "chatgpt", "google_workspace"],
     "q3": "ship_v1", "q4": "copy_paste"},

    # ---- Legal ----
    {"name": "Rashid Lawyer", "q1": ("lawyer", "senior", "legal"),
     "q2": ["word", "outlook", "lexis", "docusign", "chatgpt"],
     "q3": "contract_review", "q4": "redrafting"},
    {"name": "Sana Paralegal", "q1": ("paralegal", "mid", "legal"),
     "q2": ["word", "outlook", "lexis", "ediscovery"],
     "q3": "due_diligence", "q4": "data_cleanup"},

    # ---- Finance / Accounting ----
    {"name": "Tariq Auditor", "q1": ("auditor", "senior", "finance_accounting"),
     "q2": ["excel", "outlook", "sharepoint", "teams", "erp", "chatgpt"],
     "q3": "full_audit", "q4": "data_cleanup"},
    {"name": "Uma Accountant", "q1": ("accountant", "mid", "finance_accounting"),
     "q2": ["excel", "outlook", "quickbooks", "teams", "chatgpt"],
     "q3": "quarter_close", "q4": "copy_paste"},

    # ---- Operations / HR ----
    {"name": "Vihaan Ops Lead", "q1": ("operations", "lead", "operations"),
     "q2": ["excel", "slack", "notion", "zapier", "airtable", "asana", "metabase"],
     "q3": "process_build", "q4": "waiting"},
    {"name": "Wendy HR Manager", "q1": ("hr", "manager", "hr"),
     "q2": ["slack", "notion", "hr_system", "docusign", "zoom"],
     "q3": "hr_cycle", "q4": "meeting_catchup"},

    # ---- Customer Success ----
    {"name": "Xian CS Manager", "q1": ("customer_success", "manager", "software_tech"),
     "q2": ["zendesk", "salesforce", "slack", "loom", "zoom", "notion"],
     "q3": "qbr", "q4": "redrafting"},

    # ---- Students / Teachers ----
    {"name": "Yusuf Grad Student", "q1": ("student", "student", "education"),
     "q2": ["google_docs", "zotero", "overleaf", "chatgpt", "notion", "anki"],
     "q3": "thesis_chapter", "q4": "searching_my_writing"},
    {"name": "Zara Teacher", "q1": ("teacher", "mid", "education"),
     "q2": ["google_docs", "canvas", "zoom", "google_workspace"],
     "q3": "exam_prep", "q4": "redrafting"},

    # ---- Consultants ----
    {"name": "Ahmed Consultant", "q1": ("consultant", "senior", "consulting"),
     "q2": ["ppt", "excel", "word", "outlook", "teams", "thinkcell", "chatgpt"],
     "q3": "full_engagement", "q4": "redrafting"},
]


def _profile_text(p: dict[str, Any]) -> str:
    """Build the same structured paragraph the live engine builds.
    Inlined here so the seed script doesn't depend on the live engine
    code path (and is robust if that builder changes shape)."""
    job, level, industry = p["q1"]
    parts = [f"I'm a {level.replace('_',' ')} {job.replace('_',' ')} in {industry.replace('_',' ')}."]
    parts.append(
        "On a typical day I have these tools open: "
        + ", ".join(s.replace("_", " ") for s in p["q2"])
        + "."
    )
    parts.append(f"A 'big task' I actually finish at work: {p['q3'].replace('_',' ')}")
    parts.append(f"What slows me down most: {p['q4'].replace('_',' ')}")
    return " ".join(parts)


async def _seed_one(p: dict[str, Any]) -> str:
    name = p["name"]
    email = (
        "seed-"
        + name.lower().replace(" ", "-")
        .replace("/", "-")
        + "@mesh.local"
    )
    existing = await find_user_by_email(email)
    if existing is not None:
        return f"skip {email} (exists)"

    user = await insert_user(
        email=email,
        password_hash=hash_password("seeded123"),
        role_type="user",
        display_name=name,
    )
    user_id = user["_id"]

    # Profile row first.
    await get_or_create_profile(user)

    # Live-answer rows for Q1-Q4 so /home renders properly when a real
    # admin loads one of these accounts.
    job, level, industry = p["q1"]
    await upsert_live_answer(
        user_id=user_id, q_index=1,
        value={"job_title": job, "level": level, "industry": industry},
    )
    await upsert_live_answer(
        user_id=user_id, q_index=2,
        value={"selected_values": p["q2"]},
    )
    await upsert_live_answer(
        user_id=user_id, q_index=3,
        value={"selected_value": p["q3"]},
    )
    await upsert_live_answer(
        user_id=user_id, q_index=4,
        value={"selected_value": p["q4"]},
    )

    # Embed + publish to Weaviate's ProfileEmbedding class. This is
    # what makes the user findable via the founder-side concierge scan.
    text = _profile_text(p)
    await ensure_profile_embedding(
        user, force_recompute=True, override_text=text,
    )

    return f"seeded {email}"


async def _main() -> int:
    load_dotenv("/home/haseeb/dl-onboarding/.env")
    await init_mongo()
    try:
        for p in PERSONAS:
            try:
                msg = await _seed_one(p)
                print(f"[seed-users] {msg}", flush=True)
            except Exception as exc:
                print(f"[seed-users] FAILED {p['name']}: {exc}", flush=True)
        print(f"[seed-users] done — {len(PERSONAS)} personas", flush=True)
    finally:
        await close_weaviate_client()
        await close_mongo()
    return 0


def main() -> None:
    sys.exit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
