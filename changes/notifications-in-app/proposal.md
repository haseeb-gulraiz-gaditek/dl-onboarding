# Proposal: notifications-in-app

## Problem

Cycle #8 created the `notifications` collection and started writing rows on launch approve/reject. Cycle #9 added `concierge_nudge` writes when the publish orchestrator scans profiles. But the inbox is write-only — Maya gets nudged about a launch that matches her profile and the system has no way for her to *see* it. Aamir gets approved/rejected and has no inbox.

This cycle gives every authenticated user (founder OR user) a read surface over the rows that are already being written:

- **Bell badge** — `{count: int}` for the unread total.
- **List** — paginated newest-first feed with optional unread-only filter.
- **Top banner** — the single most-recent unread nudge (the "high-signal launch matched your profile" surface from the system_design); dedicated endpoint so the client doesn't have to filter.
- **Mark read** — single + all.

Plus one new write trigger: `community_reply` notifications on `POST /api/comments` when the comment is on a post whose author is someone other than the commenter.

The inbox is role-agnostic: each user reads their own notifications regardless of `role_type`. Founders see launch_approved/rejected; users see concierge_nudge + community_reply.

## Solution

**5 read endpoints** (all behind `current_user`):
- `GET /api/me/notifications` — paginated list, `?unread_only=true&before=&limit=` cursor on `created_at`.
- `GET /api/me/notifications/unread-count` — `{count: int}`.
- `GET /api/me/notifications/banner` — most recent unread `concierge_nudge` row or `null`. Dedicated endpoint so banner UX doesn't roundtrip + filter.
- `POST /api/me/notifications/{id}/read` — mark single. Idempotent (re-reading is a no-op). 404 if not the user's row (no existence leak).
- `POST /api/me/notifications/read-all` — bulk mark; returns `{updated: int}`.

**1 new write trigger** (cycle #7 MODIFIED):
- `app/api/comments.py POST /api/comments` writes a `community_reply` notification to the post's author when `comment.author_user_id != post.author_user_id`. Best-effort — failure does NOT abort the comment write.

**Naming-collision documentation:** cycle #9's `concierge_nudge` IS the `launch_match` notification described in the backlog. We keep the cycle #9 wire name (`concierge_nudge`) to avoid a migration; this cycle's spec documents the synonym.

**Deferred kinds (reserved enum values, no V1 triggers):**
- `new_recommendation` — needs a weekly scheduler that doesn't exist in V1.
- `system` — needs an admin broadcast endpoint; defer to a future operational cycle.

## Scope

**In:**
- 5 read endpoints + 1 write trigger.
- Pydantic schemas: `NotificationCard`, `NotificationListResponse`, `UnreadCountResponse`, `BannerResponse`, `MarkReadResponse`.
- Helpers in `app/db/notifications.py`: `list_for_user(user_id, unread_only?, before?, limit)`, `count_unread(user_id)`, `find_by_id(id)`, `mark_read(user_id, notification_id) -> bool`, `mark_all_read(user_id) -> int`, `find_latest_unread_banner(user_id)`.
- Tests F-NOTIF-1..7 covering listing, paginating, unread-count, banner selection, mark-read happy/idempotent/non-owner, role-agnostic surface, community_reply trigger.

**Out:**
- `new_recommendation` trigger (no scheduler in V1).
- `system` broadcast endpoint (no admin write surface in V1).
- Email digests (V1.5+).
- Browser push (V1.5+).
- Real-time websockets (polling is fine for V1).
- Notification preferences / user settings (V1.5+).
- Frontend bell + dropdown component (parallel React track).

## Risks

1. **Self-reply notifications.** A user commenting on their own post should NOT get notified. Trigger checks `comment.author_user_id != post.author_user_id` before writing. Tested.
2. **Banner endpoint over-fires.** If a user has unread nudges from multiple launches, the banner returns only the most recent. Older unread nudges are still visible in the list, just not banner-promoted. Documented.
3. **Mark-read existence-leak.** `POST /api/me/notifications/{id}/read` for someone else's notification returns `404 notification_not_found` (mirrors cycle #8/#11 pattern). Tests assert this.
4. **Comment-trigger failure cascading.** The trigger is best-effort: an exception in the notification write must NOT abort the comment write. Wrapped in try/except + logged.
5. **Notification volume on noisy threads.** A post with 50 comments creates 50 notifications for the post's author. V1 doesn't dedupe or roll-up. Acceptable trade-off for demo; V1.5 can group.
6. **Role-agnostic semantics.** A founder's "inbox" mixes business kinds (launch_approved) with social ones (community_reply if they ever participated as a user — they can't, since they're 403'd from posting). In practice, founders only see launch_* kinds; users only see concierge_nudge + community_reply. Documented.
