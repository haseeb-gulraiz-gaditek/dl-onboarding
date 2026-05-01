"""Admin catalog router.

Implements F-CAT-5 of spec-delta catalog-seed-and-curation. All
endpoints are behind `Depends(require_admin())` (F-CAT-4).
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.admin import require_admin
from app.db.tools_seed import find_tool_by_slug, list_tools_by_status, set_status
from app.models.tool import CurationStatus, ToolPublic, ToolReject, to_public


router = APIRouter(
    prefix="/admin/catalog",
    tags=["admin", "catalog"],
)


@router.get("", response_model=list[ToolPublic])
async def list_catalog(
    status: str | None = None,
    _: dict[str, Any] = Depends(require_admin()),
) -> list[ToolPublic]:
    """F-CAT-5: list catalog entries optionally filtered by curation_status.

    `status` ∈ {`pending`, `approved`, `rejected`, `all`}. `None` and
    `all` both return every entry.
    """
    if status not in (None, "all", "pending", "approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "status_invalid",
                "allowed": ["pending", "approved", "rejected", "all"],
            },
        )
    docs = await list_tools_by_status(status)
    return [to_public(d) for d in docs]


@router.get("/{slug}", response_model=ToolPublic)
async def get_catalog_entry(
    slug: str,
    _: dict[str, Any] = Depends(require_admin()),
) -> ToolPublic:
    """F-CAT-5: return a single catalog entry by slug."""
    doc = await find_tool_by_slug(slug)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )
    return to_public(doc)


@router.post("/{slug}/approve", response_model=ToolPublic)
async def approve_catalog_entry(
    slug: str,
    admin: dict[str, Any] = Depends(require_admin()),
) -> ToolPublic:
    """F-CAT-5: set curation_status=approved + reviewer metadata.

    Clears any prior rejection_comment.
    """
    updated = await set_status(
        slug=slug,
        status="approved",
        reviewer_email=admin["email"],
        rejection_comment=None,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )
    return to_public(updated)


@router.post("/{slug}/reject", response_model=ToolPublic)
async def reject_catalog_entry(
    slug: str,
    payload: ToolReject,
    admin: dict[str, Any] = Depends(require_admin()),
) -> ToolPublic:
    """F-CAT-5: set curation_status=rejected with a non-empty comment.

    Pydantic enforces min_length=1 on `comment` at the schema layer; an
    additional whitespace check is applied here so a string of spaces
    does not slip through as a "valid" comment.
    """
    if not payload.comment.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "comment_invalid"},
        )

    updated = await set_status(
        slug=slug,
        status="rejected",
        reviewer_email=admin["email"],
        rejection_comment=payload.comment.strip(),
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "tool_not_found"},
        )
    return to_public(updated)
