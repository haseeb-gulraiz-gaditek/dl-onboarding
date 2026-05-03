"""Cross-collection tool resolver.

Per spec-delta my-tools-explore-new-tabs F-TOOL-2.

Tools live in two sealed collections (cycle #3 + cycle #8):
  - tools_seed (organic, source != "founder_launch")
  - tools_founder_launched (source == "founder_launch")

Both store stable, globally-unique slugs (cycle #8 F-LAUNCH-6).
The resolver scans tools_seed first, then tools_founder_launched.
"""
from typing import Any

from bson import ObjectId

from app.db.tools_founder_launched import (
    find_by_id as fl_find_by_id,
    find_by_slug as fl_find_by_slug,
)
from app.db.tools_seed import find_tool_by_slug, tools_seed_collection


async def find_tool_anywhere(
    slug_or_id: str | ObjectId,
) -> tuple[dict[str, Any] | None, bool]:
    """Resolve a tool by either slug or ObjectId across both
    collections. Returns (doc, is_founder_launched).

    tools_seed wins on collision. (In practice the unique-slug
    convention from F-LAUNCH-6 prevents collisions.)
    """
    if isinstance(slug_or_id, ObjectId):
        doc = await tools_seed_collection().find_one({"_id": slug_or_id})
        if doc is not None:
            return doc, False
        doc = await fl_find_by_id(slug_or_id)
        if doc is not None:
            return doc, True
        return None, False

    # String — assume slug.
    doc = await find_tool_by_slug(slug_or_id)
    if doc is not None:
        return doc, False
    doc = await fl_find_by_slug(slug_or_id)
    if doc is not None:
        return doc, True
    return None, False
