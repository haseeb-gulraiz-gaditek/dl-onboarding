"""F-LIVE-3: hybrid_search() helper.

Smoke tests of the public surface — None client → [], non-None
client + thrown error → [], the helper exposes (props, score)
tuple shape.
"""
import pytest

from app.embeddings.vector_store import hybrid_search


pytestmark = pytest.mark.asyncio


async def test_hybrid_search_returns_empty_when_no_client(monkeypatch):
    """No Weaviate creds → _get_weaviate_client returns None → []."""
    async def none_client():
        return None
    monkeypatch.setattr(
        "app.embeddings.vector_store._get_weaviate_client", none_client, raising=True,
    )
    result = await hybrid_search(
        weaviate_class="ToolEmbedding",
        query="test",
        vector=[0.1] * 1536,
        alpha=0.5,
        limit=5,
        filters={"curation_status": "approved"},
    )
    assert result == []


async def test_hybrid_search_swallows_query_exception(monkeypatch):
    """Any exception inside the v4 query call returns [], no raise."""
    class FakeColl:
        class _query:
            @staticmethod
            async def hybrid(**_kw):
                raise RuntimeError("simulated weaviate failure")
        query = _query

    class FakeClient:
        class _collections:
            @staticmethod
            def use(_name):
                return FakeColl()
        collections = _collections

    async def fake_client():
        return FakeClient()

    monkeypatch.setattr(
        "app.embeddings.vector_store._get_weaviate_client", fake_client, raising=True,
    )
    result = await hybrid_search(
        weaviate_class="ToolEmbedding",
        query="test",
        vector=[0.1] * 1536,
        alpha=0.5,
        limit=5,
    )
    assert result == []


async def test_hybrid_search_returns_pairs(monkeypatch):
    """Smoke: maps client response.objects to [(props, score)] list."""
    class FakeMetadata:
        score = 0.77

    class FakeObject:
        def __init__(self, slug):
            self.properties = {"slug": slug, "category": "x"}
            self.metadata = FakeMetadata()

    class FakeResp:
        def __init__(self, slugs):
            self.objects = [FakeObject(s) for s in slugs]

    class FakeColl:
        class _query:
            @staticmethod
            async def hybrid(**_kw):
                return FakeResp(["alpha", "bravo"])
        query = _query

    class FakeClient:
        class _collections:
            @staticmethod
            def use(_name):
                return FakeColl()
        collections = _collections

    async def fake_client():
        return FakeClient()

    monkeypatch.setattr(
        "app.embeddings.vector_store._get_weaviate_client", fake_client, raising=True,
    )
    result = await hybrid_search(
        weaviate_class="ToolEmbedding",
        query="test",
        vector=[0.1] * 1536,
        alpha=0.5,
        limit=2,
    )
    assert len(result) == 2
    assert result[0][0]["slug"] == "alpha"
    assert result[0][1] == 0.77
