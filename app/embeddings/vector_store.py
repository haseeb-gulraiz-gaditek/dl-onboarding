"""Vector store integration: Weaviate Cloud Services with a
Mongo-side fallback for tests and graceful degradation.

Per spec-delta weaviate-pipeline (amended mid-cycle from Atlas
Vector Search to Weaviate Cloud per user call).

Architecture:
  - Mongo `embedding` field on tools_seed / profiles is the source of
    truth (constitutional invariant: profile is exportable). It is
    written first, regardless of Weaviate state.
  - Weaviate is the production search index. `publish_*` is best-
    effort: failures are logged and the call continues. The next
    backfill / re-publish picks up missed writes.
  - similarity_search prefers Weaviate when reachable, falls back to
    Python-side cosine over Mongo documents otherwise. Tests use the
    fallback because their fake WEAVIATE_URL fails to connect.

Weaviate v4 client is gRPC-based and async. Lazy-init: the first
call to `_get_weaviate_client` connects (or fails and caches None).
"""
import math
import os
import uuid as uuid_module
from typing import Any


# ---- Weaviate class names ----

TOOL_CLASS = "ToolEmbedding"
PROFILE_CLASS = "ProfileEmbedding"


# ---- Stable UUID derivation from app-level keys ----

def tool_uuid(slug: str) -> str:
    return str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, f"mesh-tool-{slug}"))


def profile_uuid(user_id: str) -> str:
    return str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, f"mesh-profile-{user_id}"))


# ---- Lazy client lifecycle ----

_client: Any = None
_init_attempted = False


async def _get_weaviate_client() -> Any:
    """Return a connected async Weaviate client, or None if Weaviate
    is unreachable / not configured / package missing.

    The result is cached: on failure, None is cached and we don't try
    again until `reset_weaviate_client_for_tests()` is called.

    F-LIVE-7: when env `WEAVIATE_USE_GRPC=false`, the client is
    constructed with `skip_init_checks=True` and a tiny gRPC port
    (still required by the v4 client signature, but never actually
    probed). All queries go over REST `/v1/graphql`. ~3× slower per
    query but works on networks where the gRPC subdomain is firewalled.
    """
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True

    url = os.environ.get("WEAVIATE_URL", "").strip()
    api_key = os.environ.get("WEAVIATE_API_KEY", "").strip()
    if not url or not api_key:
        return None

    use_grpc = os.environ.get("WEAVIATE_USE_GRPC", "true").strip().lower() != "false"

    try:
        import weaviate
        from weaviate.classes.init import Auth, AdditionalConfig, Timeout

        if not use_grpc:
            # REST-only mode: skip the gRPC health probe entirely.
            # Queries fall back to /v1/graphql automatically when the
            # client can't reach the gRPC port.
            print(
                "[vector_store] WEAVIATE_USE_GRPC=false; using REST-only "
                "mode (slower but works on networks that block gRPC)",
                flush=True,
            )
            client = weaviate.use_async_with_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
                skip_init_checks=True,
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=2, query=10, insert=10),
                ),
            )
        else:
            # init=8s — gRPC handshake under VPN takes 3–5 RTTs which
            # routinely exceeds 2s. Failure (no network / firewalled
            # gRPC) still caps at 8s instead of the v4 client's ~30s
            # default. The failure caches _client=None so subsequent
            # calls short-circuit without re-trying.
            client = weaviate.use_async_with_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=8, query=10, insert=10),
                ),
            )
        await client.connect()
        _client = client
        return _client
    except Exception as exc:
        print(f"[vector_store] weaviate connection failed: {exc}")
        _client = None
        return None


async def close_weaviate_client() -> None:
    """Close the Weaviate client at app shutdown."""
    global _client, _init_attempted
    if _client is not None:
        try:
            await _client.close()
        except Exception:
            pass
    _client = None
    _init_attempted = False


def reset_weaviate_client_for_tests() -> None:
    """Test helper: forget the cached client + init-attempted flag so
    a fresh test can re-probe."""
    global _client, _init_attempted
    _client = None
    _init_attempted = False


# ---- Schema bootstrap (called by `python -m app.embeddings init-weaviate`) ----

async def init_weaviate_schema() -> int:
    """Create the ToolEmbedding and ProfileEmbedding classes if they
    don't exist. Returns 0 on success, 2 if Weaviate is not
    reachable / configured."""
    client = await _get_weaviate_client()
    if client is None:
        print(
            "[init-weaviate] cannot reach Weaviate -- check WEAVIATE_URL "
            "and WEAVIATE_API_KEY in your .env",
            flush=True,
        )
        return 2

    try:
        from weaviate.classes.config import (
            Configure,
            DataType,
            Property,
            VectorDistances,
        )
    except ImportError as exc:
        print(f"[init-weaviate] weaviate-client import failed: {exc}")
        return 2

    created = []
    skipped = []

    schema_spec = [
        (
            TOOL_CLASS,
            [
                Property(name="slug", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
                Property(name="curation_status", data_type=DataType.TEXT),
                Property(name="labels", data_type=DataType.TEXT_ARRAY),
                # Cycle #15 hybrid-search BM25 surface (F-LIVE addendum):
                # full-text properties so the keyword side of hybrid
                # search has rich phrasing to match against.
                Property(name="name", data_type=DataType.TEXT),
                Property(name="tagline", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
            ],
        ),
        (
            PROFILE_CLASS,
            [
                Property(name="user_id", data_type=DataType.TEXT),
            ],
        ),
    ]

    extended: list[str] = []
    for cls_name, properties in schema_spec:
        if not await client.collections.exists(cls_name):
            await client.collections.create(
                name=cls_name,
                properties=properties,
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                ),
            )
            created.append(cls_name)
            continue

        # Class exists — additive migration: add any properties that
        # aren't there yet. Weaviate v4 supports add_property on a
        # live class without recreate / data loss.
        col = client.collections.use(cls_name)
        cfg = await col.config.get()
        existing_names = {p.name for p in (cfg.properties or [])}
        for prop in properties:
            if prop.name in existing_names:
                continue
            try:
                await col.config.add_property(prop)
                extended.append(f"{cls_name}.{prop.name}")
            except Exception as exc:
                print(
                    f"[init-weaviate] could not add {cls_name}.{prop.name}: {exc}",
                    flush=True,
                )
        skipped.append(cls_name)

    print(
        f"[init-weaviate] created: {created or '(none)'} | "
        f"already-existed: {skipped or '(none)'} | "
        f"properties added: {extended or '(none)'}",
        flush=True,
    )
    return 0


# ---- Publish / delete (best-effort writes) ----

async def _upsert(coll: Any, uid: str, properties: dict[str, Any], vector: list[float]) -> None:
    """True upsert by UUID: try insert first; on conflict, replace.

    Weaviate v4 splits the operation: `insert` raises if UUID exists;
    `replace` raises if UUID does NOT exist. Neither is upsert on its
    own. Try insert -> fall back to replace on any failure (which
    catches the "already exists" case).
    """
    try:
        await coll.data.insert(uuid=uid, properties=properties, vector=vector)
    except Exception:
        await coll.data.replace(uuid=uid, properties=properties, vector=vector)


async def publish_tool(
    *, slug: str, vector: list[float], properties: dict[str, Any]
) -> None:
    """Best-effort publish of a tool embedding to Weaviate. Silent skip
    on any failure (no Weaviate, network blip, etc.)."""
    client = await _get_weaviate_client()
    if client is None:
        return
    try:
        coll = client.collections.use(TOOL_CLASS)
        await _upsert(coll, tool_uuid(slug), properties, vector)
    except Exception as exc:
        print(f"[vector_store] publish_tool failed for {slug}: {exc}")


async def delete_tool(slug: str) -> None:
    """Best-effort delete from Weaviate."""
    client = await _get_weaviate_client()
    if client is None:
        return
    try:
        coll = client.collections.use(TOOL_CLASS)
        await coll.data.delete_by_id(uuid=tool_uuid(slug))
    except Exception as exc:
        print(f"[vector_store] delete_tool failed for {slug}: {exc}")


async def publish_profile(
    *, user_id: str, vector: list[float], properties: dict[str, Any]
) -> None:
    client = await _get_weaviate_client()
    if client is None:
        return
    try:
        coll = client.collections.use(PROFILE_CLASS)
        await _upsert(coll, profile_uuid(user_id), properties, vector)
    except Exception as exc:
        print(f"[vector_store] publish_profile failed for {user_id}: {exc}")


# ---- similarity_search ----

def _is_mongomock(coll: Any) -> bool:
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


async def _mongo_fallback_search(
    *,
    collection_name: str,
    query_vector: list[float],
    top_k: int,
    filters: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Python-side cosine fallback over Mongo documents. Used when
    Weaviate isn't reachable, OR in tests where mongomock-motor is
    the active client."""
    from app.db.mongo import get_db

    coll = get_db()[collection_name]
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


async def similarity_search(
    *,
    collection_name: str,
    query_vector: list[float],
    top_k: int = 10,
    filters: dict[str, Any] | None = None,
    weaviate_class: str | None = None,
) -> list[dict[str, Any]]:
    """Return top-k matching Mongo documents ranked by cosine similarity.

    Production path:
      1. Try Weaviate `near_vector` against `weaviate_class`. Returns
         a list of slugs / user_ids. Fetch full documents from Mongo
         via the corresponding identifier field.

    Fallback paths (any of the below triggers Mongo-side cosine):
      - mongomock-motor is the active Mongo client (test environment)
      - Weaviate is unreachable
      - `weaviate_class` is None

    `collection_name` is always the Mongo collection (`tools_seed` or
    `profiles`); `weaviate_class` is the corresponding Weaviate class
    (`ToolEmbedding` / `ProfileEmbedding`).
    """
    from app.db.mongo import get_db

    coll = get_db()[collection_name]

    # Test fallback: mongomock client.
    if _is_mongomock(coll):
        return await _mongo_fallback_search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )

    # Production: try Weaviate first.
    if weaviate_class is not None:
        client = await _get_weaviate_client()
        if client is not None:
            try:
                from weaviate.classes.query import Filter

                w_coll = client.collections.use(weaviate_class)
                wvw_filter = None
                if filters:
                    wvw_filter = _build_weaviate_filter(filters)
                resp = await w_coll.query.near_vector(
                    near_vector=query_vector,
                    limit=top_k,
                    filters=wvw_filter,
                )
                # Resolve back to Mongo docs by the identifier field.
                identifier = (
                    "slug" if collection_name == "tools_seed" else "user_id"
                )
                str_identifiers = [
                    obj.properties.get(identifier) for obj in resp.objects
                ]
                str_identifiers = [i for i in str_identifiers if i is not None]
                if not str_identifiers:
                    return []
                # Bug fix: profiles.user_id is stored as ObjectId in
                # Mongo but as TEXT in Weaviate. Convert back to
                # ObjectId for the Mongo query, otherwise $in matches
                # nothing and concierge_scan reports 0 matches even
                # when Weaviate found great hits.
                if collection_name == "profiles":
                    from bson import ObjectId
                    query_ids: list[Any] = []
                    for s in str_identifiers:
                        try:
                            query_ids.append(ObjectId(s))
                        except Exception:
                            continue
                else:
                    query_ids = list(str_identifiers)
                if not query_ids:
                    return []
                docs = await coll.find(
                    {identifier: {"$in": query_ids}}
                ).to_list(length=top_k)
                # Preserve Weaviate's similarity ranking. Match by the
                # original-string-form identifier (str(_id) for profiles).
                order = {s: i for i, s in enumerate(str_identifiers)}
                def _key(d: dict[str, Any]) -> int:
                    raw = d.get(identifier)
                    return order.get(str(raw) if raw is not None else "", 999)
                docs.sort(key=_key)
                return docs
            except Exception as exc:
                print(f"[vector_store] weaviate query failed, falling back: {exc}")

    # Production fallback if Weaviate unreachable or query failed.
    return await _mongo_fallback_search(
        collection_name=collection_name,
        query_vector=query_vector,
        top_k=top_k,
        filters=filters,
    )


def _build_weaviate_filter(filters: dict[str, Any]):
    """Translate a Mongo-style filter dict into a Weaviate v4 Filter
    expression. Supports equality on strings and `$in` on arrays."""
    from weaviate.classes.query import Filter

    expr = None
    for key, value in filters.items():
        if isinstance(value, dict) and "$in" in value:
            f = Filter.by_property(key).contains_any(value["$in"])
        else:
            f = Filter.by_property(key).equal(value)
        expr = f if expr is None else (expr & f)
    return expr


async def hybrid_search(
    *,
    weaviate_class: str,
    query: str,
    vector: list[float],
    alpha: float,
    limit: int,
    filters: dict[str, Any] | None = None,
) -> list[tuple[dict[str, Any], float]]:
    """F-LIVE-3: Weaviate v4 hybrid search (BM25 + vector cosine,
    alpha-blended).

    Returns `[(properties_dict, score)]` sorted descending by score.
    Returns `[]` when the Weaviate client is unreachable or the
    `weaviate_class` doesn't exist.

    `alpha` is the standard Weaviate convention:
      - 0.0 → pure BM25 (keyword)
      - 1.0 → pure vector (semantic)
      - 0.5 → balanced

    No Mongo hydrate — caller passes the slug list to its own
    Mongo lookup. This separates the search concern from the
    catalog hydrate concern (the live engine in cycle #15 needs to
    pair scores with full tool docs, while pure search callers
    might not).
    """
    client = await _get_weaviate_client()
    if client is None:
        return []
    try:
        coll = client.collections.use(weaviate_class)
        wvw_filter = _build_weaviate_filter(filters) if filters else None
        from weaviate.classes.query import MetadataQuery

        resp = await coll.query.hybrid(
            query=query,
            vector=vector,
            alpha=alpha,
            limit=limit,
            filters=wvw_filter,
            return_metadata=MetadataQuery(score=True),
        )
        results: list[tuple[dict[str, Any], float]] = []
        for obj in resp.objects:
            props = dict(obj.properties or {})
            score = 0.0
            try:
                score = float(obj.metadata.score) if obj.metadata else 0.0
            except (AttributeError, TypeError, ValueError):
                pass
            results.append((props, score))
        return results
    except Exception as exc:
        print(f"[vector_store] hybrid_search failed: {exc}")
        return []
