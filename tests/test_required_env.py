"""F-EMB-1 + cycle #1/#3 contract: app refuses to boot without
required env vars.

Each parameterized test deletes ONE required env var and asserts
that the FastAPI lifespan refuses to start with a clear error
message naming the missing var.
"""
import pytest

from app.main import app, lifespan


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "missing_var",
    [
        "MONGODB_URI",
        "JWT_SECRET",
        "ADMIN_EMAILS",
        "OPENAI_API_KEY",
        "WEAVIATE_URL",
        "WEAVIATE_API_KEY",
    ],
)
async def test_missing_required_env_raises_at_boot(monkeypatch, missing_var):
    monkeypatch.delenv(missing_var, raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        async with lifespan(app):
            pass
    # The error message names the specific missing var.
    assert missing_var in str(exc_info.value)
