"""Embedding lifecycle helpers.

Per spec-delta weaviate-pipeline F-EMB-2, F-EMB-3, F-EMB-6.

  - ensure_tool_embedding(slug)    sync, write-on-first-call,
                                   idempotent. Used by admin
                                   approve and the backfill CLI.
  - clear_tool_embedding(slug)     sync, sets embedding to None.
                                   Used by admin reject.
  - ensure_profile_embedding(user) sync-on-read, regenerates only
                                   if missing or stale. Refuses
                                   founder users (defense in depth).
"""
from datetime import datetime, timezone
from typing import Any

from app.db.answers import answers_collection
from app.db.profiles import find_profile_by_user_id, profiles_collection
from app.db.tools_seed import find_tool_by_slug, tools_seed_collection
from app.embeddings.openai import embed_text


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _tool_embeddable_text(tool: dict[str, Any]) -> str:
    """Combine the fields that capture what a tool *is* into a
    single text the embedding model digests. Including category
    and labels gives the embedding cross-category disambiguation."""
    labels = tool.get("labels") or []
    parts = [
        tool.get("name", ""),
        tool.get("tagline", ""),
        tool.get("description", ""),
        f"category: {tool.get('category', '')}",
        f"labels: {', '.join(labels)}" if labels else "",
    ]
    return "\n".join(p for p in parts if p)


def _profile_embeddable_text(
    profile: dict[str, Any], recent_answers: list[dict[str, Any]]
) -> str:
    """Build the text we embed for a user profile from recent answers
    plus any populated profile fields. The aggregation cycle
    (a future feature) will populate role / current_tools /
    workflows / etc. -- once those land, they amplify the embedding."""
    parts: list[str] = []
    if profile.get("role"):
        parts.append(f"role: {profile['role']}")
    for ans in recent_answers:
        value = ans.get("value")
        if isinstance(value, list):
            parts.append(", ".join(str(v) for v in value))
        elif value:
            parts.append(str(value))
    return "\n".join(p for p in parts if p)


# ---- Tool embeddings ----

async def ensure_tool_embedding(slug: str) -> bool:
    """If the tool exists and has no embedding, generate one and
    write it. Returns True if a new embedding was written, False if
    the tool already had one OR doesn't exist OR has no embeddable
    text."""
    tool = await find_tool_by_slug(slug)
    if tool is None:
        return False
    if tool.get("embedding") is not None:
        return False
    text = _tool_embeddable_text(tool)
    if not text.strip():
        return False
    vector = await embed_text(text)
    await tools_seed_collection().update_one(
        {"slug": slug}, {"$set": {"embedding": vector}}
    )
    return True


async def clear_tool_embedding(slug: str) -> None:
    """Set the tool's embedding to None (called on reject).

    The row stays in the collection (audit trail, future re-approval),
    but it disappears from similarity-search results because Atlas
    Vector Search ignores documents whose vector field is null."""
    await tools_seed_collection().update_one(
        {"slug": slug}, {"$set": {"embedding": None}}
    )


# ---- Profile embeddings ----

async def ensure_profile_embedding(user: dict[str, Any]) -> bool:
    """Lazy profile embedding (F-EMB-3).

    Regenerates only if the profile has no embedding OR
    last_invalidated_at > last_recompute_at. No-op otherwise.

    Refuses founder users -- founders have no profile per F-QB-5
    so this branch is unreachable in production but guarded for
    safety.
    """
    role_type = user.get("role_type")
    if role_type != "user":
        raise ValueError(
            f"ensure_profile_embedding: founders have no profile; "
            f"got role_type={role_type!r}"
        )

    profile = await find_profile_by_user_id(user["_id"])
    if profile is None:
        return False

    has_embedding = profile.get("embedding") is not None
    last_recompute_at = profile.get("last_recompute_at")
    last_invalidated_at = profile.get("last_invalidated_at")

    fresh = (
        has_embedding
        and last_recompute_at is not None
        and last_invalidated_at is not None
        and last_recompute_at >= last_invalidated_at
    )
    if fresh:
        return False

    cursor = answers_collection().find(
        {"user_id": user["_id"]}
    ).sort("captured_at", -1).limit(20)
    recent = await cursor.to_list(length=20)

    text = _profile_embeddable_text(profile, recent)
    if not text.strip():
        # Brand-new user with no answers yet; nothing to embed.
        return False

    vector = await embed_text(text)
    await profiles_collection().update_one(
        {"user_id": user["_id"]},
        {"$set": {"embedding": vector, "last_recompute_at": _now()}},
    )
    return True
