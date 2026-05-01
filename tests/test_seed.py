"""F-QB-1: question-bank seed loader."""
import pytest

from app.db.questions import questions_collection
from app.seed.questions import (
    SEED_PATH,
    apply_questions_seed,
    load_seed_file,
)


pytestmark = pytest.mark.asyncio


async def test_seed_loads_questions_idempotent(app_client):
    entries = load_seed_file(SEED_PATH)

    # First run: inserts everything.
    inserted, updated, total = await apply_questions_seed(entries)
    assert total == len(entries)
    assert inserted == len(entries)
    assert updated == 0

    # Second run: nothing new, nothing changed.
    inserted2, updated2, total2 = await apply_questions_seed(entries)
    assert total2 == len(entries)
    assert inserted2 == 0
    assert updated2 == 0

    # DB has exactly len(entries) rows -- no duplicate keys.
    count = await questions_collection().count_documents({})
    assert count == len(entries)


async def test_seed_updates_existing_on_text_change(app_client):
    entries = load_seed_file(SEED_PATH)
    await apply_questions_seed(entries)

    # Mutate the first entry in memory and re-apply.
    entries[0]["text"] = "EDITED — what's your role?"
    inserted, updated, _ = await apply_questions_seed(entries)
    assert inserted == 0
    assert updated >= 1

    doc = await questions_collection().find_one({"key": entries[0]["key"]})
    assert doc["text"] == "EDITED — what's your role?"


async def test_seed_invalid_shape_no_partial_writes(app_client):
    bad_entries = [
        {  # Valid -- would insert if validation passed.
            "key": "x.valid", "text": "Valid?", "kind": "free_text",
            "category": "workflow", "order": 1, "version": 1,
            "active": True, "is_core": True, "options": [],
        },
        {  # Invalid -- unknown kind.
            "key": "x.bad", "text": "Bad", "kind": "weird_kind",
            "category": "workflow", "order": 2, "version": 1,
            "active": True, "is_core": True, "options": [],
        },
    ]
    with pytest.raises(ValueError):
        await apply_questions_seed(bad_entries)

    # Confirm NO entry was written -- validation runs before any upsert.
    count = await questions_collection().count_documents({})
    assert count == 0
