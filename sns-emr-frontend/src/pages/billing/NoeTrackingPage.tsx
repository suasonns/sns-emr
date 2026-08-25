import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  FormControlLabel,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { fetchNoeTracking, type NoeTrackingResponse, type NoeTrackingRow } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";

function MetricCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2, minWidth: 140, borderTop: `3px solid ${color}` }}>
      <Typography sx={{ fontSize: 10.5, fontWeight: 700, color: "#64748b", letterSpacing: 0.3 }}>
        {label.toUpperCase()}
      </Typography>
      <Typography sx={{ fontSize: 26, fontWeight: 800, color }}>{value}</Typography>
    </Paper>
  );
}

function NoeChip({ row }: { row: NoeTrackingRow }) {
  if (row.penalty_reason && !row.election_date) {
    return <Chip label="Data gap" size="small" sx={{ bgcolor: "#e2e8f0", color: "#334155", fontWeight: 700 }} />;
  }
  if (row.is_exempt) {
    return <Chip label="Exempt" size="small" sx={{ bgcolor: "#e0e7ff", color: "#3730a3", fontWeight: 700 }} />;
  }
  if (row.is_late) {
    return <Chip label="Late" size="small" sx={{ bgcolor: "#fee2e2", color: "#991b1b", fontWeight: 700 }} />;
  }
  if (!row.noe_filed) {
    return <Chip label="Unfiled" size="small" sx={{ bgcolor: "#fef3c7", color: "#92400e", fontWeight: 700 }} />;
  }
  return <Chip label="On time" size="small" sx={{ bgcolor: "#dcfce7", color: "#166534", fontWeight: 700 }} />;
}

export default function NoeTrackingPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<NoeTrackingResponse | null>(null);
  const [lateOnly, setLateOnly] = useState(false);
  const [unfiledOnly, setUnfiledOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchNoeTracking(selectedAgencyId, { late_only: lateOnly, unfiled_only: unfiledOnly, limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load NOE tracking.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId, lateOnly, unfiledOnly]);

  return (
    <Box>
      <Typography sx={{ fontSize: 20, fontWeight: 800, color: "#0f172a" }}>NOE Tracking</Typography>
      <Typography sx={{ fontSize: 12.5, color: "#64748b", mb: 2 }}>
        Real CMS 5-calendar-day Notice of Election filing rule (42 CFR 418.24(b)) applied to every initial benefit
        period. Periods missing a real election date show a data gap rather than a fabricated status.
      </Typography>

      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its NOE tracking.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <Box>
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <MetricCard label="Total Periods" value={data?.count ?? 0} color="#1f4a78" />
            <MetricCard label="Late Filings" value={data?.late_count ?? 0} color="#dc2626" />
            <MetricCard label="Unfiled" value={data?.unfiled_count ?? 0} color="#f59e0b" />
          </Stack>

          <Stack direction="row" spacing={3} sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch checked={lateOnly} onChange={(e) => setLateOnly(e.target.checked)} />}
              label="Late only"
            />
            <FormControlLabel
              control={<Switch checked={unfiledOnly} onChange={(e) => setUnfiledOnly(e.target.checked)} />}
              label="Unfiled only"
            />
          </Stack>

          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "#f1f5f9" }}>
                    <TableCell sx={{ fontWeight: 700 }}>Patient</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>MRN</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Election Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>NOE Submitted</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Non-Covered Days</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Detail</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.noe_tracking.length ?? 0) === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: "center", color: "#94a3b8", py: 4 }}>
                        No initial benefit periods match this filter for this agency.
                      </TableCell>
                    </TableRow>
                  ) : (
                    data!.noe_tracking.map((row) => (
                      <TableRow key={row.benefit_period_id} hover>
                        <TableCell>{row.patient_name || "—"}</TableCell>
                        <TableCell>{row.mrn || "—"}</TableCell>
                        <TableCell>{row.election_date || "—"}</TableCell>
                        <TableCell>{row.noe_submitted_date || "Not filed"}</TableCell>
                        <TableCell>{row.non_covered_days ?? "—"}</TableCell>
                        <TableCell>
                          <NoeChip row={row} />
                        </TableCell>
                        <TableCell sx={{ fontSize: 12, color: "#64748b" }}>{row.penalty_reason || "—"}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      )}
    </Box>
  );
}
