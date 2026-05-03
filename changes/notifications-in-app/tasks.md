# Tasks: notifications-in-app

## Implementation Checklist

### DB layer
- [ ] `app/db/notifications.py` — extend with read helpers: `find_by_id(notification_id)`, `list_for_user(user_id, unread_only?, before?, limit)`, `count_unread(user_id)`, `find_latest_unread_banner(user_id)`, `mark_read(user_id, notification_id) -> bool`, `mark_all_read(user_id) -> int`. Existing `insert(user_id, kind, payload)` unchanged.

### Pydantic models
- [ ] `app/models/notification.py` — `NotificationCard` (id, kind, payload, read: bool, created_at), `NotificationListResponse` (notifications: list, next_before: datetime | None), `UnreadCountResponse` (count: int), `BannerResponse` (notification: NotificationCard | None), `MarkReadResponse` (updated: bool), `MarkAllReadResponse` (updated: int)

### Endpoints
- [ ] `app/api/me_notifications.py` — five GET/POST endpoints behind `current_user`:
  - `GET /api/me/notifications` (?unread_only, ?before, ?limit)
  - `GET /api/me/notifications/unread-count`
  - `GET /api/me/notifications/banner`
  - `POST /api/me/notifications/{id}/read` (404 on non-owner)
  - `POST /api/me/notifications/read-all`

### Wiring
- [ ] Mount router in `app/main.py`

### community_reply trigger (F-NOTIF-7 / F-COM-5 MODIFIED)
- [ ] `app/api/comments.py` — after the existing `insert_comment` + `bump_comment_count`, look up parent post; if `post.author_user_id != commenter`, call `notifications.insert(user_id=post.author_user_id, kind="community_reply", payload={post_id, comment_id, commenter_display_name})`. Wrap in try/except; log + swallow any exception.

### Tests
- [ ] F-NOTIF-2: list returns rows newest-first; ?unread_only filter narrows; ?before cursor pagination works
- [ ] F-NOTIF-2: list scoped to requesting user (other users' notifications never appear)
- [ ] F-NOTIF-2: empty list returns {notifications: [], next_before: null}
- [ ] F-NOTIF-2: response shape projects `read: bool` not the timestamp
- [ ] F-NOTIF-3: unread-count returns the integer; matches list ?unread_only count
- [ ] F-NOTIF-3: 0 when user has no unread
- [ ] F-NOTIF-4: banner returns the most-recent unread concierge_nudge
- [ ] F-NOTIF-4: banner returns {notification: null} when user has no unread nudges
- [ ] F-NOTIF-4: banner SKIPS read concierge_nudges (only unread)
- [ ] F-NOTIF-4: banner does NOT return community_reply or launch_approved (only concierge_nudge)
- [ ] F-NOTIF-5: mark-single sets read_at on first POST, returns {updated: true}
- [ ] F-NOTIF-5: re-marking the same row returns {updated: false} (idempotent)
- [ ] F-NOTIF-5: marking another user's notification → 404 notification_not_found (existence leak protection)
- [ ] F-NOTIF-5: malformed id → 404
- [ ] F-NOTIF-6: read-all updates all unread rows, returns {updated: N} matching count
- [ ] F-NOTIF-6: subsequent read-all returns {updated: 0}
- [ ] F-NOTIF-7: comment on someone else's post writes a community_reply notification with correct payload
- [ ] F-NOTIF-7: self-reply (commenter == post author) does NOT write a notification
- [ ] F-NOTIF-7: comment write succeeds even if the notification write would fail (trigger is best-effort; covered by patching insert to raise)
- [ ] Inbox is role-agnostic: founder reading /api/me/notifications sees their launch_approved/launch_rejected rows; user reading sees concierge_nudge/community_reply rows

### Conftest updates
- [ ] `seed_notification(user_id, kind, payload?, read=False)` helper for the inbox tests so we don't have to invoke publish_launch every test

## Validation

- [ ] All implementation tasks above checked off
- [ ] Full test suite green (cycles #1–#11 must continue to pass)
- [ ] Smoke (user side): Maya signs up, gets nudged via cycle #9 fan-out; GET /api/me/notifications shows the nudge; GET /api/me/notifications/banner returns it; POST .../read; subsequent banner returns null
- [ ] Smoke (founder side): Aamir signs up, submits launch, admin approves; GET /api/me/notifications shows the launch_approved row
- [ ] Smoke (community_reply): Maya posts a comment on Sam's post; GET /api/me/notifications as Sam shows a community_reply with payload.commenter_display_name == "maya"
- [ ] Spec-delta scenarios verifiably hold in implementation
- [ ] No constitutional regression: notifications NEVER expose another user's unread state; mark-read on non-owner row → 404 (no existence leak); founder posts cannot trigger community_reply notifications because founders are 403'd from POST /api/comments at the route layer
