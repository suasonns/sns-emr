import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import {
  fetchFacilityCollectionsReport,
  type FacilityCollectionsReportResponse,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

// Facility & Residence Payment Visibility -- pure presentation over
// GET /billing/facility-payments/collections-report. All expectation vs.
// received-payment reconciliation, aging, and classification is computed
// server-side (app.billing.services.facility_payment_service); this page
// never fabricates or infers a value. Reuses the existing Payment/
// RemittanceAdvice pipeline via FacilityPaymentAllocation references --
// no second payment ledger.

type ViewMode = "single" | "all";

const RESPONSIBILITY_CATEGORIES = [
  "HOSPICE_SERVICE",
  "ROOM_AND_BOARD",
  "BOARD_AND_LODGING",
  "FACILITY_REIMBURSEMENT",
  "SHARE_OF_COST",
  "PATIENT_RESPONSIBILITY",
  "FAMILY_CONTRIBUTION",
  "ALW_SUPPORT",
  "PRIVATE_PAY",
  "OTHER",
  "UNKNOWN",
];

const FUNDING_SOURCES = [
  "MEDICARE",
  "MEDICAID_FFS",
  "MEDICAID_MANAGED_CARE",
  "COMMERCIAL_HMO",
  "COMMERCIAL_PPO",
  "ALW",
  "SHARE_OF_COST",
  "SOCIAL_SECURITY",
  "PATIENT_RESPONSIBILITY",
  "FAMILY_CONTRIBUTION",
  "PRIVATE_PAY",
  "COUNTY_OR_REGIONAL_ASSISTANCE",
  "FACILITY_ARRANGEMENT",
  "OTHER",
  "NOT_VERIFIED",
];

const RECONCILIATION_STATUSES = [
  "NOT_EXPECTED",
  "EXPECTED",
  "NOT_BILLED",
  "BILLED",
  "PAYMENT_PENDING",
  "PARTIALLY_PAID",
  "PAID",
  "OVERPAID",
  "UNMATCHED_PAYMENT",
  "MANUAL_REVIEW_REQUIRED",
  "DENIED",
  "RECOUPED",
  "REFUNDED",
  "CLOSED",
  "NOT_VERIFIED",
];

const AGING_BUCKETS = ["0-30", "31-60", "61-90", "91-120", "120+"];

const STATUS_COLORS: Record<string, string> = {
  PAID: "#4ade80",
  PARTIALLY_PAID: "#fbbf24",
  OVERPAID: "#38bdf8",
  UNMATCHED_PAYMENT: "#fb923c",
  MANUAL_REVIEW_REQUIRED: "#f87171",
  NOT_VERIFIED: "#94a3b8",
  EXPECTED: "#94a3b8",
  NOT_BILLED: "#94a3b8",
};

function currency(value: string | undefined | null): string {
  if (value === undefined || value === null) return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "NOT AVAILABLE";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function label(value: string | null | undefined): string {
  if (!value) return "NOT VERIFIED";
  return value
    .split("_")
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(" ");
}

export default function FacilityCollectionsReportPage() {
  const { selectedAgencyId } = useAgency();
  const [viewMode, setViewMode] = useState<ViewMode>("single");
  const [data, setData] = useState<FacilityCollectionsReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [responsibilityCategory, setResponsibilityCategory] = useState("");
  const [fundingSource, setFundingSource] = useState("");
  const [reconciliationStatus, setReconciliationStatus] = useState("");
  const [agingBucket, setAgingBucket] = useState("");

  useEffect(() => {
    if (viewMode === "single" && !selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    const filters = {
      responsibility_category: responsibilityCategory || undefined,
      funding_source: fundingSource || undefined,
      reconciliation_status: reconciliationStatus || undefined,
      aging_bucket: agingBucket || undefined,
    };
    const request =
      viewMode === "all"
        ? fetchFacilityCollectionsReport(undefined, { all_agencies: true, ...filters })
        : fetchFacilityCollectionsReport(selectedAgencyId, filters);
    request
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load Facility Collections report.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId, viewMode, responsibilityCategory, fundingSource, reconciliationStatus, agingBucket]);

  const metrics = useMemo(() => {
    const s = data?.summary;
    return [
      { label: "Total Expected", value: currency(s?.total_expected), caption: "Facility/residence obligations on file" },
      { label: "Total Received", value: currency(s?.total_received), caption: "Confirmed allocations only" },
      { label: "Total Outstanding", value: currency(s?.total_outstanding), caption: "Expected minus confirmed", color: "#f87171" },
      {
        label: "Collection Rate",
        value: `${(Number(s?.collection_rate ?? 0) * 100).toFixed(0)}%`,
        caption: `${s?.overdue_obligations_count ?? 0} overdue • ${s?.unmatched_payments_count ?? 0} unmatched`,
      },
    ];
  }, [data]);

  return (
    <Box>
      <PageHeader
        title="Facility Collections"
        subtitle="Expected vs. received facility, room & board, and share-of-cost obligations, reconciled against existing payment postings"
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

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative billing/collection statuses and financial tallies. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {viewMode === "single" && !selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its facility collections, or switch to "All Assigned Agencies".</Alert>
      ) : (
        <>
          <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap", mb: 2 }}>
            <TextField
              select
              size="small"
              label="Responsibility Category"
              value={responsibilityCategory}
              onChange={(e) => setResponsibilityCategory(e.target.value)}
              sx={{ minWidth: 200 }}
            >
              <MenuItem value="">All</MenuItem>
              {RESPONSIBILITY_CATEGORIES.map((c) => (
                <MenuItem key={c} value={c}>
                  {label(c)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Funding Source"
              value={fundingSource}
              onChange={(e) => setFundingSource(e.target.value)}
              sx={{ minWidth: 200 }}
            >
              <MenuItem value="">All</MenuItem>
              {FUNDING_SOURCES.map((f) => (
                <MenuItem key={f} value={f}>
                  {label(f)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Reconciliation Status"
              value={reconciliationStatus}
              onChange={(e) => setReconciliationStatus(e.target.value)}
              sx={{ minWidth: 200 }}
            >
              <MenuItem value="">All</MenuItem>
              {RECONCILIATION_STATUSES.map((s) => (
                <MenuItem key={s} value={s}>
                  {label(s)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Aging Bucket"
              value={agingBucket}
              onChange={(e) => setAgingBucket(e.target.value)}
              sx={{ minWidth: 160 }}
            >
              <MenuItem value="">All</MenuItem>
              {AGING_BUCKETS.map((b) => (
                <MenuItem key={b} value={b}>
                  {b} days
                </MenuItem>
              ))}
            </TextField>
          </Box>

          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
              <CircularProgress size={28} />
            </Box>
          ) : (
            <>
              <MetricCardRow metrics={metrics} />

              <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
                <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
                  FACILITY / RESIDENCE OBLIGATION DETAIL
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {[
                          "Agency",
                          "Patient",
                          "MRN",
                          "Facility",
                          "Residence Type",
                          "Service Period",
                          "Responsibility",
                          "Funding Source",
                          "Primary Payer",
                          "Secondary Payer",
                          "Expected",
                          "Received",
                          "Outstanding",
                          "Last Payment",
                          "Due Date",
                          "Days Out",
                          "Status",
                        ].map((h) => (
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
                      {(data?.rows ?? []).map((row) => (
                        <TableRow key={row.expectation_id}>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>{row.agency_name}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>{row.patient_name || "NOT AVAILABLE"}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{row.mrn || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>{row.facility_name_snapshot || "NOT AVAILABLE"}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{label(row.residence_type_snapshot)}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>
                            {row.service_period.start} – {row.service_period.end}
                          </TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <Chip size="small" label={label(row.responsibility_category)} sx={{ bgcolor: "#1f3a5c", color: "#e2e8f0", fontSize: 11 }} />
                          </TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{label(row.expected_funding_source)}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{row.primary_payer_name || "NOT VERIFIED"}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{row.secondary_payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.expected_amount)}</TableCell>
                          <TableCell sx={{ color: "#4ade80", fontSize: 12.5, borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.amount_received)}</TableCell>
                          <TableCell sx={{ color: "#f87171", fontSize: 12.5, borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.outstanding_amount)}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{row.most_recent_payment_date || "NOT AVAILABLE"}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{row.due_date || "NOT VERIFIED"}</TableCell>
                          <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c", textAlign: "right" }}>{row.days_outstanding ?? "—"}</TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <Chip
                              size="small"
                              label={label(row.reconciliation_status)}
                              sx={{
                                bgcolor: `${STATUS_COLORS[row.reconciliation_status] || "#94a3b8"}22`,
                                color: STATUS_COLORS[row.reconciliation_status] || "#94a3b8",
                                fontWeight: 700,
                                fontSize: 11,
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                      {(data?.rows?.length ?? 0) === 0 ? (
                        <TableRow>
                          <TableCell colSpan={17} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                            No facility payment expectations on file for the selected filters.
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </>
          )}
        </>
      )}
    </Box>
  );
}
