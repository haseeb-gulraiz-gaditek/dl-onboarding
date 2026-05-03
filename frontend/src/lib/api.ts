// Mesh — typed fetch wrapper.
// Per spec-delta frontend-core F-FE-5.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const JWT_KEY = "mesh.jwt";

export interface ApiOpts {
  auth?: boolean;             // default true
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API ${status}: ${JSON.stringify(body)}`);
  }
}

export function getJwt(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(JWT_KEY);
}

export function setJwt(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(JWT_KEY, token);
}

export function clearJwt(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(JWT_KEY);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  opts: ApiOpts = {},
): Promise<T> {
  const { auth = true, headers = {}, signal } = opts;
  const url = `${BASE_URL}${path}`;
  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (auth) {
    const jwt = getJwt();
    if (jwt) finalHeaders.Authorization = `Bearer ${jwt}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    throw new ApiError(0, { error: "network", detail: String(err) });
  }

  let parsed: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (response.status === 401 && auth) {
    // Token rejected (expired / invalid). Clear it and redirect
    // to /login — the user already has an account, so /signup
    // would be the wrong landing.
    clearJwt();
    if (typeof window !== "undefined") {
      window.location.assign("/login");
    }
    throw new ApiError(401, parsed);
  }

  if (!response.ok) {
    throw new ApiError(response.status, parsed);
  }

  return parsed as T;
}

export const api = {
  get: <T,>(path: string, opts?: ApiOpts) => request<T>("GET", path, undefined, opts),
  post: <T,>(path: string, body?: unknown, opts?: ApiOpts) =>
    request<T>("POST", path, body, opts),
  patch: <T,>(path: string, body?: unknown, opts?: ApiOpts) =>
    request<T>("PATCH", path, body, opts),
  del: <T,>(path: string, opts?: ApiOpts) =>
    request<T>("DELETE", path, undefined, opts),
};
