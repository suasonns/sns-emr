import { Chip } from "@mui/material";

// Color map mirrors the 9-state lifecycle enforced server-side in
// app/billing/models/facility_collection_alert.py
// (FACILITY_COLLECTION_ALERT_STATUSES). Purely presentational -- the
// backend is the single source of truth for which transitions are legal.
const STATUS_COLORS: Record<string, string> = {
  OPEN: "#f87171",
  ACKNOWLEDGED: "#fbbf24",
  IN_PROGRESS: "#38bdf8",
  SNOOZED: "#a78bfa",
  DISMISSED: "#64748b",
  RESOLVED: "#4ade80",
  AUTO_RESOLVED: "#22d3ee",
  SUPPRESSED: "#94a3b8",
  EXPIRED: "#64748b",
};

function label(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

export default function AlertStatusChip({ value }: { value: string }) {
  const color = STATUS_COLORS[value] || "#94a3b8";
  return (
    <Chip
      size="small"
      label={label(value)}
      sx={{ bgcolor: `${color}22`, color, fontWeight: 700, fontSize: 11 }}
    />
  );
}
