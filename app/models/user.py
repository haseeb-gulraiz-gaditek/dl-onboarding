"""Pydantic schemas for the `users` collection.

Per spec-delta auth-role-split F-AUTH-1..F-AUTH-5.

Constitutional invariant (F-AUTH-4): role_type is set at insert and
is NEVER mutable. The Pydantic update model intentionally excludes
role_type, and there is no API path that accepts a role_type write.
Code review treats any introduction of such a path as a regression
against the principle "Never let founder accounts post in user
communities" (specs/constitution/principles.md).
"""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field


RoleType = Literal["user", "founder"]
"""The two non-transferable account roles. See specs/constitution/principles.md."""


RoleQuestionAnswer = Literal["finding_tools", "launching_product"]
"""User-facing signup-question answers; mapped to RoleType at signup."""


def role_type_for_answer(answer: RoleQuestionAnswer) -> RoleType:
    """Map a signup question answer to the internal role_type."""
    return "user" if answer == "finding_tools" else "founder"


class UserCreate(BaseModel):
    """Payload for POST /api/auth/signup."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    role_question_answer: RoleQuestionAnswer


class UserLogin(BaseModel):
    """Payload for POST /api/auth/login."""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Shape returned to clients (no password_hash, no internal fields)."""

    id: str
    email: EmailStr
    role_type: RoleType
    display_name: str
    created_at: datetime
    last_active_at: datetime
    onboarding_variant: str = "classic"   # F-LIVE-9


class AuthResponse(BaseModel):
    """Shape returned by signup and login."""

    jwt: str
    user: UserPublic


def to_public(doc: dict) -> UserPublic:
    """Project a stored user document into the client-safe shape."""
    import os
    variant = os.environ.get("MESH_ONBOARDING_VARIANT", "classic").strip().lower()
    if variant not in ("classic", "live"):
        variant = "classic"
    return UserPublic(
        id=str(doc["_id"]),
        email=doc["email"],
        role_type=doc["role_type"],
        display_name=doc["display_name"],
        created_at=doc["created_at"],
        last_active_at=doc["last_active_at"],
        onboarding_variant=variant,
    )
