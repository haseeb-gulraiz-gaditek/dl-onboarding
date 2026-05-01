"""F-QB-2: GET /api/questions/next."""
import pytest
from bson import ObjectId

from app.db.profiles import profiles_collection
from tests.conftest import (
    auth_header,
    signed_up_user_with_profile,
    signup_founder,
    signup_user,
)


pytestmark = pytest.mark.asyncio


async def test_user_with_no_profile_gets_first_question(
    app_client, seed_test_questions
):
    body = await signup_user(app_client, "maya@example.com")

    r = await app_client.get(
        "/api/questions/next", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["done"] is False
    assert payload["question"]["order"] == 1
    assert payload["question"]["category"] == "role"

    # Profile was created lazily.
    user_id = ObjectId(body["user"]["id"])
    profile = await profiles_collection().find_one({"user_id": user_id})
    assert profile is not None
    assert profile["role"] is None  # populated by a future aggregation cycle


async def test_user_gets_next_in_order_after_answering_one(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    first_q = info["first"]["question"]

    # Answer the first question (single_select role question).
    r1 = await app_client.post(
        "/api/answers",
        json={"question_id": first_q["id"], "value": "designer"},
        headers=auth_header(info["token"]),
    )
    assert r1.status_code == 200

    # Next call returns question at order=2 (stack).
    r2 = await app_client.get(
        "/api/questions/next", headers=auth_header(info["token"])
    )
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["done"] is False
    assert payload["question"]["order"] == 2
    assert payload["question"]["category"] == "stack"


async def test_user_who_answered_all_gets_done(app_client, seed_test_questions):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    token = info["token"]

    # Answer all 3 test questions in order.
    answers = [
        ("designer",),
        (["notion"],),  # multi-select, list
        ("My weekly campaign reporting takes 3 hours",),
    ]
    for value_tuple in answers:
        next_r = await app_client.get(
            "/api/questions/next", headers=auth_header(token)
        )
        q = next_r.json()["question"]
        post_r = await app_client.post(
            "/api/answers",
            json={"question_id": q["id"], "value": value_tuple[0]},
            headers=auth_header(token),
        )
        assert post_r.status_code == 200

    # All answered.
    r = await app_client.get("/api/questions/next", headers=auth_header(token))
    assert r.status_code == 200
    payload = r.json()
    assert payload["done"] is True
    assert payload["question"] is None


async def test_founder_gets_403_role_mismatch(app_client, seed_test_questions):
    body = await signup_founder(app_client, "aamir@example.com")

    r = await app_client.get(
        "/api/questions/next", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["error"] == "role_mismatch"
    assert detail["required"] == "user"
    assert detail["actual"] == "founder"


async def test_unauthenticated_gets_401_auth_required(
    app_client, seed_test_questions
):
    r = await app_client.get("/api/questions/next")
    assert r.status_code == 401
    assert r.json()["detail"]["error"] == "auth_required"
