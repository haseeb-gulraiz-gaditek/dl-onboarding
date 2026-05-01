"""Atlas Vector Search index definitions + similarity_search helper.

The two search indices below MUST be created manually via the
Atlas UI before similarity_search will return results in
production. Programmatic creation requires the Atlas Admin API
which is V1.5+.

Atlas UI path:
  Cluster -> Search -> Create Search Index -> JSON Editor
  Database: mesh
  Collection: tools_seed (or profiles)
  Index name: <see constants below>
  Definition: <copy the corresponding _SPEC dict, JSON-encoded>

Test environment uses mongomock-motor which does not support
$vectorSearch. The similarity_search helper detects this and
falls back to a Python-side cosine pass over the documents.
"""
import math
from typing import Any

from app.db.mongo import get_db


# ---- Tools index ----

TOOLS_VECTOR_INDEX_NAME = "tools_seed_vector_index"

TOOLS_VECTOR_INDEX_SPEC: dict[str, Any] = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": 1536,
            "similarity": "cosine",
        },
        {"type": "filter", "path": "curation_status"},
        {"type": "filter", "path": "category"},
        {"type": "filter", "path": "labels"},
    ]
}


# ---- Profiles index ----

PROFILES_VECTOR_INDEX_NAME = "profiles_vector_index"

PROFILES_VECTOR_INDEX_SPEC: dict[str, Any] = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": 1536,
            "similarity": "cosine",
        }
    ]
}


# ---- similarity_search ----

def _is_mongomock(coll: Any) -> bool:
    """Detect the test environment so we can fall back to Python-side
    cosine. mongomock-motor proxies through real Motor classes, so the
    type's module path is misleading -- isinstance against the actual
    AsyncMongoMockClient is the reliable signal."""
    try:
        from mongomock_motor import AsyncMongoMockClient
    except ImportError:
        return False
    return isinstance(coll.database.client, AsyncMongoMockClient)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


async def similarity_search(
    *,
    collection_name: str,
    index_name: str,
    query_vector: list[float],
    top_k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return top-k documents ranked by cosine similarity to query_vector.

    Production path: Atlas $vectorSearch aggregation against the named
    Atlas Search index. Optional `filters` is passed through to
    $vectorSearch.filter (the index must declare those paths as filter
    fields -- see the *_SPEC dicts above).

    Test path (mongomock-motor): in-memory cosine over documents
    matching `filters`. The `index_name` argument is ignored in this
    path because mongomock has no Atlas Search analog.
    """
    coll = get_db()[collection_name]

    if _is_mongomock(coll):
        query: dict[str, Any] = {"embedding": {"$ne": None}}
        if filters:
            query.update(filters)
        cursor = coll.find(query)
        docs = await cursor.to_list(length=None)
        scored = [
            (doc, _cosine_similarity(query_vector, doc.get("embedding") or []))
            for doc in docs
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]

    # Production path: Atlas $vectorSearch.
    vector_search_stage: dict[str, Any] = {
        "$vectorSearch": {
            "index": index_name,
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": max(top_k * 10, 100),
            "limit": top_k,
        }
    }
    if filters:
        vector_search_stage["$vectorSearch"]["filter"] = filters

    cursor = coll.aggregate([vector_search_stage])
    return await cursor.to_list(length=top_k)
