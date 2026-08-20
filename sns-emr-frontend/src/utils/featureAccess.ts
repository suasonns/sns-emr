import { getCurrentUser } from "../api/session";
import { hasFeatureAccess } from "./authorization";

export function canAccessBilling(): boolean {
  return hasFeatureAccess(getCurrentUser(), "billing");
}

export function canAccessAi(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  return Boolean(user.ai_enabled);
}
