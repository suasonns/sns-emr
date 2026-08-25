import { Box, Chip, Paper, Typography } from "@mui/material";

import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";

// This page previously rendered getDemoInbox() -- 6 fully fabricated message
// threads (fake senders, fake patient names, fake unread counts) with no
// backend behind any of it. There is no secure-messaging/message-center
// model, API, or data store anywhere in this codebase. Per the project's
// standing "never fabricate data" policy (same rule behind billing's
// ComingSoonPage), this now shows an honest not-yet-available state instead
// of sample threads.
export default function SecureInboxDataPage() {
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.";

  return (
    <PortalShell activeTab="Secure Inbox">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
          <Box>
            <Typography sx={{ fontSize: portalTypography.title, fontWeight: 800, color: "#1f3552", lineHeight: 1.05 }}>
              Secure Inbox Workspace
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mt: 0.7 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: portalTypography.subtitle }}>
                Active Agency Workspace:
              </Typography>
              <Chip label={workspaceName} size="small" sx={{ background: "#ccfbf1", color: "#0f766e", fontWeight: 700, height: 24 }} />
            </Box>
          </Box>
        </Box>

        <Paper
          variant="outlined"
          sx={{
            p: 4,
            borderRadius: 2,
            borderStyle: "dashed",
            borderWidth: 2,
            borderColor: "#cfdbe5",
            background: "#fbfdfe",
            textAlign: "center",
          }}
        >
          <Typography sx={{ fontWeight: 800, color: "#1f3552", mb: 1 }}>Secure messaging not available yet</Typography>
          <Typography sx={{ fontSize: 13.5, color: "#6b7d90", maxWidth: 560, mx: "auto" }}>
            There is no secure message-center backend built yet (no message/thread model, no send/receive API). This
            page will not show sample threads or fabricated senders until a real messaging system exists. Contact
            your care team directly, or ask your administrator about priorities for building this feature.
          </Typography>
        </Paper>
      </Box>
    </PortalShell>
  );
}
