// Mesh — auth helpers.
// Per spec-delta frontend-core F-FE-5.

import { api, clearJwt, getJwt, setJwt } from "./api";
import { clearAdminCache } from "./admin";
import type { AuthResponse, UserPublic } from "./api-types";

export type RoleQuestionAnswer = "finding_tools" | "launching_product";

export interface SignupParams {
  email: string;
  password: string;
  role_question_answer: RoleQuestionAnswer;
}

export interface LoginParams {
  email: string;
  password: string;
}

export async function signup(params: SignupParams): Promise<AuthResponse> {
  const resp = await api.post<AuthResponse>(
    "/api/auth/signup",
    params,
    { auth: false },
  );
  setJwt(resp.jwt);
  return resp;
}

export async function login(params: LoginParams): Promise<AuthResponse> {
  const resp = await api.post<AuthResponse>(
    "/api/auth/login",
    params,
    { auth: false },
  );
  setJwt(resp.jwt);
  return resp;
}

export function logout(): void {
  clearJwt();
  clearAdminCache();
  if (typeof window !== "undefined") {
    window.location.assign("/");
  }
}

export function isAuthenticated(): boolean {
  return getJwt() !== null;
}

export async function currentUser(): Promise<UserPublic | null> {
  if (!isAuthenticated()) return null;
  try {
    return await api.get<UserPublic>("/api/me");
  } catch {
    return null;
  }
}
