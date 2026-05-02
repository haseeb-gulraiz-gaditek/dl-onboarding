"""Founder-side launch endpoints.

Per spec-delta founder-launch-submission-and-verification
F-LAUNCH-1, F-LAUNCH-2.
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.middleware import require_role
from app.db.launches import find_by_id, find_for_founder, insert
from app.models.launch import (
    LaunchListResponse,
    LaunchResponse,
    LaunchSubmitRequest,
    to_launch_response,
)


router = APIRouter(prefix="/api/founders", tags=["founders"])


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


def _is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


@router.post(
    "/launch", response_model=LaunchResponse, status_code=status.HTTP_201_CREATED
)
async def submit_launch(
    payload: LaunchSubmitRequest,
    user: dict[str, Any] = Depends(require_role("founder")),
) -> LaunchResponse:
    """F-LAUNCH-1: founder submits a launch."""
    product_url = payload.product_url.strip()
    if not _is_http_url(product_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "url_invalid", "field": "product_url"},
        )

    problem = payload.problem_statement.strip()
    icp = payload.icp_description.strip()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "field_required", "field": "problem_statement"},
        )
    if not icp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "field_required", "field": "icp_description"},
        )

    cleaned_links: list[str] = []
    for link in payload.existing_presence_links:
        link = link.strip()
        if not link:
            continue
        if not _is_http_url(link):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "field_invalid",
                    "field": "existing_presence_links",
                },
            )
        cleaned_links.append(link)

    doc = await insert(
        founder_user_id=user["_id"],
        product_url=product_url,
        problem_statement=problem,
        icp_description=icp,
        existing_presence_links=cleaned_links,
    )
    return to_launch_response(doc)


@router.get("/launches", response_model=LaunchListResponse)
async def list_my_launches(
    status: str | None = Query(default=None),  # noqa: A002 (shadows std `status`; scoped)
    user: dict[str, Any] = Depends(require_role("founder")),
) -> LaunchListResponse:
    """F-LAUNCH-2: founder's own launches, optional status filter."""
    docs = await find_for_founder(user["_id"], status=status)
    return LaunchListResponse(launches=[to_launch_response(d) for d in docs])


@router.get("/launches/{launch_id}", response_model=LaunchResponse)
async def get_my_launch(
    launch_id: str,
    user: dict[str, Any] = Depends(require_role("founder")),
) -> LaunchResponse:
    """F-LAUNCH-2: founder reads their own launch.

    Returns 404 if the launch belongs to a different founder, to
    avoid leaking existence."""
    oid = _parse_oid(launch_id)
    if oid is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    doc = await find_by_id(oid)
    if doc is None or doc.get("founder_user_id") != user["_id"]:
        raise HTTPException(
            status_code=404,
            detail={"error": "launch_not_found"},
        )
    return to_launch_response(doc)
