"""Pydantic shapes for the posts endpoints.

Per spec-delta communities-and-flat-comments F-COM-3, F-COM-4.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PostAuthor(BaseModel):
    id: str
    display_name: str


class PostCreateRequest(BaseModel):
    """POST /api/posts body."""

    community_slug: str
    cross_post_slugs: list[str] = Field(default_factory=list)
    title: str = Field(..., min_length=1, max_length=200)
    body_md: str = Field(default="", max_length=10000)


class PostCard(BaseModel):
    """A post in a feed listing or detail view."""

    id: str
    community_slug: str
    cross_posted_to: list[str]
    author: PostAuthor
    title: str
    body_md: str
    attached_launch_id: str | None
    vote_score: int
    comment_count: int
    user_vote: int        # -1, 0, 1 — the requesting user's vote
    flagged: bool
    created_at: datetime
    last_activity_at: datetime


class PostListResponse(BaseModel):
    posts: list[PostCard]
    next_before: datetime | None     # cursor for pagination; None on last page


class CommentCard(BaseModel):
    id: str
    post_id: str
    author: PostAuthor
    body_md: str
    vote_score: int
    user_vote: int
    flagged: bool
    created_at: datetime


class PostDetailResponse(BaseModel):
    post: PostCard
    comments: list[CommentCard]


def to_post_author(user_doc: dict[str, Any]) -> PostAuthor:
    return PostAuthor(
        id=str(user_doc["_id"]),
        display_name=user_doc.get("display_name", ""),
    )
