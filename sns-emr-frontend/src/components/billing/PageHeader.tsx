import type { ReactNode } from "react";
import { Box, Button, Typography } from "@mui/material";
import CloudSyncIcon from "@mui/icons-material/CloudSync";
import DownloadIcon from "@mui/icons-material/Download";

// Page header pattern reconciled from the SNS Hospice Solutions Figma
// "External Billing Services" reference (docs/design/biller-dashboard-figma):
// large title + one-line subtitle on the left, one outlined secondary action
// and one solid teal primary action on the right. Defaults to the
// "Export Audit Logs" / "Sync Clearinghouse" pair used on every page in the
// reference; pass `actions` to override for a page with different real
// capabilities (never invent a write action that has no backend yet).
export default function PageHeader({
  title,
  subtitle,
  actions,
  onExportAuditLogs,
  onSyncClearinghouse,
}: {
  title: string;
  subtitle: string;
  actions?: ReactNode;
  onExportAuditLogs?: () => void;
  onSyncClearinghouse?: () => void;
}) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 2.5, gap: 2 }}>
      <Box sx={{ minWidth: 0 }}>
        <Typography sx={{ fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>{title}</Typography>
        <Typography sx={{ fontSize: 13, color: "#94a3b8", mt: 0.3 }}>{subtitle}</Typography>
      </Box>
      <Box sx={{ display: "flex", gap: 1.2, flexShrink: 0 }}>
        {actions ?? (
          <>
            <Button
              variant="outlined"
              size="small"
              startIcon={<DownloadIcon fontSize="small" />}
              onClick={onExportAuditLogs}
              sx={{ borderColor: "#334155", color: "#cbd5e1", textTransform: "none", fontWeight: 700, "&:hover": { borderColor: "#475569" } }}
            >
              Export Audit Logs
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<CloudSyncIcon fontSize="small" />}
              onClick={onSyncClearinghouse}
              sx={{ bgcolor: "#10b7a2", textTransform: "none", fontWeight: 700, "&:hover": { bgcolor: "#0f766e" } }}
            >
              Sync Clearinghouse
            </Button>
          </>
        )}
      </Box>
    </Box>
  );
}
