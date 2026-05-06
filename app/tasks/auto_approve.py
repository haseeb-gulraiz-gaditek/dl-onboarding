"""Auto-approver background task — DEMO / TESTING ONLY.

Polls the launches collection every 30s for `verification_status:
pending` rows older than `after_seconds`, and approves them via the
same service path as the admin UI.

Enable with env `AUTO_APPROVE_LAUNCHES_AFTER_SECONDS=60` (or any
positive int). Default 0 = task never starts.

Why a background task instead of admin auto-clicking:
  - Tester hits POST /api/founders/launch and immediately wants to
    see the downstream pipeline (community fan-out, concierge nudges,
    /home reach summary). Manual admin approval blocks the demo.
  - Production keeps this OFF (default). Real launches always require
    a human review.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.launches import launches_collection
from app.launches.approve import (
    LaunchAlreadyResolved,
    LaunchNotFound,
    approve_launch,
)


POLL_INTERVAL_SECONDS = 30
REVIEWED_BY = "auto-approver@mesh.local"


async def _find_due_pending(after_seconds: int) -> list[dict[str, Any]]:
    """Return pending launches submitted at least `after_seconds` ago."""
    threshold = datetime.now(timezone.utc) - timedelta(seconds=after_seconds)
    cursor = launches_collection().find({
        "verification_status": "pending",
        "created_at": {"$lte": threshold},
    })
    return await cursor.to_list(length=50)


async def _tick(after_seconds: int) -> int:
    """One pass — returns the count of launches approved this tick."""
    due = await _find_due_pending(after_seconds)
    approved = 0
    for launch in due:
        launch_id = launch["_id"]
        try:
            await approve_launch(
                launch_id=launch_id, reviewed_by=REVIEWED_BY,
            )
            approved += 1
            print(
                f"[auto-approver] approved launch {launch_id} "
                f"(submitted by {launch.get('founder_user_id')})",
                flush=True,
            )
        except LaunchNotFound:
            # Race: another caller deleted the row.
            continue
        except LaunchAlreadyResolved:
            # Race: admin manually approved/rejected between our find
            # and our approve call. That's fine.
            continue
        except Exception as exc:
            print(
                f"[auto-approver] approve failed for {launch_id}: {exc}",
                flush=True,
            )
    return approved


async def run_auto_approver_loop(*, after_seconds: int) -> None:
    """Long-running coroutine. Cancelled on app shutdown."""
    print(
        f"[auto-approver] running every {POLL_INTERVAL_SECONDS}s; "
        f"approving pending launches older than {after_seconds}s",
        flush=True,
    )
    while True:
        try:
            await _tick(after_seconds)
        except Exception as exc:
            # Never let a bad tick kill the loop.
            print(f"[auto-approver] tick raised: {exc}", flush=True)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
