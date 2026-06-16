import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { fetchOwnerDashboard } from "../api/dashboard";
import type { OwnerDashboardResponse } from "../api/dashboard";

// =========================================================
// METRIC CARD
// =========================================================

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
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

export default function OwnerDashboard() {
  const [data, setData] = useState<OwnerDashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOwnerDashboard()
      .then(setData)
      .catch(() => setError("Failed to load owner dashboard"))
      .finally(() => setLoading(false));
  }, []);

  // =========================================================
  // STATES
  // =========================================================

  if (loading) {
    return (
      <Box
        sx={{
          py: 6,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!data) {
    return <Alert severity="warning">No owner dashboard data</Alert>;
  }

  // =========================================================
  // UI
  // =========================================================

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Owner Dashboard
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        System-wide visibility across all tenants, tasks, incidents, and compliance status.
      </Typography>

      {/* ✅ METRICS */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {data.metrics.length === 0 ? (
          <Grid>
            <Alert severity="info">No system metrics available</Alert>
          </Grid>
        ) : (
          data.metrics.map((metric) => (
            <Grid key={metric.key}>
              <MetricCard
                label={metric.label}
                value={metric.value}
              />
            </Grid>
          ))
        )}
      </Grid>

      {/* ✅ TENANT SUMMARY */}
      {data.tenant_summary && data.tenant_summary.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Tenant Summary
          </Typography>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Tenant</strong></TableCell>
                <TableCell><strong>Open Tasks</strong></TableCell>
                <TableCell><strong>Incidents</strong></TableCell>
                <TableCell><strong>IDG Blockers</strong></TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {data.tenant_summary.map((tenant) => (
                <TableRow key={tenant.tenant_id}>
                  <TableCell>{tenant.tenant_name}</TableCell>
                  <TableCell>{tenant.open_tasks}</TableCell>
                  <TableCell>{tenant.incidents}</TableCell>
                  <TableCell>{tenant.blocked_patients}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* ✅ EMPTY STATE */}
      {data.tenant_summary && data.tenant_summary.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No tenant summary data available
        </Alert>
      )}
    </Container>
  );
}
