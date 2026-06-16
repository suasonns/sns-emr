import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  Button,
} from "@mui/material";

// ✅ CLEAN IMPORTS
import {
  fetchTenantDashboard,
  fetchPatientComplianceDetail,
} from "../api/dashboard";

import type {
  TenantDashboardResponse,
  PatientComplianceDetailResponse,
} from "../api/dashboard";

// =========================================================
// METRIC CARD
// =========================================================

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5">{value}</Typography>
    </Paper>
  );
}

// =========================================================
// COMPONENT
// =========================================================

export default function TenantDashboard() {
  const [data, setData] = useState<TenantDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [patientDetail, setPatientDetail] = useState<PatientComplianceDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchTenantDashboard()
      .then(setData)
      .catch(() => setError("Failed to load tenant dashboard"))
      .finally(() => setLoading(false));
  }, []);

  const openPatientDetail = async (patientId: string) => {
    setSelectedPatientId(patientId);
    setDetailLoading(true);

    try {
      const res = await fetchPatientComplianceDetail(patientId);
      setPatientDetail(res as PatientComplianceDetailResponse);
    } catch {
      setPatientDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const closePatientDetail = () => {
    setSelectedPatientId(null);
    setPatientDetail(null);
  };

  // =========================================================
  // STATES
  // =========================================================

  if (loading) {
    return (
      <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) return <Alert severity="error">{error}</Alert>;
  if (!data) return <Alert severity="warning">No tenant dashboard data</Alert>;

  const dashboard = data.dashboard;

  // =========================================================
  // UI
  // =========================================================

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Tenant Dashboard
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        AI Enabled: {data.ai_enabled ? "YES" : "NO"}
      </Typography>

      {/* METRICS */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {dashboard.metrics.map((metric) => (
          <Grid key={metric.key}>
            <MetricCard label={metric.label} value={metric.value} />
          </Grid>
        ))}
      </Grid>

      {/* CONTENT */}
      <Grid container spacing={3}>
        {/* TASKS */}
        <Grid>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Open Tasks</Typography>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Task</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Due</TableCell>
                  <TableCell align="right">Action</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {dashboard.open_tasks.map((task) => (
                  <TableRow key={task.task_id}>
                    <TableCell>{task.patient_id}</TableCell>
                    <TableCell>{task.task_type}</TableCell>
                    <TableCell>
                      <Chip label={task.status} size="small" color="warning" />
                    </TableCell>
                    <TableCell>{task.due_at ?? "-"}</TableCell>
                    <TableCell align="right">
                      <Button onClick={() => openPatientDetail(task.patient_id)}>
                        Open
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* INCIDENTS */}
        <Grid>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Pending Incidents</Typography>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell align="right">Action</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {dashboard.pending_incidents.map((incident) => (
                  <TableRow key={incident.incident_id}>
                    <TableCell>{incident.patient_id}</TableCell>
                    <TableCell>{incident.incident_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={incident.incident_severity}
                        color={incident.incident_severity === "SENTINEL" ? "error" : "warning"}
                      />
                    </TableCell>
                    <TableCell>{incident.incident_date ?? "-"}</TableCell>
                    <TableCell align="right">
                      <Button onClick={() => openPatientDetail(incident.patient_id)}>
                        Open
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>

      {/* DIALOG */}
      <Dialog open={!!selectedPatientId} onClose={closePatientDetail}>
        <DialogTitle>Patient Compliance Detail</DialogTitle>

        <DialogContent>
          {detailLoading ? (
            <CircularProgress />
          ) : patientDetail ? (
            <Box>
              <Typography>
                Blocked: {patientDetail.blocked ? "YES" : "NO"}
              </Typography>
              <Typography>
                {patientDetail.blockers.join(" | ") || "No blockers"}
              </Typography>
            </Box>
          ) : (
            <Alert severity="warning">No patient detail available</Alert>
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
}
