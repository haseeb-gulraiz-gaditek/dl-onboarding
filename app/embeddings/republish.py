"""Re-publish existing Mongo embeddings to Weaviate.

Useful when:
  - Weaviate was unreachable during the original backfill (publishes
    were silently skipped per F-EMB-2 graceful degradation).
  - The Weaviate cluster was rebuilt and lost its data.
  - publish_tool semantics changed (e.g., upsert fix) and existing
    Mongo embeddings need re-pushing.

The command is purely a Weaviate write: it does NOT call OpenAI, so
it costs nothing and runs in seconds.

Run via:  python -m app.embeddings republish-tools
"""
import asyncio
import sys

from dotenv import load_dotenv

from app.db.mongo import close_mongo, init_mongo
from app.db.tools_seed import tools_seed_collection
from app.embeddings.vector_store import close_weaviate_client, publish_tool


async def republish_tools() -> dict[str, int]:
    """Re-publish all approved tools that have a Mongo embedding to
    Weaviate. Idempotent because publish_tool is an upsert."""
    coll = tools_seed_collection()
    cursor = coll.find(
        {"curation_status": "approved", "embedding": {"$ne": None}}
    )
    candidates = await cursor.to_list(length=None)

    published = 0
    failed = 0
    for tool in candidates:
        try:
            await publish_tool(
                slug=tool["slug"],
                vector=tool["embedding"],
                properties={
                    "slug": tool["slug"],
                    "category": tool.get("category"),
                    "curation_status": tool.get("curation_status", "approved"),
                    "labels": tool.get("labels") or [],
                    # Cycle #15 hybrid-search BM25 surface.
                    "name": tool.get("name") or "",
                    "tagline": tool.get("tagline") or "",
                    "description": tool.get("description") or "",
                },
            )
            published += 1
        except Exception as exc:
            failed += 1
            print(f"[republish] failed {tool['slug']}: {exc}", file=sys.stderr)

    return {"published": published, "failed": failed, "total": len(candidates)}


async def _main_async() -> int:
    load_dotenv("/home/haseeb/dl-onboarding/.env")
    await init_mongo()
    try:
        result = await republish_tools()
    finally:
        await close_weaviate_client()
        await close_mongo()
    print(
        f"[republish] published: {result['published']}, "
        f"failed: {result['failed']}, "
        f"total: {result['total']}"
    )
    return 0 if result["failed"] == 0 else 1


def main() -> None:
    sys.exit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()
