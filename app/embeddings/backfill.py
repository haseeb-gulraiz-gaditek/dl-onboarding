"""Backfill embeddings for approved tools that lack them.

Per spec-delta weaviate-pipeline F-EMB-2 (backfill CLI):
  - Iterates every `tools_seed` row where curation_status="approved"
    and embedding is null.
  - Calls ensure_tool_embedding for each.
  - Prints `embedded: N, skipped: M, failed: K, total: T`.
  - Exits 0 if failed==0, else 1.

Run via:  python -m app.embeddings backfill-tools
"""
import asyncio
import sys

from dotenv import load_dotenv

from app.db.mongo import close_mongo, init_mongo
from app.db.tools_seed import tools_seed_collection
from app.embeddings.lifecycle import ensure_tool_embedding


async def backfill_tools() -> dict[str, int]:
    """Embed every approved tool that lacks an embedding.

    Returns a stats dict with keys: embedded, skipped, failed, total.
      - embedded: tools that gained a fresh embedding this run.
      - skipped: approved tools that already had an embedding.
      - failed: tools where the OpenAI call raised; the row is left
        with embedding=null and the loop continues.
      - total: count of approved tools (regardless of embedding state).
    """
    coll = tools_seed_collection()

    total = await coll.count_documents({"curation_status": "approved"})
    skipped = await coll.count_documents(
        {"curation_status": "approved", "embedding": {"$ne": None}}
    )

    cursor = coll.find({"curation_status": "approved", "embedding": None})
    candidates: list[dict] = await cursor.to_list(length=None)

    embedded = 0
    failed = 0
    for tool in candidates:
        slug = tool["slug"]
        try:
            did_embed = await ensure_tool_embedding(slug)
            if did_embed:
                embedded += 1
        except Exception as exc:
            failed += 1
            print(f"[backfill] failed {slug}: {exc}", file=sys.stderr)

    return {
        "embedded": embedded,
        "skipped": skipped,
        "failed": failed,
        "total": total,
    }


async def _main_async() -> int:
    load_dotenv()
    await init_mongo()
    try:
        result = await backfill_tools()
    finally:
        await close_mongo()
    print(
        f"[backfill] embedded: {result['embedded']}, "
        f"skipped: {result['skipped']}, "
        f"failed: {result['failed']}, "
        f"total: {result['total']}"
    )
    return 0 if result["failed"] == 0 else 1


def main() -> None:
    sys.exit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()
