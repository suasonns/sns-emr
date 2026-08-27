const AUTH_TOKEN_KEY = "sns-hospice-solutions-access-token";
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
