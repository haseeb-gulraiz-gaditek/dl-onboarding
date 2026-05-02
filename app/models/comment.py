"""Pydantic shapes for the comments endpoint.

Per spec-delta communities-and-flat-comments F-COM-5.
"""
from pydantic import BaseModel, Field

from app.models.post import CommentCard


class CommentCreateRequest(BaseModel):
    """POST /api/comments body. parent_comment_id is intentionally
    omitted from the request schema -- threading is V1.5+; if a client
    sends it, the value is silently ignored at the route layer."""

    post_id: str
    body_md: str = Field(..., min_length=1, max_length=5000)


class CommentCreateResponse(BaseModel):
    comment: CommentCard
