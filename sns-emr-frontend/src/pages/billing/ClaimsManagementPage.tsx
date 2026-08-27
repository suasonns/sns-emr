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

import { fetchClaims, type ClaimsResponse } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const STATUS_CHIP: Record<string, { label: string; bg: string; fg: string }> = {
  READY: { label: "Draft", bg: "#334155", fg: "#cbd5e1" },
  SENT: { label: "Submitted", bg: "#78350f", fg: "#fcd34d" },
  ACCEPTED: { label: "Accepted", bg: "#134e4a", fg: "#5eead4" },
  PAID: { label: "Paid", bg: "#14532d", fg: "#86efac" },
  DENIED: { label: "Denied", bg: "#7f1d1d", fg: "#fca5a5" },
};

function StatusChip({ status }: { status: string | null }) {
  const s = STATUS_CHIP[String(status || "").toUpperCase()] || { label: status || "—", bg: "#334155", fg: "#cbd5e1" };
  return <Chip label={s.label} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

function currency(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function ClaimsManagementPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<ClaimsResponse | null>(null);
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
    fetchClaims(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load claims.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const rows = data?.claims ?? [];

  const metrics = useMemo(
    () => [
      { label: "Total Claims", value: String(data?.total_claims ?? 0), caption: "Active in current billing cycle" },
      { label: "Submitted", value: String(data?.submitted_count ?? 0), caption: "Awaiting clearinghouse response", color: "#fbbf24" },
      { label: "Accepted", value: String(data?.accepted_count ?? 0), caption: "Validated and queued for remittance", color: "#5eead4" },
      { label: "Denied", value: String(data?.denied_count ?? 0), caption: "Requires appeal review", color: data && data.denied_count > 0 ? "#f87171" : "#4ade80" },
    ],
    [data]
  );

  const lifecycle = data?.lifecycle;

  return (
    <Box>
      <PageHeader title="Claims Management" subtitle="Claim submission, tracking, and lifecycle management" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its claims.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          {lifecycle ? (
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2, mb: 2.5 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                CLAIM LIFECYCLE PIPELINE
              </Typography>
              <Box sx={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 2 }}>
                {[
                  { label: "Draft Batching", value: lifecycle.draft, caption: "Pre-audit verification", color: "#cbd5e1" },
                  { label: "Submitted", value: lifecycle.submitted, caption: "Awaiting clearinghouse", color: "#fbbf24" },
                  { label: "Accepted", value: lifecycle.accepted, caption: "Validated without errors", color: "#5eead4" },
                  { label: "Paid / Remitted", value: lifecycle.paid, caption: "Fully remitted", color: "#4ade80" },
                ].map((stage) => (
                  <Box key={stage.label} sx={{ bgcolor: "#0b1626", border: "1px solid #1f3a5c", borderRadius: 1.5, p: 1.5 }}>
                    <Typography sx={{ fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, color: stage.color }}>
                      {stage.label.toUpperCase()}
                    </Typography>
                    <Typography sx={{ fontSize: 20, fontWeight: 800, color: "#fff" }}>
                      {stage.value} Claim{stage.value === 1 ? "" : "s"}
                    </Typography>
                    <Typography sx={{ fontSize: 11, color: "#7f97b3" }}>{stage.caption}</Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          ) : null}

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              ACTIVE CLAIMS REGISTRY
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Claim ID", "Patient", "Payer", "Service Date", "Amount", "Status", "Days in Status"].map((h) => (
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
                      <TableCell colSpan={7} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No claims found for this agency.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rows.map((c) => (
                      <TableRow key={c.claim_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c", fontWeight: 700 }}>
                          {c.claim_control_number || c.claim_id.slice(0, 8)}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {c.patient_name || c.mrn || c.patient_id}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.payer_name || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.service_date || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.total_charge)}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <StatusChip status={c.status} />
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {c.days_in_status !== null ? `${c.days_in_status}d` : "—"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography sx={{ fontSize: 11.5, color: "#7f97b3", px: 2, py: 1.2 }}>
              Showing {rows.length} of {data?.total_claims ?? 0} claims
            </Typography>
          </Paper>
        </>
      )}
    </Box>
  );
}
