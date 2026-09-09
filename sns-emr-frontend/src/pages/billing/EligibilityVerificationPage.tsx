import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import {
  fetchEligibilityDetail,
  fetchEligibilityRoster,
  type EligibilityDetailResponse,
  type EligibilityRosterResponse,
} from "../../api/dashboard";
import {
  addEligibilityBillingNote,
  createEligibilityVerification,
  escalateEligibilityIssue,
  submitRnReviewAction,
  uploadEligibilityDocument,
  type EscalationIssueType,
  type RnReviewAction,
} from "../../api/eligibilityActions";
import { fetchReadinessHistory, type ReadinessAuditEventRow } from "../../api/readinessWorkflow";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const ELIGIBILITY_DOCUMENT_TYPES = [
  "MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
  "PAYER_ELIGIBILITY_RESPONSE",
  "AUTHORIZATION_DOCUMENT",
  "ELIGIBILITY_SUPPORTING_DOCUMENT",
  "OTHER",
];

const PAYER_ELIGIBILITY_STATUSES = [
  "VERIFIED_ACTIVE",
  "VERIFIED_INACTIVE",
  "COVERAGE_CONFLICT",
  "REVIEW_REQUIRED",
  "PENDING",
];

const RN_ACTIONS: { value: RnReviewAction; label: string }[] = [
  { value: "APPROVE_DETERMINATION", label: "Approve Determination" },
  { value: "REJECT_DETERMINATION", label: "Reject Determination" },
  { value: "REQUEST_CLARIFICATION", label: "Request Clarification" },
  { value: "MARK_F2F_REQUIRED", label: "Mark F2F Required" },
  { value: "MARK_F2F_NOT_REQUIRED", label: "Mark F2F Not Required" },
  { value: "PLACE_ADMISSION_HOLD", label: "Place Admission Hold" },
  { value: "RELEASE_ADMISSION_HOLD", label: "Release Admission Hold" },
];

const STATUS_CHIP: Record<string, { label: string; bg: string; fg: string }> = {
  ACTIVE: { label: "Active", bg: "#14532d", fg: "#86efac" },
  INACTIVE: { label: "Inactive", bg: "#7f1d1d", fg: "#fca5a5" },
  UNKNOWN: { label: "Pending", bg: "#78350f", fg: "#fcd34d" },
  ERROR: { label: "Pending", bg: "#78350f", fg: "#fcd34d" },
};

function StatusChip({ status }: { status: string | null }) {
  const s = STATUS_CHIP[String(status || "").toUpperCase()] || { label: status || "—", bg: "#334155", fg: "#cbd5e1" };
  return <Chip label={s.label} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

// Human-readable labels -- this page must never show a raw backend enum
// value (e.g. "BENEFIT_PERIOD_CONFIRMED", "VERIFIED_ACTIVE") to a biller.
function humanizeEnum(value: string | null | undefined): string {
  if (!value) return "—";
  return value
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function readableDate(value: string | null | undefined): string {
  if (!value) return "—";
  // Dates/timestamps from the backend are ISO -- show only the
  // human-readable calendar date, never a raw ISO/UTC timestamp string.
  return value.slice(0, 10);
}

function EligibilityDetailDialog({
  patientId,
  tenantId,
  onClose,
}: {
  patientId: string;
  tenantId: string | null;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<EligibilityDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  const [auditEvents, setAuditEvents] = useState<ReadinessAuditEventRow[] | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);

  // Action-form local state -- deliberately simple controlled inputs, not a
  // form library, to keep this dialog's footprint small.
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState(ELIGIBILITY_DOCUMENT_TYPES[1]);
  const [uploadNotes, setUploadNotes] = useState("");

  const [verifyStatus, setVerifyStatus] = useState(PAYER_ELIGIBILITY_STATUSES[0]);
  const [verifyNotes, setVerifyNotes] = useState("");
  const [verifyPayerChange, setVerifyPayerChange] = useState(false);
  const [verifyCoverageChange, setVerifyCoverageChange] = useState(false);

  const [rnAction, setRnAction] = useState<RnReviewAction>("APPROVE_DETERMINATION");
  const [rnReason, setRnReason] = useState("");

  const [escalateType, setEscalateType] = useState<EscalationIssueType>("COVERAGE");
  const [escalateNotes, setEscalateNotes] = useState("");

  const [noteText, setNoteText] = useState("");

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchEligibilityDetail(patientId, tenantId)
      .then((res) => {
        if (isMounted) setDetail(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load eligibility detail.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [patientId, tenantId, refreshKey]);

  useEffect(() => {
    let isMounted = true;
    fetchReadinessHistory(patientId, tenantId)
      .then((res) => {
        if (isMounted) setAuditEvents(res.audit_trail);
      })
      .catch((err) => {
        if (isMounted) setAuditError(err?.message || "Unable to load audit history.");
      });
    return () => {
      isMounted = false;
    };
  }, [patientId, tenantId, refreshKey]);

  // Every action funnels through here: run it, surface a plain-language
  // result (including the Phase C billing-readiness impact when present),
  // then refetch both the detail view and the audit trail so the dialog
  // never shows stale state after a mutation.
  async function runAction(label: string, action: () => Promise<{ impact?: { billing_readiness_reevaluated: boolean; readiness_status: string | null } }>) {
    setActionBusy(true);
    setActionError(null);
    setActionMessage(null);
    try {
      const result = await action();
      const impactNote = result.impact
        ? result.impact.billing_readiness_reevaluated
          ? ` Billing readiness re-evaluated: ${humanizeEnum(result.impact.readiness_status)}.`
          : " Patient is not admitted -- billing readiness was not re-evaluated."
        : "";
      setActionMessage(`${label} succeeded.${impactNote}`);
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || err?.message || `${label} failed.`);
    } finally {
      setActionBusy(false);
    }
  }

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", bgcolor: "#0f1b2d", color: "#fff" }}>
        <Box>
          <Typography sx={{ fontWeight: 800, fontSize: 16 }}>{detail?.patient_name || detail?.mrn || "Eligibility Detail"}</Typography>
          <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>MRN {detail?.mrn || "—"}</Typography>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: "#7f97b3" }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ bgcolor: "#0f1b2d", borderBottom: "1px solid #1f3a5c", minHeight: 36, "& .MuiTab-root": { color: "#7f97b3", minHeight: 36, fontSize: 12, fontWeight: 700 }, "& .Mui-selected": { color: "#fff !important" } }}
      >
        <Tab label="Overview" />
        <Tab label="Actions" />
        <Tab label="Audit History" />
      </Tabs>
      <DialogContent sx={{ bgcolor: "#0f1b2d", pt: 2 }}>
        {error ? (
          <Alert severity="error">{error}</Alert>
        ) : loading || !detail ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : tab === 0 ? (
          <Box sx={{ display: "grid", gap: 2 }}>
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.5 }}>ADMISSION REVIEW STATUS</Typography>
              {detail.admission_gate_status === "ADMISSION_REVIEW_REQUIRED" ? (
                <Box sx={{ display: "grid", gap: 0.5 }}>
                  {detail.admission_gate_blockers.map((b, i) => (
                    <Chip key={i} label={b} size="small" sx={{ bgcolor: "#78350f", color: "#fcd34d", fontWeight: 700, height: "auto", py: 0.5, "& .MuiChip-label": { whiteSpace: "normal" } }} />
                  ))}
                </Box>
              ) : (
                <Chip label="Clear -- no open eligibility or benefit-period review" size="small" sx={{ bgcolor: "#14532d", color: "#86efac", fontWeight: 700 }} />
              )}
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.5 }}>
                BENEFIT-PERIOD DETERMINATION HISTORY
              </Typography>
              {detail.benefit_period_determination_history.length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No benefit-period determination recorded yet.</Typography>
              ) : (
                detail.benefit_period_determination_history.map((d) => (
                  <Box key={d.id} sx={{ display: "flex", justifyContent: "space-between", py: 0.75, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>
                      {humanizeEnum(d.determination_status)}
                      {d.anticipated_benefit_period_number ? ` -- Period ${d.anticipated_benefit_period_number}` : ""}
                      {d.superseded ? " (superseded)" : ""}
                    </Typography>
                    <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{readableDate(d.created_at)}</Typography>
                  </Box>
                ))
              )}
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.5 }}>VERIFICATION HISTORY</Typography>
              {detail.verification_history.length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No eligibility verification recorded yet.</Typography>
              ) : (
                detail.verification_history.map((v) => (
                  <Box key={v.id} sx={{ display: "flex", justifyContent: "space-between", py: 0.75, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>
                      {humanizeEnum(v.status)} ({humanizeEnum(v.verification_method)})
                      {v.superseded ? " (superseded)" : ""}
                    </Typography>
                    <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{readableDate(v.verification_date || v.created_at)}</Typography>
                  </Box>
                ))
              )}
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.5 }}>SOURCE DOCUMENTS</Typography>
              {detail.source_documents.length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No eligibility source document uploaded yet.</Typography>
              ) : (
                detail.source_documents.map((doc) => (
                  <Box key={doc.id} sx={{ display: "flex", justifyContent: "space-between", py: 0.75, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>
                      {humanizeEnum(doc.document_type)} -- {humanizeEnum(doc.status)}
                    </Typography>
                    <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{readableDate(doc.uploaded_at)}</Typography>
                  </Box>
                ))
              )}
            </Box>
          </Box>
        ) : tab === 1 ? (
          <Box sx={{ display: "grid", gap: 2.5 }}>
            {actionMessage ? <Alert severity="success" onClose={() => setActionMessage(null)}>{actionMessage}</Alert> : null}
            {actionError ? <Alert severity="error" onClose={() => setActionError(null)}>{actionError}</Alert> : null}

            {/* Phase A -- document upload */}
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.75 }}>UPLOAD ELIGIBILITY DOCUMENT</Typography>
              <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "1fr 1fr", alignItems: "center" }}>
                <TextField
                  select
                  size="small"
                  label="Document Type"
                  value={uploadDocType}
                  onChange={(e) => setUploadDocType(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
                >
                  {ELIGIBILITY_DOCUMENT_TYPES.map((t) => (
                    <MenuItem key={t} value={t}>
                      {humanizeEnum(t)}
                    </MenuItem>
                  ))}
                </TextField>
                <Button component="label" variant="outlined" size="small" sx={{ borderColor: "#1f3a5c", color: "#e2e8f0" }}>
                  {uploadFile ? uploadFile.name : "Choose File"}
                  <input
                    hidden
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                  />
                </Button>
              </Box>
              <TextField
                size="small"
                fullWidth
                placeholder="Notes"
                value={uploadNotes}
                onChange={(e) => setUploadNotes(e.target.value)}
                sx={{ mt: 1, input: { color: "#e2e8f0" } }}
              />
              <Button
                variant="contained"
                size="small"
                disabled={actionBusy || !uploadFile}
                sx={{ mt: 1 }}
                onClick={() =>
                  uploadFile &&
                  runAction("Document upload", () =>
                    uploadEligibilityDocument(
                      patientId,
                      { file: uploadFile, document_type: uploadDocType, notes: uploadNotes || null },
                      tenantId
                    ).then(() => ({}))
                  )
                }
              >
                Upload
              </Button>
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            {/* Phase B -- reverification */}
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.75 }}>RECORD ELIGIBILITY VERIFICATION / REVERIFICATION</Typography>
              <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "1fr 1fr" }}>
                <TextField
                  select
                  size="small"
                  label="Status"
                  value={verifyStatus}
                  onChange={(e) => setVerifyStatus(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
                >
                  {PAYER_ELIGIBILITY_STATUSES.map((s) => (
                    <MenuItem key={s} value={s}>
                      {humanizeEnum(s)}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  size="small"
                  placeholder="Notes"
                  value={verifyNotes}
                  onChange={(e) => setVerifyNotes(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" } }}
                />
              </Box>
              <Box sx={{ display: "flex", gap: 2, mt: 0.75 }}>
                <label style={{ color: "#7f97b3", fontSize: 12 }}>
                  <input type="checkbox" checked={verifyPayerChange} onChange={(e) => setVerifyPayerChange(e.target.checked)} /> Payer changed
                </label>
                <label style={{ color: "#7f97b3", fontSize: 12 }}>
                  <input type="checkbox" checked={verifyCoverageChange} onChange={(e) => setVerifyCoverageChange(e.target.checked)} /> Coverage changed
                </label>
              </Box>
              <Button
                variant="contained"
                size="small"
                disabled={actionBusy || detail.source_documents.length === 0}
                sx={{ mt: 1 }}
                onClick={() =>
                  runAction("Eligibility verification", () =>
                    createEligibilityVerification(
                      patientId,
                      {
                        source_document_id: detail.source_documents[0].id,
                        status: verifyStatus,
                        notes: verifyNotes || null,
                        payer_change_flag: verifyPayerChange,
                        coverage_change_flag: verifyCoverageChange,
                      },
                      tenantId
                    )
                  )
                }
              >
                Submit Verification
              </Button>
              {detail.source_documents.length === 0 ? (
                <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mt: 0.5 }}>
                  Upload a source document above first -- a verification must reference one.
                </Typography>
              ) : null}
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            {/* Phase D -- RN review actions */}
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.75 }}>RN REVIEW ACTION</Typography>
              <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "1fr 1fr" }}>
                <TextField
                  select
                  size="small"
                  label="Action"
                  value={rnAction}
                  onChange={(e) => setRnAction(e.target.value as RnReviewAction)}
                  sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
                >
                  {RN_ACTIONS.map((a) => (
                    <MenuItem key={a.value} value={a.value}>
                      {a.label}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  size="small"
                  placeholder="Reason (required)"
                  value={rnReason}
                  onChange={(e) => setRnReason(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" } }}
                />
              </Box>
              <Button
                variant="contained"
                size="small"
                disabled={actionBusy || !rnReason.trim()}
                sx={{ mt: 1 }}
                onClick={() =>
                  runAction("RN review action", () =>
                    submitRnReviewAction(patientId, { action: rnAction, reason: rnReason }, tenantId)
                  )
                }
              >
                Submit RN Action
              </Button>
            </Box>

            <Divider sx={{ borderColor: "#1f3a5c" }} />

            {/* Phase E -- biller workspace actions */}
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3", mb: 0.75 }}>BILLER ACTIONS</Typography>
              <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "1fr 1fr" }}>
                <TextField
                  select
                  size="small"
                  label="Escalate Issue"
                  value={escalateType}
                  onChange={(e) => setEscalateType(e.target.value as EscalationIssueType)}
                  sx={{ input: { color: "#e2e8f0" }, label: { color: "#7f97b3" } }}
                >
                  <MenuItem value="COVERAGE">Coverage</MenuItem>
                  <MenuItem value="MSP">MSP</MenuItem>
                  <MenuItem value="MA">Medicare Advantage</MenuItem>
                </TextField>
                <TextField
                  size="small"
                  placeholder="Escalation notes"
                  value={escalateNotes}
                  onChange={(e) => setEscalateNotes(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" } }}
                />
              </Box>
              <Button
                variant="outlined"
                size="small"
                disabled={actionBusy || !escalateNotes.trim()}
                sx={{ mt: 1, mr: 1, borderColor: "#78350f", color: "#fcd34d" }}
                onClick={() =>
                  runAction("Escalation", () =>
                    escalateEligibilityIssue(patientId, { issue_type: escalateType, notes: escalateNotes }, tenantId).then(() => ({}))
                  )
                }
              >
                Escalate
              </Button>

              <Box sx={{ display: "flex", gap: 1, mt: 1.5 }}>
                <TextField
                  size="small"
                  fullWidth
                  placeholder="Add a billing note"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  sx={{ input: { color: "#e2e8f0" } }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  disabled={actionBusy || !noteText.trim()}
                  sx={{ borderColor: "#1f3a5c", color: "#e2e8f0", whiteSpace: "nowrap" }}
                  onClick={() =>
                    runAction("Note", () =>
                      addEligibilityBillingNote(patientId, noteText, tenantId).then(() => {
                        setNoteText("");
                        return {};
                      })
                    )
                  }
                >
                  Add Note
                </Button>
              </Box>
            </Box>
          </Box>
        ) : (
          <Box sx={{ display: "grid", gap: 1 }}>
            <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#7f97b3" }}>AUDIT TRAIL</Typography>
            {auditError ? (
              <Alert severity="error">{auditError}</Alert>
            ) : auditEvents === null ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
                <CircularProgress size={20} />
              </Box>
            ) : auditEvents.length === 0 ? (
              <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No workflow events recorded yet.</Typography>
            ) : (
              auditEvents.map((e) => (
                <Box key={e.id} sx={{ display: "flex", justifyContent: "space-between", py: 0.75, borderBottom: "1px solid #1f3a5c" }}>
                  <Box>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 600 }}>
                      {humanizeEnum(e.entity_type)} -- {humanizeEnum(e.event_type)}
                    </Typography>
                    {e.reason ? (
                      <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{e.reason}</Typography>
                    ) : null}
                  </Box>
                  <Typography sx={{ fontSize: 11.5, color: "#7f97b3", whiteSpace: "nowrap" }}>{readableDate(e.occurred_at)}</Typography>
                </Box>
              ))
            )}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}


export default function EligibilityVerificationPage() {
  const { selectedAgencyId } = useAgency();
  const [data, setData] = useState<EligibilityRosterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchEligibilityRoster(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load eligibility roster.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const rows = data?.roster ?? [];
  const verifiedPct =
    data && data.total_active > 0 ? Math.round((data.eligible_count / data.total_active) * 1000) / 10 : 0;

  const metrics = useMemo(
    () => [
      { label: "Total Active Census", value: String(data?.total_active ?? 0), caption: "Active patient insurance records" },
      {
        label: "Eligible Status",
        value: String(data?.eligible_count ?? 0),
        caption: `${verifiedPct}% of active roster verified`,
        color: "#4ade80",
      },
      {
        label: "Pending Re-Verify",
        value: String(data?.pending_count ?? 0),
        caption: "Verification needed",
        color: (data?.pending_count ?? 0) > 0 ? "#fbbf24" : "#4ade80",
      },
      {
        label: "Inactive / No Coverage",
        value: String(data?.inactive_count ?? 0),
        caption: "Immediate administrative action required",
        color: (data?.inactive_count ?? 0) > 0 ? "#f87171" : "#4ade80",
      },
    ],
    [data, verifiedPct]
  );

  return (
    <Box>
      <PageHeader title="Eligibility Verification" subtitle="Real-time eligibility status and verification tracking" />

      <HipaaBanner message='Under HIPAA "Minimum Necessary" guidelines, this view is restricted to administrative claim statuses, financial tallies, and routing identifiers. Clinical notes, narrative medical histories, and physician notes are hidden.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its eligibility roster.</Alert>
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
                PATIENT COVERAGE STATUS ROSTER
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {["Patient", "Primary Payer", "Subscriber ID", "Status", "Last Verified", "Next Due", "Action Required"].map((h) => (
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
                          No active insurance records found for this agency.
                        </TableCell>
                      </TableRow>
                    ) : (
                      rows.map((r) => (
                        <TableRow
                          key={r.insurance_id}
                          hover
                          onClick={() => setSelectedPatientId(r.patient_id)}
                          sx={{ cursor: "pointer" }}
                        >
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.patient_name || r.mrn || r.patient_id}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.payer_name || "—"}</TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.subscriber_id || "—"}</TableCell>
                          <TableCell sx={{ borderColor: "#1f3a5c" }}>
                            <StatusChip status={r.eligibility_status} />
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.verified_at ? r.verified_at.slice(0, 10) : "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.next_verification_due || "—"}
                          </TableCell>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                            {r.admission_gate_status === "ADMISSION_REVIEW_REQUIRED" ? (
                              <Chip
                                label={r.action_required || "Review required"}
                                size="small"
                                sx={{ fontSize: 11, height: 22, bgcolor: "#78350f", color: "#fcd34d", fontWeight: 700, maxWidth: 260 }}
                              />
                            ) : (
                              "—"
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", px: 2, py: 1.2 }}>
                Showing {rows.length} of {data?.total_active ?? 0} patients
              </Typography>
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 12.5, fontWeight: 800, color: "#fff", mb: 0.5 }}>Upcoming Reverifications</Typography>
              <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mb: 1.5 }}>Due within the next 7 days</Typography>
              {(data?.upcoming_reverifications ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>Nothing due in the next 7 days.</Typography>
              ) : (
                <Box sx={{ display: "grid", gap: 1 }}>
                  {(data?.upcoming_reverifications ?? []).map((u) => (
                    <Box
                      key={u.insurance_id}
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        bgcolor: "#0b1626",
                        border: "1px solid #1f3a5c",
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 1,
                      }}
                    >
                      <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 600 }}>
                        {u.patient_name || u.mrn}
                      </Typography>
                      <Chip
                        label={`In ${u.days_until_due} day${u.days_until_due === 1 ? "" : "s"}`}
                        size="small"
                        sx={{ fontSize: 11, height: 20, bgcolor: "#78350f", color: "#fcd34d", fontWeight: 700 }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </Paper>
          </Box>
        </>
      )}

      {selectedPatientId ? (
        <EligibilityDetailDialog
          patientId={selectedPatientId}
          tenantId={selectedAgencyId}
          onClose={() => setSelectedPatientId(null)}
        />
      ) : null}
    </Box>
  );
}
