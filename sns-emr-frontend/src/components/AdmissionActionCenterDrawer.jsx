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
  createRnicaActionCenterRequest,
  listRnicaActionCenterRequests,
  updateRnicaActionCenterRequestStatus,
} from "../api/icaAssessments";

export const ACTION_CENTER_REQUEST_TYPES = [
  { value: "MEDICATION_REQUEST", label: "Medication Request" },
  { value: "PHYSICIAN_ORDER", label: "Physician Order" },
  { value: "DME_ORDER", label: "DME Order" },
  { value: "SUPPLY_ORDER", label: "Supply Order" },
  { value: "REFERRAL", label: "Referral" },
];

export const ACTION_CENTER_STATUSES = [
  "REQUESTED",
  "ORDERED",
  "SENT",
  "ACKNOWLEDGED",
  "DELIVERED",
  "COMPLETED",
];

const REQUEST_TYPE_LABELS = Object.fromEntries(
  ACTION_CENTER_REQUEST_TYPES.map((t) => [t.value, t.label]),
);

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
  styles,
  COLORS,
}) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");

  const [requestType, setRequestType] = useState(ACTION_CENTER_REQUEST_TYPES[0].value);
  const [details, setDetails] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [statusDrafts, setStatusDrafts] = useState({});
  const [statusError, setStatusError] = useState("");

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

  useEffect(() => {
    if (open) {
      refresh();
    }
  }, [open, refresh]);

  if (!open) return null;

  const handleCreate = async () => {
    if (!details.trim()) {
      setSubmitError("Details are required.");
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    try {
      await createRnicaActionCenterRequest(assessmentId, {
        request_type: requestType,
        details: details.trim(),
        source_section: sourceSection,
      });
      setDetails("");
      await refresh();
    } catch (error) {
      setSubmitError(error.message || "Unable to create request.");
    } finally {
      setSubmitting(false);
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
      onClick={onClose}
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
          <div style={styles.sectionTitle}>Admission Action Center</div>
          <button type="button" style={styles.btnSecondary} onClick={onClose}>
            Close
          </button>
        </div>
        <div style={styles.sectionSubtitle}>
          Request Medications, Physician Orders, DME, Supplies, or Referrals without leaving this assessment.
          This tracks request status only — fulfillment, approval routing, and notifications are out of scope.
        </div>

        <div style={styles.card}>
          <div style={styles.cardTitle}>New Request</div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Request Type</label>
            <select
              style={styles.select}
              value={requestType}
              onChange={(e) => setRequestType(e.target.value)}
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

          {!loading && requests.length === 0 && !loadError && (
            <div style={{ fontSize: 12, color: COLORS.gray }}>No requests yet.</div>
          )}

          {requests.map((r) => (
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

              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
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
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
