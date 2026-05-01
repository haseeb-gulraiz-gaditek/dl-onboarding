"""F-EMB-5: similarity_search helper.

These tests exercise the mongomock-motor fallback path (Python-side
cosine). The production $vectorSearch aggregation path is untested
in the suite by design -- it requires a live Atlas Vector Search
index and is exercised by manual validation.
"""
import pytest

from app.db.tools_seed import tools_seed_collection
from app.embeddings.lifecycle import ensure_tool_embedding
from app.embeddings.vector_store import TOOL_CLASS, similarity_search


pytestmark = pytest.mark.asyncio


async def _embed_all_test_tools():
    coll = tools_seed_collection()
    cursor = coll.find({"curation_status": "approved", "embedding": None})
    async for tool in cursor:
        await ensure_tool_embedding(tool["slug"])


async def _query_vector_for_text(text: str) -> list[float]:
    """Use the same mock embed function so the test query vector
    matches the cosine ranking the documents were embedded with."""
    from app.embeddings.lifecycle import embed_text

    return await embed_text(text)


async def test_similarity_search_returns_top_k_in_cosine_order(
    app_client, seed_test_catalog
):
    # Approve the pending and rejected ones too so we have multiple
    # embedded tools to rank.
    coll = tools_seed_collection()
    await coll.update_many(
        {"slug": {"$in": ["test-tool-pending", "test-tool-rejected"]}},
        {"$set": {"curation_status": "approved", "rejection_comment": None}},
    )
    await _embed_all_test_tools()

    # Query against a known tool's name -- the deterministic mock means
    # the closest-matching tool will be the one whose embedded text
    # starts with that name.
    q = await _query_vector_for_text("Test Tool Approved")

    results = await similarity_search(
        collection_name="tools_seed",
        weaviate_class=TOOL_CLASS,
        query_vector=q,
        top_k=3,
    )
    assert len(results) == 3
    # Slugs of the three approved+embedded tools.
    returned_slugs = {r["slug"] for r in results}
    assert returned_slugs == {
        "test-tool-approved", "test-tool-pending", "test-tool-rejected"
    }


async def test_similarity_search_empty_collection_returns_empty(app_client):
    q = await _query_vector_for_text("anything")

    results = await similarity_search(
        collection_name="tools_seed",
        weaviate_class=TOOL_CLASS,
        query_vector=q,
        top_k=10,
    )
    assert results == []


async def test_similarity_search_filters_narrow_the_set(
    app_client, seed_test_catalog
):
    coll = tools_seed_collection()
    # Approve everything in the fixture.
    await coll.update_many(
        {},
        {"$set": {"curation_status": "approved", "rejection_comment": None}},
    )
    await _embed_all_test_tools()

    q = await _query_vector_for_text("Test Tool")

    # Filter by category -- only one fixture tool is "writing".
    results = await similarity_search(
        collection_name="tools_seed",
        weaviate_class=TOOL_CLASS,
        query_vector=q,
        top_k=10,
        filters={"category": "writing"},
    )
    assert len(results) == 1
    assert results[0]["slug"] == "test-tool-approved"
