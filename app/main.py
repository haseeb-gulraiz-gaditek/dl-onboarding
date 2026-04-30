"""Mesh FastAPI application entrypoint.

Wires the Mongo lifecycle into FastAPI lifespan, mounts routers,
and translates Pydantic validation errors into the error-code
shapes mandated by the spec-deltas.
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import auth as auth_router
from app.api import me as me_router
from app.db.mongo import close_mongo, init_mongo
from app.db.users import ensure_indexes as ensure_user_indexes


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongo()
    await ensure_user_indexes()
    try:
        yield
    finally:
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
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "invalid_request"},
    )


app.include_router(auth_router.router)
app.include_router(me_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
