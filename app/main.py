"""Mesh FastAPI application entrypoint.

Wires the Mongo lifecycle to the FastAPI app via lifespan. Routers
are mounted from app.api as they land in subsequent cycles.
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.db.mongo import close_mongo, init_mongo


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongo()
    try:
        yield
    finally:
        await close_mongo()


app = FastAPI(
    title="Mesh",
    description="Context-graph launch platform for AI tools.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
