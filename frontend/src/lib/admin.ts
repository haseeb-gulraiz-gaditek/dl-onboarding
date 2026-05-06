// Mesh — admin status detection (no backend change).
// Per spec-delta frontend-secondary F-FE2-2.
//
// Strategy: probe GET /admin/launches?status=pending once on /home
// mount. If 200 → user is admin (cycle #3 ADMIN_EMAILS allowlist
// matched). If 403 → not admin. Cache the bit in localStorage so
// subsequent renders don't probe again.

import { api, ApiError } from "./api";

const KEY = "mesh.isAdmin";

export function isAdmin(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(KEY) === "1";
}

export function clearAdminCache(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(KEY);
}

export async function probeAdminAndCache(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  // Quick win: never probed → run; previously probed → trust cache.
  const cached = window.localStorage.getItem(KEY);
  if (cached !== null) return cached === "1";

  try {
    await api.get("/admin/launches?status=pending");
    window.localStorage.setItem(KEY, "1");
    return true;
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      window.localStorage.setItem(KEY, "0");
      return false;
    }
    // Network blip / 5xx — leave cache unset, retry on next mount.
    return false;
  }
}
