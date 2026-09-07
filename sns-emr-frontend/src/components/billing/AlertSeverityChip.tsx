import { Chip } from "@mui/material";

// Color map mirrors FACILITY_COLLECTION_ALERT_SEVERITIES
// (app/billing/models/facility_collection_alert.py): LOW/MEDIUM/HIGH/CRITICAL.
const SEVERITY_COLORS: Record<string, string> = {
  LOW: "#94a3b8",
  MEDIUM: "#fbbf24",
  HIGH: "#f97316",
  CRITICAL: "#f87171",
};

function label(value: string): string {
  return value.charAt(0) + value.slice(1).toLowerCase();
}

export default function AlertSeverityChip({ value }: { value: string }) {
  const color = SEVERITY_COLORS[value] || "#94a3b8";
  return (
    <Chip
      size="small"
      label={label(value)}
      sx={{ bgcolor: `${color}22`, color, fontWeight: 700, fontSize: 11 }}
    />
  );
}
