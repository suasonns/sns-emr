import { describe, expect, it } from "vitest";

import { canAccessPath, getDefaultRoute, hasRouteAccess } from "./authorization";
import type { SessionUser } from "../api/session";

// SUPERADMIN developer login is implemented as the platform-scoped OWNER
// role/account for "SNS Tech Solutions" (see
// docs/phase2/SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md). These tests verify
// that the frontend's route/navigation guards match the backend's
// access_scope-based authorization for that account, and that routine
// tenant staff cannot reach the developer/Owner Platform workspace.

function makeUser(overrides: Partial<SessionUser>): SessionUser {
  return {
    id: "user-1",
    tenant_id: "tenant-1",
    role: "OWNER",
    access_scope: "platform",
    ...overrides,
  } as SessionUser;
}

describe("SUPERADMIN (OWNER) developer login routing", () => {
  it("routes the OWNER developer login to the Owner Platform workspace", () => {
    const owner = makeUser({ role: "OWNER", access_scope: "platform" });
    expect(hasRouteAccess(owner, "owner")).toBe(true);
    expect(getDefaultRoute(owner)).toBe("/owner");
    expect(canAccessPath(owner, "/owner")).toBe(true);
  });

  it("excludes routine tenant clinical roles from the Owner Platform workspace", () => {
    const tenantUser = makeUser({ role: "RN", access_scope: "tenant" });
    expect(hasRouteAccess(tenantUser, "owner")).toBe(false);
    expect(getDefaultRoute(tenantUser)).toBe("/portal");
    expect(canAccessPath(tenantUser, "/owner")).toBe(false);
  });

  it("excludes a billing-scoped account from the Owner Platform workspace", () => {
    const billingUser = makeUser({ role: "PLATFORM_BILLING", access_scope: "billing", billing_enabled: true });
    expect(hasRouteAccess(billingUser, "owner")).toBe(false);
    expect(getDefaultRoute(billingUser)).toBe("/billing");
  });

  it("treats an unauthenticated session as having no developer route access", () => {
    expect(hasRouteAccess(null, "owner")).toBe(false);
    expect(getDefaultRoute(null)).toBe("/portal");
    expect(canAccessPath(null, "/owner")).toBe(false);
  });
});
