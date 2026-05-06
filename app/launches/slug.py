"""Slug derivation for founder-launched tools.

Per spec-delta founder-launch-submission-and-verification F-LAUNCH-6.

Algorithm:
  1. Parse host from product_url, strip leading "www."
  2. Lowercase. Replace any character outside [a-z0-9-] with "-".
     Collapse repeated "-". Strip leading/trailing "-".
  3. If empty after normalization, fall back to "launch-{epoch}".
  4. Cross-collection collision check: scan tools_seed AND
     tools_founder_launched. If neither has the slug, return it.
  5. Suffix -2, -3, ..., -99. If exhausted, raise.
"""
import re
import time
from urllib.parse import urlparse

from app.db.tools_founder_launched import find_by_slug as fl_find_by_slug
from app.db.tools_seed import find_tool_by_slug


MAX_SLUG_SUFFIX = 99


_SLUG_INVALID_RE = re.compile(r"[^a-z0-9-]+")
_DASH_RUN_RE = re.compile(r"-{2,}")

# Common app/marketing subdomain prefixes that are not part of the
# product name. Stripped before we consider the host for slug/name.
_NOISE_SUBDOMAINS = (
    "www.", "app.", "my.", "go.", "try.", "get.",
    "dashboard.", "admin.", "portal.", "beta.", "staging.",
)


def derive_tool_slug(product_url: str) -> str:
    """Pure synchronous: URL → normalized slug base. No DB scan.

    Examples:
      https://app.contentplanner.site/foo  →  contentplanner
      https://notion.so                    →  notion
      https://www.zapier.com               →  zapier
      https://blog.example.io              →  blog-example
    """
    parsed = urlparse(product_url.strip())
    host = (parsed.hostname or "").lower()

    # Strip noise prefixes (idempotently — handles www.app.foo.com).
    changed = True
    while changed:
        changed = False
        for prefix in _NOISE_SUBDOMAINS:
            if host.startswith(prefix):
                host = host[len(prefix):]
                changed = True
                break

    # Strip the TLD (last dot-segment) so names don't end in -com/-site/-io.
    if "." in host:
        host = host.rsplit(".", 1)[0]

    if not host:
        return f"launch-{int(time.time())}"

    # Replace invalid chars (including remaining dots) with "-",
    # collapse runs, strip ends.
    slug = _SLUG_INVALID_RE.sub("-", host)
    slug = _DASH_RUN_RE.sub("-", slug).strip("-")
    if not slug:
        return f"launch-{int(time.time())}"
    return slug


async def _slug_taken(slug: str) -> bool:
    if await find_tool_by_slug(slug) is not None:
        return True
    if await fl_find_by_slug(slug) is not None:
        return True
    return False


async def find_available_slug(base: str) -> str:
    """Take a base slug, return an actually-available slug. Raises
    RuntimeError if all -2..-99 variants are taken."""
    if not await _slug_taken(base):
        return base
    for n in range(2, MAX_SLUG_SUFFIX + 1):
        candidate = f"{base}-{n}"
        if not await _slug_taken(candidate):
            return candidate
    raise RuntimeError(
        f"slug exhausted: {base} and {base}-2..{base}-{MAX_SLUG_SUFFIX} all taken"
    )
