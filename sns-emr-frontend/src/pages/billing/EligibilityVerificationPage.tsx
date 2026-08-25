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

import { fetchEligibilityRoster, type EligibilityRosterResponse } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const STATUS_CHIP: Record<string, { label: string; bg: string; fg: string }> = {
  ACTIVE: { label: "Active", bg: "#14532d", fg: "#86efac" },
  INACTIVE: { label: "Inactive", bg: "#7f1d1d", fg: "#fca5a5" },
  UNKNOWN: { label: "Pending", bg: "#78350f", fg: "#fcd34d" },
  ERROR: { label: "Pending", bg: "#78350f", fg: "#fcd34d" },
};

function StatusChip({ status }: { status: string | null }) {
  const s = STATUS_CHIP[String(status || "").toUpperCase()] || { label: status || "—", bg: "#334155", fg: "#cbd5e1" };
  return <Chip label={s.label} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

export default function EligibilityVerificationPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<EligibilityRosterResponse | null>(null);
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
    fetchEligibilityRoster(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load eligibility roster.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const rows = data?.roster ?? [];
  const verifiedPct =
    data && data.total_active > 0 ? Math.round((data.eligible_count / data.total_active) * 1000) / 10 : 0;

  const metrics = useMemo(
    () => [
      { label: "Total Active Census", value: String(data?.total_active ?? 0), caption: "Active patient insurance records" },
      {
        label: "Eligible Status",
        value: String(data?.eligible_count ?? 0),
        caption: `${verifiedPct}% of active roster verified`,
        color: "#4ade80",
      },
      {
        label: "Pending Re-Verify",
        value: String(data?.pending_count ?? 0),
        caption: "Verification needed",
        color: (data?.pending_count ?? 0) > 0 ? "#fbbf24" : "#4ade80",
      },
      {
        label: "Inactive / No Coverage",
        value: String(data?.inactive_count ?? 0),
        caption: "Immediate administrative action required",
        color: (data?.inactive_count ?? 0) > 0 ? "#f87171" : "#4ade80",
      },
    ],
    [data, verifiedPct]
  );

  return (
    <Box>
      <PageHeader title="Eligibility Verification" subtitle="Real-time eligibility status and verification tracking" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its eligibility roster.</Alert>
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
                PATIENT COVERAGE STATUS ROSTER
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {["Patient", "Primary Payer", "Subscriber ID", "Status", "Last Verified", "Next Due"].map((h) => (
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
                          No active insurance records found for this agency.
                        </TableCell>
                      </TableRow>
                    ) : (
                      rows.map((r) => (
                        <TableRow key={r.insurance_id} hover>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.patient_name || r.mrn || r.patient_id}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.subscriber_id || "—"}</TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <StatusChip status={r.eligibility_status} />
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.verified_at ? r.verified_at.slice(0, 10) : "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.next_verification_due || "—"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", px: 2, py: 1.2 }}>
                Showing {rows.length} of {data?.total_active ?? 0} patients
              </Typography>
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 0.5 }}>Upcoming Reverifications</Typography>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mb: 1.5 }}>Due within the next 7 days</Typography>
              {(data?.upcoming_reverifications ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>Nothing due in the next 7 days.</Typography>
              ) : (
                <Box sx={{ display: "grid", gap: 1 }}>
                  {(data?.upcoming_reverifications ?? []).map((u) => (
                    <Box
                      key={u.insurance_id}
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        bgcolor: "#0b1626",
                        border: "1px solid #1f3a5c",
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 1,
                      }}
                    >
                      <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 600 }}>
                        {u.patient_name || u.mrn}
                      </Typography>
                      <Chip
                        label={`In ${u.days_until_due} day${u.days_until_due === 1 ? "" : "s"}`}
                        size="small"
                        sx={{ fontSize: 11, height: 20, bgcolor: "#78350f", color: "#fcd34d", fontWeight: 700 }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </Paper>
          </Box>
        </>
      )}
    </Box>
  );
}
