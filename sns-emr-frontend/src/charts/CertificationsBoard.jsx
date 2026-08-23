import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { getCurrentUser } from "../api/session";
import { listBenefitPeriods } from "../api/benefitPeriods";
import {
  listCertifications,
  createCertDraft,
  updateCertNarrative,
  submitCertForSignature,
  signCertification,
} from "../api/certifications";

// Physician-level roles authorized to sign a CTI. Enforced server-side
// (certification_service.CTI_SIGNER_ROLES); mirrored here only to hide the
// Sign action for roles that would receive a 403 — never a security
// boundary by itself.
const CTI_SIGNER_ROLES = ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"];

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

const STATUS_COLORS = {
  DRAFT: COLORS.muted,
  PENDING_SIGNATURE: COLORS.orange,
  FINALIZED: COLORS.green,
  SUPERSEDED: COLORS.muted,
};

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

export default function CertificationsBoard({ patientId }) {
  const currentUser = getCurrentUser();
  const canSign = CTI_SIGNER_ROLES.includes(currentUser?.role);

  const [certs, setCerts] = useState([]);
  const [benefitPeriods, setBenefitPeriods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [formMessage, setFormMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    benefit_period_id: "",
    physician_narrative: "",
    supporting_evidence: "",
    clinical_decline_indicators: "",
  });

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    Promise.all([listCertifications(patientId), listBenefitPeriods(patientId)])
      .then(([certList, bpList]) => {
        setCerts(certList || []);
        setBenefitPeriods(bpList || []);
        setForm((f) => ({
          ...f,
          benefit_period_id: f.benefit_period_id || (bpList || []).find((bp) => bp.is_current)?.id || (bpList || [])[0]?.id || "",
        }));
      })
      .catch((err) => {
        console.error("Failed to load certifications:", err);
        setError(err?.response?.data?.detail || "Unable to load certifications.");
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => { reload(); }, [reload]);

  const handleCreateDraft = async () => {
    if (!form.benefit_period_id) {
      setFormMessage("Select a benefit period before creating a CTI draft.");
      return;
    }
    if (!form.physician_narrative.trim()) {
      setFormMessage("Physician narrative is required.");
      return;
    }
    setSubmitting(true);
    setFormMessage("");
    try {
      await createCertDraft(patientId, {
        benefit_period_id: form.benefit_period_id,
        physician_narrative: form.physician_narrative,
        supporting_evidence: form.supporting_evidence || undefined,
        clinical_decline_indicators: form.clinical_decline_indicators || undefined,
      });
      setForm((f) => ({ ...f, physician_narrative: "", supporting_evidence: "", clinical_decline_indicators: "" }));
      setFormMessage("CTI draft created.");
      reload();
    } catch (err) {
      console.error("Failed to create CTI draft:", err);
      setFormMessage(err?.response?.data?.detail || "Unable to create CTI draft.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitForSignature = async (cert) => {
    setBusyId(cert.id);
    setError("");
    try {
      await submitCertForSignature(cert.id);
      reload();
    } catch (err) {
      console.error("Failed to submit CTI for signature:", err);
      setError(err?.response?.data?.detail || "Unable to submit for signature.");
    } finally {
      setBusyId(null);
    }
  };

  const handleSign = async (cert) => {
    setBusyId(cert.id);
    setError("");
    try {
      await signCertification(cert.id);
      reload();
    } catch (err) {
      console.error("Failed to sign CTI:", err);
      setError(err?.response?.data?.detail || "Unable to sign certification.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ ...S.card, padding: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, marginBottom: 12 }}>
          Certification of Terminal Illness (CTI / Recert)
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
          <label style={label}>Physician Narrative</label>
          <textarea
            style={textarea}
            value={form.physician_narrative}
            onChange={(e) => setForm((f) => ({ ...f, physician_narrative: e.target.value }))}
            placeholder="Clinical narrative supporting terminal prognosis / continued eligibility…"
          />
        </div>

        <div style={formGroup}>
          <label style={label}>Supporting Evidence (LCD)</label>
          <textarea
            style={textarea}
            value={form.supporting_evidence}
            onChange={(e) => setForm((f) => ({ ...f, supporting_evidence: e.target.value }))}
            placeholder="LCD-aligned clinical evidence…"
          />
        </div>

        <div style={formGroup}>
          <label style={label}>Clinical Decline Indicators</label>
          <textarea
            style={textarea}
            value={form.clinical_decline_indicators}
            onChange={(e) => setForm((f) => ({ ...f, clinical_decline_indicators: e.target.value }))}
            placeholder="Objective decline indicators…"
          />
        </div>

        {formMessage && (
          <div style={{ fontSize: 12.5, color: COLORS.orange, marginBottom: 10 }}>{formMessage}</div>
        )}

        <button style={S.btn(COLORS.teal)} disabled={submitting} onClick={handleCreateDraft}>
          {submitting ? "Creating…" : "Create CTI Draft"}
        </button>
      </div>

      <div style={{ ...S.card, padding: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, marginBottom: 12 }}>
          Certification History
        </div>
        {loading && <div style={{ color: COLORS.dim, fontSize: 13 }}>Loading…</div>}
        {error && <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 10 }}>{error}</div>}
        {!loading && certs.length === 0 && (
          <div style={{ color: COLORS.dim, fontSize: 13 }}>No certifications recorded for this patient yet.</div>
        )}
        {certs.map((cert) => (
          <div
            key={cert.id}
            style={{
              padding: "10px 0",
              borderBottom: `1px solid ${COLORS.border}`,
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: COLORS.white }}>{cert.cert_type}</span>
              <StatusBadge status={cert.status} label={cert.status_label} />
            </div>
            {cert.physician_narrative && (
              <div style={{ fontSize: 12, color: COLORS.dim }}>{cert.physician_narrative}</div>
            )}
            {cert.signed_by_name && (
              <div style={{ fontSize: 11, color: COLORS.dim }}>
                Signed by {cert.signed_by_name} ({cert.signed_by_role}) on {cert.signed_at}
              </div>
            )}
            <div style={{ display: "flex", gap: 8 }}>
              {cert.status === "DRAFT" && (
                <button
                  style={S.btnOutline}
                  disabled={busyId === cert.id}
                  onClick={() => handleSubmitForSignature(cert)}
                >
                  Submit for Signature
                </button>
              )}
              {cert.status === "PENDING_SIGNATURE" && canSign && (
                <button style={S.btn(COLORS.green)} disabled={busyId === cert.id} onClick={() => handleSign(cert)}>
                  Sign (Physician)
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
