"""Test fixtures for the Mesh test suite.

Strategy:
  - Set required env vars BEFORE importing app modules (JWT_SECRET,
    MONGODB_URI, MONGODB_DB, JWT_EXPIRY_DAYS).
  - Pre-inject an `AsyncMongoMockClient` into `app.db.mongo` before
    each test so the FastAPI lifespan's `init_mongo()` is a no-op
    (it bails early when `_client` is already set).
  - Provide an httpx `AsyncClient` against the live FastAPI app.
"""
import os

os.environ.setdefault("JWT_SECRET", "test-secret-mesh-suite-not-for-prod-use")
os.environ.setdefault("MONGODB_URI", "mongodb://test")
os.environ.setdefault("MONGODB_DB", "mesh_test")
os.environ.setdefault("JWT_EXPIRY_DAYS", "7")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.db import mongo as mongo_module
from app.db import users as users_module


@pytest_asyncio.fixture
async def app_client() -> AsyncClient:
    """A fresh httpx AsyncClient with an isolated mongomock DB."""
    test_client = AsyncMongoMockClient()
    test_db = test_client["mesh_test"]

    # Inject into the module BEFORE the FastAPI lifespan runs so
    # init_mongo() short-circuits and doesn't try to connect to a
    # real Motor URI.
    mongo_module._client = test_client
    mongo_module._db = test_db
    await users_module.ensure_indexes()

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # AsyncClient exit triggered lifespan shutdown which called
    # close_mongo() and nulled the globals -- nothing more to do
    # for cleanup. The mongomock client is per-test so isolation
    # is automatic.


# ---- Convenience helpers used by multiple test modules ----

async def signup_user(client: AsyncClient, email: str, password: str = "password123") -> dict:
    r = await client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "role_question_answer": "finding_tools",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


async def signup_founder(client: AsyncClient, email: str, password: str = "password123") -> dict:
    r = await client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "role_question_answer": "launching_product",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def auth_header(jwt_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt_token}"}


# ---- Question-bank fixtures (cycle: question-bank-and-answer-capture) ----

import pytest_asyncio  # noqa: E402  -- already imported above; safe re-import


_TEST_QUESTIONS: list[dict] = [
    {
        "key": "test.role_q",
        "text": "What's your role?",
        "kind": "single_select",
        "category": "role",
        "order": 1,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "designer", "label": "Designer"},
            {"value": "engineer", "label": "Engineer"},
        ],
    },
    {
        "key": "test.stack_q",
        "text": "Which tools do you use?",
        "kind": "multi_select",
        "category": "stack",
        "order": 2,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "notion", "label": "Notion"},
            {"value": "linear", "label": "Linear"},
        ],
    },
    {
        "key": "test.workflow_q",
        "text": "Describe a recurring task.",
        "kind": "free_text",
        "category": "workflow",
        "order": 3,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [],
    },
]


@pytest_asyncio.fixture
async def seed_test_questions(app_client):
    """Seed a small fixed set of 3 questions across 3 kinds and 3
    categories. Depends on app_client so the mongomock DB is already
    initialized."""
    from app.db.questions import questions_collection

    await questions_collection().insert_many([dict(q) for q in _TEST_QUESTIONS])
    yield _TEST_QUESTIONS


async def signed_up_user_with_profile(client, email: str = "maya@example.com") -> dict:
    """Sign up a user, hit GET /api/questions/next once to create the
    profile, return {token, user, first_question_payload}."""
    body = await signup_user(client, email)
    r = await client.get(
        "/api/questions/next", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    return {
        "token": body["jwt"],
        "user": body["user"],
        "first": r.json(),
    }
