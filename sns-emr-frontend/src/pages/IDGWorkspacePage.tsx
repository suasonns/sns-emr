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
  Divider,
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";
import { getCurrentUser } from "../api/session";
import {
  listIdgSessions,
  getIdgSessionPatients,
  setPatientReviewStatus,
  getBatchSignatureQueue,
  batchSignOrders,
  type IDGSessionSummary,
  type IDGSessionPatientRow,
  type BatchQueueEntry,
} from "../api/idgWorkspace";

const DEFER_REASONS: { value: string; label: string }[] = [
  { value: "NEED_TO_CONTACT_ATTENDING_PHYSICIAN", label: "Need to contact attending physician" },
  { value: "NEED_MORE_INFORMATION", label: "Needs additional information" },
  { value: "NEED_LABS_RESULTS", label: "Awaiting labs/results" },
  { value: "MEDICATION_ISSUE_UNRESOLVED", label: "Medication issue unresolved" },
  { value: "NEED_FAMILY_CAREGIVER_CLARIFICATION", label: "Need family/caregiver clarification" },
  { value: "NEED_TO_REVIEW_CHART", label: "Need to review chart" },
  { value: "OTHER", label: "Other" },
];

function formatMeetingDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function statusColor(status: string): "default" | "success" | "warning" | "error" {
  if (status === "REVIEWED") return "success";
  if (status === "DEFERRED") return "warning";
  return "default";
}

export default function IDGWorkspacePage() {
  const currentUser = getCurrentUser();
  const role = currentUser?.role || "";
  const isMD = role === "MD";
  // OWNER (platform/vendor super-user) and BILLER have no clinical reason
  // to view IDG patient rosters, review status, or defer reasons — this is
  // PHI that must stay minimum-necessary. The nav already hides this link
  // for those roles; this guard blocks direct-URL/back-button access too.
  // The backend independently enforces the same restriction on every
  // /idg/sessions* endpoint, so this is defense-in-depth, not the only gate.
  const isRestrictedRole = role === "OWNER" || role === "BILLING";

  const user = {
    name: currentUser?.full_name || "Signed-in user",
    role,
    tenant_name: currentUser?.tenant_name,
  };

  const [sessions, setSessions] = useState<IDGSessionSummary[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [patients, setPatients] = useState<IDGSessionPatientRow[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [error, setError] = useState<string>("");

  const [reviewTarget, setReviewTarget] = useState<IDGSessionPatientRow | null>(null);
  const [deferReason, setDeferReason] = useState(DEFER_REASONS[0].value);
  const [deferNote, setDeferNote] = useState("");
  const [savingReview, setSavingReview] = useState(false);

  const [batchQueue, setBatchQueue] = useState<BatchQueueEntry[] | null>(null);
  const [loadingBatchQueue, setLoadingBatchQueue] = useState(false);
  const [signing, setSigning] = useState(false);

  useEffect(() => {
    if (isRestrictedRole) return;
    let active = true;
    listIdgSessions()
      .then((data) => {
        if (!active) return;
        setSessions(data);
        if (data.length && !selectedDate) {
          setSelectedDate(data[0].meeting_date);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load IDG sessions"))
      .finally(() => active && setLoadingSessions(false));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPatients = (meetingDate: string) => {
    setLoadingPatients(true);
    setBatchQueue(null);
    getIdgSessionPatients(meetingDate)
      .then((rows) => setPatients(rows))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load patients for this session"))
      .finally(() => setLoadingPatients(false));
  };

  useEffect(() => {
    if (selectedDate) loadPatients(selectedDate);
  }, [selectedDate]);

  const reviewedCount = useMemo(() => patients.filter((p) => p.review_status === "REVIEWED").length, [patients]);
  const deferredCount = useMemo(() => patients.filter((p) => p.review_status === "DEFERRED").length, [patients]);
  const pendingCount = useMemo(() => patients.filter((p) => p.review_status === "PENDING").length, [patients]);

  const currentMeetingId = patients[0]?.idg_meeting_id ?? null;

  const handleMarkReviewed = async (row: IDGSessionPatientRow) => {
    if (!currentUser?.id) return;
    setSavingReview(true);
    try {
      await setPatientReviewStatus(row.idg_meeting_id, row.patient_id as string, {
        physician_user_id: currentUser.id,
        review_status: "REVIEWED",
        poc_reviewed: true,
        medication_list_reviewed: true,
        medication_reconciliation_reviewed: true,
        orders_reviewed: true,
        discussion_reviewed: true,
      });
      if (selectedDate) loadPatients(selectedDate);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record review");
    } finally {
      setSavingReview(false);
    }
  };

  const openDeferDialog = (row: IDGSessionPatientRow) => {
    setReviewTarget(row);
    setDeferReason(DEFER_REASONS[0].value);
    setDeferNote("");
  };

  const handleConfirmDefer = async () => {
    if (!reviewTarget || !currentUser?.id) return;
    setSavingReview(true);
    try {
      await setPatientReviewStatus(reviewTarget.idg_meeting_id, reviewTarget.patient_id as string, {
        physician_user_id: currentUser.id,
        review_status: "DEFERRED",
        defer_reason: deferReason,
        defer_note: deferNote || null,
      });
      setReviewTarget(null);
      if (selectedDate) loadPatients(selectedDate);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to defer review");
    } finally {
      setSavingReview(false);
    }
  };

  const handleOpenBatchQueue = async () => {
    if (!currentMeetingId) return;
    setLoadingBatchQueue(true);
    try {
      const queue = await getBatchSignatureQueue(currentMeetingId);
      setBatchQueue(queue);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load batch signature queue");
    } finally {
      setLoadingBatchQueue(false);
    }
  };

  const handleBatchSignAll = async () => {
    if (!currentMeetingId || !batchQueue?.length) return;
    setSigning(true);
    try {
      await batchSignOrders(
        currentMeetingId,
        batchQueue.map((e) => e.patient_id),
      );
      await handleOpenBatchQueue();
      if (selectedDate) loadPatients(selectedDate);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch signing failed");
    } finally {
      setSigning(false);
    }
  };

  if (isRestrictedRole) {
    return (
      <Box sx={{ display: "flex" }}>
        <Sidebar role={role} user={user} />
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <Header user={user} />
          <Box sx={{ p: 3 }}>
            <Alert severity="warning">
              The IDG Meeting Workspace contains patient clinical information and is not
              available to the {role} role. Please contact a clinical or agency admin user
              if you need this data.
            </Alert>
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex" }}>
      <Sidebar role={role} user={user} />
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Header user={user} />
        <Box sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: 800 }} gutterBottom>
            IDG Meeting Workspace
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Review is separate from signature. Deferred patients are excluded from batch
            signing and generate an MD alert task automatically.
          </Typography>

          {error ? (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
              {error}
            </Alert>
          ) : null}

          <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
            {/* Session date list */}
            <Paper sx={{ width: 280, p: 1 }}>
              <Typography variant="subtitle2" sx={{ px: 1, py: 1, fontWeight: 700 }}>
                IDG Sessions
              </Typography>
              <Divider />
              {loadingSessions ? (
                <Box sx={{ p: 2, textAlign: "center" }}>
                  <CircularProgress size={20} />
                </Box>
              ) : sessions.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                  No IDG sessions scheduled yet.
                </Typography>
              ) : (
                <List dense>
                  {sessions.map((s) => (
                    <ListItemButton
                      key={s.meeting_date}
                      selected={s.meeting_date === selectedDate}
                      onClick={() => setSelectedDate(s.meeting_date)}
                    >
                      <ListItemText
                        primary={formatMeetingDate(s.meeting_date)}
                        secondary={`${s.patient_count} patient(s)`}
                      />
                    </ListItemButton>
                  ))}
                </List>
              )}
            </Paper>

            {/* Patient roster for selected session */}
            <Paper sx={{ flex: 1, p: 2 }}>
              {selectedDate ? (
                <>
                  <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {formatMeetingDate(selectedDate)}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip label={`${reviewedCount} Reviewed`} color="success" size="small" />
                      <Chip label={`${deferredCount} Deferred`} color="warning" size="small" />
                      <Chip label={`${pendingCount} Pending`} size="small" />
                    </Stack>
                  </Stack>

                  {isMD ? (
                    <Button
                      variant="outlined"
                      size="small"
                      sx={{ mb: 2 }}
                      disabled={!currentMeetingId}
                      onClick={handleOpenBatchQueue}
                    >
                      View Batch Signature Queue
                    </Button>
                  ) : null}

                  {loadingPatients ? (
                    <Box sx={{ p: 2, textAlign: "center" }}>
                      <CircularProgress size={20} />
                    </Box>
                  ) : (
                    <List>
                      {patients.map((row) => (
                        <Paper
                          key={row.idg_meeting_id}
                          variant="outlined"
                          sx={{ p: 1.5, mb: 1, display: "flex", alignItems: "center", justifyContent: "space-between" }}
                        >
                          <Box>
                            <Typography sx={{ fontWeight: 700 }}>{row.patient_name || "Unnamed patient"}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              MRN {row.mrn || "—"}
                              {row.review_status === "DEFERRED" && row.defer_reason
                                ? ` · Deferred: ${row.defer_reason}`
                                : null}
                            </Typography>
                          </Box>
                          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                            <Chip
                              label={row.review_status}
                              color={statusColor(row.review_status)}
                              size="small"
                            />
                            {isMD ? (
                              <>
                                <Button
                                  size="small"
                                  variant="contained"
                                  disabled={savingReview || row.review_status === "REVIEWED"}
                                  onClick={() => handleMarkReviewed(row)}
                                >
                                  Reviewed
                                </Button>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  color="warning"
                                  disabled={savingReview || row.review_status === "DEFERRED"}
                                  onClick={() => openDeferDialog(row)}
                                >
                                  Defer
                                </Button>
                              </>
                            ) : null}
                          </Stack>
                        </Paper>
                      ))}
                    </List>
                  )}
                </>
              ) : (
                <Typography color="text.secondary">Select an IDG session to view its patient roster.</Typography>
              )}
            </Paper>
          </Stack>
        </Box>
      </Box>

      {/* Defer dialog */}
      <Dialog open={!!reviewTarget} onClose={() => setReviewTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Defer physician review — {reviewTarget?.patient_name}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Deferring creates an MD alert task to review and sign this patient later. Deferred
            patients are excluded from batch signing until reviewed.
          </Typography>
          <TextField
            select
            label="Defer reason"
            fullWidth
            value={deferReason}
            onChange={(e) => setDeferReason(e.target.value)}
            sx={{ mb: 2 }}
          >
            {DEFER_REASONS.map((r) => (
              <MenuItem key={r.value} value={r.value}>
                {r.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Additional note (optional)"
            fullWidth
            multiline
            minRows={2}
            value={deferNote}
            onChange={(e) => setDeferNote(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewTarget(null)}>Cancel</Button>
          <Button variant="contained" color="warning" disabled={savingReview} onClick={handleConfirmDefer}>
            Confirm Defer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Batch signature queue dialog */}
      <Dialog open={batchQueue !== null} onClose={() => setBatchQueue(null)} maxWidth="md" fullWidth>
        <DialogTitle>Batch Signature Queue</DialogTitle>
        <DialogContent>
          {loadingBatchQueue ? (
            <Box sx={{ p: 2, textAlign: "center" }}>
              <CircularProgress size={20} />
            </Box>
          ) : !batchQueue?.length ? (
            <Typography color="text.secondary">
              No eligible orders. Only Reviewed patients with unsigned, signable orders appear here.
            </Typography>
          ) : (
            <Stack spacing={2}>
              {batchQueue.map((entry) => (
                <Paper key={entry.patient_id} variant="outlined" sx={{ p: 1.5 }}>
                  <Typography sx={{ fontWeight: 700 }}>Patient {entry.patient_id}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Reviewed {new Date(entry.reviewed_at).toLocaleString()}
                  </Typography>
                  {entry.orders.map((o) => (
                    <Typography key={o.id} variant="body2">
                      • {o.order_text} ({o.order_category})
                    </Typography>
                  ))}
                </Paper>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchQueue(null)}>Close</Button>
          <Button
            variant="contained"
            disabled={signing || !batchQueue?.length}
            onClick={handleBatchSignAll}
          >
            Sign All Eligible Orders
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
