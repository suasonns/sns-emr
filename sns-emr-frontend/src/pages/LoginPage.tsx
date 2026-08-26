import { useState, type FormEvent } from "react";
import { Alert, Box, Button, Container, Paper, TextField, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";

import { isAgencySelectionRequired, login, type LoginAgencyOption } from "../api/auth";
import { canAccessPath, getDefaultRoute } from "../utils/authorization";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agencyOptions, setAgencyOptions] = useState<LoginAgencyOption[] | null>(null);
  const [selectedAgency, setSelectedAgency] = useState<LoginAgencyOption | null>(null);
  const [agencyPassword, setAgencyPassword] = useState("");

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || "/portal";

  async function attemptLogin(loginEmail: string, loginPassword: string, tenantId?: string) {
    setLoading(true);
    setError(null);

    try {
      const result = await login(loginEmail.trim(), loginPassword, tenantId);
      if (isAgencySelectionRequired(result)) {
        // Password matched (or the person is identity-linked to) more
        // than one agency -- show a picker instead of guessing which one
        // was meant. Some of these agencies may use a different email
        // and/or password than what was just typed.
        setAgencyOptions(result.agencies);
        return;
      }
      navigate(canAccessPath(result.user, from) ? from : getDefaultRoute(result.user), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to login");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await attemptLogin(email, password);
  }

  function handleAgencyPick(agency: LoginAgencyOption) {
    setSelectedAgency(agency);
    // Prefill with the password just typed -- it's correct for at least
    // one of the listed agencies (that's how they ended up in this list),
    // so this saves re-typing when it happens to also be right for the
    // chosen one; the field stays editable for agencies with their own
    // separate password.
    setAgencyPassword(password);
    setError(null);
  }

  async function handleAgencySubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedAgency) return;
    await attemptLogin(selectedAgency.email, agencyPassword, selectedAgency.tenant_id);
  }

  return (
   <Box
     sx={{
       minHeight: "100vh",
       display: "grid",
       placeItems: "center",
       py: 4,
       background: "linear-gradient(180deg, #f4f8f7 0%, #edf3f5 100%)",
       position: "relative",
       overflow: "hidden",
       "&::before": {
         content: '""',
         position: "absolute",
         inset: 0,
         background: "radial-gradient(circle at top, rgba(13, 148, 136, 0.08), transparent 40%), radial-gradient(circle at bottom right, rgba(14, 116, 144, 0.08), transparent 30%)",
         pointerEvents: "none",
       },
     }}
   >
     <Container maxWidth="sm" sx={{ position: "relative", zIndex: 1, maxWidth: 500 }}>
       <Box sx={{ width: "100%", display: "grid", gap: 2, justifyItems: "center" }}>
         <Box
           component="img"
           src="/brand/sns-logo-dark.svg"
           alt="SNS Hospice Solutions"
           onError={(event) => {
             const target = event.currentTarget as HTMLImageElement;
             if (!target.src.endsWith("/brand/sns-logo-icon.svg")) {
               target.src = "/brand/sns-logo-icon.svg";
             }
           }}
           sx={{
             width: "100%",
             maxWidth: 620,
             height: "auto",
             display: "block",
             filter: "drop-shadow(0 18px 28px rgba(15, 82, 96, 0.12))",
           }}
         />
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
             backdropFilter: "blur(12px)",
           }}
         >
           <Box sx={{ mb: 2.5, textAlign: "center" }}>
             <Typography variant="overline" sx={{ color: "#4b6470", letterSpacing: "0.12em", fontWeight: 700 }}>
               Secure clinical access
             </Typography>
             <Typography variant="h5" sx={{ mt: 0.75, color: "#112131", fontWeight: 700, letterSpacing: "-0.03em" }}>
               Welcome back
             </Typography>
           </Box>

           {error ? (
             <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
               {error}
             </Alert>
           ) : null}
           {agencyOptions && !selectedAgency ? (
             <Box sx={{ display: "grid", gap: 1.5 }}>
               <Typography sx={{ color: "#1f2f3d", fontWeight: 700, fontSize: 14 }}>
                 Choose which agency to sign in to
               </Typography>
               {agencyOptions.map((agency) => (
                 <Button
                   key={agency.tenant_id}
                   type="button"
                   variant="outlined"
                   disabled={loading}
                   onClick={() => handleAgencyPick(agency)}
                   sx={{
                     justifyContent: "flex-start",
                     textTransform: "none",
                     fontWeight: 700,
                     borderRadius: 2,
                     color: "#0d3b5a",
                     borderColor: "rgba(13, 59, 90, 0.4)",
                   }}
                 >
                   {agency.tenant_name}
                 </Button>
               ))}
               <Button
                 type="button"
                 variant="text"
                 disabled={loading}
                 onClick={() => setAgencyOptions(null)}
                 sx={{ justifySelf: "start", fontWeight: 600 }}
               >
                 Back
               </Button>
             </Box>
           ) : agencyOptions && selectedAgency ? (
             <Box component="form" onSubmit={handleAgencySubmit} sx={{ display: "grid", gap: 2 }}>
               <Typography sx={{ color: "#1f2f3d", fontWeight: 700, fontSize: 14 }}>
                 Sign in to {selectedAgency.tenant_name}
               </Typography>
               <Typography sx={{ color: "#4b6470", fontSize: 13 }}>
                 This agency may use its own password. Enter it below.
               </Typography>
               <TextField
                 label="Password"
                 type="password"
                 value={agencyPassword}
                 onChange={(event) => setAgencyPassword(event.target.value)}
                 autoComplete="current-password"
                 fullWidth
                 sx={{
                   "& .MuiInputLabel-root": { color: "#1f2f3d", fontWeight: 700 },
                   "& .MuiOutlinedInput-root": { borderRadius: 2, backgroundColor: "rgba(255,255,255,0.8)" },
                   "& .MuiOutlinedInput-input": { color: "#0f172a" },
                 }}
               />
               <Button
                 type="submit"
                 variant="contained"
                 disabled={loading || !agencyPassword}
                 sx={{
                   height: 46,
                   borderRadius: 2,
                   background: "#0d3b5a",
                   color: "#ffffff",
                   fontWeight: 900,
                   textTransform: "none",
                 }}
               >
                 {loading ? "Signing in..." : "Sign in"}
               </Button>
               <Button
                 type="button"
                 variant="text"
                 disabled={loading}
                 onClick={() => {
                   setSelectedAgency(null);
                   setAgencyPassword("");
                   setError(null);
                 }}
                 sx={{ justifySelf: "start", fontWeight: 600 }}
               >
                 Back
               </Button>
             </Box>
           ) : (
             <Box component="form" onSubmit={handleSubmit} sx={{ display: "grid", gap: 2 }}>
               <TextField
                 label="Email"
                 value={email}
                 onChange={(event) => setEmail(event.target.value)}
                 autoComplete="email"
                 fullWidth
                 sx={{
                   "& .MuiInputLabel-root": {
                     color: "#1f2f3d",
                     fontWeight: 700,
                   },
                   "& .MuiOutlinedInput-root": {
                     borderRadius: 2,
                     backgroundColor: "rgba(255,255,255,0.8)",
                   },
                   "& .MuiOutlinedInput-input": {
                     color: "#0f172a",
                   },
                 }}
               />
               <TextField
                 label="Password"
                 type="password"
                 value={password}
                 onChange={(event) => setPassword(event.target.value)}
                 autoComplete="current-password"
                 fullWidth
                 sx={{
                   "& .MuiInputLabel-root": {
                     color: "#1f2f3d",
                     fontWeight: 700,
                   },
                   "& .MuiOutlinedInput-root": {
                     borderRadius: 2,
                     backgroundColor: "rgba(255,255,255,0.8)",
                   },
                   "& .MuiOutlinedInput-input": {
                     color: "#0f172a",
                   },
                 }}
               />
               <Button
                 type="submit"
                 variant="contained"
                 disabled={loading || !password}
                 sx={{
                   height: 46,
                   borderRadius: 2,
                   background: "#0d3b5a",
                   color: "#ffffff",
                   boxShadow: "0 14px 24px rgba(13, 59, 90, 0.25)",
                   fontWeight: 900,
                   textTransform: "none",
                   letterSpacing: "0.02em",
                   border: "1px solid rgba(13, 59, 90, 0.5)",
                   textShadow: "0 1px 0 rgba(0,0,0,0.2)",
                   "&:hover": {
                     background: "#0b2f4d",
                   },
                 }}
               >
                 {loading ? "Signing in..." : "Sign in"}
               </Button>
               <Button
                 type="button"
                 variant="text"
                 color="primary"
                 onClick={() => setError("Self-service password reset is unavailable. Contact an administrator.")}
                 sx={{ justifySelf: "start", fontWeight: 600 }}
               >
                 Forgot password?
               </Button>
             </Box>
            )}
         </Paper>
       </Box>
     </Container>
   </Box>
  );
}
