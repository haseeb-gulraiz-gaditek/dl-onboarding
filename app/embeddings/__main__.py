"""CLI dispatcher for `python -m app.embeddings <command>`.

Currently supports:
  backfill-tools  -- embed every approved tool that lacks an embedding
"""
import sys

from app.embeddings import backfill as backfill_module


_COMMANDS = {
    "backfill-tools": backfill_module.main,
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
