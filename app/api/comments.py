"""Comment endpoints.

Per spec-delta communities-and-flat-comments F-COM-5.
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import require_role
from app.db.comments import insert as insert_comment
from app.db.notifications import insert as insert_notification
from app.db.posts import bump_comment_count, find_by_id as find_post_by_id
from app.models.comment import CommentCreateRequest, CommentCreateResponse
from app.models.post import CommentCard, PostAuthor


router = APIRouter(prefix="/api/comments", tags=["comments"])


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


@router.post(
    "", response_model=CommentCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_comment(
    payload: CommentCreateRequest,
    user: dict[str, Any] = Depends(require_role("user")),
) -> CommentCreateResponse:
    """F-COM-5: flat comment. parent_comment_id is silently ignored.
    Increments posts.comment_count and bumps last_activity_at."""
    body = payload.body_md.strip()
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "field_required", "field": "body_md"},
        )

    post_oid = _parse_oid(payload.post_id)
    if post_oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "post_not_found"},
        )
    post = await find_post_by_id(post_oid)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "post_not_found"},
        )

    comment_doc = await insert_comment(
        post_id=post_oid, author_user_id=user["_id"], body_md=body
    )
    await bump_comment_count(post_oid, 1)

    # F-NOTIF-7 (cycle #12): community_reply notification on
    # someone-else's-post comment. Best-effort — never aborts the
    # comment write. Self-replies skipped.
    if post["author_user_id"] != user["_id"]:
        try:
            await insert_notification(
                user_id=post["author_user_id"],
                kind="community_reply",
                payload={
                    "post_id": str(post_oid),
                    "comment_id": str(comment_doc["_id"]),
                    "commenter_display_name": user.get("display_name", ""),
                },
            )
        except Exception as exc:
            print(f"[comments] community_reply notification failed: {exc}")

    return CommentCreateResponse(
        comment=CommentCard(
            id=str(comment_doc["_id"]),
            post_id=str(comment_doc["post_id"]),
            author=PostAuthor(
                id=str(user["_id"]),
                display_name=user.get("display_name", ""),
            ),
            body_md=comment_doc["body_md"],
            vote_score=0,
            user_vote=0,
            flagged=False,
            created_at=comment_doc["created_at"],
        )
    )
