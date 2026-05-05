"""Tests for GET /api/me/profile-summary (cycle: frontend-core audit)."""
import pytest

from tests.conftest import auth_header, signup_founder, signup_user


@pytest.mark.asyncio
async def test_empty_for_fresh_user(app_client):
    body = await signup_user(app_client, "maya@example.com")
    r = await app_client.get(
        "/api/me/profile-summary", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    assert r.json() == {"stack_tools": [], "all_answer_values": []}


@pytest.mark.asyncio
async def test_stack_tools_from_multi_select_stack_answer(app_client):
    """Stack panel should reflect the user's actual picks with original
    labels — never silently filtered through catalog lookup."""
    from app.db.answers import answers_collection
    from app.db.questions import questions_collection
    from bson import ObjectId

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    # Insert a stack-category multi_select question and an answer.
    q = {
        "key": "stack.workspace_tools",
        "text": "Which tools do you use most?",
        "kind": "multi_select",
        "category": "stack",
        "order": 2,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "notion", "label": "Notion"},
            {"value": "linear", "label": "Linear"},
            {"value": "figma", "label": "Figma"},
        ],
    }
    qres = await questions_collection().insert_one(q)
    qid = qres.inserted_id

    from datetime import datetime, timezone
    await answers_collection().insert_one({
        "user_id": user_id,
        "question_id": qid,
        "value": ["notion", "linear"],
        "is_typed_other": False,
        "captured_at": datetime.now(timezone.utc),
    })

    r = await app_client.get(
        "/api/me/profile-summary", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    body_json = r.json()
    stack = body_json["stack_tools"]
    assert {(s["value"], s["label"]) for s in stack} == {
        ("notion", "Notion"),
        ("linear", "Linear"),
    }


@pytest.mark.asyncio
async def test_all_answer_values_flattens_singles_and_multis(app_client):
    from app.db.answers import answers_collection
    from app.db.questions import questions_collection
    from bson import ObjectId
    from datetime import datetime, timezone

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    qa = {
        "key": "role.primary_function",
        "text": "?",
        "kind": "single_select",
        "category": "role",
        "order": 1,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [{"value": "engineering", "label": "Engineering"}],
    }
    qb = {
        "key": "stack.workspace_tools",
        "text": "?",
        "kind": "multi_select",
        "category": "stack",
        "order": 2,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [{"value": "notion", "label": "Notion"}],
    }
    a_res = await questions_collection().insert_one(qa)
    b_res = await questions_collection().insert_one(qb)

    now = datetime.now(timezone.utc)
    await answers_collection().insert_many([
        {"user_id": user_id, "question_id": a_res.inserted_id,
         "value": "engineering", "is_typed_other": False, "captured_at": now},
        {"user_id": user_id, "question_id": b_res.inserted_id,
         "value": ["notion", "linear"], "is_typed_other": False, "captured_at": now},
    ])

    r = await app_client.get(
        "/api/me/profile-summary", headers=auth_header(body["jwt"])
    )
    vals = set(r.json()["all_answer_values"])
    assert vals == {"engineering", "notion", "linear"}


@pytest.mark.asyncio
async def test_founder_returns_403(app_client):
    body = await signup_founder(app_client, "frank@example.com")
    r = await app_client.get(
        "/api/me/profile-summary", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(app_client):
    r = await app_client.get("/api/me/profile-summary")
    assert r.status_code == 401
