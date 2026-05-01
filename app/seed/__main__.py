"""CLI dispatcher for `python -m app.seed <command>`.

Currently supports:
  questions   -- load app/seed/questions.json into the `questions` collection
"""
import sys

from app.seed import questions as questions_seed


_COMMANDS = {
    "questions": questions_seed.main,
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
    # Drop the command from argv so the handler sees its own args.
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    handler()


if __name__ == "__main__":
    main()
