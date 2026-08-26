import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { getCurrentUser } from "../api/session";
import { listBenefitPeriods } from "../api/benefitPeriods";
import { listF2FEncounters, createF2FEncounter, finalizeF2FEncounter } from "../api/f2f";

// F2F_PERFORMER_ROLES (server-enforced in f2f_service.py): physician-level
// roles plus NP/PA. Mirrored here only to hide actions a role would be
// denied for — the API gate (require_roles(..., allow_clinical_admin=False))
// is the actual authority boundary.
const F2F_PERFORMER_ROLES = ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "NP", "PA"];

// F2F_PHYSICIAN_ATTESTOR_ROLES (server-enforced in f2f_service.py): only a
// physician-level role may attest/finalize an NP- or PA-performed F2F
// encounter (backend requires a non-null attestation_summary and 403s any
// other caller). NP/PA performers must NEVER see or be able to submit their
// own "Finalize" action for an encounter they performed — the backend
// would reject it every time, so the UI must reflect that boundary rather
// than let the user hit a guaranteed 422/403.
const F2F_PHYSICIAN_ATTESTOR_ROLES = ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"];

function canFinalizeEncounter(encounter, role) {
  if (encounter.performed_by_role === "NP" || encounter.performed_by_role === "PA") {
    return F2F_PHYSICIAN_ATTESTOR_ROLES.includes(role);
  }
  return F2F_PERFORMER_ROLES.includes(role);
}

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
const formGroup = { marginBottom: 10 };

const STATUS_COLORS = { DRAFT: COLORS.muted, FINALIZED: COLORS.green };

function StatusBadge({ status, label: statusLabel }) {
  const color = STATUS_COLORS[status] || COLORS.muted;
  return (
    <span
      style={{
        fontSize: 10.5,
        fontWeight: 700,
        color,
        border: `1px solid ${color}`,
        borderRadius: 6,
        padding: "2px 8px",
        textTransform: "uppercase",
        letterSpacing: 0.4,
      }}
    >
      {statusLabel || (status || "").replace(/_/g, " ")}
    </span>
  );
}

export default function F2FBoard({ patientId }) {
  const currentUser = getCurrentUser();
  const canPerform = F2F_PERFORMER_ROLES.includes(currentUser?.role);

  const [encounters, setEncounters] = useState([]);
  const [benefitPeriods, setBenefitPeriods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [formMessage, setFormMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  // Per-encounter attestation-summary drafts, keyed by encounter id, for
  // the physician-attestation textarea shown when finalizing an NP/PA-
  // performed F2F (backend requires this text; see F2F_PHYSICIAN_ATTESTOR_ROLES).
  const [attestationDrafts, setAttestationDrafts] = useState({});

  const [form, setForm] = useState({
    benefit_period_id: "",
    encounter_date: new Date().toISOString().slice(0, 10),
    primary_diagnosis: "",
    secondary_conditions: "",
    clinical_decline_summary: "",
    kps_score: "",
    pps_score_previous: "",
    pps_score_current: "",
    fast_score: "",
    nyha_class: "",
    adl_dependency_level: "",
    adl_dependency_count: "",
    is_bedbound: false,
    weight_loss_lbs: "",
    oral_intake_decline: false,
    dysphagia: false,
    hospitalizations_30d: "",
    oxygen_lpm_previous: "",
    oxygen_lpm_current: "",
  });

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    Promise.all([listF2FEncounters(patientId), listBenefitPeriods(patientId)])
      .then(([list, bpList]) => {
        setEncounters(list || []);
        setBenefitPeriods(bpList || []);
        setForm((f) => ({
          ...f,
          benefit_period_id: f.benefit_period_id || (bpList || []).find((bp) => bp.is_current)?.id || (bpList || [])[0]?.id || "",
        }));
      })
      .catch((err) => {
        console.error("Failed to load F2F encounters:", err);
        setError(err?.response?.data?.detail || "Unable to load F2F encounters.");
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => { reload(); }, [reload]);

  const handleCreate = async () => {
    if (!form.benefit_period_id) {
      setFormMessage("Select a benefit period before recording an F2F encounter.");
      return;
    }
    setSubmitting(true);
    setFormMessage("");
    try {
      const numOrUndef = (v) => (v === "" || v === null || v === undefined ? undefined : Number(v));
      await createF2FEncounter({
        patient_id: patientId,
        benefit_period_id: form.benefit_period_id,
        encounter_date: form.encounter_date,
        primary_diagnosis: form.primary_diagnosis || undefined,
        secondary_conditions: form.secondary_conditions || undefined,
        clinical_decline_summary: form.clinical_decline_summary || undefined,
        kps_score: numOrUndef(form.kps_score),
        pps_score_previous: numOrUndef(form.pps_score_previous),
        pps_score_current: numOrUndef(form.pps_score_current),
        fast_score: form.fast_score || undefined,
        nyha_class: form.nyha_class || undefined,
        adl_dependency_level: form.adl_dependency_level || undefined,
        adl_dependency_count: numOrUndef(form.adl_dependency_count),
        is_bedbound: form.is_bedbound || undefined,
        weight_loss_lbs: numOrUndef(form.weight_loss_lbs),
        oral_intake_decline: form.oral_intake_decline || undefined,
        dysphagia: form.dysphagia || undefined,
        hospitalizations_30d: numOrUndef(form.hospitalizations_30d),
        oxygen_lpm_previous: numOrUndef(form.oxygen_lpm_previous),
        oxygen_lpm_current: numOrUndef(form.oxygen_lpm_current),
      });
      setForm((f) => ({
        ...f,
        primary_diagnosis: "",
        secondary_conditions: "",
        clinical_decline_summary: "",
        kps_score: "",
        pps_score_previous: "",
        pps_score_current: "",
        fast_score: "",
        nyha_class: "",
        adl_dependency_level: "",
        adl_dependency_count: "",
        is_bedbound: false,
        weight_loss_lbs: "",
        oral_intake_decline: false,
        dysphagia: false,
        hospitalizations_30d: "",
        oxygen_lpm_previous: "",
        oxygen_lpm_current: "",
      }));
      setFormMessage("F2F draft encounter recorded.");
      reload();
    } catch (err) {
      console.error("Failed to create F2F encounter:", err);
      setFormMessage(err?.response?.data?.detail || "Unable to record F2F encounter.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinalize = async (encounter) => {
    const requiresAttestation = encounter.performed_by_role === "NP" || encounter.performed_by_role === "PA";
    const attestationSummary = (attestationDrafts[encounter.id] || "").trim();
    if (requiresAttestation && !attestationSummary) {
      setError(`A physician attestation summary is required to finalize this ${encounter.performed_by_role}-performed F2F.`);
      return;
    }
    setBusyId(encounter.id);
    setError("");
    try {
      await finalizeF2FEncounter(encounter.id, requiresAttestation ? attestationSummary : undefined);
      setAttestationDrafts((prev) => {
        const next = { ...prev };
        delete next[encounter.id];
        return next;
      });
      reload();
    } catch (err) {
      console.error("Failed to finalize F2F encounter:", err);
      setError(err?.response?.data?.detail || "Unable to finalize F2F encounter.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {canPerform && (
        <div style={{ ...S.card, padding: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, marginBottom: 12 }}>
            Face-to-Face (F2F) Encounter
          </div>

          <div style={formGroup}>
            <label style={label}>Benefit Period</label>
            <select
              style={input}
              value={form.benefit_period_id}
              onChange={(e) => setForm((f) => ({ ...f, benefit_period_id: e.target.value }))}
            >
              <option value="">Select benefit period…</option>
              {benefitPeriods.map((bp) => (
                <option key={bp.id} value={bp.id}>
                  {bp.benefit_type} — Period {bp.period_number}{bp.is_current ? " (current)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div style={formGroup}>
            <label style={label}>Encounter Date</label>
            <input
              type="date"
              style={input}
              value={form.encounter_date}
              onChange={(e) => setForm((f) => ({ ...f, encounter_date: e.target.value }))}
            />
          </div>

          <div style={formGroup}>
            <label style={label}>Primary Diagnosis</label>
            <input
              style={input}
              value={form.primary_diagnosis}
              onChange={(e) => setForm((f) => ({ ...f, primary_diagnosis: e.target.value }))}
            />
          </div>

          <div style={formGroup}>
            <label style={label}>Secondary Conditions</label>
            <input
              style={input}
              value={form.secondary_conditions}
              onChange={(e) => setForm((f) => ({ ...f, secondary_conditions: e.target.value }))}
            />
          </div>

          <div style={formGroup}>
            <label style={label}>Clinical Decline Summary</label>
            <textarea
              style={textarea}
              value={form.clinical_decline_summary}
              onChange={(e) => setForm((f) => ({ ...f, clinical_decline_summary: e.target.value }))}
              placeholder="Findings supporting continued decline / hospice eligibility…"
            />
          </div>

          <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.dim, margin: "14px 0 8px" }}>
            Functional &amp; Disease Scoring
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <div style={formGroup}>
              <label style={label}>KPS Score</label>
              <input type="number" min="0" max="100" style={input} value={form.kps_score}
                onChange={(e) => setForm((f) => ({ ...f, kps_score: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>PPS — Previous</label>
              <input type="number" min="0" max="100" style={input} value={form.pps_score_previous}
                onChange={(e) => setForm((f) => ({ ...f, pps_score_previous: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>PPS — Current</label>
              <input type="number" min="0" max="100" style={input} value={form.pps_score_current}
                onChange={(e) => setForm((f) => ({ ...f, pps_score_current: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>FAST Score</label>
              <input style={input} value={form.fast_score}
                onChange={(e) => setForm((f) => ({ ...f, fast_score: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>NYHA Class</label>
              <input style={input} value={form.nyha_class}
                onChange={(e) => setForm((f) => ({ ...f, nyha_class: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>ADL Dependency Level</label>
              <input style={input} value={form.adl_dependency_level}
                onChange={(e) => setForm((f) => ({ ...f, adl_dependency_level: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>ADL Dependency Count</label>
              <input type="number" min="0" style={input} value={form.adl_dependency_count}
                onChange={(e) => setForm((f) => ({ ...f, adl_dependency_count: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>Weight Loss (lbs)</label>
              <input type="number" step="0.1" style={input} value={form.weight_loss_lbs}
                onChange={(e) => setForm((f) => ({ ...f, weight_loss_lbs: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>Hospitalizations (30d)</label>
              <input type="number" min="0" style={input} value={form.hospitalizations_30d}
                onChange={(e) => setForm((f) => ({ ...f, hospitalizations_30d: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>O2 (L/min) — Previous</label>
              <input type="number" step="0.1" style={input} value={form.oxygen_lpm_previous}
                onChange={(e) => setForm((f) => ({ ...f, oxygen_lpm_previous: e.target.value }))} />
            </div>
            <div style={formGroup}>
              <label style={label}>O2 (L/min) — Current</label>
              <input type="number" step="0.1" style={input} value={form.oxygen_lpm_current}
                onChange={(e) => setForm((f) => ({ ...f, oxygen_lpm_current: e.target.value }))} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", margin: "6px 0 14px" }}>
            <label style={{ fontSize: 12, color: COLORS.dim, display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={form.is_bedbound}
                onChange={(e) => setForm((f) => ({ ...f, is_bedbound: e.target.checked }))} />
              Bedbound
            </label>
            <label style={{ fontSize: 12, color: COLORS.dim, display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={form.oral_intake_decline}
                onChange={(e) => setForm((f) => ({ ...f, oral_intake_decline: e.target.checked }))} />
              Oral intake decline
            </label>
            <label style={{ fontSize: 12, color: COLORS.dim, display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={form.dysphagia}
                onChange={(e) => setForm((f) => ({ ...f, dysphagia: e.target.checked }))} />
              Dysphagia
            </label>
          </div>

          {formMessage && (
            <div style={{ fontSize: 12.5, color: COLORS.orange, marginBottom: 10 }}>{formMessage}</div>
          )}

          <button style={S.btn(COLORS.teal)} disabled={submitting} onClick={handleCreate}>
            {submitting ? "Recording…" : "Record F2F Encounter"}
          </button>
        </div>
      )}
      {!canPerform && (
        <div style={{ ...S.card, padding: 16, fontSize: 12.5, color: COLORS.dim }}>
          Only physician-level, NP, or PA users may record a new F2F encounter. You may still view existing
          encounters below.
        </div>
      )}

      <div style={{ ...S.card, padding: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, marginBottom: 12 }}>
          F2F Encounter History
        </div>
        {loading && <div style={{ color: COLORS.dim, fontSize: 13 }}>Loading…</div>}
        {error && <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 10 }}>{error}</div>}
        {!loading && encounters.length === 0 && (
          <div style={{ color: COLORS.dim, fontSize: 13 }}>No F2F encounters recorded for this patient yet.</div>
        )}
        {encounters.map((enc) => (
          <div
            key={enc.id}
            style={{
              padding: "10px 0",
              borderBottom: `1px solid ${COLORS.border}`,
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: COLORS.white }}>{enc.encounter_date}</span>
              <StatusBadge status={enc.status} label={enc.status_label} />
            </div>
            {enc.performed_by_name && (
              <div style={{ fontSize: 11, color: COLORS.dim }}>
                Performed by {enc.performed_by_name} ({enc.performed_by_role})
              </div>
            )}
            {enc.summary && <div style={{ fontSize: 12, color: COLORS.dim }}>{enc.summary}</div>}
            {enc.status === "DRAFT" && (enc.performed_by_role === "NP" || enc.performed_by_role === "PA") && (
              <div style={{ fontSize: 11, color: COLORS.dim }}>
                Requires physician-level review and attestation before finalization (Medical Director / Attending Physician / Hospice Physician).
              </div>
            )}
            {enc.status === "DRAFT" && canFinalizeEncounter(enc, currentUser?.role) && (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {(enc.performed_by_role === "NP" || enc.performed_by_role === "PA") && (
                  <div style={formGroup}>
                    <label style={label}>Physician Attestation Summary (required)</label>
                    <textarea
                      style={textarea}
                      value={attestationDrafts[enc.id] || ""}
                      onChange={(e) =>
                        setAttestationDrafts((prev) => ({ ...prev, [enc.id]: e.target.value }))
                      }
                      placeholder="Document physician review of the encounter and clinical justification for continued hospice eligibility…"
                    />
                  </div>
                )}
                <button style={S.btn(COLORS.green)} disabled={busyId === enc.id} onClick={() => handleFinalize(enc)}>
                  Finalize F2F
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
