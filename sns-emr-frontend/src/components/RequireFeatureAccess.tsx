import { CircularProgress, Box } from "@mui/material";
import { useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import api from "../api/client";
import { getAccessToken } from "../api/session";
import { getCurrentUser, setCurrentUser, type SessionUser } from "../api/session";

type FeatureKey = "billing";

function hasFeatureAccess(user: SessionUser | null, feature: FeatureKey): boolean {
  if (!user) return false;
  if (feature === "billing") {
    return Boolean(user.billing_enabled);
  }
  return false;
}

export default function RequireFeatureAccess({
  feature,
  children,
  fallbackPath = "/portal",
}: {
  feature: FeatureKey;
  children: ReactNode;
  fallbackPath?: string;
}) {
  const location = useLocation();
  const token = getAccessToken();
  const cachedUser = getCurrentUser();
  const [user, setUser] = useState<SessionUser | null>(cachedUser);
  const [loading, setLoading] = useState(Boolean(token && !cachedUser));

  useEffect(() => {
    if (!token || user) return;

    let mounted = true;

    api.get<SessionUser>("/auth/me")
      .then((response) => {
        if (!mounted) return;
        setCurrentUser(response.data);
        setUser(response.data);
      })
      .catch(() => {
        if (mounted) setUser(null);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [token, user]);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (loading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!hasFeatureAccess(user, feature)) {
    return <Navigate to={fallbackPath} replace state={{ from: location }} />;
  }

  return children;
}
