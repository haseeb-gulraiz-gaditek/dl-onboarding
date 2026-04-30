"""JWT issue + decode helpers.

# Transport decision (locked V1)
#
# Mesh V1 carries the JWT in the `Authorization: Bearer <token>` header.
# Rationale:
#   - Simplest for a SPA frontend that talks to FastAPI cross-origin.
#   - Avoids cookie / CORS / CSRF interplay during V1 development.
#   - Matches the FastAPI/OAuth2 convention; HTTP clients understand it.
# Future: if XSS-resistance becomes a priority, a separate cycle can
# move to httpOnly + SameSite cookies behind a same-origin proxy.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt as pyjwt


_ALGORITHM = "HS256"


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET is not set. Generate one with "
            'python -c "import secrets; print(secrets.token_urlsafe(48))" '
            "and add it to your .env file."
        )
    return secret


def _expiry_days() -> int:
    raw = os.environ.get("JWT_EXPIRY_DAYS", "7")
    try:
        return int(raw)
    except ValueError:
        return 7


def issue_jwt(user_id: str, role_type: str) -> str:
    """Produce a signed JWT for the given user.

    Claims:
      sub: user_id (string ObjectId)
      role: role_type ("user" | "founder")
      iat: issued-at (UTC)
      exp: expiry (UTC, JWT_EXPIRY_DAYS in the future)
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role_type,
        "iat": now,
        "exp": now + timedelta(days=_expiry_days()),
    }
    return pyjwt.encode(payload, _secret(), algorithm=_ALGORITHM)


class JWTError(Exception):
    """Raised when a token cannot be decoded or has expired."""


def decode_jwt(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises JWTError on failure.

    Returned dict has keys: sub, role, iat, exp.
    """
    try:
        return pyjwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except pyjwt.ExpiredSignatureError as exc:
        raise JWTError("token_expired") from exc
    except pyjwt.InvalidTokenError as exc:
        raise JWTError("token_invalid") from exc
