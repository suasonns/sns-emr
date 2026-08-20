import type { ReactNode } from "react";

import { hasRouteAccess, type RouteAccess } from "../utils/authorization";
import RequireSessionAccess from "./RequireSessionAccess";

export default function RequireRoleAccess({
  access,
  children,
}: {
  access: RouteAccess;
  children: ReactNode;
}) {
  return (
    <RequireSessionAccess authorize={(user) => hasRouteAccess(user, access)}>
      {children}
    </RequireSessionAccess>
  );
}
