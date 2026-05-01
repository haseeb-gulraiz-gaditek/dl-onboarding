"""CLI dispatcher for `python -m app.seed <command>`.

Currently supports:
  questions  -- load app/seed/questions.json into the `questions` collection
  catalog    -- load app/seed/catalog.json into the `tools_seed` collection
"""
import sys

from app.seed import catalog as catalog_seed
from app.seed import questions as questions_seed


_COMMANDS = {
    "questions": questions_seed.main,
    "catalog": catalog_seed.main,
}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.seed <command>", file=sys.stderr)
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
