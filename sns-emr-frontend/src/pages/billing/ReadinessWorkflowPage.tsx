// sns-emr-frontend/src/pages/billing/ReadinessWorkflowPage.tsx
//
// Sprint 2 -- Billing Readiness Operational Workflow dashboard.
//
// Deliverable 1 (Dashboard): counts, patients requiring attention, recently
// changed status, recent evaluations, readiness trend.
// Deliverable 6 (Readiness History): read-only drill-down per patient,
// sourced directly from Sprint 1's BillingReadinessVerdict persistence plus
// the Sprint 2 blocker lifecycle / audit trail -- no writes happen here.
// Deliverable 7 (Operational Queue): filterable by readiness/operational
// bucket, assignment status, and due-soon/overdue.
//
// This is dev/test-data-scoped like every other page in this shell -- it
// reads whatever the selected agency's real evaluation data already is,
// with no assumption of production tenants.
import { useCallback, useEffect, useMemo, useState } from "react";
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
  Typography,
} from "@mui/material";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";

import {
  fetchReadinessDashboard,
  fetchReadinessHistory,
  fetchReadinessQueue,
  resolveReadinessBlocker,
  upsertReadinessAssignment,
  upsertReadinessFollowUp,
  type AssignmentStatus,
  type OperationalBucket,
  type ReadinessHistoryResponse,
  type ReadinessQueueRow,
  type TenantReadinessDashboardResponse,
} from "../../api/readinessWorkflow";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const BUCKET_COLOR: Record<OperationalBucket, string> = {
  READY: "#4ade80",
  AT_RISK: "#fbbf24",
  NOT_READY: "#f87171",
  BLOCKED: "#94a3b8",
};

const BUCKET_CHIP: Record<OperationalBucket, { bg: string; fg: string }> = {
  READY: { bg: "#14532d", fg: "#86efac" },
  AT_RISK: { bg: "#78350f", fg: "#fcd34d" },
  NOT_READY: { bg: "#7f1d1d", fg: "#fca5a5" },
  BLOCKED: { bg: "#334155", fg: "#cbd5e1" },
};

function BucketChip({ bucket }: { bucket: OperationalBucket }) {
  const c = BUCKET_CHIP[bucket];
  return (
    <Chip
      label={bucket.replace("_", " ")}
      size="small"
      sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: c.bg, color: c.fg }}
    />
  );
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function ReadinessWorkflowPage() {
  const { selectedAgencyId } = useAgency();

  const [dashboard, setDashboard] = useState<TenantReadinessDashboardResponse | null>(null);
  const [queue, setQueue] = useState<ReadinessQueueRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<OperationalBucket | "">("");
  const [assignmentFilter, setAssignmentFilter] = useState<AssignmentStatus | "">("");
  const [dueFilter, setDueFilter] = useState<"" | "SOON" | "OVERDUE">("");

  const [historyPatientId, setHistoryPatientId] = useState<string | null>(null);
  const [history, setHistory] = useState<ReadinessHistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [assignRow, setAssignRow] = useState<ReadinessQueueRow | null>(null);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRole, setAssignRole] = useState("");
  const [assignBusy, setAssignBusy] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  const [followUpRow, setFollowUpRow] = useState<ReadinessQueueRow | null>(null);
  const [followUpStatus, setFollowUpStatus] = useState<"OPEN" | "IN_PROGRESS" | "BLOCKED" | "RESOLVED">("OPEN");
  const [followUpDueDate, setFollowUpDueDate] = useState("");
  const [followUpNotes, setFollowUpNotes] = useState("");
  const [followUpBusy, setFollowUpBusy] = useState(false);
  const [followUpError, setFollowUpError] = useState<string | null>(null);

  const loadAll = useCallback(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    Promise.all([
      fetchReadinessDashboard(todayIso(), selectedAgencyId),
      fetchReadinessQueue(selectedAgencyId, {
        status: statusFilter || undefined,
        assignmentStatus: assignmentFilter || undefined,
        due: dueFilter || undefined,
      }),
    ])
      .then(([dashboardRes, queueRes]) => {
        setDashboard(dashboardRes);
        setQueue(queueRes.patients);
      })
      .catch((err) => {
        setError(err?.message || "Unable to load billing readiness workflow data.");
      })
      .finally(() => setLoading(false));
  }, [selectedAgencyId, statusFilter, assignmentFilter, dueFilter]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const metrics = useMemo(() => {
    const counts = dashboard?.counts;
    return [
      { label: "Ready", value: String(counts?.READY ?? 0), caption: "No blockers or warnings", color: BUCKET_COLOR.READY },
      { label: "At Risk", value: String(counts?.AT_RISK ?? 0), caption: "Warnings present, no blockers", color: BUCKET_COLOR.AT_RISK },
      { label: "Not Ready", value: String(counts?.NOT_READY ?? 0), caption: "One or more open blockers", color: BUCKET_COLOR.NOT_READY },
      { label: "Blocked", value: String(counts?.BLOCKED ?? 0), caption: "Not Ready + staff-marked Blocked follow-up", color: BUCKET_COLOR.BLOCKED },
    ];
  }, [dashboard]);

  function openHistory(patientId: string) {
    setHistoryPatientId(patientId);
    setHistory(null);
    setHistoryError(null);
    setHistoryLoading(true);
    fetchReadinessHistory(patientId, selectedAgencyId)
      .then(setHistory)
      .catch((err) => setHistoryError(err?.message || "Unable to load readiness history."))
      .finally(() => setHistoryLoading(false));
  }

  function openAssign(row: ReadinessQueueRow) {
    setAssignRow(row);
    setAssignUserId(row.assigned_user_id || "");
    setAssignRole(row.assigned_role || "");
    setAssignError(null);
  }

  async function submitAssign() {
    if (!assignRow) return;
    setAssignBusy(true);
    setAssignError(null);
    try {
      await upsertReadinessAssignment(
        {
          patient_id: assignRow.patient_id,
          assigned_user_id: assignUserId || null,
          assigned_role: assignRole || null,
          assignment_status: "ASSIGNED",
        },
        selectedAgencyId
      );
      setAssignRow(null);
      loadAll();
    } catch (err) {
      setAssignError((err as { message?: string })?.message || "Unable to save assignment.");
    } finally {
      setAssignBusy(false);
    }
  }

  function openFollowUp(row: ReadinessQueueRow) {
    setFollowUpRow(row);
    setFollowUpStatus("OPEN");
    setFollowUpDueDate("");
    setFollowUpNotes("");
    setFollowUpError(null);
  }

  async function submitFollowUp() {
    if (!followUpRow) return;
    setFollowUpBusy(true);
    setFollowUpError(null);
    try {
      await upsertReadinessFollowUp(
        {
          patient_id: followUpRow.patient_id,
          status: followUpStatus,
          due_date: followUpDueDate || null,
          notes: followUpNotes || null,
        },
        selectedAgencyId
      );
      setFollowUpRow(null);
      loadAll();
    } catch (err) {
      setFollowUpError((err as { message?: string })?.message || "Unable to save follow-up.");
    } finally {
      setFollowUpBusy(false);
    }
  }

  async function handleResolveBlocker(blockerId: string, reason: string | undefined) {
    if (!historyPatientId) return;
    await resolveReadinessBlocker(blockerId, reason, selectedAgencyId);
    openHistory(historyPatientId);
    loadAll();
  }

  return (
    <Box>
      <PageHeader
        title="Billing Readiness"
        subtitle="Operational triage workflow layered on top of every persisted readiness evaluation -- test/dev data only"
        actions={<></>}
      />
      <HipaaBanner message='This view shows administrative readiness status, typed blocker categories, and workflow assignment metadata only. Clinical chart content, assessment answers, and narrative notes are never displayed here.' />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its billing readiness workflow.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 2.5, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                PATIENTS REQUIRING ATTENTION
              </Typography>
              {(dashboard?.patients_requiring_attention ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No patients currently require attention.</Typography>
              ) : (
                (dashboard?.patients_requiring_attention ?? []).map((p) => (
                  <Box key={p.patient_id} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", py: 0.6, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>{p.mrn || p.patient_id}</Typography>
                    <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>
                      {p.blocker_count} blocker{p.blocker_count === 1 ? "" : "s"} / {p.warning_count} warning{p.warning_count === 1 ? "" : "s"}
                    </Typography>
                    <BucketChip bucket={p.operational_bucket} />
                  </Box>
                ))
              )}
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                RECENT READINESS EVALUATIONS
              </Typography>
              {(dashboard?.recent_evaluations ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No evaluations recorded yet.</Typography>
              ) : (
                (dashboard?.recent_evaluations ?? []).map((e) => (
                  <Box key={`${e.patient_id}-${e.evaluated_at}`} sx={{ display: "flex", justifyContent: "space-between", py: 0.6, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>{e.mrn || e.patient_id}</Typography>
                    <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>{e.evaluated_at} ({e.triggered_by})</Typography>
                    <Typography sx={{ fontSize: 12, fontWeight: 700, color: "#e2e8f0" }}>{e.readiness_status}</Typography>
                  </Box>
                ))
              )}
            </Paper>
          </Box>

          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 2.5, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                RECENTLY CHANGED READINESS STATUS
              </Typography>
              {(dashboard?.recently_changed_status ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No status changes detected.</Typography>
              ) : (
                (dashboard?.recently_changed_status ?? []).map((c) => (
                  <Box key={`${c.patient_id}-${c.changed_at}`} sx={{ display: "flex", justifyContent: "space-between", py: 0.6, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>{c.mrn || c.patient_id}</Typography>
                    <Typography sx={{ fontSize: 12, color: "#7f97b3" }}>
                      {c.previous_status} → <Box component="span" sx={{ color: "#e2e8f0", fontWeight: 700 }}>{c.new_status}</Box>
                    </Typography>
                  </Box>
                ))
              )}
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                READINESS TREND (LAST 14 DAYS)
              </Typography>
              {(dashboard?.readiness_trend ?? []).length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No evaluations in this window.</Typography>
              ) : (
                <TableContainer sx={{ maxHeight: 220 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {["Date", "Ready", "At Risk", "Not Ready"].map((h) => (
                          <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, borderColor: "#1f3a5c" }}>
                            {h}
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(dashboard?.readiness_trend ?? []).map((t) => (
                        <TableRow key={t.service_date}>
                          <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>{t.service_date}</TableCell>
                          <TableCell sx={{ color: "#4ade80", fontSize: 12.5, borderColor: "#1f3a5c" }}>{t.ready_count}</TableCell>
                          <TableCell sx={{ color: "#fbbf24", fontSize: 12.5, borderColor: "#1f3a5c" }}>{t.at_risk_count}</TableCell>
                          <TableCell sx={{ color: "#f87171", fontSize: 12.5, borderColor: "#1f3a5c" }}>{t.not_ready_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>
          </Box>

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 2, pt: 1.5, pb: 1, flexWrap: "wrap", gap: 1.5 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3" }}>
                OPERATIONAL QUEUE
              </Typography>
              <Box sx={{ display: "flex", gap: 1 }}>
                <TextField
                  select
                  size="small"
                  label="Status"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as OperationalBucket | "")}
                  sx={{ minWidth: 140 }}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="READY">Ready</MenuItem>
                  <MenuItem value="AT_RISK">At Risk</MenuItem>
                  <MenuItem value="NOT_READY">Not Ready</MenuItem>
                  <MenuItem value="BLOCKED">Blocked</MenuItem>
                </TextField>
                <TextField
                  select
                  size="small"
                  label="Assignment"
                  value={assignmentFilter}
                  onChange={(e) => setAssignmentFilter(e.target.value as AssignmentStatus | "")}
                  sx={{ minWidth: 140 }}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="UNASSIGNED">Unassigned</MenuItem>
                  <MenuItem value="ASSIGNED">Assigned</MenuItem>
                  <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
                  <MenuItem value="COMPLETED">Completed</MenuItem>
                </TextField>
                <TextField
                  select
                  size="small"
                  label="Due"
                  value={dueFilter}
                  onChange={(e) => setDueFilter(e.target.value as "" | "SOON" | "OVERDUE")}
                  sx={{ minWidth: 140 }}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="SOON">Due Soon</MenuItem>
                  <MenuItem value="OVERDUE">Overdue</MenuItem>
                </TextField>
              </Box>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Patient", "Status", "Blockers", "Assignment", "Due", "Actions"].map((h) => (
                      <TableCell key={h} sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}>
                        {h.toUpperCase()}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {queue.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No patients match the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    queue.map((row) => (
                      <TableRow key={row.patient_id} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{row.mrn || row.patient_id}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <BucketChip bucket={row.operational_bucket} />
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>
                          {row.blockers.length > 0 ? `${row.blockers.length} open` : "—"}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>
                          {row.assignment_status}
                          {row.assigned_role ? ` (${row.assigned_role})` : ""}
                        </TableCell>
                        <TableCell sx={{ color: row.earliest_due_date && row.earliest_due_date < todayIso() ? "#f87171" : "#e2e8f0", fontSize: 12.5, borderColor: "#1f3a5c" }}>
                          {row.earliest_due_date || "—"}
                        </TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Box sx={{ display: "flex", gap: 0.5 }}>
                            <Button size="small" onClick={() => openAssign(row)} sx={{ textTransform: "none", fontSize: 11.5 }}>
                              Assign
                            </Button>
                            <Button size="small" onClick={() => openFollowUp(row)} sx={{ textTransform: "none", fontSize: 11.5 }}>
                              Follow-up
                            </Button>
                            <Button
                              size="small"
                              startIcon={<HistoryOutlinedIcon fontSize="small" />}
                              onClick={() => openHistory(row.patient_id)}
                              sx={{ textTransform: "none", fontSize: 11.5 }}
                            >
                              History
                            </Button>
                          </Box>
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

      {/* ASSIGNMENT DIALOG */}
      <Dialog open={assignRow !== null} onClose={() => setAssignRow(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: 15, fontWeight: 700 }}>Assign Patient</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {assignError ? <Alert severity="error">{assignError}</Alert> : null}
          <TextField
            label="Assigned User ID"
            size="small"
            value={assignUserId}
            onChange={(e) => setAssignUserId(e.target.value)}
            helperText="Development/test data only -- a real user id in this tenant."
          />
          <TextField
            label="Assigned Role"
            size="small"
            value={assignRole}
            onChange={(e) => setAssignRole(e.target.value)}
            helperText="Generic free-text role label (e.g. BILLING_SPECIALIST) -- not a fixed enum."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignRow(null)} disabled={assignBusy} sx={{ textTransform: "none" }}>
            Cancel
          </Button>
          <Button onClick={submitAssign} disabled={assignBusy} variant="contained" sx={{ textTransform: "none" }}>
            {assignBusy ? "Saving…" : "Save Assignment"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* FOLLOW-UP DIALOG */}
      <Dialog open={followUpRow !== null} onClose={() => setFollowUpRow(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: 15, fontWeight: 700 }}>Create / Update Follow-Up</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {followUpError ? <Alert severity="error">{followUpError}</Alert> : null}
          <TextField
            select
            label="Status"
            size="small"
            value={followUpStatus}
            onChange={(e) => setFollowUpStatus(e.target.value as typeof followUpStatus)}
          >
            <MenuItem value="OPEN">Open</MenuItem>
            <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
            <MenuItem value="BLOCKED">Blocked</MenuItem>
            <MenuItem value="RESOLVED">Resolved</MenuItem>
          </TextField>
          <TextField
            label="Due Date"
            type="date"
            size="small"
            value={followUpDueDate}
            onChange={(e) => setFollowUpDueDate(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            label="Notes"
            size="small"
            multiline
            minRows={2}
            value={followUpNotes}
            onChange={(e) => setFollowUpNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFollowUpRow(null)} disabled={followUpBusy} sx={{ textTransform: "none" }}>
            Cancel
          </Button>
          <Button onClick={submitFollowUp} disabled={followUpBusy} variant="contained" sx={{ textTransform: "none" }}>
            {followUpBusy ? "Saving…" : "Save Follow-Up"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* READONLY HISTORY DIALOG */}
      <Dialog open={historyPatientId !== null} onClose={() => setHistoryPatientId(null)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontSize: 15, fontWeight: 700 }}>
          Readiness History{historyPatientId ? ` -- ${historyPatientId}` : ""}
        </DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {historyError ? <Alert severity="error">{historyError}</Alert> : null}
          {historyLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : history ? (
            <>
              <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#334155" }}>Evaluations</Typography>
              <Box sx={{ display: "grid", gap: 0.8 }}>
                {history.verdicts.length === 0 ? (
                  <Typography sx={{ fontSize: 12.5, color: "#64748b" }}>No evaluations recorded yet.</Typography>
                ) : (
                  history.verdicts.map((v) => (
                    <Box key={v.id} sx={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", py: 0.6 }}>
                      <Typography sx={{ fontSize: 12.5 }}>{v.evaluated_at}</Typography>
                      <Typography sx={{ fontSize: 12.5, fontWeight: 700 }}>{v.readiness_status}</Typography>
                      <Typography sx={{ fontSize: 12, color: "#64748b" }}>{v.triggered_by}</Typography>
                    </Box>
                  ))
                )}
              </Box>

              <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#334155", mt: 1 }}>Blocker History</Typography>
              <Box sx={{ display: "grid", gap: 0.8 }}>
                {history.blocker_history.length === 0 ? (
                  <Typography sx={{ fontSize: 12.5, color: "#64748b" }}>No blockers recorded.</Typography>
                ) : (
                  history.blocker_history.map((b) => (
                    <Box key={b.id} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e2e8f0", py: 0.6, gap: 1 }}>
                      <Box sx={{ minWidth: 0 }}>
                        <Typography sx={{ fontSize: 12.5, fontWeight: 700 }}>{b.blocker_code}</Typography>
                        <Typography sx={{ fontSize: 11.5, color: "#64748b" }}>{b.message}</Typography>
                      </Box>
                      <Chip label={b.status} size="small" color={b.status === "OPEN" ? "warning" : "success"} />
                      {b.status === "OPEN" ? (
                        <Button size="small" onClick={() => handleResolveBlocker(b.id, "Resolved manually from dashboard.")} sx={{ textTransform: "none" }}>
                          Resolve
                        </Button>
                      ) : null}
                    </Box>
                  ))
                )}
              </Box>

              <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#334155", mt: 1 }}>Audit Trail</Typography>
              <Box sx={{ display: "grid", gap: 0.8 }}>
                {history.audit_trail.length === 0 ? (
                  <Typography sx={{ fontSize: 12.5, color: "#64748b" }}>No workflow events recorded.</Typography>
                ) : (
                  history.audit_trail.map((e) => (
                    <Box key={e.id} sx={{ borderBottom: "1px solid #e2e8f0", py: 0.6 }}>
                      <Typography sx={{ fontSize: 12.5 }}>
                        {e.occurred_at} -- {e.entity_type} {e.event_type}
                        {e.reason ? ` (${e.reason})` : ""}
                      </Typography>
                    </Box>
                  ))
                )}
              </Box>
            </>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryPatientId(null)} sx={{ textTransform: "none" }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
