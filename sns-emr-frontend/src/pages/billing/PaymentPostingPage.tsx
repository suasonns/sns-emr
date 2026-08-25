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

import { fetchRemittances, type RemittancesResponse } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const STATUS_CHIP: Record<string, { bg: string; fg: string }> = {
  POSTED: { bg: "#14532d", fg: "#86efac" },
  PARTIALLY_POSTED: { bg: "#78350f", fg: "#fcd34d" },
  RECEIVED: { bg: "#334155", fg: "#cbd5e1" },
};

function StatusChip({ status }: { status: string | null }) {
  const s = STATUS_CHIP[String(status || "").toUpperCase()] || { bg: "#334155", fg: "#cbd5e1" };
  return <Chip label={status || "—"} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

function currency(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const BAR_COLORS = ["#10b7a2", "#60a5fa", "#fbbf24", "#f87171", "#94a3b8"];

export default function PaymentPostingPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<RemittancesResponse | null>(null);
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
    fetchRemittances(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load payment posting data.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const rows = data?.remittances ?? [];
  const maxPayerTotal = Math.max(1, ...(data?.payer_breakdown ?? []).map((p) => p.total_paid));

  const metrics = useMemo(
    () => [
      { label: "Total Payments (MTD)", value: currency(data?.total_payments_mtd), caption: "All posted payments this month", color: "#4ade80" },
      { label: "ERA Received", value: String(data?.era_received_count ?? 0), caption: "Electronic Remittance Advices loaded" },
      { label: "Posted", value: String(data?.posted_count ?? 0), caption: "Successfully matched & credited", color: "#5eead4" },
      {
        label: "Pending Manual Match",
        value: String(data?.pending_manual_match_count ?? 0),
        caption: "Awaiting administrative review",
        color: (data?.pending_manual_match_count ?? 0) > 0 ? "#fbbf24" : "#4ade80",
      },
    ],
    [data]
  );

  return (
    <Box>
      <PageHeader title="Payment Posting" subtitle="ERA processing, payment reconciliation, and posting management" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its payment posting activity.</Alert>
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
                ELECTRONIC REMITTANCE REGISTRY
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {["ERA ID", "Payer", "Received Date", "Claims", "Amount", "Status"].map((h) => (
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
                          No electronic remittance advices found for this agency.
                        </TableCell>
                      </TableRow>
                    ) : (
                      rows.map((r) => (
                        <TableRow key={r.era_id} hover>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c", fontWeight: 700 }}>
                            {r.era_id.slice(0, 8)}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.received_at ? r.received_at.slice(0, 10) : "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.claim_count ?? "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {currency(r.total_paid_amount)}
                          </TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <StatusChip status={r.status} />
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", px: 2, py: 1.2 }}>
                Showing {rows.length} of {data?.era_received_count ?? 0} ERAs
              </Typography>
            </Paper>

            <Box sx={{ display: "grid", gap: 2 }}>
              <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
                <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>Remittance by Payer</Typography>
                {(data?.payer_breakdown ?? []).length === 0 ? (
                  <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No remittances posted yet.</Typography>
                ) : (
                  <Box sx={{ display: "grid", gap: 1.3 }}>
                    {(data?.payer_breakdown ?? []).map((p, i) => (
                      <Box key={p.payer_name}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.4 }}>
                          <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>{p.payer_name}</Typography>
                          <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 700 }}>{currency(p.total_paid)}</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={(p.total_paid / maxPayerTotal) * 100}
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
                <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>Unmatched Payments</Typography>
                {(data?.unmatched_payments ?? []).length === 0 ? (
                  <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No unmatched payments.</Typography>
                ) : (
                  <Box sx={{ display: "grid", gap: 1 }}>
                    {(data?.unmatched_payments ?? []).map((u) => (
                      <Box
                        key={u.payment_id}
                        sx={{
                          bgcolor: "#0b1626",
                          border: "1px solid #1f3a5c",
                          borderRadius: 1.5,
                          px: 1.5,
                          py: 1,
                        }}
                      >
                        <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                          <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 700 }}>
                            {u.claim_control_number || u.patient_name || u.payment_id.slice(0, 8)}
                          </Typography>
                          <Typography sx={{ fontSize: 12.5, color: "#fca5a5", fontWeight: 700 }}>{currency(u.paid_amount)}</Typography>
                        </Box>
                        <Typography sx={{ fontSize: 11, color: "#7f97b3" }}>{u.match_status}</Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </Paper>
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
