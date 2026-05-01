"""CLI dispatcher for `python -m app.embeddings <command>`.

Currently supports:
  init-weaviate    -- create the Weaviate schema (ToolEmbedding,
                      ProfileEmbedding classes). Run once after
                      setting WEAVIATE_URL + WEAVIATE_API_KEY in .env.
  backfill-tools   -- embed every approved tool that lacks an
                      embedding (Mongo) and publish to Weaviate.
  republish-tools  -- push every approved tool's existing Mongo
                      embedding to Weaviate. No OpenAI calls. Use
                      after Weaviate downtime / cluster rebuild.
"""
import asyncio
import sys

from app.embeddings import backfill as backfill_module


def _init_weaviate_main() -> None:
    """Synchronous entry point for `python -m app.embeddings init-weaviate`."""
    from dotenv import load_dotenv

    from app.embeddings.vector_store import (
        close_weaviate_client,
        init_weaviate_schema,
    )

    async def _run() -> int:
        load_dotenv("/home/haseeb/dl-onboarding/.env")
        try:
            return await init_weaviate_schema()
        finally:
            await close_weaviate_client()

    sys.exit(asyncio.run(_run()))


def _republish_tools_main() -> None:
    """Sync entry point for `python -m app.embeddings republish-tools`."""
    from app.embeddings import republish as republish_module

    republish_module.main()


_COMMANDS = {
    "init-weaviate": _init_weaviate_main,
    "backfill-tools": backfill_module.main,
    "republish-tools": _republish_tools_main,
}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.embeddings <command>", file=sys.stderr)
        print(f"Commands: {', '.join(sorted(_COMMANDS))}", file=sys.stderr)
        sys.exit(2)
    cmd = sys.argv[1]
    handler = _COMMANDS.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd!r}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(_COMMANDS))}", file=sys.stderr)
        sys.exit(2)
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    handler()


if __name__ == "__main__":
    main()
