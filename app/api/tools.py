"""Canonical product page endpoint.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-4.

GET /api/tools/{slug} — reads tools_seed first, then
tools_founder_launched. Returns unified card + launch metadata
(only populated when is_founder_launched=true).
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import current_user
from app.db.launches import find_by_id as find_launch_by_id
from app.db.tools_founder_launched import find_by_slug as fl_find_by_slug
from app.db.tools_seed import find_tool_by_slug
from app.db.users import find_user_by_id
from app.models.tool_page import LaunchMeta, ProductPageResponse, to_product_card


router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/{slug}", response_model=ProductPageResponse)
async def get_product_page(
    slug: str,
    _user: dict[str, Any] = Depends(current_user),
) -> ProductPageResponse:
    """F-PUB-4: tool details + optional launch metadata."""
    seed_doc = await find_tool_by_slug(slug)
    if seed_doc is not None:
        return ProductPageResponse(
            tool=to_product_card(seed_doc, is_founder_launched=False),
            launch=None,
        )

    fl_doc = await fl_find_by_slug(slug)
    if fl_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )

    # Hydrate launch meta.
    launch_meta: LaunchMeta | None = None
    launched_via_id = fl_doc.get("launched_via_id")
    if launched_via_id is not None:
        launch_doc = await find_launch_by_id(launched_via_id)
        if launch_doc is not None:
            founder = await find_user_by_id(str(launch_doc["founder_user_id"]))
            launch_meta = LaunchMeta(
                founder_email=founder.get("email", "") if founder else "",
                founder_display_name=(
                    founder.get("display_name", "") if founder else ""
                ),
                problem_statement=launch_doc.get("problem_statement", ""),
                icp_description=launch_doc.get("icp_description", ""),
                approved_at=launch_doc.get("reviewed_at"),
                target_community_slugs=launch_doc.get(
                    "target_community_slugs"
                ) or [],
            )

    return ProductPageResponse(
        tool=to_product_card(fl_doc, is_founder_launched=True),
        launch=launch_meta,
    )
