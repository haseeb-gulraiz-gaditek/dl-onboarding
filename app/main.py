"""Mesh FastAPI application entrypoint.

Wires the Mongo lifecycle into FastAPI lifespan, mounts routers,
and translates Pydantic validation errors into the error-code
shapes mandated by the spec-deltas.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import admin_catalog as admin_catalog_router
from app.api import admin_launches as admin_launches_router
from app.api import answers as answers_router
from app.api import auth as auth_router
from app.api import comments as comments_router
from app.api import communities as communities_router
from app.api import founders as founders_router
from app.api import me as me_router
from app.api import onboarding as onboarding_router
from app.api import posts as posts_router
from app.api import questions as questions_router
from app.api import recommendations as recommendations_router
from app.api import votes as votes_router
from app.db.answers import ensure_indexes as ensure_answer_indexes
from app.db.comments import ensure_indexes as ensure_comment_indexes
from app.db.communities import ensure_indexes as ensure_community_indexes
from app.db.community_memberships import (
    ensure_indexes as ensure_membership_indexes,
)
from app.db.launches import ensure_indexes as ensure_launch_indexes
from app.db.mongo import close_mongo, init_mongo
from app.db.notifications import (
    ensure_indexes as ensure_notification_indexes,
)
from app.db.posts import ensure_indexes as ensure_post_indexes
from app.db.profiles import ensure_indexes as ensure_profile_indexes
from app.db.questions import ensure_indexes as ensure_question_indexes
from app.db.recommendations import ensure_indexes as ensure_rec_indexes
from app.db.tools_founder_launched import (
    ensure_indexes as ensure_tools_fl_indexes,
)
from app.db.tools_seed import ensure_indexes as ensure_tools_seed_indexes
from app.db.users import ensure_indexes as ensure_user_indexes
from app.db.votes import ensure_indexes as ensure_vote_indexes
from app.embeddings.vector_store import close_weaviate_client


load_dotenv()


_REQUIRED_ENV = (
    "MONGODB_URI",
    "JWT_SECRET",
    "ADMIN_EMAILS",
    "OPENAI_API_KEY",
    "WEAVIATE_URL",
    "WEAVIATE_API_KEY",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast at boot rather than on the first request that needs
    # the variable. Each line of .env that's blank or missing surfaces
    # here with a clear message.
    missing = [var for var in _REQUIRED_ENV if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill them in. "
            "Generate JWT_SECRET with: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    await init_mongo()
    await ensure_user_indexes()
    await ensure_question_indexes()
    await ensure_answer_indexes()
    await ensure_profile_indexes()
    await ensure_tools_seed_indexes()
    await ensure_rec_indexes()
    await ensure_community_indexes()
    await ensure_membership_indexes()
    await ensure_post_indexes()
    await ensure_comment_indexes()
    await ensure_vote_indexes()
    await ensure_launch_indexes()
    await ensure_tools_fl_indexes()
    await ensure_notification_indexes()
    try:
        yield
    finally:
        await close_weaviate_client()
        await close_mongo()


app = FastAPI(
    title="Mesh",
    description="Context-graph launch platform for AI tools.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Translate Pydantic validation errors into spec-delta error codes.

    The spec-deltas (F-AUTH-1 etc.) prescribe specific error codes
    like `email_invalid`, `password_too_short`, `role_question_required`
    rather than FastAPI's default 422 + structured error body. This
    handler picks the first reportable error and maps it.
    """
    for err in exc.errors():
        loc = err.get("loc", ())
        err_type = err.get("type", "")
        if "email" in loc and ("value_error" in err_type or "email" in err_type):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "email_invalid"},
            )
        if "password" in loc and "string_too_short" in err_type:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "password_too_short"},
            )
        if "role_question_answer" in loc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "role_question_required"},
            )
        # F-QB-3 missing-field cases (POST /api/answers).
        if loc and loc[-1] in ("question_id", "value"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "field_required", "field": loc[-1]},
            )
        # F-CAT-5 missing-comment on POST /admin/catalog/{slug}/reject.
        if loc and loc[-1] == "comment":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "field_required", "field": "comment"},
            )
        # F-COM-3 / F-COM-5 field-required cases.
        if loc and loc[-1] in ("title", "body_md", "post_id"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "field_required", "field": loc[-1]},
            )
        # F-LAUNCH-1 field-required cases.
        if loc and loc[-1] in (
            "product_url", "problem_statement", "icp_description"
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "field_required", "field": loc[-1]},
            )
        # F-LAUNCH-1 length cap on existing_presence_links.
        if loc and loc[-1] == "existing_presence_links":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "field_invalid", "field": "existing_presence_links"},
            )
        # F-COM-6: target_type / direction enum failures.
        if loc and loc[-1] in ("target_type", "direction", "target_id"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "target_invalid"},
            )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "invalid_request"},
    )


app.include_router(auth_router.router)
app.include_router(me_router.router)
app.include_router(questions_router.router)
app.include_router(answers_router.router)
app.include_router(admin_catalog_router.router)
app.include_router(onboarding_router.router)
app.include_router(recommendations_router.router)
app.include_router(communities_router.router)
app.include_router(posts_router.router)
app.include_router(posts_router.feed_router)
app.include_router(comments_router.router)
app.include_router(votes_router.router)
app.include_router(founders_router.router)
app.include_router(admin_launches_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
