import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import {
  acceptDisciplineService,
  acceptIdgRecommendation,
  activateDisciplineService,
  assignRnMonitoring,
  completeIdgReview,
  createIdgRecommendation,
  declineIdgRecommendation,
  endDisciplineService,
  endRnMonitoring,
  getDisciplineService,
  identifyDisciplineService,
  listDisciplineServiceEvents,
  listIdgRecommendations,
  listPatientIdgReviews,
  offerDisciplineService,
  pauseDisciplineService,
  pendingDecision,
  recordDecisionMakerUnavailable,
  recordUnableToContact,
  refuseDisciplineService,
  reofferDisciplineService,
  resumeDisciplineService,
  scheduleReoffer,
  withdrawRefusal,
} from "../api/disciplineServices";
import type {
  ContinuityDiscipline,
  DisciplineServiceEventRecord,
  DisciplineServiceRecord,
  IdgRecommendationRecord,
  PatientIdgReviewSummary,
} from "../api/disciplineServices";
import { useThemeMode } from "../theme/theme";

type InterdisciplinaryContinuityBoardProps = {
  patientId: string;
};

const DISCIPLINES: { key: ContinuityDiscipline; label: string }[] = [
  { key: "MSW", label: "Medical Social Work" },
  { key: "CHAPLAIN", label: "Chaplain" },
  { key: "VOLUNTEER", label: "Volunteer" },
];

const getColors = (mode: string) => (mode === "light" ? {
  bg: "#f3f8f7",
  panel: "#ffffff",
  muted: "#5f7286",
  text: "#18354c",
  accent: "#0d7d7a",
  border: "#d9e6eb",
  surface: "#f8fbfb",
  success: "#2d7b63",
  warning: "#d38a2b",
  danger: "#d64d57",
} : {
  bg: "#0f172a",
  panel: "#111827",
  muted: "#94a3b8",
  text: "#e2e8f0",
  accent: "#10b7a2",
  border: "#334155",
  surface: "#162132",
  success: "#34d399",
  warning: "#f59e0b",
  danger: "#fb7185",
});

const formatDateTime = (value: string | null | undefined) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleString([], { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

const stateTone = (state: DisciplineServiceRecord["current_state"] | undefined) => {
  if (!state) return "teal" as const;
  if (state === "REFUSED_MONITORING_CONTINUES" || state === "DECISION_MAKER_UNAVAILABLE" || state === "UNABLE_TO_CONTACT") return "danger" as const;
  if (state === "ACTIVE" || state === "ACCEPTED_AWAITING_ACTIVATION") return "green" as const;
  if (state === "PAUSED" || state === "REOFFER_DUE" || state === "REOFFERED_AWAITING_DECISION" || state === "OFFERED_AWAITING_DECISION" || state === "OFFER_DUE") return "amber" as const;
  return "teal" as const;
};

// Action descriptors. The backend's DisciplineServiceEngine is the single
// source of truth for which transitions are actually valid from the
// current_state -- this board does not duplicate that table. Every action
// is always offered; an invalid attempt surfaces the engine's own 409
// error message so the clinician learns the correct next step from the
// same place the rule lives.
type ActionField = {
  name: string;
  label: string;
  type: "text" | "textarea" | "date" | "checkbox";
  required?: boolean;
};

type ActionDescriptor = {
  key: string;
  label: string;
  fields: ActionField[];
  run: (
    patientId: string,
    discipline: ContinuityDiscipline,
    values: Record<string, string | boolean>,
    rowVersion: number | undefined,
  ) => Promise<DisciplineServiceRecord>;
};

const ACTIONS: ActionDescriptor[] = [
  {
    key: "offer",
    label: "Offer service",
    fields: [
      { name: "information_source", label: "Information source", type: "text" },
      { name: "reason", label: "Reason / context", type: "textarea" },
    ],
    run: (p, d, v, rv) => offerDisciplineService(p, d, { information_source: v.information_source as string || undefined, reason: v.reason as string || undefined, expected_row_version: rv }),
  },
  {
    key: "pending-decision",
    label: "Mark pending decision",
    fields: [],
    run: (p, d, _v, rv) => pendingDecision(p, d, { expected_row_version: rv }),
  },
  {
    key: "accept",
    label: "Record acceptance",
    fields: [
      { name: "decision_maker_name", label: "Decision maker name", type: "text", required: true },
      { name: "decision_maker_relationship", label: "Decision maker relationship", type: "text", required: true },
      { name: "information_source", label: "Information source", type: "text" },
    ],
    run: (p, d, v, rv) => acceptDisciplineService(p, d, {
      decision_maker_name: v.decision_maker_name as string,
      decision_maker_relationship: v.decision_maker_relationship as string,
      information_source: v.information_source as string || undefined,
      expected_row_version: rv,
    }),
  },
  {
    key: "refuse",
    label: "Record refusal",
    fields: [
      { name: "reason", label: "Reason", type: "textarea", required: true },
      { name: "decision_maker_name", label: "Decision maker name", type: "text", required: true },
      { name: "decision_maker_relationship", label: "Decision maker relationship", type: "text", required: true },
      { name: "information_source", label: "Information source", type: "text" },
      { name: "requires_idg_review", label: "Requires IDG review", type: "checkbox" },
      { name: "create_reoffer_task", label: "Create re-offer task", type: "checkbox" },
      { name: "reoffer_due_date", label: "Re-offer due date", type: "date" },
    ],
    run: (p, d, v, rv) => refuseDisciplineService(p, d, {
      reason: v.reason as string,
      decision_maker_name: v.decision_maker_name as string,
      decision_maker_relationship: v.decision_maker_relationship as string,
      information_source: v.information_source as string || undefined,
      requires_idg_review: Boolean(v.requires_idg_review),
      create_reoffer_task: v.create_reoffer_task === undefined ? true : Boolean(v.create_reoffer_task),
      reoffer_due_date: v.reoffer_due_date as string || undefined,
      expected_row_version: rv,
    }),
  },
  {
    key: "activate",
    label: "Activate",
    fields: [],
    run: (p, d, _v, rv) => activateDisciplineService(p, d, { expected_row_version: rv }),
  },
  {
    key: "pause",
    label: "Pause",
    fields: [{ name: "reason", label: "Reason", type: "textarea" }],
    run: (p, d, v, rv) => pauseDisciplineService(p, d, { reason: v.reason as string || undefined, expected_row_version: rv }),
  },
  {
    key: "resume",
    label: "Resume",
    fields: [],
    run: (p, d, _v, rv) => resumeDisciplineService(p, d, { expected_row_version: rv }),
  },
  {
    key: "end",
    label: "End service",
    fields: [{ name: "reason", label: "Reason", type: "textarea", required: true }],
    run: (p, d, v, rv) => endDisciplineService(p, d, { reason: v.reason as string, expected_row_version: rv }),
  },
  {
    key: "withdraw-refusal",
    label: "Withdraw refusal",
    fields: [
      { name: "reason", label: "Reason", type: "textarea", required: true },
      { name: "decision_maker_name", label: "Decision maker name", type: "text", required: true },
      { name: "decision_maker_relationship", label: "Decision maker relationship", type: "text", required: true },
    ],
    run: (p, d, v, rv) => withdrawRefusal(p, d, {
      reason: v.reason as string,
      decision_maker_name: v.decision_maker_name as string,
      decision_maker_relationship: v.decision_maker_relationship as string,
      expected_row_version: rv,
    }),
  },
  {
    key: "schedule-reoffer",
    label: "Schedule re-offer",
    fields: [
      { name: "due_date", label: "Due date", type: "date" },
      { name: "trigger_description", label: "Trigger description", type: "textarea" },
    ],
    run: (p, d, v, rv) => scheduleReoffer(p, d, { due_date: v.due_date as string || undefined, trigger_description: v.trigger_description as string || undefined, expected_row_version: rv }),
  },
  {
    key: "reoffer",
    label: "Re-offer now",
    fields: [{ name: "information_source", label: "Information source", type: "text" }],
    run: (p, d, v, rv) => reofferDisciplineService(p, d, { information_source: v.information_source as string || undefined, expected_row_version: rv }),
  },
  {
    key: "unable-to-contact",
    label: "Unable to contact",
    fields: [{ name: "reason", label: "Reason", type: "textarea" }],
    run: (p, d, v, rv) => recordUnableToContact(p, d, { reason: v.reason as string || undefined, expected_row_version: rv }),
  },
  {
    key: "decision-maker-unavailable",
    label: "Decision maker unavailable",
    fields: [{ name: "reason", label: "Reason", type: "textarea" }],
    run: (p, d, v, rv) => recordDecisionMakerUnavailable(p, d, { reason: v.reason as string || undefined, expected_row_version: rv }),
  },
];

export default function InterdisciplinaryContinuityBoard({ patientId }: InterdisciplinaryContinuityBoardProps) {
  const { mode } = useThemeMode();
  const colors = getColors(mode);

  const [discipline, setDiscipline] = useState<ContinuityDiscipline>("MSW");
  const [service, setService] = useState<DisciplineServiceRecord | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [events, setEvents] = useState<DisciplineServiceEventRecord[]>([]);
  const [recommendations, setRecommendations] = useState<IdgRecommendationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [openAction, setOpenAction] = useState<string | null>(null);
  const [actionValues, setActionValues] = useState<Record<string, string | boolean>>({});
  const [rnUserId, setRnUserId] = useState("");
  const [rnEndReason, setRnEndReason] = useState("");
  const [idgReviewOptions, setIdgReviewOptions] = useState<PatientIdgReviewSummary[]>([]);
  const [completeReviewId, setCompleteReviewId] = useState("");
  const [completeReviewNotes, setCompleteReviewNotes] = useState("");
  const [showRecommendationForm, setShowRecommendationForm] = useState(false);
  const [recommendationForm, setRecommendationForm] = useState({
    idg_review_id: "",
    recommendation_type: "FOLLOW_UP",
    recommendation_text: "",
  });

  const boardCard = {
    backgroundColor: colors.panel,
    border: `1px solid ${colors.border}`,
    borderRadius: 8,
    boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
    padding: 14,
  };

  const boardHeader = {
    color: colors.text,
    fontSize: 15,
    fontWeight: 700,
    marginBottom: 8,
    letterSpacing: 0.2,
  };

  const badge = (tone: "teal" | "amber" | "green" | "danger") => ({
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "5px 10px",
    fontSize: 10.5,
    fontWeight: 700,
    letterSpacing: 0.3,
    textTransform: "uppercase" as const,
    backgroundColor:
      tone === "teal" ? (mode === "light" ? "#dff8f4" : "#10b7a215")
      : tone === "amber" ? (mode === "light" ? "#f9edd7" : "#f59e0b15")
      : tone === "danger" ? (mode === "light" ? "#fbe3e4" : "#fb718515")
      : (mode === "light" ? "#dff5ee" : "#05966915"),
    color:
      tone === "teal" ? colors.accent
      : tone === "amber" ? colors.warning
      : tone === "danger" ? colors.danger
      : colors.success,
  });

  const loadAll = async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    setNotFound(false);
    try {
      const svc = await getDisciplineService(patientId, discipline);
      setService(svc);
      const evts = await listDisciplineServiceEvents(patientId, discipline);
      setEvents(evts);
    } catch (loadError: any) {
      if (loadError?.response?.status === 404) {
        setService(null);
        setEvents([]);
        setNotFound(true);
      } else {
        setError(loadError instanceof Error ? loadError.message : "Unable to load this discipline's continuity record.");
      }
    } finally {
      setLoading(false);
    }
    try {
      const recs = await listIdgRecommendations(patientId);
      setRecommendations(recs);
    } catch {
      setRecommendations([]);
    }
  };

  useEffect(() => {
    void loadAll();
    setOpenAction(null);
    setActionValues({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId, discipline]);

  useEffect(() => {
    if (!patientId) return;
    listPatientIdgReviews(patientId)
      .then(setIdgReviewOptions)
      .catch(() => setIdgReviewOptions([]));
  }, [patientId]);

  const discplineRecommendations = useMemo(
    () => recommendations.filter((r) => !r.discipline || r.discipline === discipline),
    [recommendations, discipline],
  );

  const handleIdentify = async () => {
    if (!patientId) return;
    setBusy(true);
    setError("");
    try {
      await identifyDisciplineService(patientId, discipline);
      await loadAll();
    } catch (identifyError: any) {
      setError(identifyError?.response?.data?.detail || identifyError?.message || "Unable to start tracking this discipline.");
    } finally {
      setBusy(false);
    }
  };

  const runAction = async (action: ActionDescriptor, event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId) return;
    for (const field of action.fields) {
      if (field.required && !actionValues[field.name]) {
        setError(`${field.label} is required.`);
        return;
      }
    }
    setBusy(true);
    setError("");
    try {
      await action.run(patientId, discipline, actionValues, service?.row_version);
      setOpenAction(null);
      setActionValues({});
      await loadAll();
    } catch (actionError: any) {
      setError(actionError?.response?.data?.detail || actionError?.message || `Unable to complete "${action.label}".`);
    } finally {
      setBusy(false);
    }
  };

  const handleAssignRn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId || !rnUserId.trim()) return;
    setBusy(true);
    setError("");
    try {
      await assignRnMonitoring(patientId, discipline, { rn_user_id: rnUserId.trim(), expected_row_version: service?.row_version });
      setRnUserId("");
      await loadAll();
    } catch (assignError: any) {
      setError(assignError?.response?.data?.detail || assignError?.message || "Unable to assign RN monitoring.");
    } finally {
      setBusy(false);
    }
  };

  const handleEndRnMonitoring = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId || !rnEndReason.trim()) return;
    setBusy(true);
    setError("");
    try {
      await endRnMonitoring(patientId, discipline, { reason: rnEndReason.trim(), expected_row_version: service?.row_version });
      setRnEndReason("");
      await loadAll();
    } catch (endError: any) {
      setError(endError?.response?.data?.detail || endError?.message || "Unable to end RN monitoring.");
    } finally {
      setBusy(false);
    }
  };

  const handleCompleteIdgReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId || !completeReviewId) return;
    setBusy(true);
    setError("");
    try {
      await completeIdgReview(patientId, discipline, {
        idg_review_id: completeReviewId,
        notes: completeReviewNotes.trim() || undefined,
        expected_row_version: service?.row_version,
      });
      setCompleteReviewId("");
      setCompleteReviewNotes("");
      await loadAll();
    } catch (completeError: any) {
      setError(completeError?.response?.data?.detail || completeError?.message || "Unable to mark this IDG review complete.");
    } finally {
      setBusy(false);
    }
  };


  const handleCreateRecommendation = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId || !recommendationForm.idg_review_id.trim() || !recommendationForm.recommendation_text.trim()) return;
    setBusy(true);
    setError("");
    try {
      await createIdgRecommendation({
        patient_id: patientId,
        idg_review_id: recommendationForm.idg_review_id.trim(),
        discipline,
        recommendation_type: recommendationForm.recommendation_type,
        recommendation_text: recommendationForm.recommendation_text.trim(),
        discipline_service_id: service?.id,
      });
      setRecommendationForm({ idg_review_id: "", recommendation_type: "FOLLOW_UP", recommendation_text: "" });
      setShowRecommendationForm(false);
      await loadAll();
    } catch (createError: any) {
      setError(createError?.response?.data?.detail || createError?.message || "Unable to create this IDG recommendation.");
    } finally {
      setBusy(false);
    }
  };

  const handleReviewRecommendation = async (recommendationId: string, decision: "accept" | "decline") => {
    setBusy(true);
    setError("");
    try {
      if (decision === "accept") await acceptIdgRecommendation(recommendationId);
      else await declineIdgRecommendation(recommendationId);
      await loadAll();
    } catch (reviewError: any) {
      setError(reviewError?.response?.data?.detail || reviewError?.message || "Unable to record this review decision.");
    } finally {
      setBusy(false);
    }
  };

  const inputStyle = { borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.surface, color: colors.text, padding: "9px 11px", fontSize: 13, width: "100%" };
  const labelStyle = { color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: 0.7 };

  if (!patientId) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: colors.bg, color: colors.text, fontFamily: "'Inter', sans-serif" }}>
        Select a patient to view interdisciplinary continuity.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: "auto", fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
        {DISCIPLINES.map((d) => (
          <button
            key={d.key}
            type="button"
            onClick={() => setDiscipline(d.key)}
            style={{
              borderRadius: 999,
              border: `1px solid ${discipline === d.key ? colors.accent : colors.border}`,
              backgroundColor: discipline === d.key ? colors.accent : colors.panel,
              color: discipline === d.key ? "#ffffff" : colors.text,
              padding: "8px 14px",
              fontSize: 12.5,
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {d.label}
          </button>
        ))}
      </div>

      {error ? <div style={{ ...boardCard, color: colors.danger, fontSize: 12.5, marginBottom: 10 }}>{error}</div> : null}

      {loading ? (
        <div style={{ color: colors.muted, fontSize: 13 }}>Loading continuity record…</div>
      ) : notFound ? (
        <div style={boardCard}>
          <div style={boardHeader}>Not yet tracked</div>
          <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 12 }}>
            No continuity record exists yet for {discipline} on this admission. Start tracking to record the first offer.
          </div>
          <button
            type="button"
            onClick={() => void handleIdentify()}
            disabled={busy}
            style={{ border: "none", borderRadius: 999, padding: "10px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12.5, cursor: busy ? "wait" : "pointer" }}
          >
            {busy ? "Starting…" : `Start tracking ${discipline}`}
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {/* Direct Service Status */}
          <div style={boardCard}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10, marginBottom: 10 }}>
              <div>
                <div style={boardHeader}>Direct service status</div>
                <div style={{ color: colors.muted, fontSize: 12.5 }}>Current state for {discipline} continuity on this admission.</div>
              </div>
              <span style={badge(stateTone(service?.current_state))}>{service?.current_state?.replace(/_/g, " ")}</span>
              {service ? (
                <span style={badge(service.admission_status === "CURRENT" ? "green" : service.admission_status === "HISTORICAL" ? "amber" : "teal")}>
                  {service.admission_status === "CURRENT" ? "CURRENT ADMISSION" : service.admission_status === "HISTORICAL" ? "HISTORICAL ADMISSION" : "LEGACY (NO ADMISSION RECORD)"}
                </span>
              ) : null}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginBottom: 12 }}>
              <div><div style={labelStyle}>Last offered</div><div style={{ color: colors.text, fontSize: 13 }}>{formatDateTime(service?.last_offered_at)}</div></div>
              <div><div style={labelStyle}>Last decision</div><div style={{ color: colors.text, fontSize: 13 }}>{formatDateTime(service?.last_decision_at)}</div></div>
              <div><div style={labelStyle}>Last refused</div><div style={{ color: colors.text, fontSize: 13 }}>{formatDateTime(service?.last_refused_at)}</div></div>
              <div><div style={labelStyle}>Re-offer due</div><div style={{ color: colors.text, fontSize: 13 }}>{formatDateTime(service?.reoffer_due_at)}</div></div>
            </div>

            {/* Clinical Needs (decision-maker / information source context) */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginBottom: 12, paddingTop: 10, borderTop: `1px solid ${colors.border}` }}>
              <div><div style={labelStyle}>Decision maker</div><div style={{ color: colors.text, fontSize: 13 }}>{service?.last_decision_maker_name || "—"}{service?.last_decision_maker_relationship ? ` (${service.last_decision_maker_relationship})` : ""}</div></div>
              <div><div style={labelStyle}>Information source</div><div style={{ color: colors.text, fontSize: 13 }}>{service?.last_information_source || "—"}</div></div>
              <div><div style={labelStyle}>IDG review required</div><div style={{ color: colors.text, fontSize: 13 }}>{service?.idg_review_required ? "Yes" : "No"}</div></div>
              <div><div style={labelStyle}>Row version</div><div style={{ color: colors.text, fontSize: 13 }}>{service?.row_version}</div></div>
            </div>

            {service?.idg_review_required ? (
              <form onSubmit={(e) => void handleCompleteIdgReview(e)} style={{ display: "grid", gap: 8, paddingTop: 10, borderTop: `1px solid ${colors.border}` }}>
                <span style={labelStyle}>Mark IDG review complete</span>
                <select value={completeReviewId} onChange={(e) => setCompleteReviewId(e.target.value)} style={inputStyle}>
                  <option value="">Select the IDG review that was completed…</option>
                  {idgReviewOptions.filter((r) => r.admission_status === "CURRENT").map((r) => (
                    <option key={r.id} value={r.id}>
                      {formatDateTime(r.review_date)}{r.is_finalized ? " (finalized)" : ""}{r.summary ? ` — ${r.summary.slice(0, 60)}` : ""}
                    </option>
                  ))}
                </select>
                <input type="text" value={completeReviewNotes} onChange={(e) => setCompleteReviewNotes(e.target.value)} style={inputStyle} placeholder="Notes (optional)" />
                <button type="submit" disabled={busy || !completeReviewId} style={{ border: "none", borderRadius: 999, padding: "9px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12, cursor: "pointer", width: "fit-content", opacity: busy || !completeReviewId ? 0.6 : 1 }}>
                  Mark review complete
                </button>
              </form>
            ) : null}

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {ACTIONS.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  onClick={() => { setOpenAction(openAction === action.key ? null : action.key); setActionValues({}); setError(""); }}
                  style={{
                    borderRadius: 999,
                    border: `1px solid ${openAction === action.key ? colors.accent : colors.border}`,
                    backgroundColor: openAction === action.key ? colors.surface : colors.panel,
                    color: openAction === action.key ? colors.accent : colors.text,
                    padding: "8px 12px",
                    fontSize: 11.5,
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>

            {openAction ? (() => {
              const action = ACTIONS.find((a) => a.key === openAction);
              if (!action) return null;
              return (
                <form onSubmit={(e) => void runAction(action, e)} style={{ display: "grid", gap: 10, marginTop: 12, paddingTop: 12, borderTop: `1px solid ${colors.border}` }}>
                  {action.fields.length === 0 ? (
                    <div style={{ color: colors.muted, fontSize: 12.5 }}>No additional information required. Confirm to proceed.</div>
                  ) : action.fields.map((field) => (
                    <label key={field.name} style={{ display: "grid", gap: 5 }}>
                      <span style={labelStyle}>{field.label}{field.required ? " *" : ""}</span>
                      {field.type === "checkbox" ? (
                        <input
                          type="checkbox"
                          checked={Boolean(actionValues[field.name])}
                          onChange={(e) => setActionValues((cur) => ({ ...cur, [field.name]: e.target.checked }))}
                        />
                      ) : field.type === "textarea" ? (
                        <textarea
                          value={(actionValues[field.name] as string) || ""}
                          onChange={(e) => setActionValues((cur) => ({ ...cur, [field.name]: e.target.value }))}
                          rows={3}
                          style={{ ...inputStyle, resize: "vertical" as const }}
                        />
                      ) : (
                        <input
                          type={field.type}
                          value={(actionValues[field.name] as string) || ""}
                          onChange={(e) => setActionValues((cur) => ({ ...cur, [field.name]: e.target.value }))}
                          style={inputStyle}
                        />
                      )}
                    </label>
                  ))}
                  <div style={{ display: "flex", gap: 8 }}>
                    <button type="submit" disabled={busy} style={{ border: "none", borderRadius: 999, padding: "9px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12.5, cursor: busy ? "wait" : "pointer" }}>
                      {busy ? "Saving…" : "Confirm"}
                    </button>
                    <button type="button" onClick={() => setOpenAction(null)} style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "9px 14px", fontWeight: 600, fontSize: 12.5, cursor: "pointer" }}>
                      Cancel
                    </button>
                  </div>
                </form>
              );
            })() : null}
          </div>

          {/* RN Monitoring */}
          <div style={boardCard}>
            <div style={boardHeader}>RN monitoring</div>
            <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 10 }}>
              Assigned RN: {service?.rn_monitoring_assigned_user_id || "None assigned"}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              <form onSubmit={(e) => void handleAssignRn(e)} style={{ display: "grid", gap: 8 }}>
                <span style={labelStyle}>Assign RN (user id)</span>
                <input type="text" value={rnUserId} onChange={(e) => setRnUserId(e.target.value)} style={inputStyle} placeholder="RN user UUID" />
                <button type="submit" disabled={busy || !rnUserId.trim()} style={{ border: "none", borderRadius: 999, padding: "9px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12, cursor: "pointer", opacity: busy || !rnUserId.trim() ? 0.6 : 1 }}>
                  Assign
                </button>
              </form>
              <form onSubmit={(e) => void handleEndRnMonitoring(e)} style={{ display: "grid", gap: 8 }}>
                <span style={labelStyle}>End RN monitoring (reason)</span>
                <input type="text" value={rnEndReason} onChange={(e) => setRnEndReason(e.target.value)} style={inputStyle} placeholder="Reason monitoring is ending" />
                <button type="submit" disabled={busy || !rnEndReason.trim()} style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "9px 14px", fontWeight: 600, fontSize: 12, cursor: "pointer", opacity: busy || !rnEndReason.trim() ? 0.6 : 1 }}>
                  End monitoring
                </button>
              </form>
            </div>
          </div>

          {/* IDG Review / IDG Recommendations */}
          <div style={boardCard}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10, marginBottom: 10 }}>
              <div>
                <div style={boardHeader}>IDG review &amp; recommendations</div>
                <div style={{ color: colors.muted, fontSize: 12.5 }}>
                  Recommendations without a direct visit always display "IDG RECOMMENDATION / NO DIRECT VISIT" and require individual acceptance before any POC action.
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowRecommendationForm((v) => !v)}
                style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.accent, padding: "8px 12px", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
              >
                {showRecommendationForm ? "Cancel" : "New recommendation"}
              </button>
            </div>

            {showRecommendationForm ? (
              <form onSubmit={(e) => void handleCreateRecommendation(e)} style={{ display: "grid", gap: 10, marginBottom: 14, paddingBottom: 14, borderBottom: `1px solid ${colors.border}` }}>
                <label style={{ display: "grid", gap: 5 }}>
                  <span style={labelStyle}>IDG review *</span>
                  <select value={recommendationForm.idg_review_id} onChange={(e) => setRecommendationForm((f) => ({ ...f, idg_review_id: e.target.value }))} style={inputStyle}>
                    <option value="">Select this patient's IDG review…</option>
                    {idgReviewOptions.filter((r) => r.admission_status === "CURRENT").map((r) => (
                      <option key={r.id} value={r.id}>
                        {formatDateTime(r.review_date)}{r.is_finalized ? " (finalized)" : ""}{r.summary ? ` — ${r.summary.slice(0, 60)}` : ""}
                      </option>
                    ))}
                  </select>
                  {idgReviewOptions.length > 0 && idgReviewOptions.every((r) => r.admission_status !== "CURRENT") ? (
                    <span style={{ fontSize: 11.5, color: colors.warning }}>
                      Only this patient&apos;s current-admission IDG reviews can be selected here. This patient has
                      no IDG review tied to the current admission yet -- record one before attaching a recommendation.
                    </span>
                  ) : null}
                </label>
                <label style={{ display: "grid", gap: 5 }}>
                  <span style={labelStyle}>Recommendation type</span>
                  <input type="text" value={recommendationForm.recommendation_type} onChange={(e) => setRecommendationForm((f) => ({ ...f, recommendation_type: e.target.value }))} style={inputStyle} />
                </label>
                <label style={{ display: "grid", gap: 5 }}>
                  <span style={labelStyle}>Recommendation text *</span>
                  <textarea value={recommendationForm.recommendation_text} onChange={(e) => setRecommendationForm((f) => ({ ...f, recommendation_text: e.target.value }))} rows={3} style={{ ...inputStyle, resize: "vertical" as const }} />
                </label>
                <button type="submit" disabled={busy || !recommendationForm.idg_review_id.trim() || !recommendationForm.recommendation_text.trim()} style={{ border: "none", borderRadius: 999, padding: "9px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12.5, cursor: "pointer", width: "fit-content" }}>
                  Create recommendation
                </button>
              </form>
            ) : null}

            {discplineRecommendations.length === 0 ? (
              <div style={{ color: colors.muted, fontSize: 13 }}>No IDG recommendations on file for {discipline}.</div>
            ) : (
              <div style={{ display: "grid", gap: 10 }}>
                {discplineRecommendations.map((rec) => (
                  <div key={rec.id} style={{ border: `1px solid ${colors.border}`, borderRadius: 10, padding: 12, backgroundColor: colors.surface }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
                      <span style={badge(rec.status === "ACCEPTED" ? "green" : rec.status === "DECLINED" ? "danger" : "amber")}>{rec.status}</span>
                      <span style={{ color: colors.muted, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.6 }}>{rec.recommendation_type}</span>
                      {rec.no_direct_visit ? <span style={{ ...badge("teal"), fontSize: 9 }}>IDG RECOMMENDATION / NO DIRECT VISIT</span> : null}
                      {rec.requires_poc_change ? <span style={{ ...badge("amber"), fontSize: 9 }}>REQUIRES POC CHANGE</span> : null}
                      <span style={{ ...badge(rec.admission_status === "CURRENT" ? "green" : rec.admission_status === "HISTORICAL" ? "amber" : "teal"), fontSize: 9 }}>
                        {rec.admission_status === "CURRENT" ? "CURRENT ADMISSION" : rec.admission_status === "HISTORICAL" ? "HISTORICAL ADMISSION" : "LEGACY (NO ADMISSION RECORD)"}
                      </span>
                    </div>
                    <div style={{ color: colors.text, fontSize: 13, marginBottom: 6 }}>{rec.recommendation_text}</div>
                    <div style={{ color: colors.muted, fontSize: 12 }}>Created {formatDateTime(rec.created_at)}{rec.reviewed_at ? ` • Reviewed ${formatDateTime(rec.reviewed_at)}` : ""}</div>
                    {rec.status === "PENDING" ? (
                      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                        <button type="button" onClick={() => void handleReviewRecommendation(rec.id, "accept")} disabled={busy} style={{ border: "none", borderRadius: 999, padding: "7px 12px", backgroundColor: colors.success, color: "#ffffff", fontWeight: 700, fontSize: 11.5, cursor: "pointer" }}>Accept</button>
                        <button type="button" onClick={() => void handleReviewRecommendation(rec.id, "decline")} disabled={busy} style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "7px 12px", fontWeight: 600, fontSize: 11.5, cursor: "pointer" }}>Decline</button>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Linked Patient Issues (H2 fix: this section shows only linked
              PatientIssue identifiers, not real Plan of Care content --
              it was previously mislabeled "Plan of care linkage") */}
          <div style={boardCard}>
            <div style={boardHeader}>Linked patient issues</div>
            <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 8 }}>
              PatientIssue records opened by this discipline's workflow. Open "Issues &amp; Outcomes" for full POC problem/goal/intervention content.
            </div>
            {events.some((e) => e.related_patient_issue_id) ? (
              <div style={{ display: "grid", gap: 6 }}>
                {Array.from(new Set(events.filter((e) => e.related_patient_issue_id).map((e) => e.related_patient_issue_id as string))).map((issueId) => (
                  <div key={issueId} style={{ color: colors.text, fontSize: 12.5 }}>
                    Linked patient issue: <span style={{ fontFamily: "monospace" }}>{issueId}</span> (see Issues &amp; Outcomes)
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: colors.muted, fontSize: 13 }}>No linked patient issues yet. A refusal with "requires IDG review" or a related issue id will appear here.</div>
            )}
          </div>

          {/* Plan of Care Linkage -- TRUE POC linkage. Distinct from both
              "Linked patient issues" (above) and IDG Recommendations
              (above): this reuses the real POCProblem/POCGoal/
              POCIntervention records, never a second/fake POC system.
              Acceptance here is NOT the same as applying a POC change --
              that still happens through the existing Plan of Care
              screens, by RN/Case Manager/Clinical Supervisor/Medical
              Director only. */}
          <div style={boardCard}>
            <div style={boardHeader}>Plan of care linkage</div>
            <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 8 }}>
              IDG recommendations from this discipline that reference an actual Plan of Care problem, goal, or
              intervention. Accepting one here only authorizes the POC change — it does not itself edit the POC;
              open Plan of Care to apply it. Only RN, Case Manager, Clinical Supervisor, or Medical Director may accept.
            </div>
            {discplineRecommendations.filter((r) => r.requires_poc_change).length === 0 ? (
              <div style={{ color: colors.muted, fontSize: 13 }}>No Plan of Care-linked recommendations for {discipline}.</div>
            ) : (
              <div style={{ display: "grid", gap: 6 }}>
                {discplineRecommendations.filter((r) => r.requires_poc_change).map((r) => (
                  <div key={r.id} style={{ color: colors.text, fontSize: 12.5, borderBottom: `1px solid ${colors.border}`, paddingBottom: 6 }}>
                    <span style={badge(r.status === "ACCEPTED" ? "green" : r.status === "DECLINED" ? "danger" : "amber")}>{r.status}</span>{" "}
                    {r.linked_poc_problem_id ? <>Problem <span style={{ fontFamily: "monospace" }}>{r.linked_poc_problem_id}</span> </> : null}
                    {r.linked_poc_goal_id ? <>· Goal <span style={{ fontFamily: "monospace" }}>{r.linked_poc_goal_id}</span> </> : null}
                    {r.linked_poc_intervention_id ? <>· Intervention <span style={{ fontFamily: "monospace" }}>{r.linked_poc_intervention_id}</span></> : null}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Event History / Audit History (append-only, includes corrections) */}
          <div style={boardCard}>
            <div style={boardHeader}>Event history</div>
            <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 10 }}>
              Complete append-only audit trail for {discipline}. Nothing here is ever edited or deleted — corrections appear as new entries referencing the event they correct.
            </div>
            {events.length === 0 ? (
              <div style={{ color: colors.muted, fontSize: 13 }}>No events recorded yet.</div>
            ) : (
              <div style={{ display: "grid", gap: 8 }}>
                {[...events].reverse().map((evt) => (
                  <div key={evt.id} style={{ border: `1px solid ${colors.border}`, borderRadius: 10, padding: 10, backgroundColor: colors.surface }}>
                    <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 4 }}>
                      <span style={{ color: colors.text, fontSize: 12.5, fontWeight: 700 }}>{evt.event_type.replace(/_/g, " ")}</span>
                      <span style={{ color: colors.muted, fontSize: 11 }}>{formatDateTime(evt.created_at)}</span>
                    </div>
                    <div style={{ color: colors.muted, fontSize: 12 }}>
                      {evt.from_state ? `${evt.from_state} → ${evt.to_state}` : `→ ${evt.to_state}`}
                      {evt.recorded_by_role ? ` • Recorded by ${evt.recorded_by_role}` : ""}
                    </div>
                    {evt.information_source || evt.decision_maker_name ? (
                      <div style={{ color: colors.muted, fontSize: 12, marginTop: 4 }}>
                        {evt.information_source ? `Source: ${evt.information_source}. ` : ""}
                        {evt.decision_maker_name ? `Decision maker: ${evt.decision_maker_name}${evt.decision_maker_relationship ? ` (${evt.decision_maker_relationship})` : ""}.` : ""}
                      </div>
                    ) : null}
                    {evt.reason ? <div style={{ color: colors.text, fontSize: 12.5, marginTop: 6 }}>{evt.reason}</div> : null}
                    {evt.corrects_event_id ? <div style={{ color: colors.warning, fontSize: 11, marginTop: 6 }}>Corrects event {evt.corrects_event_id}</div> : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
