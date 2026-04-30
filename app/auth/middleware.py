"""FastAPI dependencies for authenticated and role-gated endpoints.

Per spec-delta auth-role-split:
  F-AUTH-3: require_role enforces role_type at the request boundary.
  F-AUTH-5: /api/me uses current_user.
"""
from typing import Any, Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import JWTError, decode_jwt
from app.db.users import find_user_by_id
from app.models.user import RoleType


_bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Resolve the authenticated user from the Authorization header.

    Returns the user document. Raises 401 with `auth_required` if the
    header is missing, the token is invalid, the token is expired, or
    the user no longer exists.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "auth_required"},
        )
    try:
        claims = decode_jwt(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "auth_required"},
        )

    user_id = claims.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "auth_required"},
        )

    user = await find_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "auth_required"},
        )
    return user


def require_role(
    role: RoleType,
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Dependency factory that enforces a specific role_type.

    Usage:
        @router.get("/something", dependencies=[Depends(require_role("user"))])

    or to receive the user object:

        async def handler(user = Depends(require_role("user"))):
            ...

    Returns 403 with `role_mismatch` if the caller is authenticated
    but has the wrong role; returns 401 with `auth_required` if the
    caller is not authenticated.
    """

    async def _checker(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        actual = user.get("role_type")
        if actual != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "role_mismatch",
                    "required": role,
                    "actual": actual,
                },
            )
        return user

    return _checker
