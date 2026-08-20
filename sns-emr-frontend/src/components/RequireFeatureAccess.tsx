import type { ReactNode } from "react";

import { hasFeatureAccess, type FeatureKey } from "../utils/authorization";
import RequireSessionAccess from "./RequireSessionAccess";

export default function RequireFeatureAccess({
  feature,
  children,
}: {
  feature: FeatureKey;
  children: ReactNode;
}) {
  return (
    <RequireSessionAccess authorize={(user) => hasFeatureAccess(user, feature)}>
      {children}
    </RequireSessionAccess>
  );
}
