import { useEffect, useState, type FormEvent } from "react";
import { Alert, Box, Button, Container, Paper, TextField, Typography } from "@mui/material";
import { useNavigate, useSearchParams } from "react-router-dom";

import { setPasswordWithToken, validateSetPasswordToken } from "../api/auth";
import BrandLogo from "../components/BrandLogo";

// Public "set your password" destination for admin-issued reset links
// (Add SNS Staff, Reset Password, and Revoke Access all mint one of
// these). No auth token is required to view/submit this page -- the
// link's own single-use token is the identity check, verified against
// /auth/set-password/validate and /auth/set-password on the backend.
export default function SetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  // No token in the URL means there's nothing to validate -- treat this
  // as a derived error instead of a synchronous setState inside the
  // effect below, so checking/tokenError never need to be set on the
  // same render pass the effect runs (avoids cascading re-renders).
  const missingTokenError = token
    ? null
    : "This link is missing a token. Ask your administrator to send a new one.";

  const [checking, setChecking] = useState(!!token);
  const [email, setEmail] = useState<string | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    validateSetPasswordToken(token)
      .then((result) => setEmail(result.email))
      .catch((err) => setTokenError(err instanceof Error ? err.message : "This link is invalid or has expired."))
      .finally(() => setChecking(false));
  }, [token]);

  const effectiveTokenError = tokenError ?? missingTokenError;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitError(null);
    if (newPassword.length < 8) {
      setSubmitError("Password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setSubmitError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await setPasswordWithToken(token, newPassword);
      setDone(true);
      setTimeout(() => navigate("/login", { replace: true }), 2000);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Unable to set password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        py: 4,
        background: "linear-gradient(180deg, #f4f8f7 0%, #edf3f5 100%)",
      }}
    >
      <Container maxWidth="sm" sx={{ maxWidth: 500 }}>
        <Box sx={{ width: "100%", display: "grid", gap: 2, justifyItems: "center" }}>
          <BrandLogo variant="dark" style={{ width: "100%", maxWidth: 620, height: "auto" }} />
          <Paper
            elevation={0}
            sx={{
              width: "100%",
              maxWidth: 430,
              p: 3,
              border: "1px solid rgba(15, 118, 110, 0.14)",
              borderRadius: 3,
              background: "rgba(255,255,255,0.9)",
              boxShadow: "0 18px 40px rgba(15, 23, 42, 0.10)",
            }}
          >
            <Box sx={{ mb: 2.5, textAlign: "center" }}>
              <Typography variant="overline" sx={{ color: "#4b6470", letterSpacing: "0.12em", fontWeight: 700 }}>
                Secure clinical access
              </Typography>
              <Typography variant="h5" sx={{ mt: 0.75, color: "#112131", fontWeight: 700, letterSpacing: "-0.03em" }}>
                Set your password
              </Typography>
            </Box>

            {checking ? (
              <Typography sx={{ color: "#4b6470", textAlign: "center" }}>Checking your link…</Typography>
            ) : effectiveTokenError ? (
              <Alert severity="error" sx={{ borderRadius: 2 }}>{effectiveTokenError}</Alert>
            ) : done ? (
              <Alert severity="success" sx={{ borderRadius: 2 }}>Password set. Redirecting to sign in…</Alert>
            ) : (
              <Box component="form" onSubmit={handleSubmit} sx={{ display: "grid", gap: 2 }}>
                {email ? (
                  <Typography sx={{ color: "#1f2f3d", fontWeight: 700, fontSize: 14 }}>
                    Account: {email}
                  </Typography>
                ) : null}
                {submitError ? (
                  <Alert severity="error" sx={{ borderRadius: 2 }}>{submitError}</Alert>
                ) : null}
                <TextField
                  label="New password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                  fullWidth
                  helperText="At least 8 characters"
                />
                <TextField
                  label="Confirm password"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  fullWidth
                />
                <Button
                  type="submit"
                  variant="contained"
                  disabled={submitting || !newPassword || !confirmPassword}
                  sx={{
                    height: 46,
                    borderRadius: 2,
                    background: "#0d3b5a",
                    color: "#ffffff",
                    fontWeight: 900,
                    textTransform: "none",
                  }}
                >
                  {submitting ? "Saving…" : "Set password & continue"}
                </Button>
              </Box>
            )}
          </Paper>
        </Box>
      </Container>
    </Box>
  );
}
