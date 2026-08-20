import { clearAccessToken, clearCurrentUser, setAccessToken, setCurrentUser, type SessionUser } from "./session";

export type AuthenticatedUser = SessionUser;

export async function login(email: string, password: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error("Invalid email or password");
  }

  const data = (await response.json()) as {
    access_token: string;
    token_type: string;
    user: AuthenticatedUser;
  };

  setAccessToken(data.access_token);
  setCurrentUser(data.user);
  return data;
}

export async function resetPassword(email: string, newPassword: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}/auth/reset-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, new_password: newPassword }),
  });

  if (!response.ok) {
    throw new Error("Unable to reset password");
  }

  return response.json();
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
