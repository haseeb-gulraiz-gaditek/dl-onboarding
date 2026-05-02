"""`tools_founder_launched` collection access layer.

Per spec-delta founder-launch-submission-and-verification F-LAUNCH-7.

The dedicated home for approved founder-submitted tools. Sealed
against `source != "founder_launch"` writes — the inverse of cycle
#3's `tools_seed` invariant. Together they enforce the
constitutional principle "Separate organic recommendations from
launch surfacing" at the storage layer.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING

from app.db.mongo import get_db


COLLECTION_NAME = "tools_founder_launched"


def tools_founder_launched_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


async def ensure_indexes() -> None:
    await tools_founder_launched_collection().create_index(
        [("slug", ASCENDING)], unique=True, name="tools_fl_slug_unique"
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def find_by_slug(slug: str) -> dict[str, Any] | None:
    return await tools_founder_launched_collection().find_one({"slug": slug})


async def find_by_id(tool_id: ObjectId) -> dict[str, Any] | None:
    return await tools_founder_launched_collection().find_one({"_id": tool_id})


async def insert(doc: dict[str, Any]) -> dict[str, Any]:
    """Insert a founder-launched tool row. Defensive guard: refuses
    any doc whose `source` is not `"founder_launch"`.

    Defaults applied if absent:
      - curation_status = "approved" (founder rows bypass cycle #3 pending state)
      - is_founder_launched = True
      - vote_score = 0
      - embedding = None (cycle #4 lifecycle picks it up lazily)
      - created_at = now
    """
    if doc.get("source") != "founder_launch":
        raise ValueError(
            f"tools_founder_launched.insert refuses source={doc.get('source')!r}; "
            f"this collection accepts only 'founder_launch'"
        )
    out = dict(doc)
    out.setdefault("curation_status", "approved")
    out.setdefault("is_founder_launched", True)
    out.setdefault("vote_score", 0)
    out.setdefault("embedding", None)
    out.setdefault("created_at", _now())
    out.setdefault("rejection_comment", None)
    result = await tools_founder_launched_collection().insert_one(out)
    out["_id"] = result.inserted_id
    return out
