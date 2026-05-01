"""F-QB-5: founder accounts cannot have profiles.

Defense-in-depth audit: even if a future handler is mounted without
require_role("user"), the helper layer still rejects founder accounts
with ValueError. This test guards that contract directly.
"""
import pytest

from app.db.profiles import get_or_create_profile


pytestmark = pytest.mark.asyncio


async def test_get_or_create_profile_rejects_founder(app_client):
    fake_founder = {
        "_id": "deadbeef" * 3,  # any ObjectId-like value; profile path won't be exercised
        "email": "aamir@example.com",
        "role_type": "founder",
    }
    with pytest.raises(ValueError, match="user-role only"):
        await get_or_create_profile(fake_founder)


async def test_get_or_create_profile_rejects_unknown_role(app_client):
    """Defensive: any role_type other than "user" is rejected."""
    fake_admin = {
        "_id": "deadbeef" * 3,
        "email": "admin@example.com",
        "role_type": "admin",
    }
    with pytest.raises(ValueError, match="user-role only"):
        await get_or_create_profile(fake_admin)
