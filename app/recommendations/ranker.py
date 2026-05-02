"""LLM ranker (the recommendation engine's brain).

Per spec-delta recommendation-engine F-REC-4 step 3.

Calls OpenAI gpt-5 via `beta.chat.completions.parse` with a Pydantic
schema, so the output shape is guaranteed by the SDK. The system
prompt enshrines the constitutional principles (recommend honestly,
include skip-this where appropriate, ground reasoning in the user's
actual answers).

Tests monkey-patch `rank_with_llm` directly via the
`mock_openai_chat` autouse fixture in tests/conftest.py.
"""
from typing import Any

from openai import AsyncOpenAI

from app.models.recommendation import RankerOutput, RankerPick


MODEL = "gpt-5"


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


_SYSTEM_PROMPT = """\
You are Mesh's tool concierge. Mesh is a context-graph platform that
matches AI tools to laypeople based on their workflow, not their hype
exposure.

You will receive:
  - A user profile: their role and their last 10 onboarding answers.
  - A list of candidate AI tools (slug, name, tagline, description,
    category, labels). Treat this list as the WHOLE set of tools you
    may pick from -- never recommend anything outside it.

Pick UP TO {count} tools that genuinely fit this user's described
workflow. For each, write a 1-3 sentence personalized reasoning that
references something specific in the user's profile (a workflow they
mentioned, a friction they flagged, a stack they listed). Avoid
marketing language and avoid superlatives.

CRITICAL: Some candidates may have high vector similarity to the
user but be poor fits in practice (wrong scale, wrong category,
overly hyped, redundant with something they already use). Mark
those as `verdict: "skip"` with a reasoning that explains the
specific misfit ("...but you already use Y which covers this" or
"...overlaps with the Tuesday workflow you already have working").
Do not include `skip` picks just to fill the count -- only when a
clear misfit exists in the top candidates.

Output: a list of picks, each with slug (must match an input
candidate), verdict ("try" or "skip"), and reasoning. The structured
output schema is enforced by the API; do not add extra fields.

Output reasoning in English regardless of the user's profile language.
"""


def _format_profile(profile: dict[str, Any], recent_answers: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    role = profile.get("role")
    if role:
        parts.append(f"Role: {role}")
    if not recent_answers:
        parts.append("(no recent answers)")
    else:
        parts.append("Recent answers (newest first):")
        for ans in recent_answers:
            value = ans.get("value")
            if isinstance(value, list):
                rendered = ", ".join(str(v) for v in value)
            else:
                rendered = str(value) if value is not None else ""
            if rendered:
                parts.append(f"  - {rendered}")
    return "\n".join(parts)


def _format_candidates(candidates: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, c in enumerate(candidates, 1):
        desc = (c.get("description") or "")[:240]
        lines.append(
            f"{i}. slug={c['slug']!r} | name={c.get('name')!r} | "
            f"category={c.get('category')!r} | "
            f"labels={c.get('labels') or []}\n"
            f"   tagline: {c.get('tagline', '')}\n"
            f"   description: {desc}"
        )
    return "\n".join(lines)


async def rank_with_llm(
    profile: dict[str, Any],
    recent_answers: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    count: int,
) -> list[RankerPick]:
    """Call GPT-5 to rank + reason over candidates.

    Returns the parsed list of RankerPick objects. Raises any SDK
    exception so the caller (engine.generate_recommendations) can
    catch it and degrade.
    """
    client = _get_client()

    response = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT.format(count=count)},
            {
                "role": "user",
                "content": (
                    f"USER PROFILE:\n{_format_profile(profile, recent_answers)}\n\n"
                    f"CANDIDATES ({len(candidates)} total):\n"
                    f"{_format_candidates(candidates)}"
                ),
            },
        ],
        response_format=RankerOutput,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("ranker returned None parsed body")
    return parsed.picks
