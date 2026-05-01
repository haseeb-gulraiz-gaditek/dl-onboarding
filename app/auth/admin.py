"""Admin gate (`require_admin`).

Per spec-delta catalog-seed-and-curation F-CAT-4.

Reads `ADMIN_EMAILS` (comma-separated, case-insensitive) at request
time and rejects authenticated callers whose email isn't in the
allowlist with 403 admin_only. Unauthenticated callers receive 401
auth_required (inherited from `current_user`).

`ADMIN_EMAILS` is required at boot (lifespan startup check in
app/main.py); the list is parsed lazily here so changes to the env
var on a reload take effect without a restart of this dependency.

This is V1's pragmatic admin auth -- no `role_type` amendment, no
RBAC. V1.5+ will replace this with real role-based access.
"""
import os
from typing import Any, Awaitable, Callable

from fastapi import Depends, HTTPException, status

from app.auth.middleware import current_user


def _admin_email_set() -> set[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def require_admin() -> Callable[..., Awaitable[dict[str, Any]]]:
    """Dependency factory that gates admin-only endpoints."""

    async def _checker(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        email = (user.get("email") or "").lower()
        if email not in _admin_email_set():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "admin_only"},
            )
        return user

    return _checker
