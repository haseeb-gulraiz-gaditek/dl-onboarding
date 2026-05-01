"""Async wrapper around OpenAI's text-embedding-3-small.

V1 contract: one entry point (`embed_text`), one model, one
dimensionality. The OpenAI SDK reads `OPENAI_API_KEY` from the env
at client-construction time.

The client is lazy-constructed and reused process-wide so we don't
re-init the HTTP pool per call. Tests monkey-patch `embed_text`
directly via the `mock_openai_embed` fixture (see tests/conftest.py)
so this module is never actually called against the real API in CI.
"""
from openai import AsyncOpenAI


MODEL = "text-embedding-3-small"
DIMENSIONS = 1536


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


async def embed_text(text: str) -> list[float]:
    """Return a 1536-dimensional embedding for the given text.

    Raises `ValueError` on empty / whitespace-only input.
    Propagates OpenAI SDK exceptions on API failure -- callers
    decide whether to swallow (graceful degradation per F-EMB-2)
    or surface.
    """
    if not text or not text.strip():
        raise ValueError("embed_text: empty text")
    client = _get_client()
    resp = await client.embeddings.create(model=MODEL, input=text)
    return resp.data[0].embedding
