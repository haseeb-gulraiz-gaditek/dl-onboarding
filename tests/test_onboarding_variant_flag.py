"""F-LIVE-9: MESH_ONBOARDING_VARIANT env flag plumbed through /api/me."""
import os
import pytest

from tests.conftest import auth_header, signup_user


pytestmark = pytest.mark.asyncio


async def test_me_returns_classic_by_default(app_client, monkeypatch):
    monkeypatch.delenv("MESH_ONBOARDING_VARIANT", raising=False)
    u = await signup_user(app_client, "v1@example.com")
    r = await app_client.get("/api/me", headers=auth_header(u["jwt"]))
    assert r.status_code == 200
    assert r.json()["onboarding_variant"] == "classic"


async def test_me_returns_live_when_env_set(app_client, monkeypatch):
    monkeypatch.setenv("MESH_ONBOARDING_VARIANT", "live")
    u = await signup_user(app_client, "v2@example.com")
    r = await app_client.get("/api/me", headers=auth_header(u["jwt"]))
    assert r.status_code == 200
    assert r.json()["onboarding_variant"] == "live"


async def test_me_unknown_value_falls_back_to_classic(app_client, monkeypatch):
    monkeypatch.setenv("MESH_ONBOARDING_VARIANT", "experimental_v9")
    u = await signup_user(app_client, "v3@example.com")
    r = await app_client.get("/api/me", headers=auth_header(u["jwt"]))
    assert r.status_code == 200
    assert r.json()["onboarding_variant"] == "classic"
