import { useState, type FormEvent } from "react";
import { Alert, Box, Button, Container, Paper, TextField, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";

import { login } from "../api/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("romel.suason@suasonns.org");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || "/portal";

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="sm" sx={{ minHeight: "100vh", display: "grid", placeItems: "center", py: 4 }}>
      <Paper elevation={0} sx={{ width: "100%", p: 4, border: "1px solid #dbe5ee", borderRadius: 3, background: "#f8fbfd" }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 800, color: "#1f3552", mb: 1 }}>
            SNS EMR Login
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Sign in with the master account to access the portal.
          </Typography>
        </Box>

        {error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : null}

        <Box component="form" onSubmit={handleSubmit} sx={{ display: "grid", gap: 2 }}>
          <TextField
            label="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            fullWidth
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            fullWidth
          />
          <Button type="submit" variant="contained" disabled={loading || !password} sx={{ height: 44 }}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
