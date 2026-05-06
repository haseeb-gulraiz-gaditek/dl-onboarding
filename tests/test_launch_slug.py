"""Tests for slug derivation (cycle: founder-launch-...).

Covers F-LAUNCH-6 (derive_tool_slug + cross-collection collision).
"""
import pytest

from app.launches.slug import derive_tool_slug, find_available_slug


# ---- Pure derivation ----


def test_derive_strips_www_and_tld():
    """Cycle #14 F-LAUNCH-7: noise-prefix + TLD stripping.

    `www.` is in the noise-prefix list and the trailing `.io` is the
    TLD, so https://www.acme.io reduces to "acme"."""
    assert derive_tool_slug("https://www.acme.io") == "acme"


def test_derive_lowercases_and_kebab_cases():
    """Subdomain becomes a kebab segment after TLD strip:
    Acme_Tools.io → acme-tools (TLD `.io` stripped)."""
    assert derive_tool_slug("https://Acme_Tools.io/about") == "acme-tools"


def test_derive_collapses_runs_and_strips():
    """Same TLD-strip rule applies; runs of dashes collapse."""
    assert derive_tool_slug("https://---acme---.io---") == "acme"


def test_derive_falls_back_when_host_missing():
    slug = derive_tool_slug("not-a-url")
    assert slug.startswith("launch-")


# ---- Collision scan (cross-collection) ----


@pytest.mark.asyncio
async def test_no_collision_returns_base(app_client):
    slug = await find_available_slug("brand-new-slug")
    assert slug == "brand-new-slug"


@pytest.mark.asyncio
async def test_collision_in_tools_seed_forces_suffix(
    app_client, seed_test_catalog
):
    """seed_test_catalog inserts test-tool-approved among others."""
    slug = await find_available_slug("test-tool-approved")
    assert slug == "test-tool-approved-2"


@pytest.mark.asyncio
async def test_collision_in_tools_founder_launched_forces_suffix(app_client):
    """F-LAUNCH-6: collision in the founder collection ALSO forces a
    suffix (cross-collection scan)."""
    from app.db.tools_founder_launched import insert as insert_fl_tool

    await insert_fl_tool({
        "slug": "occupied",
        "name": "Occupied",
        "tagline": "x",
        "description": "y",
        "url": "https://occupied.dev",
        "pricing_summary": "Free",
        "category": "automation_agents",
        "labels": ["new"],
        "source": "founder_launch",
        "launched_via_id": None,
    })
    slug = await find_available_slug("occupied")
    assert slug == "occupied-2"
