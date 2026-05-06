"""LLM-tag every approved tool in `tools_seed` with the 6-dim feature
record Approach 1 needs.

Reads the catalog from Mongo (per user direction), calls OpenAI
gpt-4o-mini with structured outputs, writes results to
validation/approach1/catalog_features.json.

Resumable: if catalog_features.json already has an entry for a slug,
that tool is skipped. Run again to fill in any tools added later.

Usage:
    cd /home/haseeb/dl-onboarding
    source venv/bin/activate
    python -m validation.approach1.tag_features
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from validation.approach1.schema import (
    INDUSTRIES,
    MATURITY,
    PARADIGMS,
    SETUP_TOLERANCE,
    TASK_SHAPES,
)


HERE = Path(__file__).parent
OUT_PATH = HERE / "catalog_features.json"
MODEL = "gpt-4o-mini"
CONCURRENCY = 12  # OpenAI accepts ~500 req/min on free tier; 12 in flight is safe


class ToolFeatures(BaseModel):
    industry: list[str] = Field(
        description=(
            "Industries this tool fits well. Pick from the closed enum. "
            "Use 'generic' if it works across industries with no skew. "
            "Multi-pick allowed; 1-4 typical."
        )
    )
    role_fit: list[str] = Field(
        description=(
            "Free-form short role names the tool is designed for. "
            "Examples: 'Backend Engineer', 'Auditor', 'Family Med Physician', "
            "'Sales Rep'. 1-5 entries. Use generic 'knowledge worker' only "
            "if the tool is truly role-agnostic."
        )
    )
    stack_integrations: list[str] = Field(
        description=(
            "Other tools this one integrates with or sits inside. Names only "
            "(e.g. 'Slack', 'Notion', 'GitHub', 'Excel', 'Outlook', 'Epic'). "
            "0-10 entries. Empty list if standalone."
        )
    )
    task_shape: list[str] = Field(
        description=(
            "Pick 1-3 task shapes from the closed enum that describe how "
            "this tool gets used."
        )
    )
    paradigm: list[str] = Field(
        description=(
            "Pick 1-3 paradigms from the closed enum that match how the "
            "tool fits into a workday."
        )
    )
    excluded_paradigms: list[str] = Field(
        description=(
            "Paradigms this tool actively does NOT fit (will tank the "
            "match). 0-2 entries from the closed paradigm enum. Use "
            "sparingly."
        )
    )
    setup_tolerance: str = Field(
        description=(
            "How long it takes to get value from this tool: 'under_2min' "
            "(install + done), 'around_10min' (some configuration), or "
            "'willing_to_customize' (real setup, weeks of tuning)."
        )
    )
    capabilities: list[str] = Field(
        description=(
            "Free-form short capability tags. 3-7 entries. Examples: "
            "'meeting-transcription', 'task-extraction', 'pdf-to-excel', "
            "'code-completion', 'inbox-triage'."
        )
    )
    maturity_required: str = Field(
        description=(
            "How AI-mature the user must be to extract value: 'low' "
            "(works for first-time AI users), 'medium', or 'high' "
            "(assumes the user already trusts AI workflows)."
        )
    )


SYSTEM_PROMPT = f"""You are tagging AI tools with structured features so a recommender can match them to users.

For each tool, output a STRICT JSON object matching the provided schema.

Closed enums (you MUST pick values from these for the listed fields):

INDUSTRIES = {INDUSTRIES}
TASK_SHAPES = {TASK_SHAPES}
PARADIGMS = {PARADIGMS}
SETUP_TOLERANCE = {SETUP_TOLERANCE}
MATURITY_REQUIRED = {MATURITY}

Be conservative: don't claim a tool serves an industry it doesn't, don't pad capabilities with generic words.

Calibration notes:
- ChatGPT-style chatbots: industry=['generic'], task_shape=['short_cycle','reactive'], paradigm=['async','ai_mature'], setup_tolerance='under_2min', maturity='low'.
- Code editors with AI (Cursor, Copilot): industry=['software_tech'], task_shape=['producer','deep_work'], paradigm=['in_flow','morning_deep','ai_mature'], setup_tolerance='around_10min', maturity='medium'.
- Ambient meeting scribes (Granola, Otter, Abridge): task_shape=['capture','short_cycle'], paradigm=['ambient','async'], setup_tolerance='under_2min', maturity='low'.
- EHR-integrated medical AI (Abridge for Epic): industry=['healthcare'], stack_integrations should include the EHR.
"""


async def load_catalog() -> list[dict]:
    """Read approved tools from Mongo. Falls back to seed JSON if the
    Mongo collection is empty (e.g. a fresh dev box that hasn't run the
    seeder yet)."""
    load_dotenv(Path(__file__).parents[2] / ".env")
    uri = os.environ["MONGODB_URI"]
    db_name = os.environ.get("MONGODB_DB", "mesh")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    cursor = db["tools_seed"].find({"curation_status": "approved"})
    docs = await cursor.to_list(length=None)
    if docs:
        return [
            {
                "slug": d["slug"],
                "name": d["name"],
                "tagline": d.get("tagline", ""),
                "description": d.get("description", ""),
                "category": d.get("category", ""),
            }
            for d in docs
        ]
    # Fallback: seed JSON
    seed_path = Path(__file__).parents[2] / "app" / "seed" / "catalog.json"
    return json.loads(seed_path.read_text())


def load_existing_features() -> dict[str, dict]:
    if not OUT_PATH.exists():
        return {}
    return json.loads(OUT_PATH.read_text())


def save_features(features: dict[str, dict]) -> None:
    OUT_PATH.write_text(json.dumps(features, indent=2, ensure_ascii=False))


async def tag_one(
    client: AsyncOpenAI, tool: dict, sem: asyncio.Semaphore
) -> tuple[str, dict | None, str | None]:
    """Returns (slug, features_dict_or_None, error_or_None)."""
    user_msg = (
        f"Tool: {tool['name']}\n"
        f"Slug: {tool['slug']}\n"
        f"Category: {tool.get('category', '')}\n"
        f"Tagline: {tool.get('tagline', '')}\n"
        f"Description: {tool.get('description', '')[:1500]}\n\n"
        f"Tag this tool with the structured feature record."
    )
    async with sem:
        try:
            resp = await client.beta.chat.completions.parse(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format=ToolFeatures,
                temperature=0,
            )
            parsed = resp.choices[0].message.parsed
            if parsed is None:
                return tool["slug"], None, "parsed=None"
            return tool["slug"], parsed.model_dump(), None
        except Exception as e:
            return tool["slug"], None, f"{type(e).__name__}: {e}"


async def main() -> None:
    load_dotenv(Path(__file__).parents[2] / ".env")
    # Strip stray whitespace from key name (".env has 'OPENAI_API_KEY ='")
    for k in list(os.environ):
        if k.strip() == "OPENAI_API_KEY" and k != "OPENAI_API_KEY":
            os.environ["OPENAI_API_KEY"] = os.environ.pop(k)
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY missing", file=sys.stderr)
        sys.exit(1)

    catalog = await load_catalog()
    print(f"[tag] catalog: {len(catalog)} approved tools")

    existing = load_existing_features()
    print(f"[tag] already tagged: {len(existing)}")

    todo = [t for t in catalog if t["slug"] not in existing]
    print(f"[tag] to tag now: {len(todo)}")

    if not todo:
        print("[tag] nothing to do.")
        return

    client = AsyncOpenAI()
    sem = asyncio.Semaphore(CONCURRENCY)
    t0 = time.time()
    completed = 0
    errors: list[tuple[str, str]] = []

    async def runner(tool: dict) -> None:
        nonlocal completed
        slug, feats, err = await tag_one(client, tool, sem)
        if err is not None:
            errors.append((slug, err))
            print(f"[tag] ERR {slug}: {err}")
        elif feats is not None:
            existing[slug] = {"name": tool["name"], **feats}
        completed += 1
        if completed % 25 == 0:
            save_features(existing)
            elapsed = time.time() - t0
            rate = completed / elapsed if elapsed else 0
            remaining = len(todo) - completed
            eta = remaining / rate if rate else 0
            print(
                f"[tag] {completed}/{len(todo)} done "
                f"({rate:.1f}/s, eta {eta:.0f}s, errs={len(errors)})"
            )

    await asyncio.gather(*(runner(t) for t in todo))
    save_features(existing)
    print(
        f"[tag] DONE in {time.time()-t0:.1f}s. "
        f"Tagged {len(existing)} total, {len(errors)} errors."
    )
    for slug, err in errors[:10]:
        print(f"  - {slug}: {err}")


if __name__ == "__main__":
    asyncio.run(main())
