import { Box, CircularProgress, Stack, Typography } from "@mui/material";

import { type FacilityCollectionAlertHistoryItem } from "../../api/dashboard";

function formatFieldChange(item: FacilityCollectionAlertHistoryItem): string {
  const field = item.field_name || "field";
  const prev = item.previous_value ?? "—";
  const next = item.new_value ?? "—";
  return `${field}: ${prev} → ${next}`;
}

function formatTimestamp(value: string | null): string {
  if (!value) return "Unknown time";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

// Renders the audit trail for a single alert (GET .../alerts/{id}/history),
// backed by the same FacilityPaymentAuditLog table already used for
// expectation/allocation audit summaries -- no new audit infrastructure.
export default function AlertHistoryTimeline({
  loading,
  error,
  items,
}: {
  loading: boolean;
  error: string | null;
  items: FacilityCollectionAlertHistoryItem[];
}) {
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
        <CircularProgress size={22} />
      </Box>
    );
  }
  if (error) {
    return (
      <Typography sx={{ color: "#f87171", fontSize: 12.5, py: 1 }}>{error}</Typography>
    );
  }
  if (items.length === 0) {
    return (
      <Typography sx={{ color: "#7f97b3", fontSize: 12.5, py: 1 }}>
        No history recorded for this alert yet.
      </Typography>
    );
  }
  return (
    <Stack spacing={1.5} sx={{ py: 1 }}>
      {items.map((item) => (
        <Box
          key={item.id}
          sx={{ borderLeft: "2px solid #1f3a5c", pl: 1.5, py: 0.25 }}
        >
          <Typography sx={{ fontSize: 12, color: "#e2e8f0", fontWeight: 700 }}>
            {formatFieldChange(item)}
          </Typography>
          {item.reason && (
            <Typography sx={{ fontSize: 12, color: "#cbd5e1" }}>{item.reason}</Typography>
          )}
          <Typography sx={{ fontSize: 11, color: "#7f97b3" }}>
            {formatTimestamp(item.created_at)}
            {item.role ? ` · ${item.role}` : ""}
          </Typography>
        </Box>
      ))}
    </Stack>
  );
}
