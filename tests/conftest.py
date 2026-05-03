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
# Two test admins. Tests that need a non-admin signed-up user simply
# pick any other email.
os.environ.setdefault("ADMIN_EMAILS", "admin@example.com,manager@example.com")
# Cycle #4 (weaviate-pipeline): OpenAI key required at boot.
# Tests never call the real API -- the mock_openai_embed autouse
# fixture below monkey-patches embed_text to a deterministic stub.
os.environ.setdefault("OPENAI_API_KEY", "test-fake-key-not-real")
# Cycle #4 (weaviate-pipeline): vector store env vars. The fake URL
# guarantees Weaviate connect attempts fail in tests, so the
# vector_store layer caches None and falls back to Mongo cosine.
os.environ.setdefault("WEAVIATE_URL", "https://test-fake.weaviate.cloud")
os.environ.setdefault("WEAVIATE_API_KEY", "test-fake-weaviate-key")

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


# ---- Catalog fixtures (cycle: catalog-seed-and-curation) ----

from datetime import datetime, timezone  # noqa: E402


_TEST_TOOLS: list[dict] = [
    {
        "slug": "test-tool-pending",
        "name": "Test Tool Pending",
        "tagline": "A pending test tool.",
        "description": "Used to verify pending-state filtering and approve flows.",
        "url": "https://example.com/pending",
        "pricing_summary": "Free",
        "category": "productivity",
        "labels": ["all_time_best"],
        "curation_status": "pending",
        "rejection_comment": None,
        "source": "manual",
        "embedding": None,
        "last_reviewed_at": None,
        "reviewed_by": None,
    },
    {
        "slug": "test-tool-approved",
        "name": "Test Tool Approved",
        "tagline": "An already-approved test tool.",
        "description": "Used to verify approved-state filtering.",
        "url": "https://example.com/approved",
        "pricing_summary": "$10/mo",
        "category": "writing",
        "labels": ["gaining_traction"],
        "curation_status": "approved",
        "rejection_comment": None,
        "source": "manual",
        "embedding": None,
        "last_reviewed_at": None,
        "reviewed_by": None,
    },
    {
        "slug": "test-tool-rejected",
        "name": "Test Tool Rejected",
        "tagline": "An already-rejected test tool.",
        "description": "Used to verify rejected-state filtering and re-approve flows.",
        "url": "https://example.com/rejected",
        "pricing_summary": "Free",
        "category": "engineering",
        "labels": ["new"],
        "curation_status": "rejected",
        "rejection_comment": "Stale URL.",
        "source": "manual",
        "embedding": None,
        "last_reviewed_at": None,
        "reviewed_by": "admin@example.com",
    },
]


@pytest_asyncio.fixture
async def seed_test_catalog(app_client):
    """Seed three fixed tool entries spanning all three curation states."""
    from app.db.tools_seed import tools_seed_collection

    now = datetime.now(timezone.utc)
    docs = []
    for t in _TEST_TOOLS:
        d = dict(t)
        d["created_at"] = now
        docs.append(d)
    await tools_seed_collection().insert_many(docs)
    yield _TEST_TOOLS


@pytest_asyncio.fixture
async def admin_token(app_client):
    """Sign up admin@example.com (in ADMIN_EMAILS allowlist) and return
    {token, email}."""
    body = await signup_user(app_client, "admin@example.com")
    return {"token": body["jwt"], "email": body["user"]["email"]}


@pytest_asyncio.fixture
async def non_admin_token(app_client):
    """Sign up a user whose email is NOT in ADMIN_EMAILS."""
    body = await signup_user(app_client, "maya@example.com")
    return {"token": body["jwt"], "email": body["user"]["email"]}


# ---- Onboarding-match fixtures (cycle: fast-onboarding-match-and-graph) ----


_MINIMAL_TOOLS: list[dict] = [
    # 5 marketing tools so role=marketing_ops bucket has >= TOP_K (no fallback).
    {"slug": "convertkit", "name": "ConvertKit", "category": "marketing", "labels": ["all_time_best"]},
    {"slug": "hubspot", "name": "HubSpot", "category": "marketing", "labels": ["all_time_best"]},
    {"slug": "klaviyo", "name": "Klaviyo", "category": "marketing", "labels": ["all_time_best"]},
    {"slug": "mailchimp", "name": "Mailchimp", "category": "marketing", "labels": ["all_time_best"]},
    {"slug": "marketo", "name": "Marketo", "category": "marketing", "labels": ["all_time_best"]},
    # 2 design tools so role=design bucket forces fallback to catalog-wide.
    {"slug": "figma", "name": "Figma", "category": "design", "labels": ["all_time_best"]},
    {"slug": "sketch", "name": "Sketch", "category": "design", "labels": ["all_time_best"]},
    # 1 productivity tool to enrich the catalog-wide pool.
    {"slug": "notion", "name": "Notion", "category": "productivity", "labels": ["all_time_best"]},
]


@pytest_asyncio.fixture
async def seed_minimal_catalog(app_client):
    """Seed 8 approved all_time_best tools across 3 categories.

    Designed for F-MATCH-3 testing:
      - role=marketing_ops: bucket has 5 (no fallback)
      - role=design: bucket has 2 (forces fallback to catalog-wide)
      - no role: catalog-wide alphabetical top-5
    """
    from app.db.tools_seed import tools_seed_collection

    now = datetime.now(timezone.utc)
    docs = []
    for entry in _MINIMAL_TOOLS:
        docs.append({
            **entry,
            "tagline": f"{entry['name']} tagline",
            "description": f"{entry['name']} description",
            "url": f"https://example.com/{entry['slug']}",
            "pricing_summary": "Free",
            "curation_status": "approved",
            "rejection_comment": None,
            "source": "manual",
            "embedding": None,
            "created_at": now,
            "last_reviewed_at": None,
            "reviewed_by": None,
        })
    await tools_seed_collection().insert_many(docs)
    yield _MINIMAL_TOOLS


@pytest_asyncio.fixture
async def seed_role_question(app_client):
    """Seed the production-named `role.primary_function` question with
    production-named option values so cycle #5 tests can use real
    role enum strings."""
    from app.db.questions import questions_collection

    await questions_collection().insert_one({
        "key": "role.primary_function",
        "text": "What's your primary job function?",
        "kind": "single_select",
        "category": "role",
        "order": 1,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "marketing_ops", "label": "Marketing ops"},
            {"value": "design", "label": "Design"},
            {"value": "engineering", "label": "Engineering"},
            {"value": "other", "label": "Other"},
        ],
    })


async def insert_role_answer(user_id, role_value: str) -> None:
    """Insert a role.primary_function answer for the user. Caller must
    ensure the role question already exists (use seed_role_question)."""
    from bson import ObjectId
    from app.db.answers import answers_collection
    from app.db.questions import questions_collection

    role_q = await questions_collection().find_one({"key": "role.primary_function"})
    assert role_q is not None, (
        "insert_role_answer requires seed_role_question fixture"
    )
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    await answers_collection().insert_one({
        "user_id": user_id,
        "question_id": role_q["_id"],
        "value": role_value,
        "is_typed_other": False,
        "captured_at": datetime.now(timezone.utc),
    })


async def insert_dummy_answers(user_id, count: int) -> None:
    """Insert `count` answers for the user with arbitrary fresh
    question_ids (each row counts as a distinct answered question).
    Used for mode-dispatch tests that don't care about answer content."""
    from bson import ObjectId
    from app.db.answers import answers_collection

    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    if count <= 0:
        return
    docs = [
        {
            "user_id": user_id,
            "question_id": ObjectId(),
            "value": f"answer-{i}",
            "is_typed_other": False,
            "captured_at": datetime.now(timezone.utc),
        }
        for i in range(count)
    ]
    await answers_collection().insert_many(docs)


# ---- Embeddings fixtures (cycle: weaviate-pipeline) ----

import hashlib  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_weaviate_client():
    """Each test gets a fresh "no Weaviate" cached state. The first
    publish/search call probes WEAVIATE_URL (fake), fails, caches None.
    Subsequent calls in the same test are silent no-ops."""
    from app.embeddings.vector_store import reset_weaviate_client_for_tests

    reset_weaviate_client_for_tests()
    yield
    reset_weaviate_client_for_tests()


@pytest.fixture(autouse=True)
def mock_openai_embed(monkeypatch):
    """Replace `embed_text` everywhere it's imported with a
    deterministic 1536-dim vector based on the input text's MD5.

    Autouse so every test gets it for free; tests that need to
    simulate an OpenAI failure can override with their own
    monkeypatch.setattr.
    """

    async def _fake_embed(text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("embed_text: empty text")
        digest = hashlib.md5(text.encode("utf-8")).digest()  # 16 bytes
        # Spread 16 bytes across 1536 dims in [-1.0, 1.0].
        return [((digest[i % 16] - 128) / 128.0) for i in range(1536)]

    monkeypatch.setattr("app.embeddings.openai.embed_text", _fake_embed)
    monkeypatch.setattr("app.embeddings.lifecycle.embed_text", _fake_embed)
    # Cycle #9: publish orchestrator imports embed_text directly.
    monkeypatch.setattr("app.launches.publish.embed_text", _fake_embed)


# ---- Recommendations fixtures (cycle: recommendation-engine) ----


@pytest.fixture(autouse=True)
def mock_openai_chat(monkeypatch):
    """Replace `rank_with_llm` with a deterministic stub.

    Patches BOTH the ranker module and the engine module (engine.py
    does `from app.recommendations.ranker import rank_with_llm`, so
    the imported reference also needs replacing).

    Default behavior: returns up to `count` picks from the candidates,
    all `verdict="try"` with reasoning that references the slug.
    Tests that need a failing ranker, hallucinated slug, or "skip"
    verdict override locally with `monkeypatch.setattr`.
    """

    async def _fake_rank(profile, recent_answers, candidates, count):
        from app.models.recommendation import RankerPick

        picks: list[RankerPick] = []
        for c in candidates[:count]:
            picks.append(
                RankerPick(
                    slug=c["slug"],
                    verdict="try",
                    reasoning=f"Mock reasoning for {c['slug']}.",
                )
            )
        return picks

    monkeypatch.setattr(
        "app.recommendations.ranker.rank_with_llm", _fake_rank
    )
    monkeypatch.setattr(
        "app.recommendations.engine.rank_with_llm", _fake_rank
    )


_RECS_TOOLS: list[dict] = [
    # 6 approved tools across categories so similarity_search has
    # enough candidates to exercise truncation/clamping.
    {"slug": "cursor", "name": "Cursor", "category": "engineering", "labels": ["all_time_best"]},
    {"slug": "linear", "name": "Linear", "category": "productivity", "labels": ["all_time_best"]},
    {"slug": "notion", "name": "Notion", "category": "productivity", "labels": ["all_time_best"]},
    {"slug": "figma", "name": "Figma", "category": "design", "labels": ["all_time_best"]},
    {"slug": "vercel", "name": "Vercel", "category": "engineering", "labels": ["new"]},
    {"slug": "raycast", "name": "Raycast", "category": "productivity", "labels": ["gaining_traction"]},
]


@pytest_asyncio.fixture
async def seed_recs_catalog(app_client):
    """Seed 6 approved tools, each with a deterministic 1536-dim
    embedding so similarity_search returns them as candidates."""
    from app.db.tools_seed import tools_seed_collection

    now = datetime.now(timezone.utc)
    docs = []
    for entry in _RECS_TOOLS:
        digest = hashlib.md5(entry["slug"].encode("utf-8")).digest()
        embedding = [((digest[i % 16] - 128) / 128.0) for i in range(1536)]
        docs.append({
            **entry,
            "tagline": f"{entry['name']} tagline",
            "description": f"{entry['name']} description for ranker prompt.",
            "url": f"https://example.com/{entry['slug']}",
            "pricing_summary": "Free",
            "curation_status": "approved",
            "rejection_comment": None,
            "source": "manual",
            "embedding": embedding,
            "created_at": now,
            "last_reviewed_at": None,
            "reviewed_by": None,
        })
    await tools_seed_collection().insert_many(docs)
    yield _RECS_TOOLS


async def prepare_user_for_recs(client, email: str = "maya@example.com", n_answers: int = 3) -> dict:
    """Sign up a user, insert N dummy answers, force a profile with a
    fresh embedding so similarity_search has a query vector.

    Returns {token, user_id (ObjectId), email}.
    """
    from bson import ObjectId
    from app.db.profiles import profiles_collection

    body = await signup_user(client, email)
    token = body["jwt"]
    user_id = ObjectId(body["user"]["id"])

    await insert_dummy_answers(user_id, n_answers)

    digest = hashlib.md5(email.encode("utf-8")).digest()
    embedding = [((digest[i % 16] - 128) / 128.0) for i in range(1536)]
    now = datetime.now(timezone.utc)
    await profiles_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "embedding": embedding,
                "last_recompute_at": now,
                "last_invalidated_at": now,
            },
            "$setOnInsert": {
                "user_id": user_id,
                "role": None,
                "current_tools": [],
                "workflows": [],
                "tools_tried_bounced": [],
                "counterfactual_wishes": [],
                "budget_tier": None,
                "exportable": True,
                "created_at": now,
            },
        },
        upsert=True,
    )
    return {"token": token, "user_id": user_id, "email": email}


# ---- Tool-stack question fixture (cycle: my-tools-explore-new-tabs) ----


@pytest_asyncio.fixture
async def seed_tool_stack_question(app_client, seed_test_catalog):
    """A multi_select question whose option values are slugs in the
    seed test catalog. Used by F-TOOL-7 auto-populate tests."""
    from app.db.questions import questions_collection

    doc = {
        "key": "stack.current_tools",
        "text": "Which of these tools do you currently use?",
        "kind": "multi_select",
        "category": "stack",
        "order": 5,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "test-tool-approved", "label": "Test Tool Approved"},
            {"value": "test-tool-pending", "label": "Test Tool Pending"},
            {"value": "not-in-catalog", "label": "Not in Catalog"},
        ],
    }
    await questions_collection().insert_one(doc)
    yield doc


# ---- Communities fixtures (cycle: communities-and-flat-comments) ----


_TEST_COMMUNITIES: list[dict] = [
    {
        "slug": "marketing-ops",
        "name": "Marketing Ops",
        "description": "Marketers running attribution and reporting.",
        "category": "role",
    },
    {
        "slug": "engineering-bench",
        "name": "Engineering Bench",
        "description": "Builders comparing AI dev tools.",
        "category": "role",
    },
    {
        "slug": "weekly-launches",
        "name": "Weekly Launches",
        "description": "What new AI tool actually solved a problem this week.",
        "category": "outcome",
    },
]


@pytest_asyncio.fixture
async def seed_test_communities(app_client):
    """Seed 3 active communities for endpoint tests."""
    from app.db.communities import communities_collection

    now = datetime.now(timezone.utc)
    docs = [
        {
            **c,
            "is_active": True,
            "mod_user_ids": [],
            "member_count": 0,
            "created_at": now,
        }
        for c in _TEST_COMMUNITIES
    ]
    await communities_collection().insert_many(docs)
    yield _TEST_COMMUNITIES


# ---- Founder-launch helpers (cycle: founder-launch-submission-and-verification) ----


async def signup_founder_with_token(client, email: str = "frank@example.com") -> dict:
    """Sign up a founder, return {token, user_id, email}."""
    from bson import ObjectId
    body = await signup_founder(client, email)
    return {
        "token": body["jwt"],
        "user_id": ObjectId(body["user"]["id"]),
        "email": email,
    }


# ---- Notification seeding helper (cycle: notifications-in-app) ----


async def seed_notification(
    *,
    user_id,
    kind: str,
    payload: dict | None = None,
    read: bool = False,
) -> dict:
    """Insert a notification row directly. Tests use this to construct
    inbox fixtures without invoking publish_launch / admin approve."""
    from datetime import datetime, timezone
    from app.db.notifications import notifications_collection

    doc = {
        "user_id": user_id,
        "kind": kind,
        "payload": payload or {},
        "read_at": datetime.now(timezone.utc) if read else None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await notifications_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


# ---- Engagement seeding helper (cycle: founder-dashboard-and-analytics) ----


async def seed_engagement(
    *,
    launch_id,
    surface: str,
    action: str,
    user_id=None,
    metadata: dict | None = None,
) -> None:
    """Insert a single engagements row directly. Tests use this to
    construct varied analytics fixtures without going through publish_launch."""
    from app.db.engagements import insert as insert_engagement

    await insert_engagement(
        launch_id=launch_id,
        surface=surface,
        action=action,
        user_id=user_id,
        metadata=metadata or {},
    )


async def submit_test_launch(client, token: str, **overrides) -> dict:
    """POST /api/founders/launch with sane defaults; returns the parsed
    response body. NOTE: callers must ensure `seed_test_communities`
    is in scope so the default `target_community_slugs` resolve.
    Pass `target_community_slugs=[...]` to override or test edge cases."""
    payload = {
        "product_url": "https://acme.io",
        "problem_statement": "Marketers waste 3 hours weekly compiling reports.",
        "icp_description": "Marketing ops at 20-200 person SaaS startups.",
        "existing_presence_links": ["https://x.com/acme"],
        "target_community_slugs": ["marketing-ops"],
    }
    payload.update(overrides)
    r = await client.post(
        "/api/founders/launch",
        json=payload,
        headers=auth_header(token),
    )
    return {"status": r.status_code, "body": r.json() if r.status_code < 500 else None, "response": r}


async def signup_user_and_join(client, email: str, slug: str) -> dict:
    """Sign up a user and join one community. Returns
    {token, user_id, email, community_slug}."""
    body = await signup_user(client, email)
    token = body["jwt"]
    r = await client.post(
        f"/api/communities/{slug}/join",
        headers=auth_header(token),
    )
    assert r.status_code == 200, r.text
    from bson import ObjectId
    return {
        "token": token,
        "user_id": ObjectId(body["user"]["id"]),
        "email": email,
        "community_slug": slug,
    }
