"""Post endpoints.

Per spec-delta communities-and-flat-comments F-COM-3, F-COM-4.

Three endpoints:
  POST /api/posts                        — create (require_role user)
  GET  /api/posts/{id}                   — detail + comments
  GET  /api/communities/{slug}/posts     — community feed (newest-first)

The feed lives on a SEPARATE router instance so it can be mounted
under /api/communities while the create/detail endpoints share the
/api/posts prefix.
"""
from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.middleware import current_user, require_role
from app.db.comments import for_post as comments_for_post
from app.db.communities import find_by_id as find_community_by_id, find_by_slug
from app.db.posts import feed_for_community, find_by_id as find_post_by_id, insert as insert_post
from app.db.users import find_user_by_id
from app.db.votes import find_user_votes_for_targets
from app.models.post import (
    CommentCard,
    PostAuthor,
    PostCard,
    PostCreateRequest,
    PostDetailResponse,
    PostListResponse,
)


router = APIRouter(prefix="/api/posts", tags=["posts"])
feed_router = APIRouter(prefix="/api/communities", tags=["posts"])


MAX_CROSS_POSTS = 2  # extras beyond the home community → total ≤3
MAX_FEED_LIMIT = 50
DEFAULT_FEED_LIMIT = 20


def _parse_oid(s: str) -> ObjectId | None:
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None


async def _author_for(user_id: ObjectId) -> PostAuthor:
    user = await find_user_by_id(str(user_id))
    if user is None:
        return PostAuthor(id=str(user_id), display_name="")
    return PostAuthor(id=str(user["_id"]), display_name=user.get("display_name", ""))


async def _hydrate_post_card(
    doc: dict[str, Any],
    author: PostAuthor,
    user_vote: int,
    community_slug_by_id: dict[ObjectId, str],
) -> PostCard:
    home_slug = community_slug_by_id.get(doc["community_id"], "")
    cross_slugs = [
        community_slug_by_id.get(cid, "")
        for cid in doc.get("cross_posted_to") or []
    ]
    cross_slugs = [s for s in cross_slugs if s]
    return PostCard(
        id=str(doc["_id"]),
        community_slug=home_slug,
        cross_posted_to=cross_slugs,
        author=author,
        title=doc["title"],
        body_md=doc.get("body_md", ""),
        attached_launch_id=str(doc["attached_launch_id"]) if doc.get("attached_launch_id") else None,
        vote_score=doc.get("vote_score", 0),
        comment_count=doc.get("comment_count", 0),
        user_vote=user_vote,
        flagged=doc.get("flagged", False),
        created_at=doc["created_at"],
        last_activity_at=doc.get("last_activity_at", doc["created_at"]),
    )


@router.post("", response_model=PostCard, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreateRequest,
    user: dict[str, Any] = Depends(require_role("user")),
) -> PostCard:
    """F-COM-3: create a post + optional cross-post."""
    home = await find_by_slug(payload.community_slug)
    if home is None or not home.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "community_not_found"},
        )

    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "field_required", "field": "title"},
        )

    cross_slugs = list(payload.cross_post_slugs)
    if len(cross_slugs) > MAX_CROSS_POSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "cross_post_invalid", "reason": "too_many"},
        )
    if len(set(cross_slugs)) != len(cross_slugs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "cross_post_invalid", "reason": "duplicates"},
        )
    if payload.community_slug in cross_slugs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "cross_post_invalid", "reason": "home_in_crossposts"},
        )

    cross_ids: list[ObjectId] = []
    for slug in cross_slugs:
        doc = await find_by_slug(slug)
        if doc is None or not doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "cross_post_invalid", "reason": "unknown_slug", "slug": slug},
            )
        cross_ids.append(doc["_id"])

    post_doc = await insert_post(
        community_id=home["_id"],
        cross_posted_to=cross_ids,
        author_user_id=user["_id"],
        title=title,
        body_md=payload.body_md,
    )

    author = PostAuthor(
        id=str(user["_id"]),
        display_name=user.get("display_name", ""),
    )
    community_slug_by_id = {home["_id"]: home["slug"]}
    for cid, cslug in zip(cross_ids, cross_slugs):
        community_slug_by_id[cid] = cslug
    return await _hydrate_post_card(
        post_doc, author, user_vote=0, community_slug_by_id=community_slug_by_id
    )


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> PostDetailResponse:
    """F-COM-4: post detail + inlined flat comments newest-first."""
    oid = _parse_oid(post_id)
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "post_not_found"},
        )
    doc = await find_post_by_id(oid)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "post_not_found"},
        )

    home = await find_community_by_id(doc["community_id"])
    community_slug_by_id: dict[ObjectId, str] = {}
    if home:
        community_slug_by_id[home["_id"]] = home["slug"]
    for cid in doc.get("cross_posted_to") or []:
        cdoc = await find_community_by_id(cid)
        if cdoc:
            community_slug_by_id[cdoc["_id"]] = cdoc["slug"]

    author = await _author_for(doc["author_user_id"])

    # User's vote on this post.
    user_vote_map = await find_user_votes_for_targets(
        user["_id"], "post", [doc["_id"]]
    )
    user_vote = user_vote_map.get(doc["_id"], 0)

    post_card = await _hydrate_post_card(
        doc, author, user_vote=user_vote, community_slug_by_id=community_slug_by_id
    )

    # Comments + per-comment user vote.
    comment_docs = await comments_for_post(doc["_id"])
    comment_ids = [c["_id"] for c in comment_docs]
    comment_vote_map = await find_user_votes_for_targets(
        user["_id"], "comment", comment_ids
    )

    comments: list[CommentCard] = []
    for c in comment_docs:
        c_author = await _author_for(c["author_user_id"])
        comments.append(CommentCard(
            id=str(c["_id"]),
            post_id=str(c["post_id"]),
            author=c_author,
            body_md=c["body_md"],
            vote_score=c.get("vote_score", 0),
            user_vote=comment_vote_map.get(c["_id"], 0),
            flagged=c.get("flagged", False),
            created_at=c["created_at"],
        ))

    return PostDetailResponse(post=post_card, comments=comments)


@feed_router.get("/{slug}/posts", response_model=PostListResponse)
async def community_feed(
    slug: str,
    before: datetime | None = Query(default=None),
    limit: int = Query(default=DEFAULT_FEED_LIMIT, ge=1, le=MAX_FEED_LIMIT),
    user: dict[str, Any] = Depends(current_user),
) -> PostListResponse:
    """F-COM-4: newest-first feed for a community, including posts that
    cross-posted INTO the community."""
    home = await find_by_slug(slug)
    if home is None or not home.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "community_not_found"},
        )

    docs = await feed_for_community(home["_id"], before=before, limit=limit)

    # Build community_slug map for all referenced communities in this page.
    needed_ids: set[ObjectId] = {home["_id"]}
    for d in docs:
        needed_ids.add(d["community_id"])
        for cid in d.get("cross_posted_to") or []:
            needed_ids.add(cid)
    community_slug_by_id: dict[ObjectId, str] = {}
    for cid in needed_ids:
        cdoc = await find_community_by_id(cid)
        if cdoc:
            community_slug_by_id[cdoc["_id"]] = cdoc["slug"]

    # Per-post user votes.
    post_ids = [d["_id"] for d in docs]
    user_vote_map = await find_user_votes_for_targets(
        user["_id"], "post", post_ids
    )

    cards: list[PostCard] = []
    for d in docs:
        author = await _author_for(d["author_user_id"])
        card = await _hydrate_post_card(
            d,
            author,
            user_vote=user_vote_map.get(d["_id"], 0),
            community_slug_by_id=community_slug_by_id,
        )
        cards.append(card)

    next_before = docs[-1]["created_at"] if len(docs) == limit else None
    return PostListResponse(posts=cards, next_before=next_before)
