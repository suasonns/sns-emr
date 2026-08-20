import { Alert, Box, Button, Paper, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { logout } from "../api/auth";
import type { SessionUser } from "../api/session";
import { getDefaultRoute } from "../utils/authorization";

export default function UnauthorizedAccess({ user }: { user: SessionUser | null }) {
  const navigate = useNavigate();

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", bgcolor: "#f4f8f7", p: 3 }}>
      <Paper sx={{ width: "min(480px, 100%)", p: 4 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>You do not have access to this workspace.</Alert>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Your current permissions were refreshed from the server. Choose your authorized workspace or sign in with another account.
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Button variant="contained" onClick={() => navigate(getDefaultRoute(user), { replace: true })}>
            Go to my workspace
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              logout();
              navigate("/login", { replace: true });
            }}
          >
            Sign in again
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
