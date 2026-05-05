"""GET /api/me/profile-summary — derive stack + all-tags from answers.

Cycle #13 audit pass: the home page's "Your stack" panel and profile
graph need data that reflects the user's actual onboarding picks,
not whatever cycle #10's slug-resolution managed to match. This
endpoint returns:

  - `stack_tools`: most-recent multi_select answer for each
    category="stack" question, projected into {value, label} using
    the question's own option list (so labels survive even if the
    catalog has different slugs).
  - `all_answer_values`: flat union of every option value across
    every answer the user has given. Frontend uses this to derive
    tags for the profile graph via tag-map.ts.
"""
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.middleware import require_role
from app.db.answers import answers_collection
from app.db.questions import questions_collection


router = APIRouter(prefix="/api/me", tags=["me_profile_summary"])


class StackToolEntry(BaseModel):
    value: str
    label: str


class ProfileSummaryResponse(BaseModel):
    stack_tools: list[StackToolEntry]
    all_answer_values: list[str]


@router.get("/profile-summary", response_model=ProfileSummaryResponse)
async def profile_summary(
    user: dict[str, Any] = Depends(require_role("user")),
) -> ProfileSummaryResponse:
    user_id: ObjectId = user["_id"]

    # Pull all of the user's answers, newest first.
    cursor = (
        answers_collection()
        .find({"user_id": user_id})
        .sort([("captured_at", -1)])
    )
    answers = await cursor.to_list(length=None)

    if not answers:
        return ProfileSummaryResponse(stack_tools=[], all_answer_values=[])

    # Resolve question docs for the answered question_ids (one query).
    qids = list({a["question_id"] for a in answers})
    qcursor = questions_collection().find({"_id": {"$in": qids}})
    qmap: dict[ObjectId, dict[str, Any]] = {}
    async for q in qcursor:
        qmap[q["_id"]] = q

    # all_answer_values: every value (string or list[string]) flattened.
    all_values: list[str] = []
    for a in answers:
        v = a.get("value")
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item:
                    all_values.append(item)
        elif isinstance(v, str) and v:
            all_values.append(v)

    # stack_tools: newest multi_select stack-category answer wins per
    # question_key. Walk newest-first, keep first hit per key.
    seen_keys: set[str] = set()
    stack: list[StackToolEntry] = []
    for a in answers:
        q = qmap.get(a["question_id"])
        if q is None:
            continue
        if q.get("category") != "stack":
            continue
        if q.get("kind") != "multi_select":
            continue
        if q.get("key") in seen_keys:
            continue
        seen_keys.add(q.get("key"))

        v = a.get("value")
        if not isinstance(v, list):
            continue
        # Project values into {value, label} using the question's options.
        opt_label: dict[str, str] = {
            o.get("value", ""): o.get("label", o.get("value", ""))
            for o in (q.get("options") or [])
            if isinstance(o, dict)
        }
        for picked in v:
            if not isinstance(picked, str) or not picked:
                continue
            stack.append(
                StackToolEntry(
                    value=picked,
                    label=opt_label.get(picked, picked),
                )
            )

    return ProfileSummaryResponse(
        stack_tools=stack, all_answer_values=all_values,
    )
