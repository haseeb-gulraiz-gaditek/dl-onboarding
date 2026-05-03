# Spec Delta: notifications-in-app

## ADDED

### F-NOTIF-1 — Notification kinds (V1 enum + naming reconciliation)

The `notifications.kind` field accepts the following values in V1:

| Kind | Written by | Trigger |
|---|---|---|
| `launch_approved` | cycle #8 F-LAUNCH-4 | admin approves a founder's launch |
| `launch_rejected` | cycle #8 F-LAUNCH-5 | admin rejects a founder's launch |
| `concierge_nudge` | cycle #9 F-PUB-2 | publish orchestrator scans profiles, top-5 matched users get one |
| `community_reply` | this cycle (F-NOTIF-7) | another user comments on a post you authored |
| `new_recommendation` | RESERVED | no V1 trigger; needs a weekly scheduler (deferred) |
| `system` | RESERVED | no V1 trigger; needs an admin broadcast endpoint (deferred) |

> **Naming note:** the system_design draft and backlog item #12 refer to a `launch_match` kind. That is the same notification as cycle #9's `concierge_nudge` — same trigger (top-5 profile match by similarity to launch ICP), same payload shape. We keep the cycle #9 wire name (`concierge_nudge`) to avoid a data migration; `launch_match` is a documentation synonym only.

Reserved kinds are valid in the schema but no V1 code path writes them. Future cycles add the triggers; the inbox endpoints already pass them through unchanged.

---

### F-NOTIF-2 — `GET /api/me/notifications` (list)

Behind `current_user`. Role-agnostic — the user reads their own notifications regardless of `role_type`.

Query params:
- `unread_only`: `true` filters to `read_at: null` rows. Default `false`.
- `before`: cursor on `created_at` (ISO 8601). Returns rows with `created_at < before`.
- `limit`: 1..50, default 20.

Sort: `created_at DESC` with `_id DESC` tie-breaker.

Response:
```json
{
  "notifications": [
    {
      "id": "<oid>",
      "kind": "concierge_nudge",
      "payload": {"launch_id": "...", "tool_slug": "..."},
      "read": false,
      "created_at": "2026-05-03T..."
    }
  ],
  "next_before": "2026-05-03T..."
}
```

`read` is a boolean projection of `read_at != null` (no need to ship the timestamp to clients). `next_before` is `null` on the last page.

**Unauthenticated** → `401 auth_required`.

---

### F-NOTIF-3 — `GET /api/me/notifications/unread-count`

Behind `current_user`. Returns the badge count.

Response: `{"count": 4}`.

`count` is `notifications.count_documents({user_id, read_at: null})`. Backed by the `(user_id, created_at DESC)` index from cycle #8 — Mongo can use the user_id prefix.

---

### F-NOTIF-4 — `GET /api/me/notifications/banner`

Behind `current_user`. Returns the most recent unread `concierge_nudge` row, or `null` if none exist.

Response (when one exists):
```json
{
  "notification": {
    "id": "<oid>",
    "kind": "concierge_nudge",
    "payload": {"launch_id": "...", "tool_slug": "..."},
    "read": false,
    "created_at": "..."
  }
}
```

Response (none):
```json
{ "notification": null }
```

> **Why a dedicated endpoint:** the system_design specifies "top banner on app open" UX. A dedicated endpoint avoids the client having to fetch the full list and filter — the banner check is a single, cheap query that doesn't paginate.

Other kinds (`community_reply`, `launch_approved`, etc.) NEVER appear in the banner — they show up as bell-only notifications via the list endpoint.

---

### F-NOTIF-5 — `POST /api/me/notifications/{id}/read` (mark single)

Behind `current_user`. Idempotent.

**Given** a notification row exists with `(_id == id, user_id == self)`
**When** the user POSTs to mark it read
**Then** the system sets `read_at = now()` (only if currently null) and returns `200 OK` with `{updated: true}`.

**Given** the row exists but `read_at` is already set (already read)
**When** the user POSTs again
**Then** the system returns `200 OK` with `{updated: false}` (idempotent — no overwrite of an earlier read timestamp).

**Given** the row does not exist OR belongs to another user
**Then** the system returns `404 notification_not_found` (existence-leak protection; mirrors cycles #8/#11 pattern).

**Malformed id** → `404 notification_not_found`.

---

### F-NOTIF-6 — `POST /api/me/notifications/read-all`

Behind `current_user`. Bulk mark all of the user's unread notifications as read.

Empty request body. Returns `{"updated": N}` where N is the count of rows updated (i.e., previously had `read_at: null`). Already-read rows are skipped (no overwrite).

---

### F-NOTIF-7 — `community_reply` write trigger (F-COM-5 MODIFIED)

`POST /api/comments` (cycle #7 F-COM-5) gains a best-effort hook after the existing comment insert + post counter bumps:

**Given** an authenticated user posts a comment on a post
**When** the comment is persisted
**Then** the system:

1. Looks up the parent post via `find_post_by_id(comment.post_id)`.
2. If `post.author_user_id != comment.author_user_id`, writes a `notifications` row:
   ```
   {
     user_id: post.author_user_id,
     kind: "community_reply",
     payload: {post_id: <oid>, comment_id: <oid>, commenter_display_name: <string>},
     read_at: null,
     created_at: now()
   }
   ```
3. If `post.author_user_id == comment.author_user_id` (self-reply), NO notification is written.
4. Best-effort: any failure inside the trigger is logged and swallowed; the comment write is NEVER aborted.

The `payload.commenter_display_name` field includes the commenter's display name to render the bell entry as "Maya commented on your post" without a follow-up lookup. This is NOT an anonymization breach — the post's author already sees the commenter's name on the post detail surface (cycle #7 F-COM-4). Notification carries the same visibility, no more, no less.

## MODIFIED

### F-COM-5 — `POST /api/comments` (cycle #7)

**Before:** F-COM-5 inserts a comment row and bumps `posts.comment_count` + `posts.last_activity_at`.

**After:** After the existing persistence, the F-NOTIF-7 trigger runs. The hook is best-effort and does NOT affect the response shape, status code, or error handling of `POST /api/comments`. Self-reply comments do NOT generate a notification.

The response shape of `POST /api/comments` is unchanged.

## REMOVED

(None.)
