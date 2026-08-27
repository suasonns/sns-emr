import { clearAccessToken, clearCurrentUser, setAccessToken, setCurrentUser, type SessionUser } from "./session";

export type AuthenticatedUser = SessionUser;

export type LoginAgencyOption = { tenant_id: string; tenant_name: string; email: string };

export type LoginResult =
  | { access_token: string; token_type: string; user: AuthenticatedUser }
  | { requires_agency_selection: true; agencies: LoginAgencyOption[] };

export async function login(email: string, password: string, tenantId?: string): Promise<LoginResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password, tenant_id: tenantId }),
  });

  if (!response.ok) {
    throw new Error("Invalid email or password");
  }

  const data = (await response.json()) as LoginResult;

  if (isAgencySelectionRequired(data)) {
    return data;
  }

  setAccessToken(data.access_token);
  setCurrentUser(data.user);
  return data;
}

export function isAgencySelectionRequired(
  data: LoginResult,
): data is Extract<LoginResult, { requires_agency_selection: true }> {
  return "requires_agency_selection" in data && data.requires_agency_selection === true;
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const token = localStorage.getItem("sns-hospice-solutions-access-token");

  const response = await fetch(`${base}/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });

  if (!response.ok) {
    throw new Error("Current password is invalid or the update failed");
  }

  return response.json();
}

export function logout() {
  clearAccessToken();
  clearCurrentUser();
  localStorage.removeItem("sns-active-agency");
  localStorage.removeItem("sns-agency-options");
}

// Public "set your password" link flow (from admin-issued staff creation,
// admin password resets, and — once wired up — emailed reset links). No
// auth token required: the token itself, proven via /auth/set-password,
// is the identity check.
export async function validateSetPasswordToken(token: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}/auth/set-password/validate?token=${encodeURIComponent(token)}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail || "This link is invalid or has expired.");
  }
  return data as { email: string; valid: boolean };
}

export async function setPasswordWithToken(token: string, newPassword: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}/auth/set-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail || "Unable to set password. The link may be invalid or expired.");
  }
  return data;
}

export type LinkedAgency = {
  user_id: string;
  tenant_id: string;
  tenant_name: string;
  email: string;
  role: string;
};

// Other agencies this same physical person has a staff account in --
// identity-matched server-side by SSN (primary) or name+DOB+license
// (fallback), independent of whether that account uses a different email
// or password. Does not require re-entering any password to list them;
// switching into one does (see switchAgency).
export async function getLinkedAgencies(): Promise<LinkedAgency[]> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const token = localStorage.getItem("sns-hospice-solutions-access-token");
  const response = await fetch(`${base}/auth/linked-agencies`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail || "Unable to load linked agencies");
  }
  return (data.agencies ?? []) as LinkedAgency[];
}

// Switches the active session into another agency found via
// getLinkedAgencies(). Requires that agency's own password even though the
// person's identity is already confirmed -- switching does not bypass a
// separate agency's credential.
export async function switchAgency(targetUserId: string, password: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const token = localStorage.getItem("sns-hospice-solutions-access-token");
  const response = await fetch(`${base}/auth/switch-agency`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_user_id: targetUserId, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail || "Unable to switch agency. Check the password and try again.");
  }

  setAccessToken(data.access_token);
  setCurrentUser(data.user);
  return data as { access_token: string; token_type: string; user: AuthenticatedUser };
}
