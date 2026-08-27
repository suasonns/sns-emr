import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { fetchPocCertificationStatus, type PocCertificationRow } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const target = new Date(dateStr);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86400000);
}

function ReadyChip({ ready }: { ready: boolean }) {
  return (
    <Chip
      label={ready ? "Billing Ready" : "Not Ready"}
      size="small"
      sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: ready ? "#14532d" : "#7f1d1d", color: ready ? "#86efac" : "#fca5a5" }}
    />
  );
}

export default function PocCertificationPage() {
  const { selectedAgencyId } = useAgency();
  const [rows, setRows] = useState<PocCertificationRow[]>([]);
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
    fetchPocCertificationStatus(selectedAgencyId, { current_period_only: true, limit: 500 })
      .then((res) => {
        if (isMounted) setRows(res.poc_certification_status);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load POC & certification status.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const metrics = useMemo(() => {
    const total = rows.length;
    const signed = rows.filter((r) => r.plan_of_care?.physician_approval_status).length;
    const expiringSoon = rows.filter((r) => {
      const d = daysUntil(r.benefit_period.end_date);
      return d !== null && d >= 0 && d <= 14;
    }).length;
    const signedPct = total > 0 ? Math.round((signed / total) * 1000) / 10 : 0;
    return [
      { label: "Census Active Patients", value: String(total), caption: "Patients tracked for POC validation" },
      { label: "POC Current & Signed", value: String(signed), caption: `${signedPct}% of patients fully certified`, color: "#4ade80" },
      { label: "POC Expiring Soon", value: String(expiringSoon), caption: "Critical focus window (within 14 days)", color: expiringSoon > 0 ? "#fbbf24" : "#4ade80" },
      { label: "Cert Periods Active", value: String(total), caption: "Active tracking without gaps" },
    ];
  }, [rows]);

  const upcomingRecerts = useMemo(
    () =>
      rows
        .map((r) => ({ row: r, days: daysUntil(r.benefit_period.end_date) }))
        .filter((r) => r.days !== null && r.days <= 14)
        .sort((a, b) => (a.days ?? 0) - (b.days ?? 0))
        .slice(0, 8),
    [rows]
  );

  return (
    <Box>
      <PageHeader
        title="Plan of Care & Certifications"
        subtitle="Audit physician signatures on CMS-485 forms and track certification periods to maintain billing readiness."
      />
      <HipaaBanner />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its POC &amp; certification status.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 2, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
                CMS-485 SIGNING STATUS BY PATIENT
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {["Patient ID", "Cert Period", "POC Status", "Physician", "F2F Status", "Expiry Days"].map((h) => (
                        <TableCell
                          key={h}
                          sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}
                        >
                          {h.toUpperCase()}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rows.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                          No current benefit periods found for this agency.
                        </TableCell>
                      </TableRow>
                    ) : (
                      rows.map((row) => {
                        const days = daysUntil(row.benefit_period.end_date);
                        return (
                          <TableRow key={`${row.patient_id}-${row.benefit_period.id}`} hover>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                              {row.mrn || row.patient_id}
                            </TableCell>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                              {row.benefit_period.benefit_type} #{row.benefit_period.period_number}
                            </TableCell>
                            <TableCell sx={{ borderColor: "#1f3a5c" }}>
                              <ReadyChip ready={row.billing_ready} />
                            </TableCell>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                              {row.plan_of_care?.physician_name || "—"}
                            </TableCell>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                              {row.benefit_period.benefit_type === "RECERT" ? row.f2f_encounter?.status || "Missing" : "N/A"}
                            </TableCell>
                            <TableCell sx={{ color: days !== null && days <= 14 ? "#fbbf24" : "#e2e8f0", fontSize: 13, fontWeight: 700, borderColor: "#1f3a5c" }}>
                              {days !== null ? `${days} Days` : "—"}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 0.3 }}>Upcoming Recertifications</Typography>
              <Typography sx={{ fontSize: 11, color: "#7f97b3", mb: 1.5 }}>Expiring cert periods in the next 14 days</Typography>
              {upcomingRecerts.length === 0 ? (
                <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>No cert periods expiring in the next 14 days.</Typography>
              ) : (
                upcomingRecerts.map(({ row, days }) => (
                  <Box key={`${row.patient_id}-${row.benefit_period.id}`} sx={{ mb: 1.3, pb: 1.3, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#fff" }}>{row.mrn || row.patient_id}</Typography>
                    <Typography sx={{ fontSize: 11.5, color: (days ?? 0) <= 0 ? "#f87171" : "#fbbf24" }}>
                      {days !== null && days <= 0 ? `${Math.abs(days)} days overdue` : `${days} days remaining`}
                    </Typography>
                  </Box>
                ))
              )}
            </Paper>
          </Box>
        </>
      )}
    </Box>
  );
}
