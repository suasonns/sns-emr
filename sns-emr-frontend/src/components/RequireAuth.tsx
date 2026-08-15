import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { getAccessToken } from "../api/session";

export default function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
  const token = getAccessToken();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
