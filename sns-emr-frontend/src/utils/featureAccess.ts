import { getCurrentUser } from "../api/session";

// Feature access follows the tenant flags the backend returns at login.
// No tenant id or email is special-cased on the client.

export function canAccessBilling(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  if (user.role === "OWNER") return true;
  return Boolean(user.billing_enabled);
}

export function canAccessAi(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  if (user.role === "OWNER") return true;
  return Boolean(user.ai_enabled);
}
