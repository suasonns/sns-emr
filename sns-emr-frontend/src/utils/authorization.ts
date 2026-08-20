import type { SessionUser } from "../api/session";

export type FeatureKey = "billing";
export type RouteAccess = "analytics" | "owner" | "tenant";

export function hasFeatureAccess(
  user: SessionUser | null,
  feature: FeatureKey,
): boolean {
  if (!user) return false;
  return feature === "billing" && user.access_scope !== "platform" && Boolean(user.billing_enabled);
}

export function hasRouteAccess(
  user: SessionUser | null,
  access: RouteAccess,
): boolean {
  if (!user) return false;
  if (access === "owner") return user.access_scope === "platform" && user.role === "OWNER";
  if (access === "analytics") return user.access_scope !== "platform";
  return user.access_scope === "tenant";
}

export function getDefaultRoute(user: SessionUser | null): string {
  if (hasRouteAccess(user, "owner")) return "/owner";
  if (user?.access_scope === "platform") return "/login";
  if (user?.access_scope === "billing") {
    return hasFeatureAccess(user, "billing") ? "/billing" : "/analytics";
  }
  return "/portal";
}

export function canAccessPath(user: SessionUser | null, path: string): boolean {
  if (path === "/billing") return hasFeatureAccess(user, "billing");
  if (path === "/analytics") return hasRouteAccess(user, "analytics");
  if (path === "/owner" || path.startsWith("/owner/")) return hasRouteAccess(user, "owner");
  return hasRouteAccess(user, "tenant");
}
