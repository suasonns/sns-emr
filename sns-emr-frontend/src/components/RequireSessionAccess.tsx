import { Box, CircularProgress } from "@mui/material";
import { useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import api from "../api/client";
import {
  clearAccessToken,
  clearCurrentUser,
  getAccessToken,
  getCurrentUser,
  setCurrentUser,
  type SessionUser,
} from "../api/session";
import UnauthorizedAccess from "./UnauthorizedAccess";

export default function RequireSessionAccess({
  authorize,
  children,
}: {
  authorize: (user: SessionUser | null) => boolean;
  children: ReactNode;
}) {
  const location = useLocation();
  const token = getAccessToken();
  const [user, setUser] = useState<SessionUser | null>(getCurrentUser());
  const [loading, setLoading] = useState(Boolean(token));
  const [authenticationFailed, setAuthenticationFailed] = useState(false);

  useEffect(() => {
    if (!token) return;

    let active = true;
    api.get<SessionUser>("/auth/me")
      .then((response) => {
        if (!active) return;
        setCurrentUser(response.data);
        setUser(response.data);
      })
      .catch((error: { response?: { status?: number } }) => {
        if (!active) return;
        clearCurrentUser();
        setUser(null);
        if (error.response?.status === 401 || error.response?.status === 404) {
          clearAccessToken();
          setAuthenticationFailed(true);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  if (!token || authenticationFailed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (loading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!authorize(user)) {
    return <UnauthorizedAccess user={user} />;
  }

  return children;
}
