// src/components/AdmissionActionCenterDrawer.jsx
//
// Admission Action Center (Phase A) — a global, RN-ICA-reachable request
// tracker for Medication Request / Physician Order / DME Order / Supply
// Order / Referral. Opens as a modal/drawer from a persistent trigger
// button so it is available from every RN ICA section without navigating
// away from the assessment and without losing any in-progress draft
// (RNICA.jsx's own form state is completely untouched by opening/closing
// this drawer).
//
// Deliberately simple (Phase A scope): linear status tracking only
// (REQUESTED -> ORDERED -> SENT -> ACKNOWLEDGED -> DELIVERED -> COMPLETED).
// No fulfillment workflow, no approval routing, no notifications.

import { useCallback, useEffect, useState } from "react";
import {
  cancelRnicaActionCenterRequest,
  completeRnicaActionCenterRequest,
  createRnicaActionCenterRequest,
  listRnicaActionCenterRequests,
  updateRnicaActionCenterRequestStatus,
} from "../api/icaAssessments";

export const ACTION_CENTER_REQUEST_TYPES = [
  { value: "MEDICATION_REQUEST", label: "Medication Request" },
  { value: "PHYSICIAN_ORDER", label: "Physician Order" },
  { value: "PHYSICIAN_CONTACT", label: "Physician Contact" },
  { value: "DME_ORDER", label: "DME Order" },
  { value: "SUPPLY_ORDER", label: "Supply Order" },
  { value: "REFERRAL", label: "Referral" },
];

// Backend requires a `type_details` payload keyed by request_type (see
// admission_action_center_service.py::_REQUIRED_TYPE_DETAIL_KEYS). This
// drives which extra inputs the "New Request" form shows and what it
// sends as `type_details` on create.
const TYPE_DETAIL_FIELDS = {
  DME_ORDER: [{ key: "item_description", label: "Item Description" }],
  SUPPLY_ORDER: [{ key: "item_description", label: "Item Description" }],
  REFERRAL: [
    { key: "destination", label: "Referral Destination" },
    { key: "reason", label: "Reason for Referral" },
  ],
  PHYSICIAN_CONTACT: [
    { key: "physician_name", label: "Physician Name" },
    { key: "contact_method", label: "Contact Method (e.g. phone, fax, portal)" },
    { key: "reason", label: "Reason for Contact" },
  ],
};

// Non-terminal statuses only -- COMPLETED and CANCELED are terminal states
// the backend rejects via the generic status PATCH and instead require the
// dedicated /complete (with completion_evidence) and /cancel (with
// cancellation_reason) endpoints handled separately below.
export const ACTION_CENTER_STATUSES = [
  "REQUESTED",
  "ORDERED",
  "SENT",
  "ACKNOWLEDGED",
  "DELIVERED",
];

const REQUEST_TYPE_LABELS = Object.fromEntries(
  ACTION_CENTER_REQUEST_TYPES.map((t) => [t.value, t.label]),
);

// TEAM-BASED ADMISSION WORKFLOW DIRECTIVE: "Assign Order Task To" options.
// Stored as-is in the existing free-text `responsible_discipline` column.
const RESPONSIBLE_DISCIPLINE_OPTIONS = [
  { value: "", label: "Unassigned (I will complete it)" },
  { value: "DPCS", label: "DPCS" },
  { value: "CASE_MANAGER", label: "Case Manager" },
  { value: "RN", label: "RN" },
  { value: "OFFICE_RN", label: "Office RN" },
  { value: "OTHER", label: "Other" },
];

function statusColor(status, COLORS) {
  if (status === "COMPLETED") return COLORS.success || "#0F766E";
  if (status === "REQUESTED") return COLORS.gray;
  return COLORS.warning || "#B45309";
}

/**
 * Persistent trigger button. Render this once, outside the per-section
 * render loop (e.g. in the page footer), so it stays mounted across every
 * section switch.
 */
export function AdmissionActionCenterButton({ styles, onClick, openCount = 0 }) {
  return (
    <button type="button" style={styles.btnSecondary} onClick={onClick}>
      Admission Action Center{openCount > 0 ? ` (${openCount})` : ""}
    </button>
  );
}

export default function AdmissionActionCenterDrawer({
  open,
  onClose,
  assessmentId,
  sourceSection,
  patientName,
  initialRequestType,
  styles,
  COLORS,
}) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");

  const [requestType, setRequestType] = useState(initialRequestType || ACTION_CENTER_REQUEST_TYPES[0].value);
  const [details, setDetails] = useState("");
  const [typeDetails, setTypeDetails] = useState({});
  // TEAM-BASED ADMISSION WORKFLOW DIRECTIVE: lets the requesting RN name
  // who should complete the order/request (DPCS, Case Manager, Office RN,
  // another RN, or Other) instead of being assumed to complete it herself.
  // Reuses the existing free-text `responsible_discipline` column (no
  // schema change) -- the backend stores whatever string is sent, so this
  // is purely a frontend convenience list of the roles that actually do
  // this work at SNS, plus an "Other" free-text escape hatch.
  const [responsibleDiscipline, setResponsibleDiscipline] = useState("");
  const [responsibleDisciplineOther, setResponsibleDisciplineOther] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  // TEAM-BASED ADMISSION WORKFLOW DIRECTIVE: dirty-close protection. If the
  // RN has started a request draft (details or any type-detail field has
  // text), closing the drawer -- via header button, Escape, or
  // clicking the overlay -- must not silently discard it. There is no
  // separate "save draft" concept for this request form (submitting IS
  // the save), so the choice offered is "Submit Request and Return" /
  // "Discard and Return" / "Continue Editing" rather than inventing a
  // draft-persistence mechanism that does not exist on the backend.
  const [closeConfirmOpen, setCloseConfirmOpen] = useState(false);

  const [statusDrafts, setStatusDrafts] = useState({});
  const [statusError, setStatusError] = useState("");

  // Terminal-action (complete/cancel) drafts, keyed by request id. Each
  // request gets its own evidence/reason text and open/closed mini-form
  // state so drawer usage stays simple for the common case (no forms
  // shown until the RN picks a terminal action).
  const [completeDrafts, setCompleteDrafts] = useState({});
  const [cancelDrafts, setCancelDrafts] = useState({});
  const [openTerminalForm, setOpenTerminalForm] = useState({});
  const [terminalError, setTerminalError] = useState("");
  const [terminalSubmitting, setTerminalSubmitting] = useState({});

  const refresh = useCallback(async () => {
    if (!assessmentId) return;
    setLoading(true);
    setLoadError("");
    try {
      const result = await listRnicaActionCenterRequests(assessmentId);
      setRequests(result.requests || []);
    } catch (error) {
      setLoadError(error.message || "Unable to load Admission Action Center requests.");
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  // Escape key closes the drawer, but must route through the same
  // dirty-draft check as every other close affordance (header button,
  // overlay click) -- no silent discard-on-Escape.
  useEffect(() => {
    if (!open) return undefined;
    const handleKeyDown = (e) => {
      if (e.key !== "Escape") return;
      const dirty =
        details.trim().length > 0 ||
        Object.values(typeDetails).some((v) => (v || "").trim().length > 0);
      if (dirty) {
        setCloseConfirmOpen(true);
      } else {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, details, typeDetails, onClose]);

  useEffect(() => {
    if (open) {
      refresh();
      // Reset the draft each time the drawer opens, honoring a preselected
      // request type (e.g. Respiratory's "Create / Open Order" button)
      // when one is supplied; otherwise default to the first type as
      // before.
      setRequestType(initialRequestType || ACTION_CENTER_REQUEST_TYPES[0].value);
      setDetails("");
      setTypeDetails({});
      setResponsibleDiscipline("");
      setResponsibleDisciplineOther("");
      setSubmitError("");
      setCloseConfirmOpen(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, refresh, initialRequestType]);

  if (!open) return null;

  const requiredTypeDetailFields = TYPE_DETAIL_FIELDS[requestType] || [];

  // Dirty = the RN has started a request draft worth protecting on close.
  const hasDraftInProgress =
    details.trim().length > 0 ||
    Object.values(typeDetails).some((v) => (v || "").trim().length > 0);

  const requestClose = () => {
    if (hasDraftInProgress) {
      setCloseConfirmOpen(true);
      return;
    }
    onClose();
  };

  const handleRequestTypeChange = (nextType) => {
    setRequestType(nextType);
    setTypeDetails({});
    setSubmitError("");
  };

  const handleTypeDetailChange = (key, value) => {
    setTypeDetails((prev) => ({ ...prev, [key]: value }));
  };

  const handleCreate = async () => {
    if (!details.trim()) {
      setSubmitError("Details are required.");
      return;
    }
    const missingField = requiredTypeDetailFields.find((field) => !(typeDetails[field.key] || "").trim());
    if (missingField) {
      setSubmitError(`${missingField.label} is required for this request type.`);
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    try {
      const payloadTypeDetails = {};
      requiredTypeDetailFields.forEach((field) => {
        payloadTypeDetails[field.key] = (typeDetails[field.key] || "").trim();
      });
      const resolvedDiscipline =
        responsibleDiscipline === "OTHER" ? responsibleDisciplineOther.trim() : responsibleDiscipline;
      await createRnicaActionCenterRequest(assessmentId, {
        request_type: requestType,
        details: details.trim(),
        source_section: sourceSection,
        ...(resolvedDiscipline ? { responsible_discipline: resolvedDiscipline } : {}),
        ...(requiredTypeDetailFields.length > 0 ? { type_details: payloadTypeDetails } : {}),
      });
      setDetails("");
      setTypeDetails({});
      setResponsibleDiscipline("");
      setResponsibleDisciplineOther("");
      await refresh();
    } catch (error) {
      setSubmitError(error.message || "Unable to create request.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleTerminalForm = (requestId, form) => {
    setTerminalError("");
    setOpenTerminalForm((prev) => ({
      ...prev,
      [requestId]: prev[requestId] === form ? null : form,
    }));
  };

  const handleComplete = async (requestId) => {
    const evidence = (completeDrafts[requestId] || "").trim();
    if (!evidence) {
      setTerminalError("Completion evidence is required (e.g. delivery confirmation, signed acknowledgment, referral outcome, or physician response).");
      return;
    }
    setTerminalSubmitting((prev) => ({ ...prev, [requestId]: true }));
    setTerminalError("");
    try {
      await completeRnicaActionCenterRequest(assessmentId, requestId, { completion_evidence: evidence });
      setCompleteDrafts((prev) => ({ ...prev, [requestId]: "" }));
      setOpenTerminalForm((prev) => ({ ...prev, [requestId]: null }));
      await refresh();
    } catch (error) {
      setTerminalError(error.message || "Unable to complete request.");
    } finally {
      setTerminalSubmitting((prev) => ({ ...prev, [requestId]: false }));
    }
  };

  const handleCancel = async (requestId) => {
    const reason = (cancelDrafts[requestId] || "").trim();
    if (!reason) {
      setTerminalError("A cancellation reason is required.");
      return;
    }
    setTerminalSubmitting((prev) => ({ ...prev, [requestId]: true }));
    setTerminalError("");
    try {
      await cancelRnicaActionCenterRequest(assessmentId, requestId, { cancellation_reason: reason });
      setCancelDrafts((prev) => ({ ...prev, [requestId]: "" }));
      setOpenTerminalForm((prev) => ({ ...prev, [requestId]: null }));
      await refresh();
    } catch (error) {
      setTerminalError(error.message || "Unable to cancel request.");
    } finally {
      setTerminalSubmitting((prev) => ({ ...prev, [requestId]: false }));
    }
  };

  const handleStatusChange = async (requestId, nextStatus) => {
    setStatusError("");
    try {
      await updateRnicaActionCenterRequestStatus(assessmentId, requestId, { status: nextStatus });
      await refresh();
    } catch (error) {
      setStatusError(error.message || "Unable to update status.");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Admission Action Center"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        justifyContent: "flex-end",
        background: "rgba(15, 23, 42, 0.35)",
      }}
      onClick={requestClose}
    >
      <div
        style={{
          width: "min(480px, 100%)",
          height: "100%",
          background: COLORS.white,
          boxShadow: "-8px 0 24px rgba(15, 23, 42, 0.18)",
          padding: 20,
          overflowY: "auto",
          boxSizing: "border-box",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div>
            <div style={styles.sectionTitle}>Admission Action Center</div>
            {/* TEAM-BASED ADMISSION WORKFLOW DIRECTIVE: show the patient's
                name, never a raw patient/assessment UUID, so the RN can
                confirm she's looking at the right chart. */}
            {patientName && (
              <div style={{ fontSize: 12, color: COLORS.gray }}>{patientName}</div>
            )}
          </div>
          {/* "Back to Assessment" (not "Close"): this drawer never
              navigates away from or unmounts RNICA -- it is an overlay --
              so the label reflects what actually happens: the nurse
              returns to the assessment exactly where she left it. */}
          <button type="button" style={styles.btnSecondary} onClick={requestClose}>
            Back to Assessment
          </button>
        </div>
        <div style={styles.sectionSubtitle}>
          Request Medications, Physician Orders, DME, Supplies, or Referrals without leaving this assessment.
          This tracks request status only — fulfillment, approval routing, and notifications are out of scope.
        </div>

        {closeConfirmOpen && (
          <div style={{ ...styles.card, border: `1px solid ${COLORS.warning || "#B45309"}`, marginTop: 10 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
              You have an unsubmitted request
            </div>
            <div style={{ fontSize: 12.5, marginBottom: 10 }}>
              Details or request-specific fields have text that hasn't been submitted yet. What would you like to do?
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <button
                type="button"
                style={styles.btnPrimary}
                onClick={async () => {
                  await handleCreate();
                  setCloseConfirmOpen(false);
                }}
                disabled={submitting}
              >
                Submit Request and Return
              </button>
              <button
                type="button"
                style={styles.btnSecondary}
                onClick={() => {
                  setDetails("");
                  setTypeDetails({});
                  setResponsibleDiscipline("");
                  setResponsibleDisciplineOther("");
                  setCloseConfirmOpen(false);
                  onClose();
                }}
              >
                Discard and Return
              </button>
              <button type="button" style={styles.btnSecondary} onClick={() => setCloseConfirmOpen(false)}>
                Continue Editing
              </button>
            </div>
          </div>
        )}

        <div style={styles.card}>
          <div style={styles.cardTitle}>New Request</div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Request Type</label>
            <select
              style={styles.select}
              value={requestType}
              onChange={(e) => handleRequestTypeChange(e.target.value)}
            >
              {ACTION_CENTER_REQUEST_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Details</label>
            <textarea
              style={styles.textarea}
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Describe what is being requested..."
            />
          </div>

          {requiredTypeDetailFields.map((field) => (
            <div style={styles.formGroup} key={field.key}>
              <label style={styles.label}>{field.label}</label>
              <input
                type="text"
                style={styles.select}
                value={typeDetails[field.key] || ""}
                onChange={(e) => handleTypeDetailChange(field.key, e.target.value)}
              />
            </div>
          ))}

          {/* TEAM-BASED ADMISSION WORKFLOW DIRECTIVE: the admitting RN is
              frequently not the clinician who completes the order. This
              lets her name who should, without leaving RNICA or being
              forced to complete it herself. Stored in the existing
              free-text responsible_discipline column -- no schema change. */}
          <div style={styles.formGroup}>
            <label style={styles.label}>Assign Order Task To</label>
            <select
              style={styles.select}
              value={responsibleDiscipline}
              onChange={(e) => setResponsibleDiscipline(e.target.value)}
            >
              {RESPONSIBLE_DISCIPLINE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {responsibleDiscipline === "OTHER" && (
              <input
                type="text"
                style={{ ...styles.select, marginTop: 6 }}
                placeholder="Role or name"
                value={responsibleDisciplineOther}
                onChange={(e) => setResponsibleDisciplineOther(e.target.value)}
              />
            )}
          </div>

          {sourceSection && (
            <div style={{ fontSize: 11, color: COLORS.gray, marginBottom: 8 }}>
              Raised from section: <strong>{sourceSection}</strong>
            </div>
          )}

          {submitError && (
            <div style={{ ...styles.warningBox, marginBottom: 10 }}>{submitError}</div>
          )}

          <button
            type="button"
            style={styles.btnPrimary}
            onClick={handleCreate}
            disabled={submitting}
          >
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
        </div>

        <div style={{ marginTop: 16 }}>
          <div style={styles.cardTitle}>Requests ({requests.length})</div>

          {loading && <div style={{ fontSize: 12, color: COLORS.gray }}>Loading...</div>}
          {loadError && <div style={styles.warningBox}>{loadError}</div>}
          {statusError && <div style={styles.warningBox}>{statusError}</div>}
          {terminalError && <div style={styles.warningBox}>{terminalError}</div>}

          {!loading && requests.length === 0 && !loadError && (
            <div style={{ fontSize: 12, color: COLORS.gray }}>No requests yet.</div>
          )}

          {requests.map((r) => {
            const isFinalized = r.status === "COMPLETED" || r.status === "CANCELED";
            const activeForm = openTerminalForm[r.id];
            return (
            <div key={r.id} style={styles.card}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>
                  {REQUEST_TYPE_LABELS[r.requestType] || r.requestType}
                </div>
                <span
                  style={{
                    ...styles.statusBadge,
                    background: "transparent",
                    border: `1px solid ${statusColor(r.status, COLORS)}`,
                    color: statusColor(r.status, COLORS),
                  }}
                >
                  {r.status}
                </span>
              </div>
              <div style={{ fontSize: 12.5, color: COLORS.dark, marginBottom: 6 }}>{r.details}</div>
              {r.sourceSection && (
                <div style={{ fontSize: 10.5, color: COLORS.gray, marginBottom: 6 }}>
                  Source section: {r.sourceSection}
                </div>
              )}
              {r.responsibleDiscipline && (
                <div style={{ fontSize: 10.5, color: COLORS.gray, marginBottom: 6 }}>
                  Assigned to: {r.responsibleDiscipline}
                </div>
              )}
              {r.status === "COMPLETED" && r.completionEvidence && (
                <div style={{ fontSize: 10.5, color: COLORS.gray, marginBottom: 6 }}>
                  Completion evidence: {r.completionEvidence}
                </div>
              )}
              {r.status === "CANCELED" && r.cancellationReason && (
                <div style={{ fontSize: 10.5, color: COLORS.gray, marginBottom: 6 }}>
                  Cancellation reason: {r.cancellationReason}
                </div>
              )}

              {!isFinalized && (
                <>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                    <select
                      style={{ ...styles.select, flex: 1 }}
                      value={statusDrafts[r.id] || r.status}
                      onChange={(e) =>
                        setStatusDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))
                      }
                    >
                      {ACTION_CENTER_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      style={styles.btnSecondary}
                      onClick={() => handleStatusChange(r.id, statusDrafts[r.id] || r.status)}
                      disabled={(statusDrafts[r.id] || r.status) === r.status}
                    >
                      Update Status
                    </button>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      type="button"
                      style={styles.btnSecondary}
                      onClick={() => toggleTerminalForm(r.id, "complete")}
                    >
                      Mark Completed
                    </button>
                    <button
                      type="button"
                      style={styles.btnSecondary}
                      onClick={() => toggleTerminalForm(r.id, "cancel")}
                    >
                      Cancel Request
                    </button>
                  </div>

                  {activeForm === "complete" && (
                    <div style={{ marginTop: 8 }}>
                      <label style={styles.label}>Completion Evidence (required)</label>
                      <textarea
                        style={styles.textarea}
                        value={completeDrafts[r.id] || ""}
                        onChange={(e) => setCompleteDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                        placeholder="e.g. Delivery confirmation, signed patient/caregiver acknowledgment, referral outcome, or physician response."
                      />
                      <button
                        type="button"
                        style={styles.btnPrimary}
                        onClick={() => handleComplete(r.id)}
                        disabled={!!terminalSubmitting[r.id]}
                      >
                        {terminalSubmitting[r.id] ? "Submitting..." : "Confirm Completed"}
                      </button>
                    </div>
                  )}

                  {activeForm === "cancel" && (
                    <div style={{ marginTop: 8 }}>
                      <label style={styles.label}>Cancellation Reason (required)</label>
                      <textarea
                        style={styles.textarea}
                        value={cancelDrafts[r.id] || ""}
                        onChange={(e) => setCancelDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                        placeholder="Why is this request being canceled?"
                      />
                      <button
                        type="button"
                        style={styles.btnPrimary}
                        onClick={() => handleCancel(r.id)}
                        disabled={!!terminalSubmitting[r.id]}
                      >
                        {terminalSubmitting[r.id] ? "Submitting..." : "Confirm Cancellation"}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
