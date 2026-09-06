import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
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
  DashboardApiError,
  activateFacilityPaymentExpectation,
  cancelFacilityPaymentExpectation,
  correctFacilityPaymentExpectation,
  createFacilityPaymentExpectation,
  fetchFacilityCollectionsReport,
  fetchFacilityPaymentExpectationDetail,
  fetchFacilityPaymentExpectationHistory,
  fetchFacilityPaymentResidenceSnapshotDiff,
  type FacilityCollectionsReportResponse,
  type FacilityPaymentExpectationCorrectPayload,
  type FacilityPaymentExpectationCreatePayload,
  type FacilityPaymentExpectationDetail,
  type FacilityPaymentExpectationHistoryResponse,
  type FacilityPaymentResidenceSnapshotDiffResponse,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";
import PageHeader from "../../components/billing/PageHeader";

type ViewMode = "single" | "all";
type SubmitMode = "draft" | "activate";

type ExpectationForm = {
  patient_id: string;
  patient_pos_id: string;
  responsibility_category: string;
  expected_funding_source: string;
  expected_amount: string;
  currency: string;
  frequency: string;
  service_period_start: string;
  service_period_end: string;
  due_date: string;
  authorization_reference: string;
  contract_reference: string;
  share_of_cost_amount: string;
  source: string;
  expected_payer_name_snapshot: string;
  notes: string;
};

type CorrectionForm = Omit<ExpectationForm, "patient_id"> & {
  correction_reason: string;
};

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

const EXPECTATION_SOURCES = [
  "VERIFIED_PAYER_RULE",
  "VERIFIED_CONTRACT",
  "VERIFIED_AUTHORIZATION",
  "VERIFIED_FACILITY_ARRANGEMENT",
  "AUTHORIZED_MANUAL_ENTRY",
  "VERIFIED_IMPORT",
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
  DRAFT: "#94a3b8",
  ACTIVE: "#38bdf8",
  PARTIALLY_PAID: "#fbbf24",
  PAID: "#4ade80",
  OVERPAID: "#22d3ee",
  NOT_VERIFIED: "#94a3b8",
  SUPERSEDED: "#a78bfa",
  CANCELLED: "#f87171",
  CLOSED: "#64748b",
};

function currency(value: string | null | undefined): string {
  if (!value) return "No value available";
  const n = Number(value);
  if (Number.isNaN(n)) return "Not available";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function label(value: string | null | undefined): string {
  if (!value) return "Not verified";
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

function summarizeError(error: unknown, fallback: string): { message: string; status?: number } {
  if (error instanceof DashboardApiError) {
    if (error.status === 403) return { message: "Authorization denied for this action.", status: 403 };
    if (error.status === 409) return { message: error.message || "Concurrent update conflict.", status: 409 };
    return { message: error.message || fallback, status: error.status };
  }
  if (error instanceof Error) {
    if (/Failed to fetch|NetworkError|Load failed/i.test(error.message)) {
      return { message: "Backend unavailable. Please try again shortly." };
    }
    return { message: error.message || fallback };
  }
  return { message: fallback };
}

function dueDateBadge(source?: string, verified?: boolean, dueDate?: string | null) {
  if (!dueDate) return { label: "Not verified", color: "#94a3b8" };
  if (source === "AUTHORIZED_MANUAL_ENTRY") return { label: "Entered", color: "#fbbf24" };
  if (source === "SYSTEM_FALLBACK") return { label: "Fallback", color: "#f87171" };
  if (source === "TENANT_CONFIGURED_TERM") return { label: "Estimated", color: "#38bdf8" };
  if (verified) return { label: "Verified", color: "#4ade80" };
  return { label: "Not verified", color: "#94a3b8" };
}

function buildCreateForm(detail?: FacilityPaymentExpectationDetail | null): ExpectationForm {
  return {
    patient_id: detail?.patient_id ?? "",
    patient_pos_id: detail?.patient_pos_id ?? "",
    responsibility_category: detail?.responsibility_category ?? "ROOM_AND_BOARD",
    expected_funding_source: detail?.expected_funding_source ?? "NOT_VERIFIED",
    expected_amount: detail?.expected_amount ?? "",
    currency: detail?.currency ?? "USD",
    frequency: detail?.frequency ?? "",
    service_period_start: detail?.service_period_start ?? "",
    service_period_end: detail?.service_period_end ?? "",
    due_date: detail?.due_date ?? "",
    authorization_reference: detail?.authorization_reference ?? "",
    contract_reference: detail?.contract_reference ?? "",
    share_of_cost_amount: detail?.share_of_cost_amount ?? "",
    source: detail?.source ?? "NOT_VERIFIED",
    expected_payer_name_snapshot: detail?.expected_payer_name_snapshot ?? "",
    notes: detail?.notes ?? "",
  };
}

function buildCorrectionForm(detail: FacilityPaymentExpectationDetail): CorrectionForm {
  return { ...buildCreateForm(detail), correction_reason: "" };
}

function validateForm(form: ExpectationForm, mode: SubmitMode): string | null {
  if (!form.patient_id.trim()) return "Patient ID is required.";
  if (!form.expected_amount.trim() || Number(form.expected_amount) < 0) {
    return "Expected amount must be zero or greater.";
  }
  if (!form.service_period_start || !form.service_period_end) {
    return "Service period start and end are required.";
  }
  if (form.service_period_end < form.service_period_start) {
    return "Service period end must be on or after service period start.";
  }
  if (mode === "activate" && form.source === "NOT_VERIFIED") {
    return "Activation requires a verified or authorized source.";
  }
  return null;
}

function toCreatePayload(form: ExpectationForm): FacilityPaymentExpectationCreatePayload {
  return {
    patient_id: form.patient_id.trim(),
    patient_pos_id: form.patient_pos_id.trim() || undefined,
    responsibility_category: form.responsibility_category,
    expected_funding_source: form.expected_funding_source,
    expected_amount: form.expected_amount,
    currency: form.currency || "USD",
    frequency: form.frequency.trim() || undefined,
    service_period_start: form.service_period_start,
    service_period_end: form.service_period_end,
    due_date: form.due_date || undefined,
    authorization_reference: form.authorization_reference.trim() || undefined,
    contract_reference: form.contract_reference.trim() || undefined,
    share_of_cost_amount: form.share_of_cost_amount.trim() || undefined,
    source: form.source,
    expected_payer_name_snapshot: form.expected_payer_name_snapshot.trim() || undefined,
    notes: form.notes.trim() || undefined,
    client_request_id:
      typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : undefined,
  };
}

function toCorrectionPayload(
  form: CorrectionForm,
  rowVersion: number
): FacilityPaymentExpectationCorrectPayload {
  return {
    patient_pos_id: form.patient_pos_id.trim() || undefined,
    responsibility_category: form.responsibility_category,
    expected_funding_source: form.expected_funding_source,
    expected_amount: form.expected_amount,
    currency: form.currency || "USD",
    frequency: form.frequency.trim() || undefined,
    service_period_start: form.service_period_start,
    service_period_end: form.service_period_end,
    due_date: form.due_date || undefined,
    authorization_reference: form.authorization_reference.trim() || undefined,
    contract_reference: form.contract_reference.trim() || undefined,
    share_of_cost_amount: form.share_of_cost_amount.trim() || undefined,
    source: form.source,
    expected_payer_name_snapshot: form.expected_payer_name_snapshot.trim() || undefined,
    notes: form.notes.trim() || undefined,
    correction_reason: form.correction_reason.trim(),
    expected_row_version: rowVersion,
  };
}

function StatusChip({ value }: { value: string }) {
  const color = STATUS_COLORS[value] || "#94a3b8";
  return (
    <Chip
      size="small"
      label={label(value)}
      sx={{ bgcolor: `${color}22`, color, fontWeight: 700, fontSize: 11 }}
    />
  );
}

function Field({
  labelText,
  value,
}: {
  labelText: string;
  value: string;
}) {
  return (
    <>
      <Typography sx={{ color: "#7f97b3", fontSize: 12 }}>{labelText}</Typography>
      <Typography sx={{ color: "#e2e8f0", fontSize: 12.5 }}>{value}</Typography>
    </>
  );
}

export default function FacilityCollectionsReportPage() {
  const { selectedAgencyId } = useAgency();
  const [viewMode, setViewMode] = useState<ViewMode>("single");
  const [data, setData] = useState<FacilityCollectionsReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const [responsibilityCategory, setResponsibilityCategory] = useState("");
  const [fundingSource, setFundingSource] = useState("");
  const [reconciliationStatus, setReconciliationStatus] = useState("");
  const [agingBucket, setAgingBucket] = useState("");
  const [includeAllStatuses, setIncludeAllStatuses] = useState(false);

  const [selectedExpectationId, setSelectedExpectationId] = useState<string | null>(null);
  const [detail, setDetail] = useState<FacilityPaymentExpectationDetail | null>(null);
  const [history, setHistory] = useState<FacilityPaymentExpectationHistoryResponse | null>(null);
  const [snapshotDiff, setSnapshotDiff] =
    useState<FacilityPaymentResidenceSnapshotDiffResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState<ExpectationForm>(buildCreateForm());

  const [correctionOpen, setCorrectionOpen] = useState(false);
  const [correctionBusy, setCorrectionBusy] = useState(false);
  const [correctionError, setCorrectionError] = useState<string | null>(null);
  const [correctionForm, setCorrectionForm] = useState<CorrectionForm | null>(null);

  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelBusy, setCancelBusy] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelAcknowledged, setCancelAcknowledged] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const [message, setMessage] = useState<{ severity: "success" | "error" | "info"; text: string } | null>(
    null
  );

  // Reset the selection only on an actual context switch (agency/view mode),
  // not on every report refresh. This is intentionally decoupled from the
  // rows-fetch effect below.
  useEffect(() => {
    setSelectedExpectationId(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgencyId, viewMode]);

  useEffect(() => {
    if (viewMode === "single" && !selectedAgencyId) {
      setLoading(false);
      setData(null);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    const request =
      viewMode === "all"
        ? fetchFacilityCollectionsReport(undefined, {
            all_agencies: true,
            responsibility_category: responsibilityCategory || undefined,
            funding_source: fundingSource || undefined,
            reconciliation_status: reconciliationStatus || undefined,
            aging_bucket: agingBucket || undefined,
            include_all_statuses: includeAllStatuses || undefined,
          })
        : fetchFacilityCollectionsReport(selectedAgencyId, {
            responsibility_category: responsibilityCategory || undefined,
            funding_source: fundingSource || undefined,
            reconciliation_status: reconciliationStatus || undefined,
            aging_bucket: agingBucket || undefined,
            include_all_statuses: includeAllStatuses || undefined,
          });
    request
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        // Only default to the first row when nothing is selected yet. The
        // report's rows only reflect currently-effective statuses by
        // default (DRAFT/SUPERSEDED/CANCELLED are excluded from totals and
        // rows), but an expectation the user explicitly selected — including
        // one they just created as a DRAFT — must stay selected across
        // reloads/filter changes. The detail panel fetches by ID directly,
        // independent of this filtered row list, so a selection outside the
        // current filter still renders correctly.
        if (!selectedExpectationId && res.rows[0]) {
          setSelectedExpectationId(res.rows[0].expectation_id);
        }
      })
      .catch((err) => {
        if (isMounted) setError(summarizeError(err, "Unable to load Facility Collections report.").message);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [
    selectedAgencyId,
    viewMode,
    responsibilityCategory,
    fundingSource,
    reconciliationStatus,
    agingBucket,
    includeAllStatuses,
    reloadToken,
    selectedExpectationId,
  ]);

  useEffect(() => {
    if (!selectedExpectationId) {
      setDetail(null);
      setHistory(null);
      setSnapshotDiff(null);
      return;
    }
    let isMounted = true;
    setDetailLoading(true);
    setDetailError(null);
    Promise.all([
      fetchFacilityPaymentExpectationDetail(selectedExpectationId),
      fetchFacilityPaymentExpectationHistory(selectedExpectationId),
      fetchFacilityPaymentResidenceSnapshotDiff(selectedExpectationId),
    ])
      .then(([nextDetail, nextHistory, nextDiff]) => {
        if (!isMounted) return;
        setDetail(nextDetail);
        setHistory(nextHistory);
        setSnapshotDiff(nextDiff);
      })
      .catch((err) => {
        if (isMounted) setDetailError(summarizeError(err, "Unable to load expectation detail.").message);
      })
      .finally(() => {
        if (isMounted) setDetailLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedExpectationId, reloadToken]);

  const activeTenantId = viewMode === "single" ? selectedAgencyId : detail?.tenant_id ?? null;
  const metrics = useMemo(() => {
    const summary = data?.summary;
    return [
      { label: "Total Expected", value: currency(summary?.total_expected), caption: "Facility obligations on file" },
      { label: "Total Received", value: currency(summary?.total_received), caption: "Confirmed allocations only" },
      {
        label: "Total Outstanding",
        value: currency(summary?.total_outstanding),
        caption: "Expected minus confirmed",
        color: "#f87171",
      },
      {
        label: "Collection Rate",
        value: `${(Number(summary?.collection_rate ?? 0) * 100).toFixed(0)}%`,
        caption: `${summary?.overdue_obligations_count ?? 0} overdue • ${summary?.unmatched_payments_count ?? 0} unmatched`,
      },
    ];
  }, [data]);

  const confirmedAllocations =
    detail?.allocations?.filter((allocation) => allocation.allocation_status === "CONFIRMED").length ?? 0;

  function refresh(nextId?: string | null) {
    if (nextId !== undefined) setSelectedExpectationId(nextId);
    setReloadToken((value) => value + 1);
  }

  async function handleCreate(mode: SubmitMode) {
    const validationError = validateForm(createForm, mode);
    if (validationError) {
      setCreateError(validationError);
      return;
    }
    if (!activeTenantId) {
      setCreateError("Select an agency context before creating an expectation.");
      return;
    }
    setCreateBusy(true);
    setCreateError(null);
    try {
      const created = await createFacilityPaymentExpectation(toCreatePayload(createForm), activeTenantId);
      const finalExpectation =
        mode === "activate"
          ? await activateFacilityPaymentExpectation(created.id, {
              expected_row_version: created.row_version,
            })
          : created;
      setCreateOpen(false);
      setMessage({
        severity: "success",
        text: mode === "activate" ? "Expectation created and activated." : "Draft expectation saved.",
      });
      refresh(finalExpectation.id);
    } catch (err) {
      setCreateError(summarizeError(err, "Unable to save expectation.").message);
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleActivateSelected() {
    if (!detail) return;
    try {
      const updated = await activateFacilityPaymentExpectation(detail.id, {
        expected_row_version: detail.row_version,
      });
      setMessage({ severity: "success", text: "Expectation activated." });
      refresh(updated.id);
    } catch (err) {
      setMessage({ severity: "error", text: summarizeError(err, "Unable to activate expectation.").message });
    }
  }

  async function handleSaveCorrection() {
    if (!detail || !correctionForm) return;
    if (!correctionForm.correction_reason.trim()) {
      setCorrectionError("Correction reason is required.");
      return;
    }
    setCorrectionBusy(true);
    setCorrectionError(null);
    try {
      const corrected = await correctFacilityPaymentExpectation(
        detail.id,
        toCorrectionPayload(correctionForm, detail.row_version)
      );
      setCorrectionOpen(false);
      setMessage({ severity: "success", text: "Correction saved as a new expectation version." });
      refresh(corrected.id);
    } catch (err) {
      const summarized = summarizeError(err, "Unable to save correction.");
      setCorrectionError(
        summarized.status === 409
          ? "This record was updated by someone else, please reload."
          : summarized.message
      );
    } finally {
      setCorrectionBusy(false);
    }
  }

  async function handleCancel() {
    if (!detail) return;
    if (!cancelReason.trim()) {
      setCancelError("Cancellation reason is required.");
      return;
    }
    if (confirmedAllocations > 0 && !cancelAcknowledged) {
      setCancelError("Acknowledge the allocation review warning before cancelling.");
      return;
    }
    setCancelBusy(true);
    setCancelError(null);
    try {
      const updated = await cancelFacilityPaymentExpectation(detail.id, {
        cancellation_reason: cancelReason.trim(),
        force: confirmedAllocations > 0,
        expected_row_version: detail.row_version,
      });
      setCancelOpen(false);
      setCancelReason("");
      setCancelAcknowledged(false);
      setMessage({ severity: "success", text: "Expectation cancelled." });
      refresh(updated.id);
    } catch (err) {
      setCancelError(summarizeError(err, "Unable to cancel expectation.").message);
    } finally {
      setCancelBusy(false);
    }
  }

  return (
    <Box>
      <PageHeader
        title="Facility Collections"
        subtitle="Expected vs. received facility, room and board, and share-of-cost obligations"
        actions={
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                setCreateForm(buildCreateForm(detail));
                setCreateError(null);
                setCreateOpen(true);
              }}
              disabled={!activeTenantId}
            >
              New Expectation
            </Button>
            <Button size="small" onClick={() => refresh()}>
              Reload
            </Button>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={viewMode}
              onChange={(_e, next) => next && setViewMode(next)}
              sx={{
                "& .MuiToggleButton-root": {
                  color: "#94a3b8",
                  borderColor: "#334155",
                  textTransform: "none",
                  fontWeight: 700,
                  fontSize: 12.5,
                },
                "& .Mui-selected": { color: "#fff !important", bgcolor: "#10b7a2 !important" },
              }}
            >
              <ToggleButton value="single">Current Agency</ToggleButton>
              <ToggleButton value="all">All Assigned Agencies</ToggleButton>
            </ToggleButtonGroup>
          </Stack>
        }
      />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is limited to administrative billing and collection statuses and financial tallies.' />

      {message ? (
        <Alert severity={message.severity} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      ) : null}
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

      {viewMode === "single" && !selectedAgencyId ? (
        <Alert severity="info">Select an agency to view facility collections, or switch to "All Assigned Agencies".</Alert>
      ) : (
        <>
          <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap", mb: 2 }}>
            <TextField select size="small" label="Responsibility Category" value={responsibilityCategory} onChange={(e) => setResponsibilityCategory(e.target.value)} sx={{ minWidth: 200 }}>
              <MenuItem value="">All</MenuItem>
              {RESPONSIBILITY_CATEGORIES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Funding Source" value={fundingSource} onChange={(e) => setFundingSource(e.target.value)} sx={{ minWidth: 200 }}>
              <MenuItem value="">All</MenuItem>
              {FUNDING_SOURCES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Reconciliation Status" value={reconciliationStatus} onChange={(e) => setReconciliationStatus(e.target.value)} sx={{ minWidth: 200 }}>
              <MenuItem value="">All</MenuItem>
              {RECONCILIATION_STATUSES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Aging Bucket" value={agingBucket} onChange={(e) => setAgingBucket(e.target.value)} sx={{ minWidth: 160 }}>
              <MenuItem value="">All</MenuItem>
              {AGING_BUCKETS.map((value) => <MenuItem key={value} value={value}>{value} days</MenuItem>)}
            </TextField>
            <FormControlLabel
              sx={{ ml: 0 }}
              control={
                <Checkbox
                  size="small"
                  checked={includeAllStatuses}
                  onChange={(e) => setIncludeAllStatuses(e.target.checked)}
                />
              }
              label="Show drafts, superseded & cancelled (historical)"
            />
          </Box>

          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
              <CircularProgress size={28} />
            </Box>
          ) : (
            <>
              <MetricCardRow metrics={metrics} />

              <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden", mb: 2 }}>
                <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
                  FACILITY / RESIDENCE OBLIGATION DETAIL
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {["Agency", "Patient", "MRN", "Facility", "Service Period", "Responsibility", "Expected", "Received", "Outstanding", "Due Date", "Status"].map((h) => (
                          <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}>
                            {h.toUpperCase()}
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(data?.rows ?? []).map((row) => {
                        const badge = dueDateBadge(row.due_date_source, row.payment_term_verified, row.due_date);
                        const selected = selectedExpectationId === row.expectation_id;
                        return (
                          <TableRow
                            key={row.expectation_id}
                            hover
                            selected={selected}
                            onClick={() => setSelectedExpectationId(row.expectation_id)}
                            sx={{ cursor: "pointer", ...(selected ? { bgcolor: "#12243d" } : {}) }}
                          >
                            <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c" }}>{row.agency_name}</TableCell>
                            <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c" }}>{row.patient_name || "Not available"}</TableCell>
                            <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{row.mrn || "Not available"}</TableCell>
                            <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c" }}>{row.facility_name_snapshot || "Not available"}</TableCell>
                            <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{row.service_period.start} – {row.service_period.end}</TableCell>
                            <TableCell sx={{ borderColor: "#1f3a5c" }}><Chip size="small" label={label(row.responsibility_category)} sx={{ bgcolor: "#1f3a5c", color: "#e2e8f0" }} /></TableCell>
                            <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.expected_amount)}</TableCell>
                            <TableCell sx={{ color: "#4ade80", borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.amount_received)}</TableCell>
                            <TableCell sx={{ color: "#f87171", borderColor: "#1f3a5c", textAlign: "right" }}>{currency(row.outstanding_amount)}</TableCell>
                            <TableCell sx={{ borderColor: "#1f3a5c" }}>
                              <Stack direction="row" spacing={1} alignItems="center">
                                <Typography sx={{ color: "#7f97b3", fontSize: 12 }}>{row.due_date || "Not available"}</Typography>
                                <Chip size="small" label={badge.label} sx={{ bgcolor: `${badge.color}22`, color: badge.color, fontWeight: 700, fontSize: 10.5 }} />
                              </Stack>
                            </TableCell>
                            <TableCell sx={{ borderColor: "#1f3a5c" }}><StatusChip value={row.status} /></TableCell>
                          </TableRow>
                        );
                      })}
                      {(data?.rows.length ?? 0) === 0 ? (
                        <TableRow>
                          <TableCell colSpan={11} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                            No facility payment expectations are on file for the selected filters.
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>

              <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
                <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 1.5 }}>
                  Expectation Workspace
                </Typography>
                {detailLoading ? (
                  <Box sx={{ display: "flex", justifyContent: "center", py: 5 }}>
                    <CircularProgress size={24} />
                  </Box>
                ) : detailError ? (
                  <Alert severity="error">{detailError}</Alert>
                ) : !detail ? (
                  <Alert severity="info">Select an expectation to review details, history, corrections, and residence snapshot changes.</Alert>
                ) : (
                  <Stack spacing={2}>
                    <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1}>
                      <Box>
                        <Typography sx={{ color: "#fff", fontWeight: 800, fontSize: 16 }}>{detail.patient_name || "Patient not available"}</Typography>
                        <Typography sx={{ color: "#7f97b3", fontSize: 12.5 }}>
                          {detail.agency_name || "Agency not available"} • MRN {detail.mrn || "Not available"}
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        <Button size="small" variant="outlined" onClick={() => { setCorrectionForm(buildCorrectionForm(detail)); setCorrectionError(null); setCorrectionOpen(true); }}>
                          Correct
                        </Button>
                        <Button size="small" variant="outlined" onClick={handleActivateSelected} disabled={detail.status !== "DRAFT"}>
                          Activate
                        </Button>
                        <Button size="small" variant="outlined" color="error" onClick={() => { setCancelOpen(true); setCancelError(null); }}>
                          Cancel
                        </Button>
                      </Stack>
                    </Stack>

                    <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", xl: "1.2fr 1fr" }, gap: 2 }}>
                      <Paper sx={{ bgcolor: "#0b1626", border: "1px solid #1f3a5c", p: 2 }}>
                        <Typography sx={{ color: "#fff", fontWeight: 700, mb: 1.5 }}>Expectation Detail</Typography>
                        <Box sx={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 1.25, mb: 2 }}>
                          <Field labelText="Expected amount" value={currency(detail.expected_amount)} />
                          <Field labelText="Amount applied" value={currency(detail.amount_received)} />
                          <Field labelText="Remaining amount" value={currency(detail.outstanding_amount)} />
                          <Field labelText="Funding source" value={label(detail.expected_funding_source)} />
                          <Field labelText="Expectation source" value={label(detail.source)} />
                          <Field labelText="Reconciliation" value={label(detail.reconciliation_status)} />
                          <Field labelText="Authorization reference" value={detail.authorization_reference || "Not available"} />
                          <Field labelText="Contract reference" value={detail.contract_reference || "Not available"} />
                          <Field labelText="Facility" value={detail.facility_name_snapshot || "Not available"} />
                          <Field labelText="Residence type" value={label(detail.residence_type_snapshot)} />
                          <Field labelText="Service period" value={`${detail.service_period_start} – ${detail.service_period_end}`} />
                          <Box>
                            <Typography sx={{ color: "#7f97b3", fontSize: 12 }}>Due date</Typography>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography sx={{ color: "#e2e8f0", fontSize: 12.5 }}>{detail.due_date || "Not available"}</Typography>
                              {(() => {
                                const badge = dueDateBadge(detail.due_date_source, detail.payment_term_verified, detail.due_date);
                                return <Chip size="small" label={badge.label} sx={{ bgcolor: `${badge.color}22`, color: badge.color, fontWeight: 700, fontSize: 10.5 }} />;
                              })()}
                            </Stack>
                          </Box>
                        </Box>
                        <StatusChip value={detail.status} />
                        <Typography sx={{ color: "#cbd5e1", fontSize: 12.5, mt: 1.5 }}>
                          {detail.notes || "No notes recorded for this expectation."}
                        </Typography>

                        <Typography sx={{ color: "#fff", fontWeight: 700, mt: 2.5, mb: 1 }}>Applied Payments</Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                {["Payer", "Date", "Amount", "Remittance Ref", "Claim", "Adjustment", "Status", "Review Flag"].map((h) => (
                                  <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, borderColor: "#1f3a5c" }}>{h.toUpperCase()}</TableCell>
                                ))}
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {(detail.allocations ?? []).map((allocation) => (
                                <TableRow key={allocation.id}>
                                  <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c" }}>{allocation.payer_name || "Not available"}</TableCell>
                                  <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{allocation.payment_date || "Not available"}</TableCell>
                                  <TableCell sx={{ color: "#e2e8f0", borderColor: "#1f3a5c" }}>{currency(allocation.amount_applied)}</TableCell>
                                  <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{allocation.remittance_advice_id || "Not available"}</TableCell>
                                  <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{allocation.claim_id || "Not available"}</TableCell>
                                  <TableCell sx={{ color: "#7f97b3", borderColor: "#1f3a5c" }}>{allocation.payment_adjustment_id || "Not available"}</TableCell>
                                  <TableCell sx={{ borderColor: "#1f3a5c" }}><Chip size="small" label={label(allocation.allocation_status)} /></TableCell>
                                  <TableCell sx={{ color: allocation.flagged_for_review ? "#fbbf24" : "#7f97b3", borderColor: "#1f3a5c" }}>
                                    {allocation.flagged_for_review ? allocation.flagged_reason || "Review required" : "No"}
                                  </TableCell>
                                </TableRow>
                              ))}
                              {(detail.allocations?.length ?? 0) === 0 ? (
                                <TableRow>
                                  <TableCell colSpan={8} sx={{ textAlign: "center", color: "#7f97b3", py: 3, borderColor: "#1f3a5c" }}>
                                    No applied payments are linked to this expectation yet.
                                  </TableCell>
                                </TableRow>
                              ) : null}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Paper>

                      <Stack spacing={2}>
                        <Paper sx={{ bgcolor: "#0b1626", border: "1px solid #1f3a5c", p: 2 }}>
                          <Typography sx={{ color: "#fff", fontWeight: 700, mb: 1.5 }}>Expectation History</Typography>
                          <Stack spacing={1}>
                            {(history?.items ?? []).map((item) => (
                              <Box key={item.id} sx={{ border: item.id === detail.id ? "1px solid #10b7a2" : "1px solid #1f3a5c", borderRadius: 1.5, p: 1.5 }}>
                                <Stack direction="row" justifyContent="space-between" spacing={1}>
                                  <Typography sx={{ color: "#e2e8f0", fontWeight: 700 }}>Version {item.version_number}</Typography>
                                  <StatusChip value={item.status} />
                                </Stack>
                                <Typography sx={{ color: "#7f97b3", fontSize: 12, mt: 0.75 }}>
                                  {item.correction_reason || item.cancellation_reason || "No version note recorded."}
                                </Typography>
                                <Typography sx={{ color: "#7f97b3", fontSize: 11.5, mt: 0.5 }}>
                                  Created {item.created_at || "Not available"} • Actor {item.corrected_by || item.created_by || "Not available"}
                                </Typography>
                              </Box>
                            ))}
                            {(history?.items.length ?? 0) === 0 ? (
                              <Typography sx={{ color: "#7f97b3", fontSize: 12.5 }}>No version history is available.</Typography>
                            ) : null}
                          </Stack>
                        </Paper>

                        <Paper sx={{ bgcolor: "#0b1626", border: "1px solid #1f3a5c", p: 2 }}>
                          <Typography sx={{ color: "#fff", fontWeight: 700, mb: 1.5 }}>Residence Snapshot Comparison</Typography>
                          <Stack spacing={1}>
                            {Object.entries(snapshotDiff?.fields ?? {}).map(([field, values]) => (
                              <Box key={field} sx={{ border: "1px solid #1f3a5c", borderRadius: 1.5, p: 1.25, bgcolor: values.changed ? "#3f1d1d" : "transparent" }}>
                                <Typography sx={{ color: "#cbd5e1", fontWeight: 700, fontSize: 12 }}>{label(field)}</Typography>
                                <Typography sx={{ color: "#7f97b3", fontSize: 12 }}>Snapshot: {values.snapshot || "Not available"}</Typography>
                                <Typography sx={{ color: "#7f97b3", fontSize: 12 }}>Current: {values.current || "Not available"}</Typography>
                              </Box>
                            ))}
                            {snapshotDiff?.has_changes ? (
                              <Button variant="outlined" size="small" onClick={() => { setCorrectionForm(buildCorrectionForm(detail)); setCorrectionError(null); setCorrectionOpen(true); }}>
                                Correct Expectation
                              </Button>
                            ) : (
                              <Typography sx={{ color: "#7f97b3", fontSize: 12.5 }}>No residence snapshot differences were detected.</Typography>
                            )}
                          </Stack>
                        </Paper>
                      </Stack>
                    </Box>
                  </Stack>
                )}
              </Paper>
            </>
          )}
        </>
      )}

      <Dialog open={createOpen} onClose={() => !createBusy && setCreateOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Create Facility Payment Expectation</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {createError ? <Alert severity="error">{createError}</Alert> : null}
            <Typography variant="subtitle2">Patient and Residence</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField fullWidth label="Patient ID" value={createForm.patient_id} onChange={(e) => setCreateForm((current) => ({ ...current, patient_id: e.target.value }))} />
              <TextField fullWidth label="Patient POS ID" value={createForm.patient_pos_id} onChange={(e) => setCreateForm((current) => ({ ...current, patient_pos_id: e.target.value }))} />
            </Stack>
            <Typography variant="subtitle2">Financial Responsibility</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField select fullWidth label="Responsibility Category" value={createForm.responsibility_category} onChange={(e) => setCreateForm((current) => ({ ...current, responsibility_category: e.target.value }))}>
                {RESPONSIBILITY_CATEGORIES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
              </TextField>
              <TextField select fullWidth label="Funding Source" value={createForm.expected_funding_source} onChange={(e) => setCreateForm((current) => ({ ...current, expected_funding_source: e.target.value }))}>
                {FUNDING_SOURCES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
              </TextField>
              <TextField fullWidth label="Expected Amount" value={createForm.expected_amount} onChange={(e) => setCreateForm((current) => ({ ...current, expected_amount: e.target.value }))} />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField fullWidth label="Share of Cost Amount" value={createForm.share_of_cost_amount} onChange={(e) => setCreateForm((current) => ({ ...current, share_of_cost_amount: e.target.value }))} />
              <TextField fullWidth label="Currency" value={createForm.currency} onChange={(e) => setCreateForm((current) => ({ ...current, currency: e.target.value }))} />
              <TextField fullWidth label="Frequency" value={createForm.frequency} onChange={(e) => setCreateForm((current) => ({ ...current, frequency: e.target.value }))} />
            </Stack>
            <Typography variant="subtitle2">Service and Payment Period</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField fullWidth type="date" label="Service Period Start" InputLabelProps={{ shrink: true }} value={createForm.service_period_start} onChange={(e) => setCreateForm((current) => ({ ...current, service_period_start: e.target.value }))} />
              <TextField fullWidth type="date" label="Service Period End" InputLabelProps={{ shrink: true }} value={createForm.service_period_end} onChange={(e) => setCreateForm((current) => ({ ...current, service_period_end: e.target.value }))} />
              <TextField fullWidth type="date" label="Explicit Due Date" InputLabelProps={{ shrink: true }} value={createForm.due_date} onChange={(e) => setCreateForm((current) => ({ ...current, due_date: e.target.value }))} />
            </Stack>
            <Typography variant="subtitle2">Supporting Basis</Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField select fullWidth label="Expectation Source" value={createForm.source} onChange={(e) => setCreateForm((current) => ({ ...current, source: e.target.value }))}>
                {EXPECTATION_SOURCES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
              </TextField>
              <TextField fullWidth label="Expected Payer Name" value={createForm.expected_payer_name_snapshot} onChange={(e) => setCreateForm((current) => ({ ...current, expected_payer_name_snapshot: e.target.value }))} />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField fullWidth label="Authorization Reference" value={createForm.authorization_reference} onChange={(e) => setCreateForm((current) => ({ ...current, authorization_reference: e.target.value }))} />
              <TextField fullWidth label="Contract Reference" value={createForm.contract_reference} onChange={(e) => setCreateForm((current) => ({ ...current, contract_reference: e.target.value }))} />
            </Stack>
            <TextField fullWidth multiline minRows={3} label="Notes" value={createForm.notes} onChange={(e) => setCreateForm((current) => ({ ...current, notes: e.target.value }))} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)} disabled={createBusy}>Close</Button>
          <Button onClick={() => handleCreate("draft")} disabled={createBusy}>Save Draft</Button>
          <Button onClick={() => handleCreate("activate")} variant="contained" disabled={createBusy}>Activate</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={correctionOpen} onClose={() => !correctionBusy && setCorrectionOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Correct Expectation</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {correctionError ? <Alert severity="error">{correctionError}</Alert> : null}
            {correctionForm ? (
              <>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <TextField fullWidth label="Patient POS ID" value={correctionForm.patient_pos_id} onChange={(e) => setCorrectionForm((current) => current ? { ...current, patient_pos_id: e.target.value } : current)} />
                  <TextField fullWidth label="Expected Amount" value={correctionForm.expected_amount} onChange={(e) => setCorrectionForm((current) => current ? { ...current, expected_amount: e.target.value } : current)} />
                </Stack>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <TextField select fullWidth label="Responsibility Category" value={correctionForm.responsibility_category} onChange={(e) => setCorrectionForm((current) => current ? { ...current, responsibility_category: e.target.value } : current)}>
                    {RESPONSIBILITY_CATEGORIES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
                  </TextField>
                  <TextField select fullWidth label="Funding Source" value={correctionForm.expected_funding_source} onChange={(e) => setCorrectionForm((current) => current ? { ...current, expected_funding_source: e.target.value } : current)}>
                    {FUNDING_SOURCES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
                  </TextField>
                  <TextField select fullWidth label="Expectation Source" value={correctionForm.source} onChange={(e) => setCorrectionForm((current) => current ? { ...current, source: e.target.value } : current)}>
                    {EXPECTATION_SOURCES.map((value) => <MenuItem key={value} value={value}>{label(value)}</MenuItem>)}
                  </TextField>
                </Stack>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <TextField fullWidth type="date" label="Service Period Start" InputLabelProps={{ shrink: true }} value={correctionForm.service_period_start} onChange={(e) => setCorrectionForm((current) => current ? { ...current, service_period_start: e.target.value } : current)} />
                  <TextField fullWidth type="date" label="Service Period End" InputLabelProps={{ shrink: true }} value={correctionForm.service_period_end} onChange={(e) => setCorrectionForm((current) => current ? { ...current, service_period_end: e.target.value } : current)} />
                  <TextField fullWidth type="date" label="Explicit Due Date" InputLabelProps={{ shrink: true }} value={correctionForm.due_date} onChange={(e) => setCorrectionForm((current) => current ? { ...current, due_date: e.target.value } : current)} />
                </Stack>
                <TextField fullWidth label="Correction Reason" value={correctionForm.correction_reason} onChange={(e) => setCorrectionForm((current) => current ? { ...current, correction_reason: e.target.value } : current)} />
                <TextField fullWidth multiline minRows={3} label="Notes" value={correctionForm.notes} onChange={(e) => setCorrectionForm((current) => current ? { ...current, notes: e.target.value } : current)} />
              </>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCorrectionOpen(false)} disabled={correctionBusy}>Close</Button>
          <Button onClick={handleSaveCorrection} variant="contained" disabled={correctionBusy}>Save Correction</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={cancelOpen} onClose={() => !cancelBusy && setCancelOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Cancel Expectation</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {cancelError ? <Alert severity="error">{cancelError}</Alert> : null}
            {confirmedAllocations > 0 ? (
              <Alert severity="warning">
                This expectation has confirmed allocations. Cancelling it will preserve payment history and flag those allocations for review.
              </Alert>
            ) : null}
            <TextField fullWidth multiline minRows={3} label="Cancellation Reason" value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} />
            {confirmedAllocations > 0 ? (
              <FormControlLabel
                control={<Checkbox checked={cancelAcknowledged} onChange={(e) => setCancelAcknowledged(e.target.checked)} />}
                label="I understand the confirmed allocations must be reviewed after cancellation."
              />
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelOpen(false)} disabled={cancelBusy}>Close</Button>
          <Button onClick={handleCancel} color="error" variant="contained" disabled={cancelBusy}>Cancel Expectation</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
