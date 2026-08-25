import { useEffect, useMemo, useState } from "react";
import { Alert, Box, Chip, CircularProgress, Paper, Typography } from "@mui/material";
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import VerifiedUserOutlinedIcon from "@mui/icons-material/VerifiedUserOutlined";
import PaymentsOutlinedIcon from "@mui/icons-material/PaymentsOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";

import {
  fetchClaims,
  fetchDenials,
  fetchEligibilityRoster,
  fetchRemittances,
  fetchTenantBillingReadinessReport,
  type ClaimsResponse,
  type DenialsResponse,
  type EligibilityRosterResponse,
  type RemittancesResponse,
  type TenantBillingReadinessReport,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";

type SnapshotCard = {
  key: string;
  icon: typeof ReceiptLongOutlinedIcon;
  title: string;
  stats: { label: string; value: string; color?: string }[];
  note: string;
};

function currency(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function ReportsPage() {
  const { selectedAgencyId } = useAgency();
  const [readiness, setReadiness] = useState<TenantBillingReadinessReport | null>(null);
  const [claims, setClaims] = useState<ClaimsResponse | null>(null);
  const [denials, setDenials] = useState<DenialsResponse | null>(null);
  const [eligibility, setEligibility] = useState<EligibilityRosterResponse | null>(null);
  const [remittances, setRemittances] = useState<RemittancesResponse | null>(null);
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
    Promise.all([
      fetchTenantBillingReadinessReport(selectedAgencyId),
      fetchClaims(selectedAgencyId, { limit: 1 }),
      fetchDenials(selectedAgencyId, { limit: 1 }),
      fetchEligibilityRoster(selectedAgencyId, { limit: 1 }),
      fetchRemittances(selectedAgencyId, { limit: 1 }),
    ])
      .then(([r, c, d, e, p]) => {
        if (!isMounted) return;
        setReadiness(r);
        setClaims(c);
        setDenials(d);
        setEligibility(e);
        setRemittances(p);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load report data.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const cards: SnapshotCard[] = useMemo(
    () => [
      {
        key: "readiness",
        icon: FactCheckOutlinedIcon,
        title: "Billing Readiness",
        stats: [
          { label: "Ready", value: String(readiness?.ready_count ?? 0), color: "#4ade80" },
          { label: "Not Ready", value: String(readiness?.not_ready_count ?? 0), color: (readiness?.not_ready_count ?? 0) > 0 ? "#f87171" : "#4ade80" },
          { label: "Total Patients", value: String(readiness?.total_patients ?? 0) },
        ],
        note: "Live snapshot as of today's service date — see the Billing Readiness page for per-patient blockers.",
      },
      {
        key: "claims",
        icon: ReceiptLongOutlinedIcon,
        title: "Claims Lifecycle",
        stats: [
          { label: "Total Claims", value: String(claims?.total_claims ?? 0) },
          { label: "Submitted", value: String(claims?.submitted_count ?? 0), color: "#fbbf24" },
          { label: "Denied", value: String(claims?.denied_count ?? 0), color: (claims?.denied_count ?? 0) > 0 ? "#f87171" : "#4ade80" },
        ],
        note: "Live snapshot — see the Claims page for the full registry.",
      },
      {
        key: "denials",
        icon: GavelOutlinedIcon,
        title: "Denials & Appeals",
        stats: [
          { label: "Total Denials", value: String(denials?.total_denials ?? 0) },
          {
            label: "Appeal Rate",
            value: denials?.appeal_rate !== null && denials?.appeal_rate !== undefined ? `${denials.appeal_rate}%` : "—",
          },
          {
            label: "Overturn Rate",
            value: denials?.overturn_rate !== null && denials?.overturn_rate !== undefined ? `${denials.overturn_rate}%` : "—",
            color: "#4ade80",
          },
        ],
        note: "Live snapshot — see the Denials & Appeals page for the reason breakdown and full registry.",
      },
      {
        key: "eligibility",
        icon: VerifiedUserOutlinedIcon,
        title: "Eligibility",
        stats: [
          { label: "Active Census", value: String(eligibility?.total_active ?? 0) },
          { label: "Eligible", value: String(eligibility?.eligible_count ?? 0), color: "#4ade80" },
          {
            label: "Inactive",
            value: String(eligibility?.inactive_count ?? 0),
            color: (eligibility?.inactive_count ?? 0) > 0 ? "#f87171" : "#4ade80",
          },
        ],
        note: "Live snapshot — see the Eligibility page for the full coverage roster.",
      },
      {
        key: "payments",
        icon: PaymentsOutlinedIcon,
        title: "Payment Posting",
        stats: [
          { label: "Payments (MTD)", value: currency(remittances?.total_payments_mtd), color: "#4ade80" },
          { label: "ERA Received", value: String(remittances?.era_received_count ?? 0) },
          {
            label: "Pending Match",
            value: String(remittances?.pending_manual_match_count ?? 0),
            color: (remittances?.pending_manual_match_count ?? 0) > 0 ? "#fbbf24" : "#4ade80",
          },
        ],
        note: "Live snapshot — see the Payment Posting page for the full ERA registry.",
      },
    ],
    [readiness, claims, denials, eligibility, remittances]
  );

  return (
    <Box>
      <PageHeader title="Reports" subtitle="Live billing operations snapshots across the agency" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      <Alert severity="info" sx={{ mb: 2.5, bgcolor: "#0f1b2d", border: "1px solid #1f3a5c", color: "#cbd5e1" }}>
        Scheduled/downloadable report generation (PDF/CSV/XLSX exports, saved schedules) is not implemented yet. The
        cards below are live data snapshots pulled directly from the same feeds behind each dashboard page — nothing
        here is a stored or fabricated report file.
      </Alert>

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its report snapshots.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 2 }}>
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Paper
                key={card.key}
                variant="outlined"
                sx={{ bgcolor: "#0f1b2d", borderColor: "#1f3a5c", borderRadius: 2, p: 2 }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
                  <Icon sx={{ fontSize: 20, color: "#14b8a6" }} />
                  <Typography sx={{ fontSize: 14, fontWeight: 800, color: "#fff" }}>{card.title}</Typography>
                </Box>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 1.5 }}>
                  {card.stats.map((s) => (
                    <Chip
                      key={s.label}
                      label={`${s.label}: ${s.value}`}
                      size="small"
                      sx={{ fontSize: 11.5, fontWeight: 700, bgcolor: "#0b1626", color: s.color || "#e2e8f0", border: "1px solid #1f3a5c" }}
                    />
                  ))}
                </Box>
                <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{card.note}</Typography>
              </Paper>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
