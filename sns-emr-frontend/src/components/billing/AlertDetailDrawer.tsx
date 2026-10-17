import { useEffect, useState } from "react";
import { Box, Divider, Drawer, IconButton, Stack, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import {
  DashboardApiError,
  fetchAlertHistory,
  type FacilityCollectionAlert,
  type FacilityCollectionAlertHistoryItem,
} from "../../api/dashboard";
import AlertActionsMenu from "./AlertActionsMenu";
import AlertHistoryTimeline from "./AlertHistoryTimeline";
import AlertSeverityChip from "./AlertSeverityChip";
import AlertStatusChip from "./AlertStatusChip";

function currency(value: string | null): string {
  if (!value) return "Not available";
  const n = Number(value);
  if (Number.isNaN(n)) return "Not available";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function label(value: string | null): string {
  if (!value) return "Not available";
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

function formatDate(value: string | null): string {
  if (!value) return "Not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function DetailRow({ labelText, value }: { labelText: string; value: string }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", py: 0.5 }}>
      <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>{labelText}</Typography>
      <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 600 }}>{value}</Typography>
    </Box>
  );
}

// Alert Detail: displays alert data, trigger explanation, ownership,
// resolution notes, and history -- per the approved Phase 2 wireframe.
// Opens as a side drawer rather than a separate route so the inbox table
// stays mounted (and its filters/scroll position preserved) behind it.
export default function AlertDetailDrawer({
  alert,
  open,
  onClose,
  onUpdated,
}: {
  alert: FacilityCollectionAlert | null;
  open: boolean;
  onClose: () => void;
  onUpdated: (alert: FacilityCollectionAlert) => void;
}) {
  const [historyItems, setHistoryItems] = useState<FacilityCollectionAlertHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !alert) return;
    let isMounted = true;
    setHistoryLoading(true);
    setHistoryError(null);
    fetchAlertHistory(alert.id)
      .then((res) => {
        if (isMounted) setHistoryItems(res.items);
      })
      .catch((err) => {
        if (!isMounted) return;
        const message =
          err instanceof DashboardApiError ? err.message : "Unable to load alert history.";
        setHistoryError(message);
      })
      .finally(() => {
        if (isMounted) setHistoryLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [open, alert]);

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 420, bgcolor: "#0b1626", height: "100%", p: 2.5, color: "#e2e8f0" }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
          <Typography sx={{ fontSize: 17, fontWeight: 800 }}>Alert Detail</Typography>
          <IconButton size="small" onClick={onClose} sx={{ color: "#94a3b8" }}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>

        {!alert ? (
          <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No alert selected.</Typography>
        ) : (
          <>
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <AlertStatusChip value={alert.status} />
              <AlertSeverityChip value={alert.severity} />
            </Stack>

            <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>Alert Data</Typography>
            <DetailRow labelText="Alert Type" value={label(alert.alert_type)} />
            <DetailRow labelText="Expected Amount" value={currency(alert.expected_amount)} />
            <DetailRow labelText="Received Amount" value={currency(alert.received_amount)} />
            <DetailRow labelText="Outstanding Amount" value={currency(alert.outstanding_amount)} />
            <DetailRow labelText="Due Date" value={alert.due_date || "Not available"} />
            <DetailRow
              labelText="Days Outstanding"
              value={alert.days_outstanding != null ? String(alert.days_outstanding) : "Not available"}
            />

            <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />

            <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>Trigger Explanation</Typography>
            <Typography sx={{ fontSize: 12.5, color: "#cbd5e1", mb: 1.5 }}>
              This alert was generated because the "{label(alert.alert_type)}" condition was met for
              the associated facility payment expectation. Auto-resolution clears it automatically
              once the underlying condition is no longer met.
            </Typography>

            <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />

            <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>Ownership</Typography>
            <DetailRow labelText="Assigned To" value={alert.assigned_to || "Unassigned"} />
            <DetailRow labelText="Acknowledged By" value={alert.acknowledged_by || "Not acknowledged"} />
            <DetailRow labelText="Acknowledged At" value={formatDate(alert.acknowledged_at)} />
            {alert.status === "SNOOZED" && (
              <DetailRow labelText="Snoozed Until" value={formatDate(alert.snoozed_until)} />
            )}

            {(alert.status === "DISMISSED" || alert.dismissal_reason_code) && (
              <>
                <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />
                <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>Dismissal</Typography>
                <DetailRow labelText="Reason" value={label(alert.dismissal_reason_code)} />
              </>
            )}

            {(alert.status === "RESOLVED" || alert.resolution_evidence) && (
              <>
                <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />
                <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>Resolution Notes</Typography>
                <Typography sx={{ fontSize: 12.5, color: "#cbd5e1" }}>
                  {alert.resolution_evidence || "Not available"}
                </Typography>
                <DetailRow labelText="Resolved By" value={alert.resolved_by || "Not available"} />
                <DetailRow labelText="Resolved At" value={formatDate(alert.resolved_at)} />
              </>
            )}

            <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />

            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
              <Typography sx={{ fontSize: 13, fontWeight: 700 }}>Actions</Typography>
              <AlertActionsMenu alert={alert} onUpdated={onUpdated} />
            </Stack>

            <Divider sx={{ my: 1.5, borderColor: "#1f3a5c" }} />

            <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 0.5 }}>History</Typography>
            <AlertHistoryTimeline loading={historyLoading} error={historyError} items={historyItems} />
          </>
        )}
      </Box>
    </Drawer>
  );
}
