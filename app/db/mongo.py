"""MongoDB client lifecycle.

Reads MONGODB_URI and MONGODB_DB from the environment. The client is
created on app startup (via FastAPI lifespan) and closed on shutdown.
Routers obtain the database handle through get_db().

Mesh V1 supports three connection paths, all routed through MONGODB_URI:
  - MongoDB Atlas free tier (recommended; no local install)
  - Local mongod install (mongodb://localhost:27017)
  - Optional docker-compose stack (mongodb://localhost:27017)
"""
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_mongo() -> None:
    """Initialize the global Motor client.

    Idempotent: if `_client` is already set (e.g., a test fixture
    injected a mongomock client before lifespan ran), this is a
    no-op.
    """
    global _client, _db
    if _client is not None:
        return
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Copy .env.example to .env and "
            "configure it. Easiest path: a free MongoDB Atlas cluster."
        )
    db_name = os.environ.get("MONGODB_DB", "mesh")
    _client = AsyncIOMotorClient(uri)
    _db = _client[db_name]


async def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "Mongo client is not initialized. Ensure the FastAPI "
            "lifespan ran init_mongo() before this call."
        )
    return _db
