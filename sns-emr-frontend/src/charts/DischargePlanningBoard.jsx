import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import {
  fetchDischargePlanning,
  updateDischargePlanning,
  finalizePatientDischarge,
} from "../api/patientCharts";

const input = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.white,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};
const textarea = { ...input, minHeight: 80, resize: "vertical", fontFamily: "inherit" };
const label = { fontSize: 11, fontWeight: 600, color: COLORS.dim, textTransform: "uppercase", marginBottom: 4, display: "block" };
const formGroup = { marginBottom: 12 };

const CHECKLIST_ITEMS = [
  { key: "discharge_plan_reviewed", stateKey: "plan_reviewed", label: "Discharge plan reviewed with IDG" },
  { key: "discharge_notified", stateKey: "notified", label: "Patient / family notified of discharge" },
  { key: "discharge_explained", stateKey: "explained", label: "Reason for discharge explained to patient / family" },
  { key: "discharge_readmission_explained", stateKey: "readmission_explained", label: "Readmission process explained" },
  { key: "discharge_medication_instruction", stateKey: "medication_instruction", label: "Medication instructions provided" },
  { key: "discharge_contact_provided", stateKey: "contact_provided", label: "Emergency / follow-up contact information provided" },
  { key: "discharge_referral_provided", stateKey: "referral_provided", label: "Referral to other services provided (if applicable)" },
];

export default function DischargePlanningBoard({ patientId }) {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [projectedDate, setProjectedDate] = useState("");
  const [comments, setComments] = useState("");
  const [checklist, setChecklist] = useState({});

  const [finalizeOpen, setFinalizeOpen] = useState(false);
  const [dischargeDate, setDischargeDate] = useState("");
  const [reasonCode, setReasonCode] = useState("");
  const [finalizeNotes, setFinalizeNotes] = useState("");
  const [finalizing, setFinalizing] = useState(false);
  const [finalizeError, setFinalizeError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const data = await fetchDischargePlanning(patientId);
      setState(data);
      setProjectedDate(data.discharge_projected_date ? data.discharge_projected_date.slice(0, 10) : "");
      setComments(data.discharge_comments || "");
      setChecklist(data.checklist || {});
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load discharge planning.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSaveChecklist = async () => {
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const payload = {
        discharge_projected_date: projectedDate ? new Date(projectedDate).toISOString() : null,
        discharge_comments: comments || null,
      };
      CHECKLIST_ITEMS.forEach(({ key, stateKey }) => {
        payload[key] = Boolean(checklist[stateKey]);
      });
      const data = await updateDischargePlanning(patientId, payload);
      setState(data);
      setMessage("Discharge planning saved.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to save discharge planning.");
    } finally {
      setSaving(false);
    }
  };

  const handleFinalize = async (e) => {
    e.preventDefault();
    if (!dischargeDate || !reasonCode) {
      setFinalizeError("Discharge date and reason are required.");
      return;
    }
    setFinalizing(true);
    setFinalizeError("");
    try {
      await finalizePatientDischarge(patientId, {
        discharge_date: dischargeDate,
        reason_code: reasonCode,
        notes: finalizeNotes || undefined,
      });
      setFinalizeOpen(false);
      await load();
      setMessage("Patient discharged. HOPE Discharge report is now available under Compliance & HOPE.");
    } catch (err) {
      setFinalizeError(err?.response?.data?.detail || err?.message || "Unable to finalize discharge.");
    } finally {
      setFinalizing(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 24, color: COLORS.dim, fontSize: 13 }}>Loading discharge planning…</div>;
  }

  const discharged = state?.discharged;

  return (
    <div style={{ padding: 20, maxWidth: 780 }}>
      <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Discharge Planning</h2>
      <p style={{ color: COLORS.dim, fontSize: 13, margin: "0 0 20px" }}>
        Track discharge-readiness checklist items and, when the patient is ready to leave hospice services, finalize the discharge to generate the CMS HOPE Discharge report.
      </p>

      {error && (
        <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
          {error}
        </div>
      )}
      {message && !error && (
        <div style={{ background: `${COLORS.teal}22`, border: `1px solid ${COLORS.teal}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.teal, fontSize: 13 }}>
          {message}
        </div>
      )}

      {discharged ? (
        <div style={{ ...S.card, marginBottom: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.teal, textTransform: "uppercase", marginBottom: 8 }}>
            Patient Discharged
          </div>
          <div style={{ color: COLORS.white, fontSize: 14, marginBottom: 4 }}>Discharge date: {state.discharge_date}</div>
          <div style={{ color: COLORS.white, fontSize: 14 }}>Reason: {state.discharge_reason}</div>
        </div>
      ) : (
        <div style={{ ...S.card, marginBottom: 20 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Discharge Readiness Checklist</h3>

          <div style={formGroup}>
            <label style={label}>Projected discharge date</label>
            <input
              type="date"
              style={input}
              value={projectedDate}
              onChange={(e) => setProjectedDate(e.target.value)}
            />
          </div>

          {CHECKLIST_ITEMS.map((item) => (
            <label key={item.key} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, fontSize: 13, color: COLORS.white }}>
              <input
                type="checkbox"
                checked={Boolean(checklist[item.stateKey])}
                onChange={(e) => setChecklist((prev) => ({ ...prev, [item.stateKey]: e.target.checked }))}
              />
              {item.label}
            </label>
          ))}

          <div style={formGroup}>
            <label style={label}>Discharge planning notes</label>
            <textarea style={textarea} value={comments} onChange={(e) => setComments(e.target.value)} />
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={handleSaveChecklist}>
              {saving ? "Saving…" : "Save Checklist"}
            </button>
            <button type="button" style={S.btn(COLORS.red)} onClick={() => setFinalizeOpen(true)}>
              Finalize Discharge
            </button>
          </div>
        </div>
      )}

      {finalizeOpen && !discharged && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <form onSubmit={handleFinalize} style={{ ...S.card, width: 440 }}>
            <h3 style={{ fontSize: 16, color: COLORS.white, margin: "0 0 16px" }}>Finalize Discharge</h3>
            {finalizeError && (
              <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "8px 12px", marginBottom: 12, color: COLORS.red, fontSize: 12 }}>
                {finalizeError}
              </div>
            )}
            <div style={formGroup}>
              <label style={label}>Discharge date *</label>
              <input type="date" style={input} required value={dischargeDate} onChange={(e) => setDischargeDate(e.target.value)} />
            </div>
            <div style={formGroup}>
              <label style={label}>Reason for Discharge * (auto-maps to CMS HOPE A2115)</label>
              <select style={input} required value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
                <option value="">Select reason…</option>
                {Object.entries(state?.reason_codes || {}).map(([code, description]) => (
                  <option key={code} value={code}>{code} - {description}</option>
                ))}
              </select>
            </div>
            <div style={formGroup}>
              <label style={label}>Notes (optional)</label>
              <textarea style={textarea} value={finalizeNotes} onChange={(e) => setFinalizeNotes(e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 8 }}>
              <button type="button" style={{ ...S.btn(COLORS.border), color: COLORS.white }} onClick={() => setFinalizeOpen(false)} disabled={finalizing}>
                Cancel
              </button>
              <button type="submit" style={S.btn(COLORS.red)} disabled={finalizing}>
                {finalizing ? "Finalizing…" : "Confirm Discharge"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
