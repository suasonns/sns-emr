import React, { useCallback, useEffect, useMemo, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { fetchBereavementRiskCatalog, listBereavementAssessments } from "../api/bereavement";
import { listBereavementPOCs } from "../api/bereavementPoc";
import {
  listPostDeathBereavement,
  createPostDeathBereavement,
  updatePostDeathBereavement,
  signPostDeathBereavement,
  fetchPostDeathBereavementDefaults,
} from "../api/postDeathBereavement";

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
const textarea = { ...input, minHeight: 90, resize: "vertical", fontFamily: "inherit" };
const label = { fontSize: 11, fontWeight: 600, color: COLORS.dim, textTransform: "uppercase", marginBottom: 4, display: "block" };
const formGroup = { marginBottom: 12 };
const grid2 = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 };
const grid3 = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 };
const riskItemsGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "4px 20px" };

const RISK_LEVEL_COLOR = {
  LOW: COLORS.green,
  MODERATE: COLORS.orange,
  HIGH: COLORS.red,
};

const PLACE_OF_DEATH_OPTIONS = [
  { value: "HOME", label: "Home" },
  { value: "INPATIENT_HOSPICE", label: "Inpatient Hospice Unit" },
  { value: "HOSPITAL", label: "Hospital" },
  { value: "NURSING_FACILITY", label: "Nursing Facility" },
  { value: "OTHER", label: "Other" },
];

function emptyForm(patientId) {
  return {
    patient_id: patientId,
    bereavement_assessment_id: null,
    bereavement_poc_id: null,
    staff_assigned: null,
    discipline: "MSW",
    visit_type: "IN_PERSON",
    visit_mode: "UNSCHEDULED",
    visit_date: new Date().toISOString().slice(0, 10),
    time_in: "",
    time_out: "",
    duration_minutes: null,

    no_family: false,
    primary_first_name: "",
    primary_last_name: "",
    primary_relationship_to_patient: "",
    primary_address: "",
    primary_city: "",
    primary_state: "",
    primary_zip: "",
    primary_home_phone: "",
    primary_cell_phone: "",
    primary_email: "",
    primary_was_caregiver: null,

    date_of_death: "",
    place_of_death: "",
    death_expected: null,
    pcg_present_at_death: null,
    family_present_at_death: null,
    funeral_plans_finalized: null,
    funeral_home_name: "",

    condolence_call_date: "",
    condolence_call_by: null,
    condolence_call_notes: "",

    emotional_status_narrative: "",

    survivor_support_system_adequate: null,
    desires_intensive_bereavement_support: null,
    complicated_grief_reactions_observed: null,
    additional_risk_factors_since_initial: null,
    additional_risk_notes: "",

    risk_items: {},
    risk_other_note: "",

    goals: [],
    interventions: [],
    other_interventions: "",
    plan_of_care_narrative: "",

    narrative: "",
  };
}

function RiskChecklistGroup({ title, points, items, riskItems, onToggle, onNote, disabled }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase", marginBottom: 8 }}>
        {title} <span style={{ color: COLORS.teal }}>({points} pt{points > 1 ? "s" : ""} each)</span>
      </div>
      <div style={riskItemsGrid}>
        {items.map((item) => {
          const entry = riskItems[item.key] || { checked: false, note: "" };
          return (
            <div key={item.key} style={{ marginBottom: 8 }}>
              <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: disabled ? "default" : "pointer" }}>
                <input
                  type="checkbox"
                  checked={Boolean(entry.checked)}
                  disabled={disabled}
                  onChange={(e) => onToggle(item.key, e.target.checked)}
                  style={{ marginTop: 2 }}
                />
                <span>
                  {item.label}
                  {item.note_hint && <span style={{ color: COLORS.dim, fontSize: 11 }}> — {item.note_hint}</span>}
                </span>
              </label>
              {(item.requires_note || item.note_hint) && entry.checked && (
                <input
                  style={{ ...input, marginTop: 6, marginLeft: 24, width: "calc(100% - 24px)" }}
                  disabled={disabled}
                  placeholder={item.requires_note ? "Specify…" : "Notes…"}
                  value={entry.note || ""}
                  onChange={(e) => onNote(item.key, e.target.value)}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function PostDeathBereavementBoard({ patientId }) {
  const [catalog, setCatalog] = useState([]);
  const [records, setRecords] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [pocs, setPOCs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [view, setView] = useState("list"); // "list" | "form"
  const [activeRecord, setActiveRecord] = useState(null); // null => new
  const [form, setForm] = useState(emptyForm(patientId));
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [catalogData, recordData, assessmentData, pocData] = await Promise.all([
        fetchBereavementRiskCatalog(),
        listPostDeathBereavement(patientId),
        listBereavementAssessments(patientId),
        listBereavementPOCs(patientId),
      ]);
      setCatalog(catalogData);
      setRecords(recordData);
      setAssessments(assessmentData);
      setPOCs(pocData);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load post-death bereavement assessments.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const grouped = useMemo(() => {
    const byPoints = { 10: [], 5: [], 2: [], 1: [] };
    catalog.forEach((item) => {
      if (byPoints[item.points]) byPoints[item.points].push(item);
    });
    return byPoints;
  }, [catalog]);

  const { totalScore, riskLevel } = useMemo(() => {
    let total = 0;
    let forcesHigh = false;
    catalog.forEach((item) => {
      const entry = form.risk_items[item.key];
      if (entry?.checked) {
        total += item.points;
        if (item.points === 10) forcesHigh = true;
      }
    });
    let level = "LOW";
    if (forcesHigh || total >= 10) level = "HIGH";
    else if (total >= 5) level = "MODERATE";
    return { totalScore: total, riskLevel: level };
  }, [catalog, form.risk_items]);

  const mostRecentAssessment = assessments[0] || null;
  const mostRecentPOC = pocs[0] || null;

  const openNew = async () => {
    setError("");
    setMessage("");
    const seedForm = {
      ...emptyForm(patientId),
      bereavement_assessment_id: mostRecentAssessment?.id || null,
      bereavement_poc_id: mostRecentPOC?.id || null,
      date_of_death: mostRecentPOC?.date_of_death || "",
    };
    setActiveRecord(null);
    setForm(seedForm);
    setView("form");
    try {
      const defaults = await fetchPostDeathBereavementDefaults("LOW");
      setForm((prev) => ({ ...prev, ...defaults }));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load default plan.");
    }
  };

  const openExisting = (record) => {
    setActiveRecord(record);
    setForm({
      ...record,
      patient_id: patientId,
      visit_date: record.visit_date || "",
      date_of_death: record.date_of_death || "",
      condolence_call_date: record.condolence_call_date || "",
    });
    setMessage("");
    setError("");
    setView("form");
  };

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const toggleRiskItem = (key, checked) => {
    setForm((prev) => ({
      ...prev,
      risk_items: { ...prev.risk_items, [key]: { ...(prev.risk_items[key] || {}), checked } },
    }));
  };
  const noteRiskItem = (key, note) => {
    setForm((prev) => ({
      ...prev,
      risk_items: { ...prev.risk_items, [key]: { ...(prev.risk_items[key] || {}), note } },
    }));
  };

  const toggleGoal = (idx, selected) =>
    setForm((prev) => {
      const next = [...prev.goals];
      next[idx] = { ...next[idx], selected };
      return { ...prev, goals: next };
    });
  const updateGoalField = (idx, field, value) =>
    setForm((prev) => {
      const next = [...prev.goals];
      next[idx] = { ...next[idx], [field]: value };
      return { ...prev, goals: next };
    });
  const toggleIntervention = (idx, selected) =>
    setForm((prev) => {
      const next = [...prev.interventions];
      next[idx] = { ...next[idx], selected };
      return { ...prev, interventions: next };
    });

  const isLocked = activeRecord?.status === "SIGNED";

  const regeneratePlan = async () => {
    try {
      const defaults = await fetchPostDeathBereavementDefaults(riskLevel || "LOW");
      setForm((prev) => ({ ...prev, ...defaults }));
      setMessage("Standard risk-level plan regenerated. Review before saving.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to regenerate plan.");
    }
  };

  const buildPayload = () => ({
    bereavement_assessment_id: form.bereavement_assessment_id || null,
    bereavement_poc_id: form.bereavement_poc_id || null,
    staff_assigned: form.staff_assigned || null,
    discipline: form.discipline || null,
    visit_type: form.visit_type || null,
    visit_mode: form.visit_mode || null,
    visit_date: form.visit_date || null,
    time_in: form.time_in || null,
    time_out: form.time_out || null,
    duration_minutes: form.duration_minutes || null,

    no_family: Boolean(form.no_family),
    primary_first_name: form.primary_first_name || null,
    primary_last_name: form.primary_last_name || null,
    primary_relationship_to_patient: form.primary_relationship_to_patient || null,
    primary_address: form.primary_address || null,
    primary_city: form.primary_city || null,
    primary_state: form.primary_state || null,
    primary_zip: form.primary_zip || null,
    primary_home_phone: form.primary_home_phone || null,
    primary_cell_phone: form.primary_cell_phone || null,
    primary_email: form.primary_email || null,
    primary_was_caregiver: form.primary_was_caregiver,

    date_of_death: form.date_of_death || null,
    place_of_death: form.place_of_death || null,
    death_expected: form.death_expected,
    pcg_present_at_death: form.pcg_present_at_death,
    family_present_at_death: form.family_present_at_death,
    funeral_plans_finalized: form.funeral_plans_finalized,
    funeral_home_name: form.funeral_home_name || null,

    condolence_call_date: form.condolence_call_date || null,
    condolence_call_by: form.condolence_call_by || null,
    condolence_call_notes: form.condolence_call_notes || null,

    emotional_status_narrative: form.emotional_status_narrative || null,

    survivor_support_system_adequate: form.survivor_support_system_adequate,
    desires_intensive_bereavement_support: form.desires_intensive_bereavement_support,
    complicated_grief_reactions_observed: form.complicated_grief_reactions_observed,
    additional_risk_factors_since_initial: form.additional_risk_factors_since_initial,
    additional_risk_notes: form.additional_risk_notes || null,

    risk_items: form.risk_items,
    risk_other_note: form.risk_other_note || null,

    goals: form.goals,
    interventions: form.interventions,
    other_interventions: form.other_interventions || null,
    plan_of_care_narrative: form.plan_of_care_narrative || null,

    narrative: form.narrative || null,
  });

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      if (activeRecord) {
        const updated = await updatePostDeathBereavement(activeRecord.id, buildPayload());
        setActiveRecord(updated);
        setForm({ ...updated, patient_id: patientId });
      } else {
        const created = await createPostDeathBereavement({ patient_id: patientId, ...buildPayload() });
        setActiveRecord(created);
        setForm({ ...created, patient_id: patientId });
      }
      setMessage("Post-death bereavement assessment saved.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to save assessment.");
    } finally {
      setSaving(false);
    }
  };

  const handleSign = async () => {
    if (!activeRecord) return;
    setSigning(true);
    setError("");
    try {
      const signed = await signPostDeathBereavement(activeRecord.id);
      setActiveRecord(signed);
      setForm({ ...signed, patient_id: patientId });
      setMessage("Post-death bereavement assessment electronically signed and locked.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to sign assessment.");
    } finally {
      setSigning(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 24, color: COLORS.dim, fontSize: 13 }}>Loading post-death bereavement assessments…</div>;
  }

  if (view === "list") {
    return (
      <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Post-Death Bereavement Assessment</h2>
            <p style={{ color: COLORS.dim, fontSize: 13, margin: 0 }}>
              Death facts, condolence-call follow-up, and grief risk re-assessment conducted after the patient's death.
            </p>
          </div>
          <button type="button" style={S.btn(COLORS.teal)} onClick={openNew}>
            + Add New Assessment
          </button>
        </div>

        {error && (
          <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={S.card}>
          {records.length === 0 ? (
            <div style={{ color: COLORS.dim, fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No post-death bereavement assessments on file yet.
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={S.tableHeader}>Date Assessed</th>
                  <th style={S.tableHeader}>Date of Death</th>
                  <th style={S.tableHeader}>Primary Bereaved</th>
                  <th style={S.tableHeader}>Risk Level</th>
                  <th style={S.tableHeader}>Status</th>
                  <th style={S.tableHeader} />
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td style={S.tableCell}>{r.visit_date || r.created_at?.slice(0, 10)}</td>
                    <td style={S.tableCell}>{r.date_of_death || "—"}</td>
                    <td style={S.tableCell}>
                      {r.no_family ? "No family" : [r.primary_first_name, r.primary_last_name].filter(Boolean).join(" ") || "—"}
                    </td>
                    <td style={S.tableCell}>
                      {r.risk_level ? (
                        <span style={S.badge(`${RISK_LEVEL_COLOR[r.risk_level]}22`, RISK_LEVEL_COLOR[r.risk_level])}>
                          {r.risk_level} ({r.risk_total_score})
                        </span>
                      ) : "—"}
                    </td>
                    <td style={S.tableCell}>
                      <span style={S.badge(r.status === "SIGNED" ? `${COLORS.teal}22` : `${COLORS.dim}22`, r.status === "SIGNED" ? COLORS.teal : COLORS.dim)}>
                        {r.status}
                      </span>
                    </td>
                    <td style={S.tableCell}>
                      <button type="button" style={S.btnOutline} onClick={() => openExisting(r)}>
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 20, maxWidth: 1800, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: COLORS.white, fontSize: 18, margin: 0 }}>Post-Death Bereavement Assessment</h2>
        <button type="button" style={S.btnOutline} onClick={() => setView("list")}>
          ← Back to history
        </button>
      </div>

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
      {isLocked && (
        <div style={{ background: `${COLORS.teal}22`, border: `1px solid ${COLORS.teal}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.teal, fontSize: 13 }}>
          Electronically signed{activeRecord?.signed_at ? ` on ${new Date(activeRecord.signed_at).toLocaleDateString()}` : ""}. This assessment is locked.
        </div>
      )}

      {/* Visit metadata */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Visit Details</h3>
        <div style={grid3}>
          <div style={formGroup}>
            <label style={label}>Discipline</label>
            <select style={input} disabled={isLocked} value={form.discipline || ""} onChange={(e) => updateField("discipline", e.target.value)}>
              <option value="MSW">MSW</option>
              <option value="BSW">BSW</option>
              <option value="RN">RN</option>
              <option value="Chaplain">Chaplain</option>
            </select>
          </div>
          <div style={formGroup}>
            <label style={label}>Visit Date</label>
            <input type="date" style={input} disabled={isLocked} value={form.visit_date || ""} onChange={(e) => updateField("visit_date", e.target.value)} />
          </div>
          <div style={formGroup}>
            <label style={label}>Visit Type</label>
            <select style={input} disabled={isLocked} value={form.visit_type || ""} onChange={(e) => updateField("visit_type", e.target.value)}>
              <option value="IN_PERSON">In-Person</option>
              <option value="TELEPHONE">Telephone</option>
            </select>
          </div>
        </div>
        {(form.bereavement_assessment_id || form.bereavement_poc_id) && (
          <div style={{ fontSize: 12, color: COLORS.dim, marginTop: 4 }}>
            {form.bereavement_assessment_id && "Linked to a Comprehensive Bereavement Assessment on file. "}
            {form.bereavement_poc_id && "Linked to a Bereavement Plan of Care on file."}
          </div>
        )}
      </div>

      {/* Death facts */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Death Facts</h3>
        <div style={grid3}>
          <div style={formGroup}>
            <label style={label}>Date of Death</label>
            <input type="date" style={input} disabled={isLocked} value={form.date_of_death || ""} onChange={(e) => updateField("date_of_death", e.target.value)} />
          </div>
          <div style={formGroup}>
            <label style={label}>Place of Death</label>
            <select style={input} disabled={isLocked} value={form.place_of_death || ""} onChange={(e) => updateField("place_of_death", e.target.value)}>
              <option value="">Select…</option>
              {PLACE_OF_DEATH_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div style={formGroup}>
            <label style={label}>Funeral Home</label>
            <input style={input} disabled={isLocked} value={form.funeral_home_name || ""} onChange={(e) => updateField("funeral_home_name", e.target.value)} />
          </div>
        </div>
        <div style={grid3}>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.death_expected)} disabled={isLocked} onChange={(e) => updateField("death_expected", e.target.checked)} />
            <span>Death was expected</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.pcg_present_at_death)} disabled={isLocked} onChange={(e) => updateField("pcg_present_at_death", e.target.checked)} />
            <span>Primary caregiver present at death</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.family_present_at_death)} disabled={isLocked} onChange={(e) => updateField("family_present_at_death", e.target.checked)} />
            <span>Family present at death</span>
          </label>
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer", marginTop: 8 }}>
          <input type="checkbox" checked={Boolean(form.funeral_plans_finalized)} disabled={isLocked} onChange={(e) => updateField("funeral_plans_finalized", e.target.checked)} />
          <span>Funeral / memorial plans finalized</span>
        </label>
      </div>

      {/* Condolence call */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Condolence Call</h3>
        <div style={grid3}>
          <div style={formGroup}>
            <label style={label}>Call Date</label>
            <input type="date" style={input} disabled={isLocked} value={form.condolence_call_date || ""} onChange={(e) => updateField("condolence_call_date", e.target.value)} />
          </div>
        </div>
        <div style={formGroup}>
          <label style={label}>Call Notes</label>
          <textarea style={textarea} disabled={isLocked} value={form.condolence_call_notes || ""} onChange={(e) => updateField("condolence_call_notes", e.target.value)} placeholder="Summary of the condolence call — how the family is coping, any concerns raised…" />
        </div>
      </div>

      {/* Primary bereaved contact */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 4px" }}>Primary Bereaved Contact</h3>
        {(form.bereavement_assessment_id || form.bereavement_poc_id) && (
          <p style={{ fontSize: 11, color: COLORS.dim, margin: "0 0 12px" }}>
            Synced from the linked assessment/POC. Editing here overrides this record only.
          </p>
        )}
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer", marginBottom: 12 }}>
          <input type="checkbox" checked={Boolean(form.no_family)} disabled={isLocked} onChange={(e) => updateField("no_family", e.target.checked)} />
          <span>No surviving family / next of kin on file</span>
        </label>
        {!form.no_family && (
          <>
            <div style={grid3}>
              <div style={formGroup}>
                <label style={label}>First Name</label>
                <input style={input} disabled={isLocked} value={form.primary_first_name || ""} onChange={(e) => updateField("primary_first_name", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Last Name</label>
                <input style={input} disabled={isLocked} value={form.primary_last_name || ""} onChange={(e) => updateField("primary_last_name", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Relationship to Patient</label>
                <input style={input} disabled={isLocked} value={form.primary_relationship_to_patient || ""} onChange={(e) => updateField("primary_relationship_to_patient", e.target.value)} placeholder="e.g. spouse, daughter" />
              </div>
            </div>
            <div style={grid3}>
              <div style={formGroup}>
                <label style={label}>Home Phone</label>
                <input style={input} disabled={isLocked} value={form.primary_home_phone || ""} onChange={(e) => updateField("primary_home_phone", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Cell Phone</label>
                <input style={input} disabled={isLocked} value={form.primary_cell_phone || ""} onChange={(e) => updateField("primary_cell_phone", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Email</label>
                <input style={input} disabled={isLocked} value={form.primary_email || ""} onChange={(e) => updateField("primary_email", e.target.value)} />
              </div>
            </div>
            <div style={grid3}>
              <div style={formGroup}>
                <label style={label}>Address</label>
                <input style={input} disabled={isLocked} value={form.primary_address || ""} onChange={(e) => updateField("primary_address", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>City</label>
                <input style={input} disabled={isLocked} value={form.primary_city || ""} onChange={(e) => updateField("primary_city", e.target.value)} />
              </div>
              <div style={{ ...formGroup, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <div>
                  <label style={label}>State</label>
                  <input style={input} disabled={isLocked} value={form.primary_state || ""} onChange={(e) => updateField("primary_state", e.target.value)} />
                </div>
                <div>
                  <label style={label}>Zip</label>
                  <input style={input} disabled={isLocked} value={form.primary_zip || ""} onChange={(e) => updateField("primary_zip", e.target.value)} />
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Emotional status */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Emotional Status &amp; Coping</h3>
        <textarea
          style={textarea}
          disabled={isLocked}
          value={form.emotional_status_narrative || ""}
          onChange={(e) => updateField("emotional_status_narrative", e.target.value)}
          placeholder="Describe the bereaved's current emotional state, coping mechanisms, and support system…"
        />
      </div>

      {/* Risk re-assessment */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>Grief Risk Re-Assessment</h3>
          <span style={S.badge(`${RISK_LEVEL_COLOR[riskLevel]}22`, RISK_LEVEL_COLOR[riskLevel])}>
            {riskLevel} (score: {totalScore})
          </span>
        </div>
        <p style={{ fontSize: 11, color: COLORS.dim, margin: "0 0 12px" }}>
          Re-scored independently using the same weighted checklist as the Initial Assessment — grief risk commonly shifts after the death itself.
          {mostRecentAssessment?.risk_level && (
            <> Initial assessment risk level was <strong>{mostRecentAssessment.risk_level}</strong> ({mostRecentAssessment.risk_total_score}).</>
          )}
        </p>
        <RiskChecklistGroup title="Critical / Safety Concerns" points={10} items={grouped[10]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} disabled={isLocked} />
        <RiskChecklistGroup title="Significant Risk Factors" points={5} items={grouped[5]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} disabled={isLocked} />
        <RiskChecklistGroup title="Moderate Risk Factors" points={2} items={grouped[2]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} disabled={isLocked} />
        <RiskChecklistGroup title="Contributing Factors" points={1} items={grouped[1]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} disabled={isLocked} />
        <div style={formGroup}>
          <label style={label}>Other Risk Factors (specify)</label>
          <textarea style={textarea} disabled={isLocked} value={form.risk_other_note || ""} onChange={(e) => updateField("risk_other_note", e.target.value)} />
        </div>

        <div style={grid2}>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.survivor_support_system_adequate)} disabled={isLocked} onChange={(e) => updateField("survivor_support_system_adequate", e.target.checked)} />
            <span>Support system appears adequate</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.desires_intensive_bereavement_support)} disabled={isLocked} onChange={(e) => updateField("desires_intensive_bereavement_support", e.target.checked)} />
            <span>Desires more intensive bereavement support</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.complicated_grief_reactions_observed)} disabled={isLocked} onChange={(e) => updateField("complicated_grief_reactions_observed", e.target.checked)} />
            <span>Complicated grief reactions observed</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
            <input type="checkbox" checked={Boolean(form.additional_risk_factors_since_initial)} disabled={isLocked} onChange={(e) => updateField("additional_risk_factors_since_initial", e.target.checked)} />
            <span>Additional risk factors emerged since initial assessment</span>
          </label>
        </div>
        {form.additional_risk_factors_since_initial && (
          <div style={{ ...formGroup, marginTop: 8 }}>
            <label style={label}>Additional Risk Notes</label>
            <textarea style={textarea} disabled={isLocked} value={form.additional_risk_notes || ""} onChange={(e) => updateField("additional_risk_notes", e.target.value)} />
          </div>
        )}
      </div>

      {/* Goals */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>Goals</h3>
          {!isLocked && (
            <button type="button" style={S.btnOutline} onClick={regeneratePlan}>
              Reset to Standard Plan for {riskLevel} Risk
            </button>
          )}
        </div>
        {form.goals.map((g, idx) => (
          <div key={g.key} style={{ marginBottom: 10 }}>
            <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer" }}>
              <input type="checkbox" checked={Boolean(g.selected)} disabled={isLocked} onChange={(e) => toggleGoal(idx, e.target.checked)} style={{ marginTop: 2 }} />
              <span>{g.label}</span>
            </label>
            {g.selected && (
              <div style={{ ...grid2, marginTop: 6, marginLeft: 24, width: "calc(100% - 24px)" }}>
                <input type="date" style={input} disabled={isLocked} value={g.target_date || ""} onChange={(e) => updateGoalField(idx, "target_date", e.target.value)} placeholder="Target date" />
                <input style={input} disabled={isLocked} value={g.notes || ""} onChange={(e) => updateGoalField(idx, "notes", e.target.value)} placeholder="Notes…" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Interventions */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Interventions</h3>
        {form.interventions.map((iv, idx) => (
          <label key={iv.key} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: isLocked ? "default" : "pointer", marginBottom: 8 }}>
            <input type="checkbox" checked={Boolean(iv.selected)} disabled={isLocked} onChange={(e) => toggleIntervention(idx, e.target.checked)} style={{ marginTop: 2 }} />
            <span>{iv.label}</span>
          </label>
        ))}
        <div style={{ ...formGroup, marginTop: 8 }}>
          <label style={label}>Other Interventions (specify)</label>
          <textarea style={textarea} disabled={isLocked} value={form.other_interventions || ""} onChange={(e) => updateField("other_interventions", e.target.value)} placeholder="Describe any additional intervention not listed above…" />
        </div>
      </div>

      {/* Plan of care narrative */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Plan of Care Notes</h3>
        <textarea
          style={{ ...textarea, minHeight: 120 }}
          disabled={isLocked}
          value={form.plan_of_care_narrative || ""}
          onChange={(e) => updateField("plan_of_care_narrative", e.target.value)}
          placeholder="Additional plan-of-care detail specific to this reassessment…"
        />
      </div>

      {/* Narrative */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Narrative</h3>
        <textarea
          style={{ ...textarea, minHeight: 120 }}
          disabled={isLocked}
          value={form.narrative || ""}
          onChange={(e) => updateField("narrative", e.target.value)}
          placeholder="Additional context, referrals made, follow-up plans…"
        />
      </div>

      {!isLocked && (
        <div style={{ display: "flex", gap: 10 }}>
          <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={handleSave}>
            {saving ? "Saving…" : "Save"}
          </button>
          {activeRecord && (
            <button type="button" style={S.btn(COLORS.purple)} disabled={signing} onClick={handleSign}>
              {signing ? "Signing…" : "Sign & Lock"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
