"""Tests for the publish orchestrator (cycle: launch-publish-...).

Covers F-LAUNCH-1 MODIFIED + F-PUB-1, F-PUB-2, F-PUB-7.
"""
import pytest

from tests.conftest import (
    auth_header,
    signup_founder_with_token,
    signup_user,
    submit_test_launch,
)


# ---- F-LAUNCH-1 MODIFIED: target_community_slugs validation ----


@pytest.mark.asyncio
async def test_submit_without_target_community_slugs_returns_400(
    app_client, seed_test_communities
):
    """F-LAUNCH-1 MODIFIED: target_community_slugs is required (min_length=1)."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=[]
    )
    assert res["status"] == 400
    detail = res["body"].get("detail") or res["body"]
    err = detail if isinstance(detail, dict) else detail[0]
    assert err.get("error") in ("field_invalid", "too_short")
    # Pydantic min_length error shape is fine either way; key is the failure.


@pytest.mark.asyncio
async def test_submit_unknown_community_slug_returns_400(
    app_client, seed_test_communities
):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=["does-not-exist"],
    )
    assert res["status"] == 400
    assert res["body"]["detail"]["error"] == "community_not_found"


@pytest.mark.asyncio
async def test_submit_too_many_community_slugs_returns_400(
    app_client, seed_test_communities
):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=[
            "marketing-ops", "engineering-bench", "weekly-launches",
            "marketing-ops", "engineering-bench", "weekly-launches",
            "marketing-ops",  # 7 entries → > max
        ],
    )
    assert res["status"] == 400


@pytest.mark.asyncio
async def test_submit_duplicate_community_slugs_returns_400(
    app_client, seed_test_communities
):
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=["marketing-ops", "marketing-ops"],
    )
    assert res["status"] == 400
    assert res["body"]["detail"]["error"] == "field_invalid"
    assert res["body"]["detail"]["field"] == "target_community_slugs"


# ---- F-PUB-2: approve fans out posts + nudges ----


@pytest.mark.asyncio
async def test_approve_fans_out_to_all_target_communities(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-2 step 3: a posts row appears in EACH target community."""
    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=["marketing-ops", "weekly-launches"],
    )
    launch_id = res["body"]["id"]

    approve = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert approve.status_code == 200
    summary = approve.json().get("publish_summary") or {}
    assert summary.get("community_posts_count") == 2

    # Post exists in marketing-ops feed.
    feed1 = await app_client.get(
        "/api/communities/marketing-ops/posts",
        headers=auth_header(admin_token["token"]),
    )
    titles1 = [p["title"] for p in feed1.json()["posts"]]
    assert any(
        "Marketers waste 3 hours" in t for t in titles1
    ), titles1

    # And in weekly-launches feed.
    feed2 = await app_client.get(
        "/api/communities/weekly-launches/posts",
        headers=auth_header(admin_token["token"]),
    )
    titles2 = [p["title"] for p in feed2.json()["posts"]]
    assert any(
        "Marketers waste 3 hours" in t for t in titles2
    ), titles2


@pytest.mark.asyncio
async def test_approve_writes_engagements_per_community_post(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-1 + F-PUB-2: one engagement row per fan-out post,
    surface=community_post."""
    from app.db.engagements import engagements_collection

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=["marketing-ops", "weekly-launches"],
    )
    launch_id = res["body"]["id"]

    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    from bson import ObjectId
    docs = await engagements_collection().find(
        {"launch_id": ObjectId(launch_id), "surface": "community_post"}
    ).to_list(length=None)
    assert len(docs) == 2


@pytest.mark.asyncio
async def test_approve_skips_inactive_target_silently(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-2: a community deactivated between submission and approval
    is skipped without aborting the publish."""
    from app.db.communities import communities_collection

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client,
        f["token"],
        target_community_slugs=["marketing-ops", "weekly-launches"],
    )
    launch_id = res["body"]["id"]

    # Deactivate one of the target communities.
    await communities_collection().update_one(
        {"slug": "weekly-launches"}, {"$set": {"is_active": False}}
    )

    approve = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert approve.status_code == 200
    summary = approve.json().get("publish_summary") or {}
    # One ran, one skipped silently.
    assert summary.get("community_posts_count") == 1


@pytest.mark.asyncio
async def test_approve_concierge_scan_writes_nudges(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-2 step 4 + F-PUB-7: top-5 profile matches get
    concierge_nudge notifications."""
    from app.db.notifications import notifications_collection
    from tests.conftest import prepare_user_for_recs

    # Prep three users with profile embeddings so similarity_search
    # has candidates.
    for i, email in enumerate(("a@example.com", "b@example.com", "c@example.com")):
        await prepare_user_for_recs(app_client, email, n_answers=3)

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]

    approve = await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )
    assert approve.status_code == 200
    summary = approve.json().get("publish_summary") or {}
    # 3 users with embeddings → 3 nudges (capped at top_k=5).
    assert summary.get("nudge_count") == 3

    nudges = await notifications_collection().find(
        {"kind": "concierge_nudge"}
    ).to_list(length=None)
    assert len(nudges) == 3
    for n in nudges:
        assert n["payload"]["launch_id"] == launch_id
        assert n["payload"]["tool_slug"] == "acme-io"


@pytest.mark.asyncio
async def test_approve_bumps_rec_cache_for_matched_users(
    app_client, seed_test_communities, admin_token
):
    """F-PUB-2 step 4: matched users' rec cache_expires_at is bumped to
    now() so the next call regenerates with the launch."""
    from datetime import datetime, timezone, timedelta

    from app.db.recommendations import recommendations_collection
    from tests.conftest import prepare_user_for_recs

    prep = await prepare_user_for_recs(app_client, "a@example.com", n_answers=3)
    # Seed a stale cache row (not actually expired).
    future = datetime.now(timezone.utc) + timedelta(days=7)
    await recommendations_collection().insert_one({
        "user_id": prep["user_id"],
        "picks": [],
        "launch_picks": [],
        "generated_at": datetime.now(timezone.utc),
        "cache_expires_at": future,
        "degraded": False,
    })

    f = await signup_founder_with_token(app_client, "aamir@example.com")
    res = await submit_test_launch(
        app_client, f["token"], target_community_slugs=["marketing-ops"]
    )
    launch_id = res["body"]["id"]
    await app_client.post(
        f"/admin/launches/{launch_id}/approve",
        headers=auth_header(admin_token["token"]),
    )

    rec = await recommendations_collection().find_one(
        {"user_id": prep["user_id"]}
    )
    assert rec is not None
    # Mongomock strips tzinfo on round-trip (cycle #6 learning).
    bumped = rec["cache_expires_at"]
    if bumped.tzinfo is None:
        bumped = bumped.replace(tzinfo=timezone.utc)
    # Bumped to ≤ now() → no longer in the future.
    assert bumped <= datetime.now(timezone.utc) + timedelta(seconds=1)
