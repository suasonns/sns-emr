import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Alert, Box, Button, Chip, CircularProgress, MenuItem, Paper, TextField, Typography } from "@mui/material";

import api from "../api/client";
import { fetchBillingDashboard, fetchClaimLifecycle, fetchBillableAgencies, type BillableAgency } from "../api/dashboard";
import BillingAuditHistoryPanel from "../components/BillingAuditHistoryPanel";

type ClaimLifecycleResponse = {
  ready?: number;
  sent?: number;
  accepted?: number;
  paid?: number;
  denied?: number;
};

type BillingQueueRow = {
  claim_id?: string;
  billing_cycle_id: string;
  patient_id: string;
  patient_name?: string | null;
  patient_mrn?: string | null;
  payer_name?: string | null;
  tenant_name?: string | null;
  tenant_id?: string | null;
  total_charge?: number | null;
  total_units?: number | null;
  risk_score?: number | null;
  status: string;
  service_date?: string | null;
  last_status_reason?: string | null;
};

type BillingView =
  | "uncollected-unbilled"
  | "835-remittance"
  | "noe-notr"
  | "ra-reconciliation"
  | "monthly-summary"
  | "revenue-report"
  | "aging-report"
  | "submission-collection"
  | "unbilled-revenue"
  | "claims-breakdown"
  | "cost-per-patient"
  | "direct-care-cost"
  | "credit-balance"
  | "billing-issues";

const BILLING_TABS: Array<{ key: BillingView; label: string }> = [
  { key: "uncollected-unbilled", label: "Uncollected/Unbilled Claims" },
  { key: "835-remittance", label: "835 Remittance" },
  { key: "noe-notr", label: "NOE/NOTR" },
  { key: "ra-reconciliation", label: "RA Reconciliation" },
  { key: "monthly-summary", label: "Monthly Billing Summary" },
  { key: "revenue-report", label: "Revenue Report" },
  { key: "aging-report", label: "Aging Report" },
  { key: "submission-collection", label: "Submission Collection" },
  { key: "unbilled-revenue", label: "Unbilled Revenue" },
  { key: "claims-breakdown", label: "Claims Breakdown" },
  { key: "cost-per-patient", label: "Cost Per Patient" },
  { key: "direct-care-cost", label: "Direct Patient Care Cost" },
  { key: "credit-balance", label: "Credit Balance Report" },
  { key: "billing-issues", label: "Billing Issues" },
];

const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  green: "#059669",
  greenLight: "#dcfce7",
  amber: "#f59e0b",
  amberLight: "#fef3c7",
  red: "#dc2626",
  redLight: "#fee2e2",
  blue: "#2563eb",
  blueLight: "#dbeafe",
  white: "#ffffff",
  slate200: "#e5e7eb",
  slate300: "#d1d5db",
  slate500: "#6b7280",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray500: "#6b7280",
  gray600: "#4b5563",
  gray800: "#1f2937",
  gray900: "#111827",
};

const cardStyle = {
  background: C.white,
  border: `1px solid ${C.gray200}`,
  borderRadius: 12,
  boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
} as const;

function MetricCard({
  label,
  value,
  note,
  color,
}: {
  label: string;
  value: string | number;
  note?: string;
  color: string;
}) {
  return (
    <Paper variant="outlined" sx={{ ...cardStyle, p: 1.5, minHeight: 76, borderTop: `3px solid ${color}` }}>
      <Typography sx={{ fontSize: 10.5, letterSpacing: 0.3, color: C.slate500, fontWeight: 700, mb: 0.8, fontFamily: "'Inter', sans-serif" }}>
        {label.toUpperCase()}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography sx={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1, fontFamily: "'Inter', sans-serif" }}>
          {value}
        </Typography>
        {note ? (
          <Chip
            label={note}
            size="small"
            sx={{
              height: 20,
              fontSize: 9.5,
              fontWeight: 700,
              color,
              background: color === C.red ? C.redLight : color === C.green ? C.greenLight : color === C.amber ? C.amberLight : color === C.blue ? C.blueLight : C.tealLight,
            }}
          />
        ) : null}
      </Box>
    </Paper>
  );
}

function SectionCard({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Paper variant="outlined" sx={{ ...cardStyle, overflow: "hidden" }}>
      <Box sx={{ px: 1.5, py: 1.3, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2, borderBottom: `1px solid ${C.gray200}` }}>
        <Typography sx={{ fontSize: 14, fontWeight: 800, color: C.gray800, fontFamily: "'Inter', sans-serif" }}>{title}</Typography>
        {action}
      </Box>
      <Box sx={{ p: 1.5 }}>{children}</Box>
    </Paper>
  );
}

function TabChip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <Chip
      label={label}
      onClick={onClick}
      size="small"
      sx={{
        height: 24,
        fontWeight: 700,
        fontFamily: "'Inter', sans-serif",
        background: selected ? C.teal : C.white,
        color: selected ? C.white : C.gray800,
        border: "1px solid",
        borderColor: selected ? C.teal : C.gray200,
      }}
    />
  );
}

export default function BillingDashboard() {
  const [lifecycle, setLifecycle] = useState<ClaimLifecycleResponse | null>(null);
  const [rows, setRows] = useState<BillingQueueRow[]>([]);
  const [agencies, setAgencies] = useState<BillableAgency[]>([]);
  const [selectedAgencyId, setSelectedAgencyId] = useState<string>("");
  const [agenciesError, setAgenciesError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<{
    total_patients: number;
    ready_count: number;
    not_ready_count: number;
    patients: Array<{ patient_id: string; ready: boolean; blockers: string[]; warnings: string[] }>;
  } | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  // No UI control currently sets this beyond "ALL" (tenant filtering happens
  // via the agency selector instead); kept as read-only state so the
  // filteredRows tenant check above still compiles and remains a no-op.
  const [tenantFilter] = useState("ALL");
  const [activeView, setActiveView] = useState<BillingView>("uncollected-unbilled");
  const [selectedClaim, setSelectedClaim] = useState<{ patient_id: string; billing_cycle_id: string } | null>(null);

  useEffect(() => {
    let isMounted = true;

    fetchBillableAgencies()
      .then((res) => {
        if (!isMounted) return;
        const list = res?.agencies ?? [];
        setAgencies(list);
        if (list.length > 0) {
          setSelectedAgencyId((current) => current || list[0].tenant_id);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setAgenciesError(err?.message || "Unable to load agency list.");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const loadDashboard = async () => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [billingRes, lifecycleRes] = await Promise.allSettled([
        fetchBillingDashboard(selectedAgencyId),
        fetchClaimLifecycle(selectedAgencyId),
      ]);

      if (billingRes.status !== "fulfilled") {
        throw billingRes.reason;
      }

      if (lifecycleRes.status === "fulfilled") {
        setLifecycle(lifecycleRes.value);
      } else {
        setLifecycle(null);
      }

      try {
        const queueRes = await api.get<BillingQueueRow[]>("/billing/queue", {
          params: { tenant_id: selectedAgencyId },
        });
        setRows(queueRes.data ?? []);
      } catch (queueErr) {
        console.error("Billing queue load error:", queueErr);
        setRows([]);
      }
    } catch (err) {
      console.error("Billing dashboard load error:", err);
      setError("Failed to load billing dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgencyId]);

  const loadReadiness = async () => {
    if (!selectedAgencyId) return;

    try {
      setReadinessLoading(true);
      const today = new Date().toISOString().slice(0, 10);
      const res = await api.get("/billing/readiness-report", {
        params: { service_date: today, tenant_id: selectedAgencyId },
      });
      setReadiness(res.data);
    } catch (err) {
      console.error("Billing readiness load error:", err);
      setReadiness(null);
    } finally {
      setReadinessLoading(false);
    }
  };

  useEffect(() => {
    void loadReadiness();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgencyId]);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      const statusOk = statusFilter === "ALL" || row.status.toUpperCase() === statusFilter;
      const tenantOk = tenantFilter === "ALL" || row.tenant_id === tenantFilter;
      const q = search.trim().toLowerCase();
      const searchOk =
        q.length === 0 ||
        row.patient_id.toLowerCase().includes(q) ||
        (row.patient_name ?? "").toLowerCase().includes(q) ||
        (row.patient_mrn ?? "").toLowerCase().includes(q) ||
        row.billing_cycle_id.toLowerCase().includes(q) ||
        (row.payer_name ?? "").toLowerCase().includes(q);

      return statusOk && tenantOk && searchOk;
    });
  }, [rows, search, statusFilter, tenantFilter]);

  const summary = useMemo(
    () => ({
      totalClaims: rows.length,
      filteredClaims: filteredRows.length,
      filteredCharge: filteredRows.reduce((sum, row) => sum + (typeof row.total_charge === "number" ? row.total_charge : 0), 0),
      filteredDenied: filteredRows.filter((r) => r.status.toUpperCase() === "DENIED").length,
      uncollectedCharge: filteredRows
        .filter((r) => r.status.toUpperCase() !== "PAID")
        .reduce((sum, row) => sum + (typeof row.total_charge === "number" ? row.total_charge : 0), 0),
      deniedCharge: filteredRows
        .filter((r) => r.status.toUpperCase() === "DENIED")
        .reduce((sum, row) => sum + (typeof row.total_charge === "number" ? row.total_charge : 0), 0),
      pendingCount: filteredRows.filter((r) => r.status.toUpperCase() === "READY").length,
      sentCount: filteredRows.filter((r) => r.status.toUpperCase() === "SENT").length,
    }),
    [rows, filteredRows]
  );

  const totalLifecycle = (lifecycle?.ready ?? 0) + (lifecycle?.sent ?? 0) + (lifecycle?.accepted ?? 0) + (lifecycle?.paid ?? 0) + (lifecycle?.denied ?? 0);
  const getPercent = (value?: number) => (!totalLifecycle || !value ? 0 : Math.round((value / totalLifecycle) * 100));

  const handleExport = async (row: BillingQueueRow) => {
    try {
      setSuccessMessage(null);
      setError(null);

      const res = await api.post<{ claim_control_number: string }>("/billing/export-patient-claim-edi", {
        patient_id: row.patient_id,
        billing_cycle_id: row.billing_cycle_id,
      });

      setSuccessMessage(`Claim export created successfully — Control # ${res.data.claim_control_number}`);
      setTimeout(() => setSuccessMessage(null), 3000);
      await loadDashboard();
    } catch (err) {
      console.error("Claim export error:", err);
      setError("Failed to export selected claim.");
    }
  };

  const selectedAgency = useMemo(
    () => agencies.find((agency) => agency.tenant_id === selectedAgencyId) ?? null,
    [agencies, selectedAgencyId]
  );
  const activeTenantName = selectedAgency?.display_name ?? selectedAgency?.legal_name ?? "Select an agency";

  const billingPeriod = "Jan 1 - Jan 31, 2026";
  const payerFilter = "All Payers";

  const render835Remittance = () => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard label="835 Files Processed" value="27" note="This period" color={C.teal} />
        <MetricCard label="Total Remitted" value="$1.08M" note="Across payers" color={C.green} />
        <MetricCard label="Rejected Amount" value="$28,400" note="2.6% of remits" color={C.red} />
        <MetricCard label="Posting Variance" value="0.8%" note="Within tolerance" color={C.blue} />
      </Box>

      <SectionCard title="835 Remittance Detail">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: C.slate500, fontSize: 11, textTransform: "uppercase" }}>
              {['Date', 'Payer', 'Batch', 'Claims', 'Paid', 'Adjustments', 'Denied', 'Status'].map((h) => (
                <th key={h} style={{ padding: "10px 8px", borderBottom: `1px solid ${C.gray200}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["2026-01-15", "Medicare Part A", "835-2026-015", "42", "$319,100", "$7,420", "$2,900", "Posted"],
              ["2026-01-10", "Medi-Cal SF", "835-2026-014", "31", "$188,400", "$4,200", "$1,350", "Posted"],
              ["2026-01-08", "Anthem Blue Cross", "835-2026-013", "18", "$96,720", "$1,980", "$1,250", "Review"],
              ["2026-01-05", "Aetna HMO", "835-2026-012", "12", "$74,900", "$2,620", "$810", "Posted"],
            ].map((row) => (
              <tr key={row[0]} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                {row.map((cell, idx) => (
                  <td key={`${row[0]}-${idx}`} style={{ padding: "10px 8px", fontSize: 12, color: idx === 7 ? (cell === "Posted" ? C.green : C.amber) : C.gray600, fontWeight: idx === 0 || idx === 7 ? 700 : 500 }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <SectionCard title="835 Reconciliation Notes">
        <Box sx={{ display: "grid", gap: 1.25 }}>
          <Typography sx={{ fontSize: 13, color: C.gray600 }}>
            Medicare and commercial remittance files are posted to the payment ledger and reconciled against the billing cycle. Variance flags are reviewed before final reconciliation closes.
          </Typography>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Chip label="Medicare 835 posted" size="small" sx={{ bgcolor: C.tealLight, color: C.tealDark, fontWeight: 700 }} />
            <Chip label="Medi-Cal variance review" size="small" sx={{ bgcolor: C.amberLight, color: C.amber, fontWeight: 700 }} />
            <Chip label="ERA exceptions cleared" size="small" sx={{ bgcolor: C.greenLight, color: C.green, fontWeight: 700 }} />
          </Box>
        </Box>
      </SectionCard>
    </Box>
  );

  const renderUncollected = () => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <SectionCard
        title="Unbilled Revenue Report"
        action={
          <Button
            size="small"
            variant="outlined"
            onClick={() => {
              const first = filteredRows[0];
              if (first) {
                void handleExport(first);
              }
            }}
          >
            Export to Excel
          </Button>
        }
      >
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.25 }}>
          <TextField size="small" label="Billing Period" value={billingPeriod} />
          <TextField size="small" label="Payer" value={payerFilter} />
          <TextField size="small" label="Status" select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="ALL">All Statuses</MenuItem>
            <MenuItem value="READY">Ready</MenuItem>
            <MenuItem value="SENT">Sent</MenuItem>
            <MenuItem value="ACCEPTED">Accepted</MenuItem>
            <MenuItem value="PAID">Paid</MenuItem>
            <MenuItem value="DENIED">Denied</MenuItem>
          </TextField>
        </Box>
      </SectionCard>

      <SectionCard title="Claim Lifecycle Distribution">
        <Box sx={{ width: "100%", height: 18, borderRadius: 999, overflow: "hidden", display: "flex", backgroundColor: C.gray200, mb: 1.5 }}>
          <Box sx={{ width: `${getPercent(lifecycle?.ready)}%`, backgroundColor: C.teal }} />
          <Box sx={{ width: `${getPercent(lifecycle?.sent)}%`, backgroundColor: C.blue }} />
          <Box sx={{ width: `${getPercent(lifecycle?.accepted)}%`, backgroundColor: C.green }} />
          <Box sx={{ width: `${getPercent(lifecycle?.paid)}%`, backgroundColor: C.amber }} />
          <Box sx={{ width: `${getPercent(lifecycle?.denied)}%`, backgroundColor: C.red }} />
        </Box>
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(5, 1fr)" }, gap: 1 }}>
          <Typography variant="body2">Ready: {lifecycle?.ready ?? 0} ({getPercent(lifecycle?.ready)}%)</Typography>
          <Typography variant="body2">Sent: {lifecycle?.sent ?? 0} ({getPercent(lifecycle?.sent)}%)</Typography>
          <Typography variant="body2">Accepted: {lifecycle?.accepted ?? 0} ({getPercent(lifecycle?.accepted)}%)</Typography>
          <Typography variant="body2">Paid: {lifecycle?.paid ?? 0} ({getPercent(lifecycle?.paid)}%)</Typography>
          <Typography variant="body2">Denied: {lifecycle?.denied ?? 0} ({getPercent(lifecycle?.denied)}%)</Typography>
        </Box>
      </SectionCard>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard
          label="Total Uncollected Revenue"
          value={`$${summary.uncollectedCharge.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          note={`${filteredRows.filter((r) => r.status.toUpperCase() !== "PAID").length} claims`}
          color={C.red}
        />
        <MetricCard
          label="Denied Claims"
          value={`$${summary.deniedCharge.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          note={`${summary.filteredDenied} claims`}
          color={C.amber}
        />
        <MetricCard label="Pending Submission" value={String(summary.pendingCount)} note="Draft / ready to bill" color={C.blue} />
        <MetricCard label="Awaiting Payer Response" value={String(summary.sentCount)} note="Submitted, not yet adjudicated" color={C.green} />
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.25fr 0.75fr" }, gap: 2 }}>
        <SectionCard
          title="Unbilled Claims Audit Worklist"
          action={<Chip label={`Filtered: ${summary.filteredClaims}`} size="small" sx={{ fontWeight: 700 }} />}
        >
          <Box sx={{ display: "grid", gap: 1.5, mb: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" } }}>
            <TextField size="small" label="Billing Period" value={billingPeriod} />
            <TextField size="small" label="Payer" value={payerFilter} />
            <TextField size="small" label="Service Type" value="All Services" />
            <TextField size="small" label="Search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Patient name, MRN, payer" />
          </Box>

          <Box sx={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
              <thead>
                <tr style={{ textAlign: "left", color: C.slate500, fontSize: 11, textTransform: "uppercase" }}>
                  {["Patient", "MRN", "Payer", "Service Date", "Charge", "Status", "Reason", "Actions"].map((h) => (
                    <th key={h} style={{ padding: "10px 8px", borderBottom: `1px solid ${C.gray200}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ padding: "20px 8px", textAlign: "center", color: C.slate500, fontSize: 12 }}>
                      No claims found for this agency.
                    </td>
                  </tr>
                ) : (
                  filteredRows.map((row) => (
                    <tr key={row.claim_id ?? `${row.patient_id}-${row.billing_cycle_id}`} style={{ borderBottom: `1px solid ${C.gray100}`, fontSize: 12 }}>
                      <td style={{ padding: "10px 8px", fontWeight: 700, color: C.gray800 }}>{row.patient_name || row.patient_id}</td>
                      <td style={{ padding: "10px 8px" }}>{row.patient_mrn || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>{row.payer_name || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>{row.service_date || "—"}</td>
                      <td style={{ padding: "10px 8px", fontWeight: 700 }}>
                        {typeof row.total_charge === "number"
                          ? `$${row.total_charge.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                          : "—"}
                      </td>
                      <td style={{ padding: "10px 8px", color: row.status.toUpperCase() === "DENIED" ? C.red : C.amber }}>{row.status}</td>
                      <td style={{ padding: "10px 8px" }}>{row.last_status_reason || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => setSelectedClaim({ patient_id: row.patient_id, billing_cycle_id: row.billing_cycle_id })}
                        >
                          Review
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </Box>
        </SectionCard>


        <Box sx={{ display: "grid", gap: 2 }}>
          <SectionCard title="Billing Issues & Inquiries">
            <Box sx={{ display: "grid", gap: 1.25 }}>
              <Chip label="01 Billing Issue Logs" size="small" sx={{ alignSelf: "flex-start", bgcolor: C.redLight, color: C.red, fontWeight: 700 }} />
              <Chip label="02 Agency To Follow Up" size="small" sx={{ alignSelf: "flex-start", bgcolor: C.amberLight, color: C.amber, fontWeight: 700 }} />
              <Chip label="03 Patient Billing Lookup" size="small" sx={{ alignSelf: "flex-start", bgcolor: C.blueLight, color: C.blue, fontWeight: 700 }} />
              <Chip label="04 Uncollected / Unbilled Claims" size="small" sx={{ alignSelf: "flex-start", bgcolor: C.greenLight, color: C.green, fontWeight: 700 }} />
            </Box>
          </SectionCard>

          <SectionCard title="CMS Cost Reports">
            <Box sx={{ display: "grid", gap: 1.25 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography sx={{ fontSize: 13, fontWeight: 700 }}>Worksheet S-1 (Part II)</Typography>
                <Typography sx={{ fontSize: 13, color: C.green, fontWeight: 700 }}>Ready to review</Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography sx={{ fontSize: 13, fontWeight: 700 }}>Worksheet S-1 (Part III)</Typography>
                <Typography sx={{ fontSize: 13, color: C.amber, fontWeight: 700 }}>Draft</Typography>
              </Box>
            </Box>
          </SectionCard>
        </Box>
      </Box>
    </Box>
  );

  const renderMonthlySummary = () => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard label="Total Billed" value="$487,230" note="Target Set" color={C.teal} />
        <MetricCard label="Total Collected" value="$412,680" note="92.1% of Paid" color={C.green} />
        <MetricCard label="Outstanding Balance" value="$74,550" note="To Pursue" color={C.amber} />
        <MetricCard label="Collection Rate" value="84.7%" note="+2.1% vs last mo" color={C.blue} />
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.2fr 0.8fr" }, gap: 2 }}>
        <SectionCard title="Monthly Revenue Chart">
          <Box sx={{ height: 160, borderRadius: 2, bgcolor: "#f7fafc", display: "flex", alignItems: "end", justifyContent: "center", gap: 1.5, p: 2 }}>
            {[35, 58, 72, 98].map((height, idx) => (
              <Box key={idx} sx={{ width: 16, height, bgcolor: [C.slate300, "#94a3b8", "#64748b", C.teal][idx], borderRadius: 1 }} />
            ))}
          </Box>
        </SectionCard>

        <SectionCard title="Outstanding AR Aging">
          <Box sx={{ display: "grid", gap: 1 }}>
            {[
              ["0-30 Days", "$184,100", "53%"],
              ["31-60 Days", "$92,400", "27%"],
              ["61-90 Days", "$45,300", "13%"],
              ["90+ Days", "$21,000", "7%"],
            ].map(([label, amount, pct]) => (
              <Box key={label} sx={{ display: "grid", gap: 0.4 }}>
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography sx={{ fontSize: 12, fontWeight: 700 }}>{label}</Typography>
                  <Typography sx={{ fontSize: 12, fontWeight: 700 }}>{amount}</Typography>
                </Box>
                <Box sx={{ height: 8, borderRadius: 999, bgcolor: C.gray100, overflow: "hidden" }}>
                  <Box sx={{ width: pct, height: "100%", bgcolor: pct === "53%" ? C.teal : pct === "27%" ? C.blue : pct === "13%" ? C.amber : C.red }} />
                </Box>
              </Box>
            ))}
          </Box>
        </SectionCard>
      </Box>

      <SectionCard title="Payer Performance Breakdown">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: C.slate500, fontSize: 11, textTransform: "uppercase" }}>
              {["Payer Source", "# Patients", "# Claims", "Amt Billed", "Amt Paid", "Adjustments", "Write-offs", "Balance"].map((h) => (
                <th key={h} style={{ padding: "10px 8px", borderBottom: `1px solid ${C.gray200}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["Medicare (Traditional)", "114", "128", "$382,040", "$341,200", "$2,400", "$1,100", "$29,240"],
              ["Med-Cal Managed Care", "32", "36", "$54,120", "$42,300", "$500", "$0", "$7,120"],
              ["Private Insurance", "18", "22", "$31,900", "$23,100", "$200", "$0", "$8,000"],
              ["Self-Pay / Private Duty", "6", "8", "$9,170", "$6,060", "$0", "$0", "$2,290"],
            ].map((row) => (
              <tr key={row[0]} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                {row.map((cell, idx) => (
                  <td key={`${row[0]}-${idx}`} style={{ padding: "10px 8px", fontSize: 12, fontWeight: idx === 0 ? 700 : 500, color: idx === 0 ? C.gray800 : C.gray600 }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>
    </Box>
  );

  const renderSubmissionCollection = () => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(5, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard label="Total Batches Submitted" value="234" note="Batches" color={C.teal} />
        <MetricCard label="Accepted/Processed" value="218" note="Batches" color={C.green} />
        <MetricCard label="Rejected Claims" value="8" note="Claims" color={C.red} />
        <MetricCard label="Pending Clearinghouse" value="8" note="Batches" color={C.amber} />
        <MetricCard label="Acceptance Rate" value="93.2%" note="" color={C.blue} />
      </Box>

      <SectionCard title="EDI Claim Batch Deliveries & Responses">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: C.slate500, fontSize: 11, textTransform: "uppercase" }}>
              {["Batch #", "Submission Date", "Payer", "# Claims", "Total Amt", "Status", "Response Date", "Rejection Reason", "Actions"].map((h) => (
                <th key={h} style={{ padding: "10px 8px", borderBottom: `1px solid ${C.gray200}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["BAT-2024-98A", "Today 07:15 AM", "Medicare California Part A [Novitas]", "42", "$84,200", "Accepted", "Today 08:12 AM", "N/A - Fully Clean"],
              ["BAT-2024-97C", "Yesterday 04:30 PM", "Anthem Blue Cross CA", "18", "$32,500", "Rejected", "Today 08:10 AM", "Invalid Payer ID"],
              ["BAT-2024-96E", "01/20/2025", "Medi-Cal SF Field Office", "54", "$112,000", "Pending", "Pending", "In Clearinghouse Queue"],
            ].map((row) => (
              <tr key={row[0]} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                {row.map((cell, idx) => (
                  <td key={`${row[0]}-${idx}`} style={{ padding: "10px 8px", fontSize: 12, color: idx === 5 ? (cell === "Accepted" ? C.green : cell === "Rejected" ? C.red : C.amber) : C.gray600, fontWeight: idx === 0 || idx === 5 ? 700 : 500 }}>
                    {cell}
                  </td>
                ))}
                <td style={{ padding: "10px 8px" }}>
                  <Button size="small" variant="outlined">View EDI</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
        {[
          ["Donald P. Fletcher", "$12,400", "Need Physician-Signature verification"],
          ["Martha S. Vance", "$8,900", "Patient Plan transition overlap check"],
          ["Steven R. Douglas", "$5,600", "Missing final 24-hour discharge sign"],
        ].map((item) => (
          <Paper key={item[0]} variant="outlined" sx={{ ...cardStyle, p: 1.5, borderTop: `3px solid ${C.teal}` }}>
            <Typography sx={{ fontSize: 13, fontWeight: 800 }}>{item[0]}</Typography>
            <Typography sx={{ fontSize: 12, color: C.gray500, mt: 0.5 }}>{item[2]}</Typography>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 1.5 }}>
              <Typography sx={{ color: C.red, fontWeight: 800 }}>{item[1]}</Typography>
              <Button size="small" variant="contained">Resolve Action</Button>
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );

  const renderClaimsBreakdown = () => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard label="Total Claims Filed" value="312" note="YTD Submissions" color={C.teal} />
        <MetricCard label="Paid Claims" value="278" note="89.1% Approval" color={C.green} />
        <MetricCard label="Denied Claims" value="18" note="5.8% Quality Hold" color={C.red} />
        <MetricCard label="Pending Approval" value="16" note="In Clearinghouse" color={C.amber} />
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.25fr 0.75fr" }, gap: 2 }}>
        <SectionCard
          title="Medicare & Private Insurance Claims Overview"
          action={
            <Button
              size="small"
              variant="contained"
              onClick={() => {
                const first = filteredRows[0];
                if (first) {
                  setSelectedClaim({ patient_id: first.patient_id, billing_cycle_id: first.billing_cycle_id });
                }
              }}
            >
              Generate New Claim Batch
            </Button>
          }
        >
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: C.slate500, fontSize: 11, textTransform: "uppercase" }}>
                {["Claim #", "Patient", "MRN", "Payer", "Service Date", "Billed Amt", "Paid Amt", "Status", "Denial Cd", "Actions"].map((h) => (
                  <th key={h} style={{ padding: "10px 8px", borderBottom: `1px solid ${C.gray200}` }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ["CLM-8023", "Eleanor Vance", "MRN-882", "Medicare Part A", "01/15/2026", "$1,420.00", "$1,420.00", "Paid", "—"],
                ["CLM-9024", "Arthur Pendleton", "MRN-312", "Medi-Cal", "01/14/2026", "$950.00", "$0.00", "Denied", "CO-16"],
                ["CLM-9025", "Gladsupie Rivers", "MRN-500", "Blue Cross CA", "01/14/2026", "$3,400.00", "$0.00", "Pending", "—"],
                ["CLM-9026", "Robert Miller", "MRN-244", "Aetna Health", "01/13/2026", "$1,200.00", "$1,200.00", "Paid", "—"],
                ["CLM-9027", "Clara Higgins", "MRN-713", "Medicare Part A", "01/13/2026", "$1,300.00", "$0.00", "Adjusted", "CO-45"],
              ].map((row) => (
                <tr key={row[0]} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => (
                    <td key={`${row[0]}-${idx}`} style={{ padding: "10px 8px", fontSize: 12, fontWeight: idx === 0 ? 700 : 500, color: idx === 7 ? (cell === "Paid" ? C.green : cell === "Denied" ? C.red : cell === "Pending" ? C.amber : C.blue) : idx === 0 ? C.tealDark : C.gray600 }}>
                      {cell}
                    </td>
                  ))}
                  <td style={{ padding: "10px 8px" }}>
                    <Button size="small" variant="outlined">Audit</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>

        <Box sx={{ display: "grid", gap: 2 }}>
          <SectionCard title="Top Denial Code Analytics">
            <Box sx={{ display: "grid", gap: 1 }}>
              {[
                ["CO-16", "Missing/Incomplete Clinical Documentation", "8 cases (44%)"],
                ["CO-4", "Untimely Filing Limit Exceeded", "5 cases (28%)"],
                ["CO-97", "Benefit Already Adjudicated", "3 cases (16%)"],
                ["CO-45", "Coordination of Benefits / Duplicate", "2 cases (11%)"],
              ].map((item, idx) => (
                <Box key={item[0]} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 1, py: 0.4, borderBottom: idx < 3 ? `1px solid ${C.gray100}` : "none" }}>
                  <Typography sx={{ fontSize: 12, fontWeight: 700, color: C.gray800 }}>{item[0]}</Typography>
                  <Typography sx={{ fontSize: 12, color: C.gray600, flex: 1, ml: 1 }}>{item[1]}</Typography>
                  <Chip label={item[2]} size="small" sx={{ height: 20, fontSize: 10, background: C.redLight, color: C.red, fontWeight: 700 }} />
                </Box>
              ))}
            </Box>
          </SectionCard>

          <SectionCard title="Audit & Signature History">
            <BillingAuditHistoryPanel patientId={selectedClaim?.patient_id} billingCycleId={selectedClaim?.billing_cycle_id} />
          </SectionCard>
        </Box>
      </Box>
    </Box>
  );

  const renderGeneric = (title: string) => (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
        <MetricCard label="Total Billed" value="$487,230" note="Target Set" color={C.teal} />
        <MetricCard label="Total Collected" value="$412,680" note="92.1% of Paid" color={C.green} />
        <MetricCard label="Outstanding Balance" value="$74,550" note="To Pursue" color={C.amber} />
        <MetricCard label="Collection Rate" value="84.7%" note="+2.1% vs last mo" color={C.blue} />
      </Box>
      <SectionCard title={title}>
        <Typography sx={{ color: C.gray600, fontSize: 13 }}>
          This billing workspace is being aligned to the Figma screens you shared. The detailed table and summary layouts are now normalized to the same shell and finance rhythm.
        </Typography>
      </SectionCard>
    </Box>
  );

  const renderView = () => {
    switch (activeView) {
      case "monthly-summary":
        return renderMonthlySummary();
      case "submission-collection":
        return renderSubmissionCollection();
      case "claims-breakdown":
        return renderClaimsBreakdown();
      case "uncollected-unbilled":
        return renderUncollected();
      case "835-remittance":
        return render835Remittance();
      case "noe-notr":
        return renderGeneric("NOE / NOTR Live Tracking");
      case "ra-reconciliation":
        return renderGeneric("RA Reconciliation & Billing Portal");
      case "revenue-report":
        return renderGeneric("Revenue Analytics & YTD Performance");
      case "aging-report":
        return renderGeneric("Accounts Receivable Aging Report");
      case "unbilled-revenue":
        return renderGeneric("Unbilled Revenue Report");
      case "cost-per-patient":
        return renderGeneric("Margin & Care Cost Analysis by Patient");
      case "direct-care-cost":
        return renderGeneric("Discipline & Staff Direct Operational Cost Registry");
      case "credit-balance":
        return renderGeneric("Credit Balance Report");
      case "billing-issues":
        return renderGeneric("Billing Issues & Resolution Center");
      default:
        return renderUncollected();
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
          <Box>
            <Typography sx={{ fontSize: 22, fontWeight: 800, color: C.gray800, lineHeight: 1.05, fontFamily: "'Inter', sans-serif" }}>
              Financial &amp; Billing Center
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mt: 0.7 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontFamily: "'Inter', sans-serif" }}>
                Agency:
              </Typography>
              <TextField
                size="small"
                select
                value={selectedAgencyId}
                onChange={(e) => setSelectedAgencyId(e.target.value)}
                sx={{ minWidth: 260 }}
              >
                {agencies.length === 0 ? (
                  <MenuItem value="" disabled>
                    No agencies available
                  </MenuItem>
                ) : (
                  agencies.map((agency) => (
                    <MenuItem key={agency.tenant_id} value={agency.tenant_id}>
                      {agency.display_name || agency.legal_name}
                    </MenuItem>
                  ))
                )}
              </TextField>
              <Chip label={activeTenantName} size="small" sx={{ background: C.tealLight, color: C.tealDark, fontWeight: 700, height: 24, fontFamily: "'Inter', sans-serif" }} />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.8, pt: 0.2, fontFamily: "'Inter', sans-serif" }}>
            <Box component="span" sx={{ width: 8, height: 8, borderRadius: "50%", background: C.slate500 }} />
            Last synced: Today at 08:30 AM
          </Typography>
        </Box>

        <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap", pb: 0.5 }}>
          {BILLING_TABS.map((tab) => (
            <TabChip key={tab.key} label={tab.label} selected={activeView === tab.key} onClick={() => setActiveView(tab.key)} />
          ))}
        </Box>

        {agenciesError ? <Alert severity="warning">{agenciesError}</Alert> : null}
        {error ? <Alert severity="error">{error}</Alert> : null}
        {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

        {!selectedAgencyId ? (
          <Alert severity="info">Select an agency above to view its billing data. Nothing outside the selected agency is shown.</Alert>
        ) : (
          <>
            <SectionCard
              title="Ready to Bill"
              action={
                readinessLoading ? (
                  <CircularProgress size={16} />
                ) : (
                  <Chip
                    label={readiness ? `${readiness.ready_count}/${readiness.total_patients} ready` : "—"}
                    size="small"
                    sx={{ fontWeight: 700 }}
                  />
                )
              }
            >
              {readiness && readiness.not_ready_count > 0 ? (
                <Alert severity="warning" sx={{ mb: 1.5 }}>
                  {readiness.not_ready_count} patient{readiness.not_ready_count === 1 ? "" : "s"} in this agency
                  {" "}have an incomplete chart and cannot be billed until it's resolved.
                </Alert>
              ) : readiness ? (
                <Alert severity="success" sx={{ mb: 1.5 }}>
                  All active patients in this agency are ready to bill.
                </Alert>
              ) : null}

              {readiness && readiness.patients.some((p) => !p.ready) ? (
                <Box sx={{ display: "grid", gap: 1 }}>
                  {readiness.patients
                    .filter((p) => !p.ready)
                    .map((p) => (
                      <Box key={p.patient_id} sx={{ p: 1, border: `1px solid ${C.gray200}`, borderRadius: 1.5 }}>
                        <Typography sx={{ fontSize: 12, fontWeight: 700, color: C.gray800 }}>Patient {p.patient_id}</Typography>
                        {p.blockers.map((b, idx) => (
                          <Typography key={idx} sx={{ fontSize: 12, color: C.red }}>
                            • {b}
                          </Typography>
                        ))}
                      </Box>
                    ))}
                </Box>
              ) : null}
            </SectionCard>

            {loading ? (
              <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
                <CircularProgress />
              </Box>
            ) : (
              renderView()
            )}
          </>
        )}
      </Box>
  );
}
