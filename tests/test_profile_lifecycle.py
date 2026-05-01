"""F-QB-4: profile lifecycle (lazy creation, invalidation timestamp)."""
import asyncio

import pytest
from bson import ObjectId

from app.db.profiles import profiles_collection
from tests.conftest import auth_header, signed_up_user_with_profile, signup_user


pytestmark = pytest.mark.asyncio


def _assert_profile_shape(profile: dict, user_id: ObjectId) -> None:
    """Assert the profile matches the F-QB-4 default schema."""
    assert profile["user_id"] == user_id
    assert profile["role"] is None
    assert profile["current_tools"] == []
    assert profile["workflows"] == []
    assert profile["tools_tried_bounced"] == []
    assert profile["counterfactual_wishes"] == []
    assert profile["budget_tier"] is None
    assert profile["embedding"] is None
    assert profile["last_recompute_at"] is None
    assert profile["last_invalidated_at"] is not None
    assert profile["exportable"] is True
    assert profile["created_at"] is not None


async def test_profile_created_on_first_get_questions_next(
    app_client, seed_test_questions
):
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    # No profile before the call.
    pre = await profiles_collection().find_one({"user_id": user_id})
    assert pre is None

    r = await app_client.get(
        "/api/questions/next", headers=auth_header(body["jwt"])
    )
    assert r.status_code == 200

    profile = await profiles_collection().find_one({"user_id": user_id})
    assert profile is not None
    _assert_profile_shape(profile, user_id)


async def test_profile_created_on_first_post_answers(
    app_client, seed_test_questions
):
    """A user who skips GET /api/questions/next and goes straight to
    POST /api/answers still gets a profile created (defense in depth)."""
    body = await signup_user(app_client, "maya@example.com")
    user_id = ObjectId(body["user"]["id"])

    # Look up the role question id directly via the collection (we
    # bypassed GET /api/questions/next deliberately).
    from app.db.questions import questions_collection

    role_q = await questions_collection().find_one({"key": "test.role_q"})

    pre = await profiles_collection().find_one({"user_id": user_id})
    assert pre is None

    r = await app_client.post(
        "/api/answers",
        json={"question_id": str(role_q["_id"]), "value": "designer"},
        headers=auth_header(body["jwt"]),
    )
    assert r.status_code == 200

    profile = await profiles_collection().find_one({"user_id": user_id})
    assert profile is not None
    _assert_profile_shape(profile, user_id)


async def test_post_answers_bumps_last_invalidated_at(
    app_client, seed_test_questions
):
    info = await signed_up_user_with_profile(app_client, "maya@example.com")
    user_id = ObjectId(info["user"]["id"])
    qid = info["first"]["question"]["id"]

    pre = await profiles_collection().find_one({"user_id": user_id})
    pre_invalidated_at = pre["last_invalidated_at"]

    # Sleep a tiny amount so the timestamp is observably newer.
    await asyncio.sleep(0.01)

    r = await app_client.post(
        "/api/answers",
        json={"question_id": qid, "value": "designer"},
        headers=auth_header(info["token"]),
    )
    assert r.status_code == 200

    post = await profiles_collection().find_one({"user_id": user_id})
    assert post["last_invalidated_at"] > pre_invalidated_at
