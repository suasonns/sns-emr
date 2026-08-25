import { useEffect, useMemo, useState } from "react";
import { Alert, Box, Button, Chip, CircularProgress, Paper, TextField, Typography } from "@mui/material";
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import VerifiedUserOutlinedIcon from "@mui/icons-material/VerifiedUserOutlined";
import PaymentsOutlinedIcon from "@mui/icons-material/PaymentsOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import GppMaybeOutlinedIcon from "@mui/icons-material/GppMaybeOutlined";

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
import {
  fetchHospiceCapRecord,
  upsertHospiceCapRecord,
  type HospiceCapRecord,
} from "../../api/hospiceCap";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";

// Cap year = the starting calendar year of the Nov 1 - Oct 31 hospice cap
// accounting year (42 CFR 418.309). Nov/Dec of year Y belong to cap year Y;
// Jan-Oct of year Y belong to cap year Y-1.
function currentCapYear(): number {
  const now = new Date();
  const year = now.getFullYear();
  return now.getMonth() >= 10 ? year : year - 1;
}

function HospiceCapCard({ tenantId }: { tenantId: string | null | undefined }) {
  const capYear = useMemo(() => currentCapYear(), []);
  const [record, setRecord] = useState<HospiceCapRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [beneficiaryCount, setBeneficiaryCount] = useState("");
  const [grossCollected, setGrossCollected] = useState("");
  const [sourceNote, setSourceNote] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!tenantId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchHospiceCapRecord(capYear, tenantId)
      .then((r) => {
        if (!isMounted) return;
        setRecord(r);
        setBeneficiaryCount(r.beneficiary_count ?? "");
        setGrossCollected(r.gross_reimbursement_collected ?? "");
        setSourceNote(r.source_note ?? "");
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load hospice cap data.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [tenantId, capYear]);

  const handleSave = async () => {
    if (!tenantId) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await upsertHospiceCapRecord(
        capYear,
        {
          cap_year: capYear,
          beneficiary_count: beneficiaryCount,
          gross_reimbursement_collected: grossCollected,
          source_note: sourceNote || undefined,
        },
        tenantId
      );
      setRecord(saved);
      setEditing(false);
    } catch (err: any) {
      setError(err?.message || "Unable to save hospice cap data.");
    } finally {
      setSaving(false);
    }
  };

  const usage = record?.cap_usage;

  return (
    <Paper variant="outlined" sx={{ bgcolor: "#0f1b2d", borderColor: "#1f3a5c", borderRadius: 2, p: 2 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <GppMaybeOutlinedIcon sx={{ fontSize: 20, color: "#14b8a6" }} />
        <Typography sx={{ fontSize: 14, fontWeight: 800, color: "#fff" }}>
          Hospice Aggregate Cap ({capYear})
        </Typography>
      </Box>

      {loading ? (
        <CircularProgress size={18} />
      ) : editing ? (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.25 }}>
          <TextField
            label="Beneficiary count (NGS/PS&R report)"
            size="small"
            value={beneficiaryCount}
            onChange={(e) => setBeneficiaryCount(e.target.value)}
            sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
          />
          <TextField
            label="Gross reimbursement collected"
            size="small"
            value={grossCollected}
            onChange={(e) => setGrossCollected(e.target.value)}
            sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
          />
          <TextField
            label="Source note (e.g. NGS PS&R report date)"
            size="small"
            value={sourceNote}
            onChange={(e) => setSourceNote(e.target.value)}
            sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
          />
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button size="small" variant="contained" disabled={saving} onClick={handleSave}>
              Save
            </Button>
            <Button size="small" onClick={() => setEditing(false)} disabled={saving} sx={{ color: "#7f97b3" }}>
              Cancel
            </Button>
          </Box>
        </Box>
      ) : usage ? (
        <>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 1.5 }}>
            <Chip
              label={`Allowed: $${usage.allowed_amount}`}
              size="small"
              sx={{ fontSize: 11.5, fontWeight: 700, bgcolor: "#0b1626", color: "#e2e8f0", border: "1px solid #1f3a5c" }}
            />
            <Chip
              label={`Collected: $${usage.gross_reimbursement_collected}`}
              size="small"
              sx={{ fontSize: 11.5, fontWeight: 700, bgcolor: "#0b1626", color: "#e2e8f0", border: "1px solid #1f3a5c" }}
            />
            <Chip
              label={usage.is_over_cap ? `Over cap: $${usage.over_cap_amount}` : `Available: $${usage.available_amount}`}
              size="small"
              sx={{
                fontSize: 11.5,
                fontWeight: 700,
                bgcolor: "#0b1626",
                color: usage.is_over_cap ? "#f87171" : "#4ade80",
                border: "1px solid #1f3a5c",
              }}
            />
          </Box>
          <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mb: 1 }}>
            Beneficiary count and collected amount are biller-entered from the agency's NGS PS&R cap report --
            {record?.source_note ? ` ${record.source_note}.` : " no source note on file."}
          </Typography>
          <Button size="small" onClick={() => setEditing(true)} sx={{ color: "#14b8a6" }}>
            Update figures
          </Button>
        </>
      ) : (
        <>
          <Typography sx={{ fontSize: 12.5, color: "#7f97b3", mb: 1 }}>
            {record?.cap_error
              ? record.cap_error
              : "Not configured yet. This app cannot compute the aggregate cap on its own -- it needs the agency's real, cross-provider beneficiary count and collected reimbursement from the NGS PS&R cap report."}
          </Typography>
          <Button size="small" variant="outlined" onClick={() => setEditing(true)} sx={{ color: "#14b8a6", borderColor: "#14b8a6" }}>
            Log cap data
          </Button>
        </>
      )}

      {error ? (
        <Alert severity="error" sx={{ mt: 1.5, fontSize: 12 }}>
          {error}
        </Alert>
      ) : null}
    </Paper>
  );
}


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
          <HospiceCapCard tenantId={selectedAgencyId} />
        </Box>
      )}
    </Box>
  );
}
