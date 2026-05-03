# Feature: In-App Notifications Inbox

> **Cycle of origin:** `notifications-in-app` (archived; see `archive/notifications-in-app/`)
> **Last reviewed:** 2026-05-03
> **Constitution touchpoints:** `principles.md` We Always #2 (*"Treat the user's profile as theirs"* — notifications are a per-user inbox; non-owner reads/writes always 404, never confirm existence); We Never #2 (*"Never let founder accounts post in user communities"* — community_reply trigger inherits cycle #7's route gate, so founders can't fire it).
> **Builds on:** `auth-role-split` (`current_user`), `founder-launch-submission-and-verification` (the `notifications` collection + `launch_approved` / `launch_rejected` writes), `launch-publish-and-concierge-nudge` (`concierge_nudge` writes), `communities-and-flat-comments` (`POST /api/comments` gains the `community_reply` trigger).

> **Read surface over an existing collection.** This cycle adds NO new collections — it reads what cycles #8 and #9 are already writing, plus one new write trigger inside cycle #7's comment endpoint.

---

## Intent

Cycle #8 created the `notifications` collection. Cycles #8 and #9 wrote rows into it (launch_approved, launch_rejected, concierge_nudge). But the inbox was write-only — nudged users had no way to see why or to dismiss; approved founders had no place to learn the system said yes.

Cycle #12 closes that gap with five read endpoints behind `current_user`. The inbox is **role-agnostic**: every authenticated user reads their own notifications regardless of `role_type`. Founders see launch_approved/launch_rejected; users see concierge_nudge + community_reply. Neither sees the other's, and non-owner reads always 404.

Plus one new write trigger (cycle #7 F-COM-5 MODIFIED): a `community_reply` notification fires when someone comments on a post you authored. Self-replies don't notify. The trigger is best-effort and never aborts the comment write.

## Surface

**HTTP:** 5 read endpoints + 1 modified write route.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET    | `/api/me/notifications` | any auth | paginated list, `?unread_only`, `?before`, `?limit` |
| GET    | `/api/me/notifications/unread-count` | any auth | bell badge `{count: int}` |
| GET    | `/api/me/notifications/banner` | any auth | most-recent unread `concierge_nudge` or null |
| POST   | `/api/me/notifications/{id}/read` | any auth | idempotent; 404 on non-owner |
| POST   | `/api/me/notifications/read-all` | any auth | bulk mark; returns `{updated: int}` |
| POST   | `/api/comments` | user | MODIFIED — fires F-NOTIF-7 community_reply trigger |

**Internal modules:**
- `app/db/notifications.py` — extended with read helpers (write API unchanged).
- `app/api/me_notifications.py` — endpoint router.
- `app/models/notification.py` — `NotificationCard`, list/banner/count/mark-read responses. Carries no user-identifying field except the `commenter_display_name` inside `community_reply` payloads (see F-NOTIF-7 visibility note).

**MongoDB collections:** none new. Reads `notifications` (cycle #8). The existing `(user_id, created_at DESC)` index covers every query.

---

## F-NOTIF-1 — Notification kinds (V1 enum + naming reconciliation)

The `notifications.kind` field accepts the following values in V1:

| Kind | Written by | Trigger |
|---|---|---|
| `launch_approved` | cycle #8 F-LAUNCH-4 | admin approves a founder's launch |
| `launch_rejected` | cycle #8 F-LAUNCH-5 | admin rejects a founder's launch |
| `concierge_nudge` | cycle #9 F-PUB-2 | publish orchestrator scans profiles, top-5 matched users get one |
| `community_reply` | this cycle (F-NOTIF-7) | another user comments on a post you authored |
| `new_recommendation` | RESERVED | no V1 trigger; needs a weekly scheduler (deferred) |
| `system` | RESERVED | no V1 trigger; needs an admin broadcast endpoint (deferred) |

> **Naming note:** the system_design draft and backlog item #12 refer to a `launch_match` kind. That is the same notification as cycle #9's `concierge_nudge` — same trigger, same payload shape. We keep the cycle #9 wire name (`concierge_nudge`); `launch_match` is a documentation synonym only. Reserved kinds are valid in the schema but no V1 code path writes them.

---

## F-NOTIF-2 — `GET /api/me/notifications` (list)

Behind `current_user`. Role-agnostic.

Query params:
- `unread_only`: `true` filters to `read_at: null`. Default `false`.
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
      "created_at": "..."
    }
  ],
  "next_before": "..."
}
```

`read` is `read_at != null` projected as a boolean — the timestamp itself is intentionally NOT shipped to clients. `next_before` is `null` on the last page.

**Unauthenticated** → `401 auth_required`.

---

## F-NOTIF-3 — `GET /api/me/notifications/unread-count`

Behind `current_user`. Returns `{"count": <int>}` for the bell badge. Backed by the `(user_id, created_at DESC)` index from cycle #8 — Mongo can use the user_id prefix.

---

## F-NOTIF-4 — `GET /api/me/notifications/banner`

Behind `current_user`. Returns the most recent unread `concierge_nudge` row, or `null` if none exist.

```json
{ "notification": { ... } }       // when one exists
{ "notification": null }          // none
```

**Why a dedicated endpoint:** the system_design specifies "top banner on app open." A dedicated endpoint avoids the client having to fetch the full list and filter — the banner check is a single, cheap query.

Other kinds (`community_reply`, `launch_approved`, `launch_rejected`, etc.) NEVER appear in the banner — they show up as bell-only notifications via the list endpoint.

---

## F-NOTIF-5 — `POST /api/me/notifications/{id}/read` (mark single)

Behind `current_user`. Idempotent.

**Given** a notification row exists with `(_id == id, user_id == self)`
**When** the user POSTs to mark it read
**Then** the system sets `read_at = now()` (only if currently null) and returns `200 OK` with `{updated: true}`.

**Given** the row exists but `read_at` is already set
**When** the user POSTs again
**Then** the system returns `200 OK` with `{updated: false}` (no overwrite of an earlier timestamp).

**Given** the row does not exist OR belongs to another user
**Then** the system returns `404 notification_not_found` (existence-leak protection; mirrors cycles #8/#11 pattern).

**Malformed id** → `404 notification_not_found`.

---

## F-NOTIF-6 — `POST /api/me/notifications/read-all`

Behind `current_user`. Empty request body. Bulk-marks the requesting user's unread rows. Returns `{"updated": N}` where N is the count of rows updated. Already-read rows are skipped (no overwrite).

---

## F-NOTIF-7 — `community_reply` write trigger (F-COM-5 MODIFIED)

`POST /api/comments` (cycle #7) gains a best-effort hook after the existing comment insert + post counter bumps:

**Given** an authenticated user posts a comment on a post
**When** the comment is persisted
**Then** the system:

1. Looks up the parent post via `find_post_by_id(comment.post_id)`.
2. If `post.author_user_id != comment.author_user_id`, writes a `notifications` row:
   ```
   {
     user_id: post.author_user_id,
     kind: "community_reply",
     payload: {
       post_id: <oid>,
       comment_id: <oid>,
       commenter_display_name: <string>
     },
     read_at: null,
     created_at: now()
   }
   ```
3. If `post.author_user_id == comment.author_user_id` (self-reply), NO notification is written.
4. Best-effort: any failure inside the trigger is logged and swallowed; the comment write is NEVER aborted.

> **`commenter_display_name` visibility:** the post's author already sees the commenter's display name on the post detail surface (cycle #7 F-COM-4). Including it in the notification payload renders "Maya commented on your post" without a follow-up lookup — same visibility, no more, no less.

The constitutional invariant *"Never let founder accounts post in user communities"* (cycle #7 F-COM-8) makes this trigger safe by construction: founders are 403'd from `POST /api/comments` at the route layer, so they can never fire `community_reply`. Same goes the other way — they never receive `community_reply` because they can't author posts either.

---

## Inbox role-agnostic surface (audit trail)

The 5 read endpoints check only `current_user` (no `require_role`). Each helper queries `{user_id: self._id}` — there is no role-conditional logic in the read path. In practice:

- Founders see launch_approved + launch_rejected rows (the only kinds written for their `_id`).
- Users see concierge_nudge + community_reply rows.

A future kind (e.g., `system` admin broadcast) would surface in both inboxes uniformly. Test `test_inbox_role_agnostic_for_founder` enforces this for the founder side; cross-user scope is enforced by `test_list_scoped_to_self` and `test_mark_read_other_users_notification_returns_404`.
