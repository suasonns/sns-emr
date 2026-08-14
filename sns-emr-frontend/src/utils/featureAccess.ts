import { getCurrentUser } from "../api/session";

const LOVE_AND_FAITH_TENANT_ID = "01271980-0000-0000-0000-000005101977";
const PRIMARY_LOGIN_EMAIL = "romel.suason@suasonns.org";

function isPrimaryLogin(user: NonNullable<ReturnType<typeof getCurrentUser>>) {
  return user.tenant_id === LOVE_AND_FAITH_TENANT_ID || user.email?.toLowerCase() === PRIMARY_LOGIN_EMAIL;
}

export function canAccessBilling(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  if (user.role === "OWNER") return true;
  if (isPrimaryLogin(user)) return user.billing_enabled !== false;
  return Boolean(user.billing_enabled);
}

export function canAccessAi(): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  if (user.role === "OWNER") return true;
  if (isPrimaryLogin(user)) return user.ai_enabled !== false;
  return Boolean(user.ai_enabled);
}
