"""Mode dispatch + per-mode match implementations.

Per spec-delta fast-onboarding-match-and-graph F-MATCH-2..4.

Module-level constants:
  GENERIC_MODE_MAX_ANSWERS  threshold below which we use generic
                            mode. Set to 3 per the user's call:
                            "first 3 questions are too generic for
                            embedding-based matching."
  TOP_K                     number of tools returned per call.
"""
from typing import Any

from bson import ObjectId

from app.db.answers import answers_collection
from app.db.profiles import find_profile_by_user_id
from app.db.questions import questions_collection
from app.db.tools_seed import tools_seed_collection
from app.embeddings.lifecycle import ensure_profile_embedding
from app.embeddings.vector_store import TOOL_CLASS, similarity_search
from app.onboarding.role_map import categories_for_role


GENERIC_MODE_MAX_ANSWERS = 3
TOP_K = 5

ROLE_QUESTION_KEY = "role.primary_function"


async def count_distinct_answers(user_id: ObjectId) -> int:
    """Count the number of DISTINCT question_ids the user has at least
    one answer for. Re-answering the same question doesn't double-count
    (per F-QB-3 append-only semantics)."""
    cursor = answers_collection().find(
        {"user_id": user_id}, {"question_id": 1}
    )
    distinct_qids: set[ObjectId] = {row["question_id"] async for row in cursor}
    return len(distinct_qids)


async def latest_role_for_user(user_id: ObjectId) -> str | None:
    """Return the user's most-recent answer to the role.primary_function
    question (a single-select string), or None if they haven't answered
    it yet."""
    role_q = await questions_collection().find_one({"key": ROLE_QUESTION_KEY})
    if role_q is None:
        return None
    cursor = answers_collection().find(
        {"user_id": user_id, "question_id": role_q["_id"]}
    ).sort("captured_at", -1).limit(1)
    docs = await cursor.to_list(length=1)
    if not docs:
        return None
    value = docs[0].get("value")
    return value if isinstance(value, str) else None


async def generic_match(user: dict[str, Any]) -> list[dict[str, Any]]:
    """F-MATCH-3: role -> categories -> all_time_best filter, alphabetical
    top-TOP_K. Falls back to catalog-wide all_time_best if (a) role is
    None / unknown, OR (b) the role-bucket query returns < TOP_K."""
    coll = tools_seed_collection()
    role = await latest_role_for_user(user["_id"])
    categories = categories_for_role(role)

    bucket_results: list[dict[str, Any]] = []
    if categories:
        cursor = coll.find(
            {
                "curation_status": "approved",
                "category": {"$in": categories},
                "labels": "all_time_best",
            }
        ).sort("name", 1).limit(TOP_K)
        bucket_results = await cursor.to_list(length=TOP_K)

    if len(bucket_results) >= TOP_K:
        return bucket_results

    # Fallback: catalog-wide all_time_best.
    cursor = coll.find(
        {
            "curation_status": "approved",
            "labels": "all_time_best",
        }
    ).sort("name", 1).limit(TOP_K)
    return await cursor.to_list(length=TOP_K)


async def embedding_match(user: dict[str, Any]) -> list[dict[str, Any]]:
    """F-MATCH-4: ensure profile embedding is fresh, then similarity_search
    against the ToolEmbedding class. Returns up to TOP_K tools.

    May call OpenAI when the profile embedding is stale (~500ms). The
    caller (`match` endpoint handler) is responsible for catching
    OpenAI exceptions and degrading to generic mode.
    """
    await ensure_profile_embedding(user)
    profile = await find_profile_by_user_id(user["_id"])
    if profile is None or profile.get("embedding") is None:
        return []
    return await similarity_search(
        collection_name="tools_seed",
        weaviate_class=TOOL_CLASS,
        query_vector=profile["embedding"],
        top_k=TOP_K,
        filters={"curation_status": "approved"},
    )
