"""Auth router: signup + login.

Implements spec-delta auth-role-split F-AUTH-1 and F-AUTH-2.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.auth.jwt import issue_jwt
from app.auth.passwords import hash_password, verify_password
from app.db.users import find_user_by_email, insert_user, touch_last_active
from app.models.user import (
    AuthResponse,
    UserCreate,
    UserLogin,
    role_type_for_answer,
    to_public,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: UserCreate) -> AuthResponse:
    """F-AUTH-1: create a user with the role_type derived from the
    signup question. Email is normalized to lowercase. Returns the
    JWT and the public user payload.
    """
    email = payload.email.lower()
    role_type = role_type_for_answer(payload.role_question_answer)
    display_name = email.split("@", 1)[0]
    try:
        doc = await insert_user(
            email=email,
            password_hash=hash_password(payload.password),
            role_type=role_type,
            display_name=display_name,
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_already_registered"},
        )
    jwt_token = issue_jwt(str(doc["_id"]), role_type)
    return AuthResponse(jwt=jwt_token, user=to_public(doc))


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin) -> AuthResponse:
    """F-AUTH-2: authenticate by email + password.

    The same generic error message is returned whether the email is
    unknown or the password is wrong, so we don't leak account
    existence (per spec-delta NOTE on F-AUTH-2).
    """
    email = payload.email.lower()
    doc = await find_user_by_email(email)
    if doc is None or not verify_password(payload.password, doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials"},
        )
    await touch_last_active(doc["_id"])
    doc["last_active_at"] = datetime.now(timezone.utc)
    jwt_token = issue_jwt(str(doc["_id"]), doc["role_type"])
    return AuthResponse(jwt=jwt_token, user=to_public(doc))
