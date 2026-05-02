"""Synchronous publish orchestrator for approved launches.

Per spec-delta launch-publish-and-concierge-nudge F-PUB-2.

Triggered from POST /admin/launches/{id}/approve AFTER the existing
tools_founder_launched insert. Five steps:
  1. Embed the ICP description.
  2. Embed and publish the just-inserted founder-launched tool so it's
     queryable for the recommendation fan-in (F-PUB-6).
  3. Fan-out community posts: one posts row per target_community_slug.
  4. Concierge scan: top-5 profiles by similarity to the ICP vector.
     Per matched user: notification + engagement + bump rec cache
     expiry to now() so the next call regenerates with the launch.
  5. Return {community_posts_count, nudge_count}.

Per-step exceptions are logged and swallowed; the launch is approved
even on partial fan-out failure (rollback would be more dangerous).
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.db.communities import find_by_slug as find_community_by_slug
from app.db.engagements import insert as insert_engagement
from app.db.notifications import insert as insert_notification
from app.db.posts import insert as insert_post
from app.db.recommendations import recommendations_collection
from app.embeddings.lifecycle import ensure_tool_embedding
from app.embeddings.openai import embed_text
from app.embeddings.vector_store import PROFILE_CLASS, similarity_search


CONCIERGE_TOP_K = 5
TITLE_MAX_LEN = 80


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _fanout_community_posts(
    *,
    launch_doc: dict[str, Any],
) -> int:
    """Step 3: insert one posts row per active target community slug.
    Returns the count of successful posts."""
    target_slugs = launch_doc.get("target_community_slugs") or []
    if not target_slugs:
        return 0

    title = launch_doc["problem_statement"][:TITLE_MAX_LEN]
    body = (
        f"{launch_doc['problem_statement']}\n\n"
        f"Ideal customer: {launch_doc['icp_description']}"
    )

    posted = 0
    for slug in target_slugs:
        try:
            community = await find_community_by_slug(slug)
            if community is None or not community.get("is_active", True):
                continue
            post_doc = await insert_post(
                community_id=community["_id"],
                cross_posted_to=[],
                author_user_id=launch_doc["founder_user_id"],
                title=title,
                body_md=body,
                attached_launch_id=launch_doc["_id"],
            )
            await insert_engagement(
                launch_id=launch_doc["_id"],
                surface="community_post",
                action="view",
                metadata={
                    "community_slug": slug,
                    "post_id": str(post_doc["_id"]),
                },
            )
            posted += 1
        except Exception as exc:
            print(
                f"[publish] community fan-out failed for slug={slug}: {exc}"
            )
    return posted


async def _concierge_scan(
    *,
    launch_doc: dict[str, Any],
    icp_vector: list[float],
) -> int:
    """Step 4: similarity_search profiles vs the ICP vector. Top-5
    matches get notification + engagement + rec cache expiry bump."""
    try:
        matches = await similarity_search(
            collection_name="profiles",
            weaviate_class=PROFILE_CLASS,
            query_vector=icp_vector,
            top_k=CONCIERGE_TOP_K,
        )
    except Exception as exc:
        print(f"[publish] concierge similarity_search failed: {exc}")
        return 0

    nudged = 0
    now = _now()
    founder_user_id = launch_doc["founder_user_id"]

    for profile in matches:
        try:
            user_id = profile.get("user_id")
            if user_id is None:
                continue
            # Defensive: founders shouldn't have profiles.
            if user_id == founder_user_id:
                continue
            await insert_notification(
                user_id=user_id,
                kind="concierge_nudge",
                payload={
                    "launch_id": str(launch_doc["_id"]),
                    "tool_slug": launch_doc.get("approved_tool_slug"),
                },
            )
            await insert_engagement(
                launch_id=launch_doc["_id"],
                surface="concierge_nudge",
                action="view",
                user_id=user_id,
            )
            await recommendations_collection().update_one(
                {"user_id": user_id},
                {"$set": {"cache_expires_at": now}},
            )
            nudged += 1
        except Exception as exc:
            print(f"[publish] concierge nudge failed for user={user_id}: {exc}")
    return nudged


async def publish_launch(
    *,
    launch_doc: dict[str, Any],
    tool_slug: str,
) -> dict[str, int]:
    """Orchestrator. Returns {community_posts_count, nudge_count}."""
    summary = {"community_posts_count": 0, "nudge_count": 0}

    # Step 1: embed ICP.
    icp_vector: list[float] = []
    try:
        icp_vector = await embed_text(launch_doc["icp_description"])
    except Exception as exc:
        print(f"[publish] ICP embedding failed: {exc}")

    # Step 2: ensure the tool's embedding so the recommendation fan-in
    # (F-PUB-6) has something to query immediately.
    try:
        await ensure_tool_embedding(tool_slug)
    except Exception as exc:
        print(f"[publish] ensure_tool_embedding failed for {tool_slug}: {exc}")

    # Step 3: community fan-out.
    summary["community_posts_count"] = await _fanout_community_posts(
        launch_doc=launch_doc,
    )

    # Step 4: concierge scan (only if ICP embedding succeeded).
    if icp_vector:
        summary["nudge_count"] = await _concierge_scan(
            launch_doc=launch_doc, icp_vector=icp_vector,
        )

    return summary
