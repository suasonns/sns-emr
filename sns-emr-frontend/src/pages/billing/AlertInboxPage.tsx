import { useEffect, useMemo, useState } from "react";
import {
  Alert as MuiAlert,
  Box,
  CircularProgress,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import {
  ALERT_SEVERITIES,
  DashboardApiError,
  fetchFacilityCollectionAlerts,
  type FacilityCollectionAlert,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import AlertDetailDrawer from "../../components/billing/AlertDetailDrawer";
import AlertSeverityChip from "../../components/billing/AlertSeverityChip";
import AlertStatusChip from "../../components/billing/AlertStatusChip";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow, type MetricCardDef } from "../../components/billing/MetricCardRow";
import PageHeader from "../../components/billing/PageHeader";

// Status filter chips required by the approved Phase 2 architecture. "All"
// fetches every non-filtered row from GET /alerts (the only server-side
// filter it supports is `status`); the rest map 1:1 to that param.
const STATUS_FILTERS = [
  "ALL",
  "OPEN",
  "ACKNOWLEDGED",
  "IN_PROGRESS",
  "SNOOZED",
  "DISMISSED",
  "RESOLVED",
  "AUTO_RESOLVED",
  "SUPPRESSED",
] as const;

function label(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

function currency(value: string | null): string {
  if (!value) return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function summarizeError(error: unknown, fallback: string): string {
  if (error instanceof DashboardApiError) {
    if (error.status === 403) return "Authorization denied for this action.";
    return error.message || fallback;
  }
  if (error instanceof Error) {
    if (/Failed to fetch|NetworkError|Load failed/i.test(error.message)) {
      return "Backend unavailable. Please try again shortly.";
    }
    return error.message || fallback;
  }
  return fallback;
}

export default function AlertInboxPage() {
  const { selectedAgencyId } = useAgency();
  const [alerts, setAlerts] = useState<FacilityCollectionAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const [statusFilter, setStatusFilter] = useState<(typeof STATUS_FILTERS)[number]>("OPEN");
  const [severityFilter, setSeverityFilter] = useState("");
  const [alertTypeFilter, setAlertTypeFilter] = useState("");
  const [search, setSearch] = useState("");

  const [selectedAlert, setSelectedAlert] = useState<FacilityCollectionAlert | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      setAlerts([]);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    const statusParam = statusFilter === "ALL" ? undefined : statusFilter;
    fetchFacilityCollectionAlerts(selectedAgencyId, statusParam)
      .then((res) => {
        if (isMounted) setAlerts(res.items);
      })
      .catch((err) => {
        if (isMounted) setError(summarizeError(err, "Unable to load facility collection alerts."));
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId, statusFilter, reloadToken]);

  const alertTypes = useMemo(
    () => Array.from(new Set(alerts.map((a) => a.alert_type))).sort(),
    [alerts]
  );

  // Additional filters (severity/type) and search apply client-side to the
  // already-fetched status-filtered list. Search matches only fields
  // present in the alert payload (id, patient_id, assigned_to, alert_type)
  // -- patient name/MRN/agency name are not part of this response and are
  // not fabricated here.
  const visibleAlerts = useMemo(() => {
    const term = search.trim().toLowerCase();
    return alerts.filter((a) => {
      if (severityFilter && a.severity !== severityFilter) return false;
      if (alertTypeFilter && a.alert_type !== alertTypeFilter) return false;
      if (!term) return true;
      return (
        a.id.toLowerCase().includes(term) ||
        (a.patient_id ?? "").toLowerCase().includes(term) ||
        (a.assigned_to ?? "").toLowerCase().includes(term) ||
        a.alert_type.toLowerCase().includes(term)
      );
    });
  }, [alerts, severityFilter, alertTypeFilter, search]);

  const metrics: MetricCardDef[] = useMemo(() => {
    const openCount = alerts.filter((a) => a.status === "OPEN").length;
    const activeCount = alerts.filter((a) => a.status === "ACKNOWLEDGED" || a.status === "IN_PROGRESS").length;
    const snoozedCount = alerts.filter((a) => a.status === "SNOOZED").length;
    const resolvedCount = alerts.filter(
      (a) => a.status === "RESOLVED" || a.status === "AUTO_RESOLVED"
    ).length;
    return [
      { label: "Open Alerts", value: String(openCount), caption: "Awaiting action", color: "#f87171" },
      { label: "In Progress", value: String(activeCount), caption: "Acknowledged or working", color: "#38bdf8" },
      { label: "Snoozed", value: String(snoozedCount), caption: "Deferred follow-up", color: "#a78bfa" },
      { label: "Resolved", value: String(resolvedCount), caption: "Closed this view", color: "#4ade80" },
    ];
  }, [alerts]);

  function openDetail(alert: FacilityCollectionAlert) {
    setSelectedAlert(alert);
    setDrawerOpen(true);
  }

  function handleUpdated(updated: FacilityCollectionAlert) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
    setSelectedAlert(updated);
    setReloadToken((t) => t + 1);
  }

  return (
    <Box>
      <PageHeader
        title="Alert Inbox"
        subtitle="Operational view of facility collection alerts across the lifecycle."
        actions={<Box />}
      />
      <HipaaBanner />
      <MetricCardRow metrics={metrics} />

      <Paper variant="outlined" sx={{ bgcolor: "#0f1b2d", borderColor: "#1f3a5c", borderRadius: 2, p: 2, mb: 2 }}>
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(_e, value) => value && setStatusFilter(value)}
          sx={{ flexWrap: "wrap", mb: 2 }}
        >
          {STATUS_FILTERS.map((status) => (
            <ToggleButton key={status} value={status} size="small" sx={{ textTransform: "none", fontSize: 12 }}>
              {status === "ALL" ? "All Alerts" : label(status)}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
          <TextField
            select
            label="Severity"
            size="small"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            sx={{ minWidth: 140 }}
          >
            <MenuItem value="">All Severities</MenuItem>
            {ALERT_SEVERITIES.map((sev) => (
              <MenuItem key={sev} value={sev}>
                {label(sev)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Alert Type"
            size="small"
            value={alertTypeFilter}
            onChange={(e) => setAlertTypeFilter(e.target.value)}
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="">All Types</MenuItem>
            {alertTypes.map((type) => (
              <MenuItem key={type} value={type}>
                {label(type)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Search (Patient ID, Alert ID, Assigned User, Type)"
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ minWidth: 320, flexGrow: 1 }}
          />
        </Box>
      </Paper>

      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}

      <TableContainer component={Paper} variant="outlined" sx={{ bgcolor: "#0f1b2d", borderColor: "#1f3a5c" }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ color: "#7f97b3" }}>Status</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Severity</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Patient</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Alert Type</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Outstanding</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Created</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Assigned To</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Last Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={22} />
                </TableCell>
              </TableRow>
            )}
            {!loading && visibleAlerts.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4, color: "#7f97b3" }}>
                  No alerts match the current filters.
                </TableCell>
              </TableRow>
            )}
            {!loading &&
              visibleAlerts.map((alert) => (
                <TableRow
                  key={alert.id}
                  hover
                  onClick={() => openDetail(alert)}
                  sx={{ cursor: "pointer" }}
                >
                  <TableCell>
                    <AlertStatusChip value={alert.status} />
                  </TableCell>
                  <TableCell>
                    <AlertSeverityChip value={alert.severity} />
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {alert.patient_id || "—"}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>{label(alert.alert_type)}</TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {currency(alert.outstanding_amount)}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {alert.created_at ? new Date(alert.created_at).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {alert.assigned_to || "Unassigned"}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {alert.updated_at ? new Date(alert.updated_at).toLocaleDateString() : "—"}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      <AlertDetailDrawer
        alert={selectedAlert}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onUpdated={handleUpdated}
      />

      {!selectedAgencyId && (
        <Typography sx={{ mt: 2, color: "#7f97b3", fontSize: 12.5 }}>
          Select an agency to view its facility collection alerts.
        </Typography>
      )}
    </Box>
  );
}
