"""F-CAT-3: catalog seed loader."""
import pytest

from app.db.tools_seed import tools_seed_collection
from app.seed.catalog import apply_catalog_seed


pytestmark = pytest.mark.asyncio


_VALID_ENTRY = {
    "slug": "valid-tool",
    "name": "Valid Tool",
    "tagline": "A tagline.",
    "description": "A real description that says what it does.",
    "url": "https://example.com",
    "pricing_summary": "Free",
    "category": "productivity",
    "labels": ["all_time_best"],
}


def _entry(**overrides) -> dict:
    return {**_VALID_ENTRY, **overrides}


async def test_loader_inserts_entries_and_is_idempotent(app_client):
    entries = [
        _entry(slug="alpha", name="Alpha"),
        _entry(slug="beta", name="Beta"),
        _entry(slug="gamma", name="Gamma"),
    ]
    inserted, updated, total = await apply_catalog_seed(entries)
    assert (inserted, updated, total) == (3, 0, 3)

    # Re-run: nothing inserted, nothing updated.
    inserted2, updated2, total2 = await apply_catalog_seed(entries)
    assert (inserted2, updated2, total2) == (0, 0, 3)

    # Defaults applied.
    doc = await tools_seed_collection().find_one({"slug": "alpha"})
    assert doc["curation_status"] == "pending"
    assert doc["source"] == "manual"
    assert doc["embedding_vector_id"] is None
    assert doc["created_at"] is not None


async def test_re_run_updates_changed_fields(app_client):
    entries = [_entry(slug="alpha", tagline="old tagline")]
    await apply_catalog_seed(entries)

    entries[0]["tagline"] = "new tagline"
    inserted, updated, _ = await apply_catalog_seed(entries)
    assert inserted == 0
    assert updated == 1

    doc = await tools_seed_collection().find_one({"slug": "alpha"})
    assert doc["tagline"] == "new tagline"


async def test_unknown_category_raises_no_partial_writes(app_client):
    entries = [
        _entry(slug="ok", name="Ok"),
        _entry(slug="bad", name="Bad", category="not_a_category"),
    ]
    with pytest.raises(ValueError, match="unknown category"):
        await apply_catalog_seed(entries)

    count = await tools_seed_collection().count_documents({})
    assert count == 0


async def test_duplicate_slugs_raises_no_partial_writes(app_client):
    entries = [
        _entry(slug="dup", name="One"),
        _entry(slug="dup", name="Two"),
    ]
    with pytest.raises(ValueError, match="duplicate slugs"):
        await apply_catalog_seed(entries)

    count = await tools_seed_collection().count_documents({})
    assert count == 0


async def test_invalid_url_raises(app_client):
    entries = [_entry(url="not-a-url")]
    with pytest.raises(ValueError, match="http"):
        await apply_catalog_seed(entries)


async def test_loader_does_not_clobber_founder_launched_rows(app_client):
    """Defense-in-depth: pre-insert a row with source=founder_launch
    using the same slug a seed entry would, and verify the loader
    doesn't touch it."""
    coll = tools_seed_collection()
    from datetime import datetime, timezone

    pre_existing = {
        "slug": "calendar-tool",
        "name": "FOUNDER ORIGINAL",
        "tagline": "founder's original",
        "description": "founder's original description",
        "url": "https://founder.example.com",
        "pricing_summary": "Free",
        "category": "productivity",
        "labels": ["new"],
        "curation_status": "approved",
        "rejection_comment": None,
        "source": "founder_launch",
        "embedding_vector_id": None,
        "created_at": datetime.now(timezone.utc),
        "last_reviewed_at": None,
        "reviewed_by": None,
    }
    await coll.insert_one(pre_existing)

    # Try to load a curated entry with the same slug.
    seed_entry = _entry(
        slug="calendar-tool",
        name="MESH SEED -- should NOT win",
        tagline="curated tagline",
    )
    inserted, updated, total = await apply_catalog_seed([seed_entry])

    # Founder-launched row is protected: the upsert was a no-op
    # (filter excludes founder_launch source rows).
    assert inserted == 0
    assert updated == 0
    assert total == 1

    # Confirm the founder's row is intact.
    doc = await coll.find_one({"slug": "calendar-tool"})
    assert doc["source"] == "founder_launch"
    assert doc["name"] == "FOUNDER ORIGINAL"
