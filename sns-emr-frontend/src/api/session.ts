const AUTH_TOKEN_KEY = "sns-hospice-solutions-access-token";
const REFRESH_TOKEN_KEY = "sns-hospice-solutions-refresh-token";
const AUTH_USER_KEY = "sns-hospice-solutions-auth-user";

export type SessionUser = {
  id: string;
  tenant_id: string;
  role: string;
  email: string;
  full_name: string;
  tenant_name?: string;
  ai_enabled?: boolean;
  billing_enabled?: boolean;
  access_scope: "platform" | "billing" | "tenant";
  must_change_password?: boolean;
};

export function getAccessToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

// Refresh token -- exchanged (via POST /auth/refresh, see api/client.ts's
// response interceptor) for a new access token when the access token
// expires, so a long clinical encounter is never suddenly logged out with
// unsaved work (e.g. mid visit-recording). Never sent to any endpoint
// except /auth/refresh itself.
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearRefreshToken(): void {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getCurrentUser(): SessionUser | null {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

export function setCurrentUser(user: SessionUser): void {
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function clearCurrentUser(): void {
  localStorage.removeItem(AUTH_USER_KEY);
}
