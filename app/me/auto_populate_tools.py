"""Auto-populate user_tools from onboarding answers.

Per spec-delta my-tools-explore-new-tabs F-TOOL-7.

Triggered after every successful POST /api/answers (F-QB-3 MODIFIED).
Only fires for multi_select questions whose value is a list of strings;
each string is resolved against tools_seed + tools_founder_launched
via find_tool_anywhere. Resolved tools become user_tools rows with
source=auto_from_profile, status=using.

Best-effort: per-row exceptions are logged + swallowed; the hook
NEVER aborts the answer-write.
"""
from typing import Any

from bson import ObjectId

from app.db.user_tools import upsert_auto_from_profile
from app.tools_resolver import find_tool_anywhere


async def auto_populate_from_answer(
    user_id: ObjectId,
    question_doc: dict[str, Any],
    answer_value: Any,
) -> int:
    """Returns the number of user_tools rows touched (inserted or
    no-op'd). Always returns 0 on bail-out conditions; never raises."""
    try:
        if question_doc.get("kind") != "multi_select":
            return 0
        if not isinstance(answer_value, list):
            return 0

        touched = 0
        for raw in answer_value:
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                tool_doc, _is_fl = await find_tool_anywhere(raw.strip())
                if tool_doc is None:
                    continue
                await upsert_auto_from_profile(
                    user_id=user_id, tool_id=tool_doc["_id"]
                )
                touched += 1
            except Exception as exc:
                print(
                    f"[auto_populate_tools] upsert failed for {raw!r}: {exc}"
                )
        return touched
    except Exception as exc:
        print(f"[auto_populate_tools] hook failed: {exc}")
        return 0
