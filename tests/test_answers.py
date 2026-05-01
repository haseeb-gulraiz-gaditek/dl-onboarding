"""F-QB-3: POST /api/answers."""
import pytest

from tests.conftest import (
    auth_header,
    signed_up_user_with_profile,
    signup_founder,
    signup_user,
)


pytestmark = pytest.mark.asyncio


async def _first_q_id(payload: dict) -> str:
    return payload["question"]["id"]


async def test_valid_single_select_stored_and_next_returned(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    qid = info["first"]["question"]["id"]

    r = await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "designer"},
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 200
    payload = r.json()
    # Returns the next question (order=2).
    assert payload["done"] is False
    assert payload["question"]["order"] == 2


async def test_valid_multi_select_array_stored(app_client, seed_test_questions):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    # Skip past role question.
    await app_client.post(
        "/api/answers",
        json={"question_id": info["first"]["question"]["id"], "value": "designer"},
        headers=auth_header(info["token"]),
    )

    next_r = await app_client.get(
        "/api/questions/next", headers=auth_header(info["token"])
    )
    multi_qid = next_r.json()["question"]["id"]

    r = await app_client.post(
        "/api/answers",
        json={"question_id": multi_qid, "value": ["notion", "linear"]},
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 200


async def test_valid_free_text_stored(app_client, seed_test_questions):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    token = info["token"]

    # Step past role, stack questions.
    role_qid = info["first"]["question"]["id"]
    await app_client.post(
        "/api/answers",
        json={"question_id": role_qid, "value": "designer"},
        headers=auth_header(token),
    )
    stack_q = (await app_client.get(
        "/api/questions/next", headers=auth_header(token)
    )).json()["question"]
    await app_client.post(
        "/api/answers",
        json={"question_id": stack_q["id"], "value": ["notion"]},
        headers=auth_header(token),
    )

    # Now free_text question.
    workflow_q = (await app_client.get(
        "/api/questions/next", headers=auth_header(token)
    )).json()["question"]
    r = await app_client.post(
        "/api/answers",
        json={
            "question_id": workflow_q["id"],
            "value": "Collecting weekly metrics from 4 sources",
        },
        headers=auth_header(token),
    )
    assert r.status_code == 200


async def test_invalid_question_id_returns_question_not_found(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")

    r = await app_client.post(
        "/api/answers",
        json={"question_id": "5f0a1b2c3d4e5f6a7b8c9d0e", "value": "x"},
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "question_not_found"


async def test_single_select_value_not_in_options(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    qid = info["first"]["question"]["id"]

    r = await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "astronaut"},  # not in options
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "value_invalid"


async def test_multi_select_empty_array(app_client, seed_test_questions):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    # Skip role question.
    await app_client.post(
        "/api/answers",
        json={"question_id": info["first"]["question"]["id"], "value": "designer"},
        headers=auth_header(info["token"]),
    )
    multi_qid = (await app_client.get(
        "/api/questions/next", headers=auth_header(info["token"])
    )).json()["question"]["id"]

    r = await app_client.post(
        "/api/answers",
        json={"question_id": multi_qid, "value": []},  # empty list
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "value_invalid"


async def test_free_text_empty_string(app_client, seed_test_questions):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    token = info["token"]

    # Walk to the free_text question.
    role_qid = info["first"]["question"]["id"]
    await app_client.post(
        "/api/answers",
        json={"question_id": role_qid, "value": "designer"},
        headers=auth_header(token),
    )
    stack_q = (await app_client.get(
        "/api/questions/next", headers=auth_header(token)
    )).json()["question"]
    await app_client.post(
        "/api/answers",
        json={"question_id": stack_q["id"], "value": ["notion"]},
        headers=auth_header(token),
    )
    workflow_q = (await app_client.get(
        "/api/questions/next", headers=auth_header(token)
    )).json()["question"]

    r = await app_client.post(
        "/api/answers",
        json={"question_id": workflow_q["id"], "value": "   "},  # whitespace only
        headers=auth_header(token),
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "value_invalid"


async def test_missing_question_id_returns_field_required(
    app_client, seed_test_questions
):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.post(
        "/api/answers",
        json={"value": "designer"},  # no question_id
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    j = r.json()
    assert j["error"] == "field_required"
    assert j["field"] == "question_id"


async def test_missing_value_returns_field_required(
    app_client, seed_test_questions
):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.post(
        "/api/answers",
        json={"question_id": "5f0a1b2c3d4e5f6a7b8c9d0e"},  # no value
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 400
    j = r.json()
    assert j["error"] == "field_required"
    assert j["field"] == "value"


async def test_founder_gets_403_role_mismatch(app_client, seed_test_questions):
    body = await signup_founder(app_client, "aamir@example.com")

    r = await app_client.post(
        "/api/answers",
        json={"question_id": "5f0a1b2c3d4e5f6a7b8c9d0e", "value": "x"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "role_mismatch"
