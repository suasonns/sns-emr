import { getCurrentUser } from "../api/session";

export function canAccessBilling(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  return Boolean(user.billing_enabled);
}

export function canAccessAi(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  return Boolean(user.ai_enabled);
}
