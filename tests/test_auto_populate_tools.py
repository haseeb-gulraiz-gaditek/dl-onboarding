"""Tests for the auto-populate hook on POST /api/answers.

Per spec-delta my-tools-explore-new-tabs F-TOOL-7 + F-QB-3 MODIFIED.
"""
import pytest

from tests.conftest import auth_header, signup_user


async def _post_answer(client, token, question_id, value):
    return await client.post(
        "/api/answers",
        json={"question_id": str(question_id), "value": value},
        headers=auth_header(token),
    )


@pytest.mark.asyncio
async def test_multi_select_resolving_slugs_auto_populates(
    app_client, seed_tool_stack_question
):
    """F-TOOL-7: multi_select with all-resolving slugs creates one
    user_tools row per slug."""
    from app.db.user_tools import user_tools_collection
    from bson import ObjectId

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    r = await _post_answer(
        app_client,
        body["jwt"],
        seed_tool_stack_question["_id"],
        ["test-tool-approved", "test-tool-pending"],
    )
    assert r.status_code == 200, r.text

    rows = await user_tools_collection().find(
        {"user_id": user_id}
    ).to_list(length=None)
    assert len(rows) == 2
    for row in rows:
        assert row["source"] == "auto_from_profile"
        assert row["status"] == "using"


@pytest.mark.asyncio
async def test_mixed_resolving_and_non_resolving_only_inserts_resolvers(
    app_client, seed_tool_stack_question
):
    """F-TOOL-7: unknown slugs in the value list are silently skipped."""
    from app.db.user_tools import user_tools_collection
    from bson import ObjectId

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    r = await _post_answer(
        app_client,
        body["jwt"],
        seed_tool_stack_question["_id"],
        ["test-tool-approved", "not-in-catalog"],
    )
    assert r.status_code == 200

    rows = await user_tools_collection().find(
        {"user_id": user_id}
    ).to_list(length=None)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_re_answering_is_idempotent(
    app_client, seed_tool_stack_question
):
    """F-TOOL-7: re-answering the same question doesn't duplicate rows."""
    from app.db.user_tools import user_tools_collection
    from bson import ObjectId

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    for _ in range(3):
        await _post_answer(
            app_client,
            body["jwt"],
            seed_tool_stack_question["_id"],
            ["test-tool-approved"],
        )

    rows = await user_tools_collection().find(
        {"user_id": user_id}
    ).to_list(length=None)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_explicit_save_not_demoted_by_subsequent_auto_populate(
    app_client, seed_tool_stack_question
):
    """F-TOOL-7: an explicit_save row stays explicit even if a later
    multi_select answer references the same slug."""
    body = await signup_user(app_client, "maya@example.com")

    await app_client.post(
        "/api/me/tools",
        json={"tool_slug": "test-tool-approved", "status": "saved"},
        headers=auth_header(body["jwt"]),
    )
    await _post_answer(
        app_client,
        body["jwt"],
        seed_tool_stack_question["_id"],
        ["test-tool-approved"],
    )

    r = await app_client.get(
        "/api/me/tools", headers=auth_header(body["jwt"])
    )
    rows = r.json()["tools"]
    assert len(rows) == 1
    assert rows[0]["source"] == "explicit_save"  # NOT demoted
    assert rows[0]["status"] == "saved"          # NOT changed


@pytest.mark.asyncio
async def test_free_text_answer_does_not_auto_populate(app_client):
    """F-TOOL-7: free_text questions don't trigger the hook."""
    from app.db.questions import questions_collection
    from app.db.user_tools import user_tools_collection
    from bson import ObjectId

    await questions_collection().insert_one({
        "key": "freetext.x",
        "text": "Tell me about your workflow.",
        "kind": "free_text",
        "category": "workflow",
        "order": 1,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [],
    })
    q = await questions_collection().find_one({"key": "freetext.x"})

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await _post_answer(
        app_client, body["jwt"], q["_id"], "I use notion every day"
    )

    rows = await user_tools_collection().find(
        {"user_id": user_id}
    ).to_list(length=None)
    assert rows == []


@pytest.mark.asyncio
async def test_single_select_does_not_auto_populate(
    app_client, seed_tool_stack_question
):
    """F-TOOL-7: single_select with a slug-shaped value doesn't trigger."""
    from app.db.questions import questions_collection
    from app.db.user_tools import user_tools_collection
    from bson import ObjectId

    await questions_collection().insert_one({
        "key": "single.choice",
        "text": "Pick one.",
        "kind": "single_select",
        "category": "stack",
        "order": 6,
        "is_core": True,
        "active": True,
        "version": 1,
        "options": [
            {"value": "test-tool-approved", "label": "Approved"},
        ],
    })
    q = await questions_collection().find_one({"key": "single.choice"})

    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])
    await _post_answer(
        app_client, body["jwt"], q["_id"], "test-tool-approved"
    )

    rows = await user_tools_collection().find(
        {"user_id": user_id}
    ).to_list(length=None)
    assert rows == []
