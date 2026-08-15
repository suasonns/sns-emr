import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Paper,
  TextField,
  Typography,
} from "@mui/material";

import { getDemoInbox, type InboxThread } from "../api/notifications";
import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";

const FOLDERS = [
  { label: "Inbox", count: 3 },
  { label: "Sent", count: 1 },
  { label: "Drafts", count: 1 },
  { label: "Archived", count: 1 },
];

function MessageRow({ thread, selected }: { thread: InboxThread; selected?: boolean }) {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 1.5,
        px: 1.35,
        py: 1.05,
        borderRadius: 1.5,
        background: selected ? "#edf9f7" : thread.unread ? "#f2fbfa" : "#fff",
        border: "1px solid",
        borderColor: selected ? "#8fe0d7" : thread.unread ? "#d4efeb" : "#e6edf3",
        mb: 1.15,
      }}
    >
      <Box
        sx={{
          width: 24,
          height: 24,
          borderRadius: "50%",
          background: thread.unread ? "#12a391" : "#d9eef0",
          color: thread.unread ? "#fff" : "#0b7d73",
          display: "grid",
          placeItems: "center",
          fontSize: portalTypography.small,
          fontWeight: 800,
          flexShrink: 0,
        }}
      >
        {thread.sender
          .split(" ")
          .map((part) => part[0])
          .slice(0, 2)
          .join("")}
      </Box>

      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1, alignItems: "start" }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: portalTypography.body, fontWeight: 800, lineHeight: 1.1 }}>
              {thread.sender}
            </Typography>
            <Typography sx={{ fontSize: portalTypography.small, color: "#6b7d90", mb: 0.2 }}>
              {thread.senderRole}
            </Typography>
          </Box>
          <Typography sx={{ fontSize: portalTypography.chip, color: "#6b7d90", whiteSpace: "nowrap" }}>
            {thread.time}
          </Typography>
        </Box>
        <Typography sx={{ fontSize: portalTypography.body, fontWeight: 700, color: "#0f172a", lineHeight: 1.2, mb: 0.2 }} noWrap>
          {thread.subject}
        </Typography>
        <Typography sx={{ fontSize: portalTypography.body - 2, color: "#475569", lineHeight: 1.35 }}>
          {thread.preview}
        </Typography>
      </Box>

      <Button variant="outlined" size="small" sx={{ alignSelf: "center", minWidth: 56, height: 22, fontSize: portalTypography.chip }}>
        Reply
      </Button>
    </Box>
  );
}

export default function SecureInboxDataPage() {
  const inbox = getDemoInbox();
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.";
  const [query, setQuery] = useState("");
  const [activeFolder, setActiveFolder] = useState("Inbox");

  const visibleThreads = useMemo(() => {
    const q = query.trim().toLowerCase();
    return inbox.threads.filter((thread) => {
      const matchesFolder = activeFolder === "Inbox" ? thread.tag === "Inbox" : thread.tag === activeFolder;
      const matchesQuery =
        !q ||
        thread.sender.toLowerCase().includes(q) ||
        thread.subject.toLowerCase().includes(q) ||
        thread.preview.toLowerCase().includes(q);
      return matchesFolder && matchesQuery;
    });
  }, [activeFolder, inbox.threads, query]);

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
      <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.8, pt: 0.2, fontSize: portalTypography.subtitle }}>
            <Box component="span" sx={{ width: 8, height: 8, borderRadius: "50%", background: "#64748b" }} />
            Last synced: Today at 08:30 AM
          </Typography>
        </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "220px 1fr" }, gap: 1.5 }}>
          <Paper variant="outlined" sx={{ borderColor: "#cfdbe5", borderWidth: 2, borderRadius: 2, overflow: "hidden", background: "#fff" }}>
          <Box sx={{ p: 1 }}>
            <Button
              fullWidth
              variant="contained"
              sx={{
                background: "#10b7a2",
                fontWeight: 800,
                textTransform: "none",
                height: 34,
                mb: 1,
                fontSize: portalTypography.button,
                lineHeight: 1.1,
                whiteSpace: "nowrap",
              }}
            >
              + Compose Message
            </Button>
              {FOLDERS.map((folder) => (
                <Button
                  key={folder.label}
                  fullWidth
                  onClick={() => setActiveFolder(folder.label)}
                  sx={{
                    justifyContent: "space-between",
                    color: "#244a64",
                    background: activeFolder === folder.label ? "#ecfaf7" : "transparent",
                    textTransform: "none",
                    px: 1,
                    py: 0.8,
                    borderRadius: 1,
                    mb: 0.25,
                    fontWeight: activeFolder === folder.label ? 800 : 600,
                    fontSize: portalTypography.body,
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, borderRadius: 0.5, background: activeFolder === folder.label ? "#10b7a2" : "#d9e4ef" }} />
                    {folder.label}
                  </Box>
                  <Chip label={folder.count} size="small" sx={{ height: 18, fontSize: portalTypography.chip, background: "#edf2f7" }} />
                </Button>
              ))}
            </Box>
          </Paper>

          <Paper variant="outlined" sx={{ borderColor: "#cfdbe5", borderWidth: 2, borderRadius: 2, overflow: "hidden", background: "#fff" }}>
            <Box sx={{ p: 1, display: "flex", alignItems: "center", gap: 0.8, borderBottom: "1px solid #e5edf3", flexWrap: "wrap" }}>
              <TextField
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search secure messages..."
                size="small"
                sx={{
                  width: { xs: "100%", md: 280 },
                  "& .MuiOutlinedInput-root": { height: 28, borderRadius: 999, background: "#fff" },
                }}
              />
              <Chip label="Date Range: Last 30 Days" size="small" sx={{ height: 24, fontSize: portalTypography.chip, background: "#f4f8fb" }} />
              <Box sx={{ flex: 1 }} />
              <Typography sx={{ fontSize: portalTypography.subtitle, color: "#6b7d90" }}>
                Showing 1-6 of 32 messages
              </Typography>
            </Box>

            <Box sx={{ p: 1.15, background: "#fbfdfe" }}>
              {visibleThreads.map((thread, index) => (
                <MessageRow key={thread.id} thread={thread} selected={index < 2} />
              ))}
            </Box>
          </Paper>
        </Box>
      </Box>
    </PortalShell>
  );
}
