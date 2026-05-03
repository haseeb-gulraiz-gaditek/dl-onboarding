# Tasks: notifications-in-app

## Implementation Checklist

### DB layer
- [x] `app/db/notifications.py` — extend with read helpers: `find_by_id(notification_id)`, `list_for_user(user_id, unread_only?, before?, limit)`, `count_unread(user_id)`, `find_latest_unread_banner(user_id)`, `mark_read(user_id, notification_id) -> bool`, `mark_all_read(user_id) -> int`. Existing `insert(user_id, kind, payload)` unchanged.

### Pydantic models
- [x] `app/models/notification.py` — `NotificationCard` (id, kind, payload, read: bool, created_at), `NotificationListResponse` (notifications: list, next_before: datetime | None), `UnreadCountResponse` (count: int), `BannerResponse` (notification: NotificationCard | None), `MarkReadResponse` (updated: bool), `MarkAllReadResponse` (updated: int)

### Endpoints
- [x] `app/api/me_notifications.py` — five GET/POST endpoints behind `current_user`:
  - `GET /api/me/notifications` (?unread_only, ?before, ?limit)
  - `GET /api/me/notifications/unread-count`
  - `GET /api/me/notifications/banner`
  - `POST /api/me/notifications/{id}/read` (404 on non-owner)
  - `POST /api/me/notifications/read-all`

### Wiring
- [x] Mount router in `app/main.py`

### community_reply trigger (F-NOTIF-7 / F-COM-5 MODIFIED)
- [x] `app/api/comments.py` — after the existing `insert_comment` + `bump_comment_count`, look up parent post; if `post.author_user_id != commenter`, call `notifications.insert(user_id=post.author_user_id, kind="community_reply", payload={post_id, comment_id, commenter_display_name})`. Wrap in try/except; log + swallow any exception.

### Tests
- [x] F-NOTIF-2: list returns rows newest-first; ?unread_only filter narrows; ?before cursor pagination works
- [x] F-NOTIF-2: list scoped to requesting user (other users' notifications never appear)
- [x] F-NOTIF-2: empty list returns {notifications: [], next_before: null}
- [x] F-NOTIF-2: response shape projects `read: bool` not the timestamp
- [x] F-NOTIF-3: unread-count returns the integer; matches list ?unread_only count
- [x] F-NOTIF-3: 0 when user has no unread
- [x] F-NOTIF-4: banner returns the most-recent unread concierge_nudge
- [x] F-NOTIF-4: banner returns {notification: null} when user has no unread nudges
- [x] F-NOTIF-4: banner SKIPS read concierge_nudges (only unread)
- [x] F-NOTIF-4: banner does NOT return community_reply or launch_approved (only concierge_nudge)
- [x] F-NOTIF-5: mark-single sets read_at on first POST, returns {updated: true}
- [x] F-NOTIF-5: re-marking the same row returns {updated: false} (idempotent)
- [x] F-NOTIF-5: marking another user's notification → 404 notification_not_found (existence leak protection)
- [x] F-NOTIF-5: malformed id → 404
- [x] F-NOTIF-6: read-all updates all unread rows, returns {updated: N} matching count
- [x] F-NOTIF-6: subsequent read-all returns {updated: 0}
- [x] F-NOTIF-7: comment on someone else's post writes a community_reply notification with correct payload
- [x] F-NOTIF-7: self-reply (commenter == post author) does NOT write a notification
- [x] F-NOTIF-7: comment write succeeds even if the notification write would fail (trigger is best-effort; covered by patching insert to raise)
- [x] Inbox is role-agnostic: founder reading /api/me/notifications sees their launch_approved/launch_rejected rows; user reading sees concierge_nudge/community_reply rows

### Conftest updates
- [x] `seed_notification(user_id, kind, payload?, read=False)` helper for the inbox tests so we don't have to invoke publish_launch every test

## Validation

- [x] All implementation tasks above checked off
- [x] Full test suite green: 276 passing (256 prior + 20 new for cycle #12)
- [x] User-side smoke: covered by `test_banner_returns_latest_unread_concierge_nudge` + `test_mark_read_first_call_returns_updated` + `test_banner_returns_null_when_none_unread` (full nudge → banner → mark-read → empty banner cycle)
- [x] Founder-side smoke: covered by `test_inbox_role_agnostic_for_founder` (founder reads `/api/me/notifications` and sees their `launch_approved` row)
- [x] community_reply smoke: covered by `test_comment_on_others_post_writes_community_reply_notification` (asserts payload.commenter_display_name == "maya" on Sam's notification after Maya comments on his post)
- [x] Spec-delta scenarios verifiably hold in implementation (F-NOTIF-2..7 each have at least one Given/When/Then-aligned test)
- [x] No constitutional regression: `test_list_scoped_to_self` enforces no cross-user reads; `test_mark_read_other_users_notification_returns_404` enforces existence-leak protection; cycle #7's `test_founder_cannot_comment` (still passing) means founders can't trigger community_reply because they're 403'd at the route — verified at the route layer above the trigger
