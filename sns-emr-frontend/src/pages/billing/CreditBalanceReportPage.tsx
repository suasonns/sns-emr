import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
  fetchCreditBalanceReasonCodes,
  fetchCreditBalanceReport,
  openCreditBalanceCase,
  performCreditBalanceCaseAction,
  type CreditBalanceClaimItem,
  type CreditBalanceReportResponse,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

// Credit Balance Report -- pure presentation over GET
// /billing/credit-balance/report. All detection math (Claim Net Balance =
// Total Charges - Posted Payments - Adjustments - Write-offs; a claim is a
// potential credit balance when this is negative) lives in the backend
// credit_balance_service; no logic is duplicated here. Claim-level rows are
// the authoritative grain -- the patient/account table is a summary only
// and never hides an individual claim's credit balance, even when the
// patient's net account balance is $0.

type ViewMode = "single" | "all";

function currency(value: { amount: string } | undefined | null): string {
  if (!value) return "—";
  const n = Number(value.amount);
  if (Number.isNaN(n)) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const MEDICARE_LABELS: Record<string, string> = {
  MEDICARE_REPORTABLE: "Medicare (CMS-838)",
  NON_MEDICARE: "Non-Medicare",
  UNKNOWN: "Unknown — needs review",
};

const STATUS_COLORS: Record<string, string> = {
  POTENTIAL: "#94a3b8",
  UNDER_REVIEW: "#fbbf24",
  CONFIRMED: "#fb923c",
  NOT_A_CREDIT_BALANCE: "#4ade80",
  REPAYMENT_REQUIRED: "#f87171",
  REFUND_PENDING: "#f87171",
  RECOUPMENT_PENDING: "#f87171",
  REALLOCATION_PENDING: "#f87171",
  RESOLVED_REPAID: "#4ade80",
  RESOLVED_RECOUPED: "#4ade80",
  RESOLVED_REALLOCATED: "#4ade80",
  CLOSED: "#7f97b3",
};

const ACTION_OPTIONS = [
  { value: "REQUEST_INVESTIGATION", label: "Request Investigation" },
  { value: "CONFIRM_CREDIT", label: "Confirm Credit" },
  { value: "REJECT_CREDIT", label: "Reject Credit" },
  { value: "DETERMINE_REPAYMENT_REQUIRED", label: "Determine Repayment Required" },
  { value: "INITIATE_REFUND", label: "Initiate Refund" },
  { value: "RECORD_REFUND", label: "Record Refund" },
  { value: "REQUEST_RECOUPMENT", label: "Request Recoupment" },
  { value: "RECORD_RECOUPMENT", label: "Record Recoupment" },
  { value: "REQUEST_REALLOCATION", label: "Request Reallocation" },
  { value: "RECORD_REALLOCATION", label: "Record Reallocation" },
  { value: "CORRECT_MISPOSTING", label: "Correct Misposting" },
  { value: "RECORD_CORRESPONDENCE", label: "Record Payer Correspondence" },
  { value: "CLOSE_CASE", label: "Close Case" },
];

// Root-cause labels for the reason_code enumeration -- a biller selects
// the actual cause after reviewing a "Potential Duplicate Payment" flag;
// the system never infers this automatically (see backend
// credit_balance_case_service.DUPLICATE_PAYMENT_REASON_CODES).
const REASON_CODE_LABELS: Record<string, string> = {
  DUPLICATE_PAYMENT: "Duplicate Payment",
  POSTING_ERROR: "Posting Error",
  COB_ISSUE: "COB Issue",
  MSP_ISSUE: "MSP Issue",
  RECOUPMENT_TIMING: "Recoupment Timing",
  OTHER: "Other",
};

export default function CreditBalanceReportPage() {
  const { selectedAgencyId } = useAgency();
  const [viewMode, setViewMode] = useState<ViewMode>("single");
  const [data, setData] = useState<CreditBalanceReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const [actionClaim, setActionClaim] = useState<CreditBalanceClaimItem | null>(null);
  const [actionCaseId, setActionCaseId] = useState<string | null>(null);
  const [actionType, setActionType] = useState("REQUEST_INVESTIGATION");
  const [actionReason, setActionReason] = useState("");
  const [actionAmount, setActionAmount] = useState("");
  const [actionReasonCode, setActionReasonCode] = useState("");
  const [reasonCodes, setReasonCodes] = useState<string[]>([]);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchCreditBalanceReasonCodes()
      .then((res) => {
        if (isMounted) setReasonCodes(res.reason_codes ?? []);
      })
      .catch(() => {
        // Non-fatal: the reason_code dropdown just stays empty/optional.
      });
    return () => {
      isMounted = false;
    };
  }, []);

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
        ? fetchCreditBalanceReport(undefined, { all_agencies: true })
        : fetchCreditBalanceReport(selectedAgencyId);
    request
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load credit balance report.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId, viewMode, reloadToken]);

  const metrics = useMemo(() => {
    const s = data?.summary;
    const cmsReportable = (data?.claim_credit_items ?? []).filter(
      (c) => c.medicare_classification === "MEDICARE_REPORTABLE"
    ).length;
    return [
      { label: "Total Potential Credits", value: currency(s?.total_potential_credits), caption: "Claims with a negative net balance", color: "#f87171" },
      { label: "Claims With Credits", value: String(s?.claim_count ?? 0), caption: "Authoritative claim-level grain" },
      { label: "Patient Accounts Affected", value: String(s?.patient_count ?? 0), caption: "Summary only -- never nets away claim credits" },
      { label: "Medicare (CMS-838) Cases", value: String(cmsReportable), caption: "Classified from real PatientPayer metadata", color: "#fb923c" },
    ];
  }, [data]);

  function openActionDialog(claim: CreditBalanceClaimItem) {
    setActionClaim(claim);
    setActionCaseId(claim.case_id);
    setActionType(claim.case_id ? "REQUEST_INVESTIGATION" : "REQUEST_INVESTIGATION");
    setActionReason("");
    setActionAmount("");
    setActionReasonCode("");
    setActionError(null);
  }

  async function handleOpenCaseThenAct() {
    if (!actionClaim) return;
    setActionBusy(true);
    setActionError(null);
    try {
      let caseId = actionCaseId;
      if (!caseId) {
        const opened = await openCreditBalanceCase(actionClaim.claim_id);
        caseId = opened.case_id;
        setActionCaseId(caseId);
      }
      if (!actionReason.trim()) {
        setActionError("A reason is required for every credit-balance case action.");
        setActionBusy(false);
        return;
      }
      await performCreditBalanceCaseAction(caseId, {
        action: actionType,
        reason: actionReason,
        amount: actionAmount || undefined,
        reason_code: actionReasonCode || undefined,
      });
      setActionClaim(null);
      setReloadToken((t) => t + 1);
    } catch (err: any) {
      setActionError(err?.message || "Unable to complete this action.");
    } finally {
      setActionBusy(false);
    }
  }

  return (
    <Box>
      <PageHeader
        title="Credit Balance Report"
        subtitle="Claim-level overpayment detection, patient/account summary, and CMS-838 case tracking"
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
        <Alert severity="info">Select an agency to view its credit balance report, or switch to "All Assigned Agencies".</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden", mb: 2.5 }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              PATIENT / ACCOUNT SUMMARY
            </Typography>
            <TableContainer sx={{ maxHeight: 320 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Patient", "Agency", "Primary Payer", "Secondary Payer", "Total Charges", "Total Payments", "Positive AR", "Credit Balance", "Net Balance", "Claims w/ Credit", "Oldest Unresolved"].map((h) => (
                      <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}>
                        {h.toUpperCase()}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.patient_accounts ?? []).length === 0 ? (
                    <TableRow>
                        <TableCell colSpan={11} sx={{ textAlign: "center", color: "#7f97b3", py: 3, borderColor: "#1f3a5c" }}>
                        No patient accounts with an outstanding credit balance.
                      </TableCell>
                    </TableRow>
                  ) : (
                    (data?.patient_accounts ?? []).map((p) => (
                      <TableRow key={p.patient_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.mrn || p.patient_name || p.patient_id}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.agency_name}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.primary_payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.secondary_payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(p.total_charges)}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(p.total_payments)}</TableCell>
                          <TableCell sx={{ color: "#4ade80", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(p.total_positive_ar)}</TableCell>
                          <TableCell sx={{ color: "#f87171", fontSize: 13, fontWeight: 700, borderColor: "#1f3a5c" }}>{currency(p.total_credit_balance)}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(p.net_patient_account_balance)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.claims_with_credit}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{p.oldest_unresolved_credit ? p.oldest_unresolved_credit.slice(0, 10) : "—"}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              CLAIM-LEVEL CREDIT DETAIL
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Patient", "Payer", "Primary Payer", "Secondary Payer", "Agency", "Charges", "Payments", "Credit Amount", "Medicare", "Flags", "Case Status", "Action"].map((h) => (
                      <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}>
                        {h.toUpperCase()}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.claim_credit_items ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={12} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No claims with a potential credit balance.
                      </TableCell>
                    </TableRow>
                  ) : (
                    (data?.claim_credit_items ?? []).map((c) => (
                      <TableRow key={c.claim_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.mrn || c.patient_name || c.patient_id}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.payer_name}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.primary_payer_name || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.secondary_payer_name || "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{c.agency_name}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.total_charge)}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{currency(c.posted_payments)}</TableCell>
                        <TableCell sx={{ color: "#f87171", fontSize: 13, fontWeight: 700, borderColor: "#1f3a5c" }}>{currency(c.credit_amount)}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Chip
                            label={MEDICARE_LABELS[c.medicare_classification] || c.medicare_classification}
                            size="small"
                            sx={{ fontWeight: 700, fontSize: 10.5, height: 22, bgcolor: "#0b1626", color: "#e2e8f0", border: "1px solid #1f3a5c" }}
                          />
                        </TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          {c.potential_duplicate_payment ? (
                            <Chip
                              label="Potential Duplicate Payment"
                              size="small"
                              sx={{ fontWeight: 700, fontSize: 10.5, height: 22, bgcolor: "#2a1810", color: "#fb923c", border: "1px solid #7c2d12" }}
                            />
                          ) : (
                            <Typography sx={{ color: "#334155", fontSize: 12 }}>—</Typography>
                          )}
                        </TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Chip
                            label={c.case_status}
                            size="small"
                            sx={{ fontWeight: 700, fontSize: 10.5, height: 22, bgcolor: "#0b1626", color: STATUS_COLORS[c.case_status] || "#e2e8f0", border: "1px solid #1f3a5c" }}
                          />
                        </TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => openActionDialog(c)}
                            sx={{ textTransform: "none", fontSize: 12, borderColor: "#334155", color: "#e2e8f0" }}
                          >
                            {c.case_id ? "Manage Case" : "Open Case"}
                          </Button>
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

      <Dialog open={actionClaim !== null} onClose={() => setActionClaim(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: 15, fontWeight: 700 }}>
          {actionClaim?.case_id ? "Manage Credit Balance Case" : "Open Credit Balance Case"}
        </DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {actionClaim ? (
            <Typography sx={{ fontSize: 13, color: "#475569" }}>
              {actionClaim.mrn || actionClaim.patient_name} -- {actionClaim.payer_name} -- Credit Amount {currency(actionClaim.credit_amount)}
            </Typography>
          ) : null}
          {actionClaim && (actionClaim.primary_payer_name || actionClaim.secondary_payer_name) ? (
            <Typography sx={{ fontSize: 12.5, color: "#64748b" }}>
              Primary Payer: {actionClaim.primary_payer_name || "—"}
              {actionClaim.primary_payer_name ? ` (Paid ${currency(actionClaim.primary_payer_paid)})` : ""}
              {" \u2014 "}
              Secondary Payer: {actionClaim.secondary_payer_name || "—"}
              {actionClaim.secondary_payer_name ? ` (Paid ${currency(actionClaim.secondary_payer_paid)})` : ""}
              {actionClaim.most_recent_payment_date ? ` \u2014 Most Recent Payment: ${actionClaim.most_recent_payment_date}` : ""}
            </Typography>
          ) : null}
          {actionClaim?.potential_duplicate_payment ? (
            <Alert severity="warning">
              This claim has 2+ payments posted for the exact same amount (Potential Duplicate Payment). This is a
              detection signal only -- review the payment history and select the actual root cause below before
              confirming.
            </Alert>
          ) : null}
          {actionError ? <Alert severity="error">{actionError}</Alert> : null}
          <TextField select label="Action" size="small" value={actionType} onChange={(e) => setActionType(e.target.value)}>
            {ACTION_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Reason (required)"
            size="small"
            multiline
            minRows={2}
            value={actionReason}
            onChange={(e) => setActionReason(e.target.value)}
          />
          <TextField
            select
            label="Root Cause / Reason Code (optional)"
            size="small"
            value={actionReasonCode}
            onChange={(e) => setActionReasonCode(e.target.value)}
          >
            <MenuItem value="">Not yet determined</MenuItem>
            {(reasonCodes.length > 0 ? reasonCodes : Object.keys(REASON_CODE_LABELS)).map((code) => (
              <MenuItem key={code} value={code}>
                {REASON_CODE_LABELS[code] || code}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Amount (optional -- refund/recoupment/reallocation actions)"
            size="small"
            value={actionAmount}
            onChange={(e) => setActionAmount(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionClaim(null)} disabled={actionBusy} sx={{ textTransform: "none" }}>
            Cancel
          </Button>
          <Button onClick={handleOpenCaseThenAct} disabled={actionBusy} variant="contained" sx={{ textTransform: "none" }}>
            {actionBusy ? "Submitting…" : "Submit"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
