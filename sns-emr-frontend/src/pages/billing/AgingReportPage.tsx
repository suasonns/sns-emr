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
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import { fetchAgingReport, type AgingReportResponse } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

// Standard healthcare AR aging report. Pure presentation over
// GET /billing/aging-report -- all calculation (Outstanding Balance =
// Total Charges - Posted Payments - Adjustments - Write-offs, aged from
// claim submission/export date) lives in the backend
// aging_report_service; no logic is duplicated here.

type ViewMode = "single" | "all";

function currency(value: string | undefined | null): string {
  if (value === undefined || value === null) return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const BUCKET_COLORS: Record<string, string> = {
  "0-30": "#4ade80",
  "31-60": "#fbbf24",
  "61-90": "#fb923c",
  "91-120": "#f87171",
  "120+": "#ef4444",
};

export default function AgingReportPage() {
  const { selectedAgencyId } = useAgency();
  const [viewMode, setViewMode] = useState<ViewMode>("single");
  const [data, setData] = useState<AgingReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (viewMode === "single" && !selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    const request =
      viewMode === "all"
        ? fetchAgingReport(undefined, { all_agencies: true })
        : fetchAgingReport(selectedAgencyId);
    request
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load aging report.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId, viewMode]);

  const metrics = useMemo(() => {
    const s = data?.summary;
    return [
      { label: "Total Outstanding", value: currency(s?.total_outstanding), caption: "Across all aged claims", color: "#f87171" },
      { label: "Claims Outstanding", value: String(s?.claim_count ?? 0), caption: "Balance > $0, submitted claims only" },
      { label: "Avg Days Outstanding", value: String(s?.average_days_outstanding ?? 0), caption: "Since claim submission/export date" },
      {
        label: "120+ Day Balance",
        value: currency(data?.by_bucket.find((b) => b.bucket === "120+")?.total_outstanding),
        caption: "Highest collection risk",
        color: "#ef4444",
      },
    ];
  }, [data]);

  const maxBucketTotal = useMemo(
    () => Math.max(1, ...(data?.by_bucket.map((b) => Number(b.total_outstanding)) ?? [1])),
    [data]
  );

  return (
    <Box>
      <PageHeader
        title="Aging Report"
        subtitle="Accounts-receivable aging by bucket, payer, agency, and claim"
        actions={
          <ToggleButtonGroup
            size="small"
            exclusive
            value={viewMode}
            onChange={(_e, next) => next && setViewMode(next)}
            sx={{
              "& .MuiToggleButton-root": { color: "#94a3b8", borderColor: "#334155", textTransform: "none", fontWeight: 700, fontSize: 12.5 },
              "& .Mui-selected": { color: "#fff !important", bgcolor: "#10b7a2 !important" },
            }}
          >
            <ToggleButton value="single">Current Agency</ToggleButton>
            <ToggleButton value="all">All Assigned Agencies</ToggleButton>
          </ToggleButtonGroup>
        }
      />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses and financial tallies. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {viewMode === "single" && !selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its aging report, or switch to "All Assigned Agencies".</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 2, mb: 2.5, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>
                Outstanding Balance by Aging Bucket
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1.2 }}>
                {(data?.by_bucket ?? []).map((b) => {
                  const pct = Math.min(100, (Number(b.total_outstanding) / maxBucketTotal) * 100);
                  return (
                    <Box key={b.bucket}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.4 }}>
                        <Typography sx={{ fontSize: 12, color: "#cbd5e1", fontWeight: 700 }}>{b.bucket} days</Typography>
                        <Typography sx={{ fontSize: 12, color: "#e2e8f0" }}>
                          {currency(b.total_outstanding)} ({b.claim_count})
                        </Typography>
                      </Box>
                      <Box sx={{ height: 8, borderRadius: 4, bgcolor: "#1f3a5c", overflow: "hidden" }}>
                        <Box sx={{ height: "100%", width: `${pct}%`, bgcolor: BUCKET_COLORS[b.bucket] || "#14b8a6", borderRadius: 4 }} />
                      </Box>
                    </Box>
                  );
                })}
              </Box>
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
                {viewMode === "all" ? "BY AGENCY" : "TOP PAYERS BY OUTSTANDING BALANCE"}
              </Typography>
              <TableContainer sx={{ maxHeight: 240 }}>
                <Table size="small">
                  <TableBody>
                    {viewMode === "all"
                      ? (data?.by_agency ?? []).map((a) => (
                          <TableRow key={a.tenant_id}>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{a.agency_name}</TableCell>
                            <TableCell sx={{ color: "#f87171", fontSize: 13, borderColor: "#1f3a5c", textAlign: "right" }}>
                              {currency(a.total_outstanding)}
                            </TableCell>
                            <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c", textAlign: "right" }}>
                              {a.claim_count} claims
                            </TableCell>
                          </TableRow>
                        ))
                      : (data?.by_payer ?? []).map((p) => (
                          <TableRow key={p.payer_name}>
                            <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.payer_name}</TableCell>
                            <TableCell sx={{ color: "#f87171", fontSize: 13, borderColor: "#1f3a5c", textAlign: "right" }}>
                              {currency(p.total_outstanding)}
                            </TableCell>
                            <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c", textAlign: "right" }}>
                              {p.claim_count} claims
                            </TableCell>
                          </TableRow>
                        ))}
                    {((viewMode === "all" ? data?.by_agency.length : data?.by_payer.length) ?? 0) === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} sx={{ textAlign: "center", color: "#7f97b3", py: 3, borderColor: "#1f3a5c" }}>
                          No outstanding balances.
                        </TableCell>
                      </TableRow>
                    ) : null}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Box>

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              CLAIM-LEVEL AGING DETAIL
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Patient", "Payer", "Agency", "Charges", "Payments", "Adjustments", "Write-offs", "Balance", "Submitted", "Days", "Bucket"].map(
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
                  {(data?.claims ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={11} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No claims with an outstanding balance.
                      </TableCell>
                    </TableRow>
                  ) : (
                    data!.claims.map((c) => (
                      <TableRow key={c.claim_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.mrn || c.patient_name || c.patient_id}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.payer_name}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.agency_name}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.total_charge)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.posted_payments)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.adjustments)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.write_offs)}</TableCell>
                        <TableCell sx={{ color: "#f87171", fontSize: 13, fontWeight: 700, borderColor: "#1f3a5c" }}>{currency(c.outstanding_balance)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.exported_at ? c.exported_at.slice(0, 10) : "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.days_outstanding}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Chip
                            label={c.bucket}
                            size="small"
                            sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: "#0b1626", color: BUCKET_COLORS[c.bucket] || "#e2e8f0", border: "1px solid #1f3a5c" }}
                          />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </>
      )}
    </Box>
  );
}
