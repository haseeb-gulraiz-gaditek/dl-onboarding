"""Current-user endpoint and role-gated smoke endpoints.

Implements spec-delta auth-role-split F-AUTH-5 and F-AUTH-6.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.middleware import current_user, require_role
from app.models.user import UserPublic, to_public


router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=UserPublic)
async def me(user: dict[str, Any] = Depends(current_user)) -> UserPublic:
    """F-AUTH-5: return the authenticated user."""
    return to_public(user)


@router.get("/user-only", response_model=UserPublic)
async def user_only(
    user: dict[str, Any] = Depends(require_role("user")),
) -> UserPublic:
    """F-AUTH-6: smoke endpoint behind require_role("user").

    Used to verify the role-middleware contract during manual
    testing. May be removed in a later cycle once real role-gated
    endpoints exercise the middleware.
    """
    return to_public(user)


@router.get("/founder-only", response_model=UserPublic)
async def founder_only(
    user: dict[str, Any] = Depends(require_role("founder")),
) -> UserPublic:
    """F-AUTH-6: smoke endpoint behind require_role("founder")."""
    return to_public(user)
