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

import { fetchDenials, type DenialsResponse } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const APPEAL_STATUS_CHIP: Record<string, { bg: string; fg: string }> = {
  "Not Appealed": { bg: "#7f1d1d", fg: "#fca5a5" },
  "In Review": { bg: "#78350f", fg: "#fcd34d" },
  Overturned: { bg: "#14532d", fg: "#86efac" },
  Upheld: { bg: "#334155", fg: "#cbd5e1" },
  "Written Off": { bg: "#334155", fg: "#94a3b8" },
};

function AppealStatusChip({ label }: { label: string | null }) {
  const s = APPEAL_STATUS_CHIP[label || ""] || { bg: "#334155", fg: "#cbd5e1" };
  return <Chip label={label || "—"} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

function currency(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const BAR_COLORS = ["#f87171", "#fbbf24", "#fb923c", "#60a5fa", "#94a3b8"];

export default function DenialsAppealsPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<DenialsResponse | null>(null);
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
    fetchDenials(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load denials.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const rows = data?.denials ?? [];

  const metrics = useMemo(
    () => [
      { label: "Total Denials", value: String(data?.total_denials ?? 0), caption: "All denial records on file" },
      {
        label: "Appeal Rate",
        value: data?.appeal_rate !== null && data?.appeal_rate !== undefined ? `${data.appeal_rate}%` : "—",
        caption: `${data?.appeals_filed ?? 0} appeals filed out of ${data?.total_denials ?? 0}`,
        color: "#fbbf24",
      },
      {
        label: "Overturn Rate",
        value: data?.overturn_rate !== null && data?.overturn_rate !== undefined ? `${data.overturn_rate}%` : "—",
        caption: "Of appeals decided so far",
        color: "#4ade80",
      },
      {
        label: "Avg Resolution",
        value: data?.avg_resolution_days !== null && data?.avg_resolution_days !== undefined ? `${data.avg_resolution_days} days` : "—",
        caption: "Mean processing appeal age",
      },
    ],
    [data]
  );

  return (
    <Box>
      <PageHeader title="Denials & Appeals" subtitle="Denial tracking, root cause analysis, and appeal management" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its denials.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 2, alignItems: "flex-start", mb: 2.5 }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                DENIAL REASONS BREAKDOWN
              </Typography>
              {(data?.reason_breakdown ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 13, color: "#7f97b3" }}>No denials on file.</Typography>
              ) : (
                <Box sx={{ display: "grid", gap: 1.5 }}>
                  {(data?.reason_breakdown ?? []).map((r, i) => (
                    <Box key={r.reason}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.4 }}>
                        <Typography sx={{ fontSize: 13, color: "#e2e8f0", fontWeight: 600 }}>{r.reason}</Typography>
                        <Typography sx={{ fontSize: 12.5, color: "#94a3b8" }}>
                          {r.count} claim{r.count === 1 ? "" : "s"} ({r.percent}%)
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={r.percent}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          bgcolor: "#1f3a5c",
                          "& .MuiLinearProgress-bar": { bgcolor: BAR_COLORS[i % BAR_COLORS.length] },
                        }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>Appeal Guidance Tips</Typography>
              <Typography sx={{ fontSize: 12, color: "#cbd5e1", mb: 1.5 }}>
                Timely filing rules apply to all appeals. Medicare Redeterminations (Level 1) must be submitted within 120
                days from the initial denial notice date.
              </Typography>
              <Typography sx={{ fontSize: 12, color: "#cbd5e1" }}>
                Always ensure supporting documentation (e.g. F2F encounter records, signed certifications) is securely
                attached before executing an expired-certification appeal.
              </Typography>
            </Paper>
          </Box>

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              ACTIVE APPEALS &amp; DENIALS REGISTRY
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Patient", "Payer", "Denial Date", "Denial Code", "Primary Reason", "Amount", "Appeal Status", "Days Elapsed"].map(
                      (h) => (
                        <TableCell
                          key={h}
                          sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}
                        >
                          {h.toUpperCase()}
                        </TableCell>
                      )
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No denial records found for this agency.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rows.map((d) => (
                      <TableRow key={d.denial_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {d.patient_name || d.mrn || d.patient_id}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{d.payer_name || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{d.denial_date || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{d.carc_code || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {d.reason_description || "—"}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(d.denied_amount)}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <AppealStatusChip label={d.appeal_status_label} />
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {d.days_elapsed !== null ? `${d.days_elapsed}d` : "—"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography sx={{ fontSize: 11.5, color: "#7f97b3", px: 2, py: 1.2 }}>
              Showing {rows.length} of {data?.total_denials ?? 0} denial records
            </Typography>
          </Paper>
        </>
      )}
    </Box>
  );
}
