"""bcrypt password hashing helpers.

Cost factor 12 is the 2026 default; raise it if benchmarks show
signup/login latency is dominated by hashing rather than DB I/O.
"""
import bcrypt


_BCRYPT_ROUNDS = 12


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for the plaintext password."""
    salted = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salted).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored hash, else False.

    Returns False on any verification error (malformed hash, type
    issue) rather than raising — so callers can treat verification
    as a single boolean check.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
