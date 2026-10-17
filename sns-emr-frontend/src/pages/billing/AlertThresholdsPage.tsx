import { useEffect, useState } from "react";
import {
  Alert as MuiAlert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import {
  DashboardApiError,
  fetchAlertThresholds,
  updateAlertThreshold,
  type FacilityCollectionAlertThreshold,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import HipaaBanner from "../../components/billing/HipaaBanner";
import PageHeader from "../../components/billing/PageHeader";

function label(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

function summarizeError(error: unknown, fallback: string): string {
  if (error instanceof DashboardApiError) {
    if (error.status === 403) return "Authorization denied for this action.";
    if (error.status === 409) return error.message || "Concurrent update conflict.";
    return error.message || fallback;
  }
  if (error instanceof Error) return error.message || fallback;
  return fallback;
}

// Threshold Management: enable/disable an alert type and edit its
// amount/day threshold, with a required justification for suppression
// changes -- one row per alert type, backed by GET/PUT
// /billing/facility-payments/alert-thresholds.
export default function AlertThresholdsPage() {
  const { selectedAgencyId } = useAgency();
  const [rows, setRows] = useState<FacilityCollectionAlertThreshold[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editRow, setEditRow] = useState<FacilityCollectionAlertThreshold | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editDays, setEditDays] = useState("");
  const [editJustification, setEditJustification] = useState("");
  const [editBusy, setEditBusy] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      setRows([]);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchAlertThresholds(selectedAgencyId)
      .then((res) => {
        if (isMounted) setRows(res.items);
      })
      .catch((err) => {
        if (isMounted) setError(summarizeError(err, "Unable to load alert thresholds."));
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  function openEdit(row: FacilityCollectionAlertThreshold) {
    setEditRow(row);
    setEditAmount(row.threshold_amount ?? "");
    setEditDays(row.threshold_days != null ? String(row.threshold_days) : "");
    setEditJustification("");
    setEditError(null);
  }

  async function toggleEnabled(row: FacilityCollectionAlertThreshold, enabled: boolean) {
    setError(null);
    try {
      const updated = await updateAlertThreshold(
        row.alert_type,
        {
          enabled,
          threshold_amount: row.threshold_amount,
          threshold_days: row.threshold_days,
          justification: enabled ? undefined : "Suppressed from Alert Thresholds page.",
        },
        selectedAgencyId
      );
      setRows((prev) => prev.map((r) => (r.alert_type === updated.alert_type ? { ...r, ...updated, is_default: false } : r)));
    } catch (err) {
      setError(summarizeError(err, "Unable to update threshold."));
    }
  }

  async function saveEdit() {
    if (!editRow) return;
    setEditBusy(true);
    setEditError(null);
    try {
      const updated = await updateAlertThreshold(
        editRow.alert_type,
        {
          enabled: editRow.enabled,
          threshold_amount: editAmount.trim() || null,
          threshold_days: editDays.trim() ? Number(editDays.trim()) : null,
          justification: editJustification.trim() || undefined,
        },
        selectedAgencyId
      );
      setRows((prev) =>
        prev.map((r) => (r.alert_type === updated.alert_type ? { ...r, ...updated, is_default: false } : r))
      );
      setEditRow(null);
    } catch (err) {
      setEditError(summarizeError(err, "Unable to update threshold."));
    } finally {
      setEditBusy(false);
    }
  }

  return (
    <Box>
      <PageHeader
        title="Alert Thresholds"
        subtitle="Configure which alert types are active and their trigger thresholds."
        actions={<Box />}
      />
      <HipaaBanner />

      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}

      <TableContainer component={Paper} variant="outlined" sx={{ bgcolor: "#0f1b2d", borderColor: "#1f3a5c" }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ color: "#7f97b3" }}>Alert Type</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Enabled</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Threshold Amount</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Threshold Days</TableCell>
              <TableCell sx={{ color: "#7f97b3" }}>Source</TableCell>
              <TableCell sx={{ color: "#7f97b3" }} align="right">
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  Loading…
                </TableCell>
              </TableRow>
            )}
            {!loading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4, color: "#7f97b3" }}>
                  No threshold configuration available.
                </TableCell>
              </TableRow>
            )}
            {!loading &&
              rows.map((row) => (
                <TableRow key={row.alert_type}>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>{label(row.alert_type)}</TableCell>
                  <TableCell>
                    <Switch
                      checked={row.enabled}
                      size="small"
                      onChange={(e) => toggleEnabled(row, e.target.checked)}
                    />
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {row.threshold_amount ? `$${row.threshold_amount}` : "—"}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {row.threshold_days ?? "—"}
                  </TableCell>
                  <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5 }}>
                    {row.is_default ? "Default" : "Configured"}
                  </TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => openEdit(row)} sx={{ textTransform: "none" }}>
                      Edit
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      {!selectedAgencyId && (
        <Typography sx={{ mt: 2, color: "#7f97b3", fontSize: 12.5 }}>
          Select an agency to view its alert thresholds.
        </Typography>
      )}

      <Dialog open={Boolean(editRow)} onClose={() => setEditRow(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{editRow ? `Edit ${label(editRow.alert_type)} Threshold` : "Edit Threshold"}</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {editError && <MuiAlert severity="error">{editError}</MuiAlert>}
          <TextField
            label="Threshold Amount"
            size="small"
            value={editAmount}
            onChange={(e) => setEditAmount(e.target.value)}
            helperText="Leave blank for no amount threshold."
          />
          <TextField
            label="Threshold Days"
            size="small"
            value={editDays}
            onChange={(e) => setEditDays(e.target.value)}
            helperText="Leave blank for no day threshold."
          />
          <TextField
            label="Justification"
            size="small"
            value={editJustification}
            onChange={(e) => setEditJustification(e.target.value)}
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRow(null)} disabled={editBusy}>
            Cancel
          </Button>
          <Button variant="contained" onClick={saveEdit} disabled={editBusy}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
