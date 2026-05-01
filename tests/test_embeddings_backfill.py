"""F-EMB-2: backfill CLI exercise."""
import pytest

from app.db.tools_seed import tools_seed_collection
from app.embeddings.backfill import backfill_tools


pytestmark = pytest.mark.asyncio


async def test_backfill_embeds_only_approved_tools(
    app_client, seed_test_catalog
):
    """The fixture has 3 tools: pending, approved, rejected. Only the
    approved one should get embedded by the backfill."""
    result = await backfill_tools()

    # Total counts the approved tools (1 in the fixture).
    assert result["total"] == 1
    assert result["embedded"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0

    # Confirm the right rows have / lack embeddings.
    approved = await tools_seed_collection().find_one(
        {"slug": "test-tool-approved"}
    )
    pending = await tools_seed_collection().find_one(
        {"slug": "test-tool-pending"}
    )
    rejected = await tools_seed_collection().find_one(
        {"slug": "test-tool-rejected"}
    )
    assert approved["embedding"] is not None
    assert pending["embedding"] is None    # pending is NOT embedded
    assert rejected["embedding"] is None   # rejected is NOT embedded


async def test_backfill_is_idempotent(app_client, seed_test_catalog):
    # First run: 1 embedded.
    first = await backfill_tools()
    assert first["embedded"] == 1
    assert first["skipped"] == 0

    # Second run: 0 embedded (already done), 1 skipped.
    second = await backfill_tools()
    assert second["embedded"] == 0
    assert second["skipped"] == 1
    assert second["total"] == 1
    assert second["failed"] == 0


async def test_backfill_records_failures_without_aborting(
    app_client, seed_test_catalog, monkeypatch
):
    async def _failing_embed(text: str) -> list[float]:
        raise RuntimeError("simulated outage")

    monkeypatch.setattr("app.embeddings.lifecycle.embed_text", _failing_embed)

    result = await backfill_tools()
    assert result["embedded"] == 0
    assert result["failed"] == 1
    assert result["total"] == 1
