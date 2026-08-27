import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import { fetchNoeTracking, type NoeTrackingResponse, type NoeTrackingRow } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const FILING_WINDOW_DAYS = 5; // 42 CFR 418.24(b): 5 calendar days from election to file the NOE

function addDays(dateStr: string, days: number): Date {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d;
}

function daysFromToday(date: Date): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  return Math.round((date.getTime() - today.getTime()) / 86400000);
}

type NoeState = "filed_on_time" | "filed_late" | "exempt" | "approaching" | "overdue" | "data_gap";

function classify(row: NoeTrackingRow): { state: NoeState; dueDate: Date | null; remaining: number | null } {
  if (!row.election_date) return { state: "data_gap", dueDate: null, remaining: null };
  const dueDate = addDays(row.election_date, FILING_WINDOW_DAYS);
  const remaining = daysFromToday(new Date(dueDate));
  if (row.is_exempt) return { state: "exempt", dueDate, remaining };
  if (row.noe_filed) return { state: row.is_late ? "filed_late" : "filed_on_time", dueDate, remaining };
  if (remaining < 0) return { state: "overdue", dueDate, remaining };
  if (remaining <= 2) return { state: "approaching", dueDate, remaining };
  return { state: "filed_on_time", dueDate, remaining }; // still within window, not yet due
}

function StatusChip({ state }: { state: NoeState }) {
  const map: Record<NoeState, { label: string; bg: string; fg: string }> = {
    filed_on_time: { label: "Filed", bg: "#14532d", fg: "#86efac" },
    filed_late: { label: "Late", bg: "#7f1d1d", fg: "#fca5a5" },
    exempt: { label: "Exempt", bg: "#312e81", fg: "#c7d2fe" },
    approaching: { label: "Approaching", bg: "#78350f", fg: "#fcd34d" },
    overdue: { label: "Overdue", bg: "#7f1d1d", fg: "#fca5a5" },
    data_gap: { label: "Data gap", bg: "#334155", fg: "#cbd5e1" },
  };
  const s = map[state];
  return <Chip label={s.label} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

export default function NoeTrackingPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<NoeTrackingResponse | null>(null);
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
    fetchNoeTracking(selectedAgencyId, { limit: 500 })
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
  }, [selectedAgencyId]);

  const rows = data?.noe_tracking ?? [];

  const classified = useMemo(() => rows.map((row) => ({ row, ...classify(row) })), [rows]);

  const metrics = useMemo(() => {
    const total = rows.length;
    const filedOnTime = classified.filter((c) => c.state === "filed_on_time" && c.row.noe_filed).length;
    const approaching = classified.filter((c) => c.state === "approaching").length;
    const lateOrMissed = classified.filter((c) => c.state === "filed_late" || c.state === "overdue").length;
    const filedTotal = classified.filter((c) => c.row.noe_filed).length;
    const onTimePct = filedTotal > 0 ? Math.round((filedOnTime / filedTotal) * 1000) / 10 : 0;
    return {
      total,
      approaching,
      lateOrMissed,
      onTimePct,
      cards: [
        { label: "Active NOEs", value: String(total), caption: "Under review or processing" },
        { label: "Filed On Time", value: `${filedOnTime} (${onTimePct}%)`, caption: "Target compliance > 95%", color: "#4ade80" },
        { label: "Approaching Deadline", value: String(approaching), caption: "Requires immediate batch upload", color: approaching > 0 ? "#fbbf24" : "#4ade80" },
        { label: "Late / Missed", value: String(lateOrMissed), caption: "Penalty assessment active", color: lateOrMissed > 0 ? "#f87171" : "#4ade80" },
      ],
    };
  }, [rows, classified]);

  return (
    <Box>
      <PageHeader
        title="NOE Tracking"
        subtitle="Notice of Election filing status and 5-day deadline compliance"
      />

      {metrics.approaching > 0 ? (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            bgcolor: "#450a0a",
            border: "1px solid #7f1d1d",
            borderRadius: 1.5,
            px: 2,
            py: 1.2,
            mb: 2,
          }}
        >
          <WarningAmberIcon sx={{ color: "#f87171", fontSize: 18 }} />
          <Typography sx={{ fontSize: 13, color: "#fca5a5", fontWeight: 700 }}>
            {metrics.approaching} NOE{metrics.approaching === 1 ? "" : "s"} approaching 5-day deadline — file immediately to
            avoid billing penalties
          </Typography>
        </Box>
      ) : null}

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its NOE tracking.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics.cards} />

          <Box sx={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 2, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
                ACTIVE NOTICE OF ELECTION FILINGS
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {["Patient ID", "Election Date", "Due Date", "Filed Date", "Status", "Remaining (Days)"].map((h) => (
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
                    {classified.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                          No initial benefit periods found for this agency.
                        </TableCell>
                      </TableRow>
                    ) : (
                      classified.map(({ row, state, remaining }) => (
                        <TableRow key={row.benefit_period_id} hover>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {row.mrn || row.patient_id}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {row.election_date || "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {row.election_date ? addDays(row.election_date, FILING_WINDOW_DAYS).toISOString().slice(0, 10) : "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {row.noe_submitted_date || "—"}
                          </TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <StatusChip state={state} />
                          </TableCell>
                          <TableCell sx={{ color: remaining !== null && remaining < 0 ? "#f87171" : "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {remaining !== null ? remaining : "—"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>5-Day Filing Rules</Typography>
              <Box sx={{ display: "grid", gap: 1.2, mb: 2 }}>
                {[
                  "Day 0: Election Date",
                  "Days 1-4: Clinical note finalized & NOE batch compiled",
                  "Day 5: Absolute filing deadline to avoid billing reduction",
                ].map((step, i) => (
                  <Box key={step} sx={{ display: "flex", gap: 1, alignItems: "flex-start" }}>
                    <Box
                      sx={{
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        bgcolor: "#0f766e",
                        color: "#fff",
                        fontSize: 11,
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      {i + 1}
                    </Box>
                    <Typography sx={{ fontSize: 12, color: "#cbd5e1" }}>{step}</Typography>
                  </Box>
                ))}
              </Box>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mb: 0.5 }}>
                Filing Compliance Rate <Box component="span" sx={{ color: "#4ade80", fontWeight: 700 }}>{metrics.onTimePct}%</Box>
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, metrics.onTimePct)}
                sx={{ height: 6, borderRadius: 3, bgcolor: "#1f3a5c", "& .MuiLinearProgress-bar": { bgcolor: "#4ade80" } }}
              />
              <Typography sx={{ fontSize: 10.5, color: "#7f97b3", mt: 1 }}>
                Failing to file within 5 days results in non-reimbursable hospice days from the date of election to the
                date of filing.
              </Typography>
            </Paper>
          </Box>
        </>
      )}
    </Box>
  );
}
