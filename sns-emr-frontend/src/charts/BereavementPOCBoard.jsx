import React, { useCallback, useEffect, useMemo, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { listBereavementAssessments } from "../api/bereavement";
import {
  listBereavementPOCs,
  createBereavementPOC,
  updateBereavementPOC,
  signBereavementPOC,
  fetchBereavementPOCDefaults,
} from "../api/bereavementPoc";

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

const RISK_LEVEL_COLOR = {
  LOW: COLORS.green,
  MODERATE: COLORS.orange,
  HIGH: COLORS.red,
};

function emptyForm(patientId) {
  return {
    patient_id: patientId,
    bereavement_assessment_id: null,
    staff_assigned: null,
    discipline: "MSW",
    date_of_death: "",
    risk_level: "LOW",
    risk_source: null,
    risk_score: null,
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
    goals: [],
    interventions: [],
    other_interventions: "",
    action_plan: [],
    narrative: "",
    closed_early: false,
    closed_reason: "",
  };
}

export default function BereavementPOCBoard({ patientId }) {
  const [pocs, setPOCs] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [view, setView] = useState("list"); // "list" | "form"
  const [activePOC, setActivePOC] = useState(null); // null => new
  const [form, setForm] = useState(emptyForm(patientId));
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [pocData, assessmentData] = await Promise.all([
        listBereavementPOCs(patientId),
        listBereavementAssessments(patientId),
      ]);
      setPOCs(pocData);
      setAssessments(assessmentData);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load bereavement POCs.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const mostRecentAssessment = assessments[0] || null;

  const openNew = async () => {
    setError("");
    setMessage("");
    const seedRiskLevel = mostRecentAssessment?.risk_level || "LOW";
    const seedForm = {
      ...emptyForm(patientId),
      bereavement_assessment_id: mostRecentAssessment?.id || null,
      risk_level: seedRiskLevel,
    };
    setActivePOC(null);
    setForm(seedForm);
    setView("form");
    try {
      const defaults = await fetchBereavementPOCDefaults(seedRiskLevel, null);
      setForm((prev) => ({ ...prev, ...defaults }));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load default POC plan.");
    }
  };

  const openExisting = (poc) => {
    setActivePOC(poc);
    setForm({ ...poc, patient_id: patientId, date_of_death: poc.date_of_death || "" });
    setMessage("");
    setError("");
    setView("form");
  };

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

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

  const updateContact = (idx, field, value) =>
    setForm((prev) => {
      const next = [...prev.action_plan];
      next[idx] = { ...next[idx], [field]: value };
      return { ...prev, action_plan: next };
    });

  const isLocked = activePOC?.status === "SIGNED";

  const regeneratePlan = async () => {
    setRegenerating(true);
    setError("");
    try {
      const defaults = await fetchBereavementPOCDefaults(form.risk_level || "LOW", form.date_of_death || null);
      setForm((prev) => ({ ...prev, ...defaults }));
      setMessage("Standard risk-level plan regenerated. Review before saving.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to regenerate plan.");
    } finally {
      setRegenerating(false);
    }
  };

  const buildPayload = () => ({
    bereavement_assessment_id: form.bereavement_assessment_id || null,
    staff_assigned: form.staff_assigned || null,
    discipline: form.discipline || null,
    date_of_death: form.date_of_death || null,
    risk_level: form.risk_level || null,
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
    goals: form.goals,
    interventions: form.interventions,
    other_interventions: form.other_interventions || null,
    action_plan: form.action_plan,
    narrative: form.narrative || null,
    closed_early: Boolean(form.closed_early),
    closed_reason: form.closed_reason || null,
  });

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      if (activePOC) {
        const updated = await updateBereavementPOC(activePOC.id, buildPayload());
        setActivePOC(updated);
        setForm({ ...updated, patient_id: patientId, date_of_death: updated.date_of_death || "" });
      } else {
        const created = await createBereavementPOC({ patient_id: patientId, ...buildPayload() });
        setActivePOC(created);
        setForm({ ...created, patient_id: patientId, date_of_death: created.date_of_death || "" });
      }
      setMessage("Bereavement POC saved.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to save POC.");
    } finally {
      setSaving(false);
    }
  };

  const handleSign = async () => {
    if (!activePOC) return;
    setSigning(true);
    setError("");
    try {
      const signed = await signBereavementPOC(activePOC.id);
      setActivePOC(signed);
      setForm({ ...signed, patient_id: patientId, date_of_death: signed.date_of_death || "" });
      setMessage("Bereavement POC electronically signed and locked.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to sign POC.");
    } finally {
      setSigning(false);
    }
  };

  const activePlanEntries = useMemo(
    () => form.action_plan.filter((a) => a.required !== false || a.included),
    [form.action_plan]
  );
  const completedCount = useMemo(
    () => activePlanEntries.filter((a) => Boolean(a.completed_date)).length,
    [activePlanEntries]
  );

  if (loading) {
    return <div style={{ padding: 24, color: COLORS.dim, fontSize: 13 }}>Loading bereavement POCs…</div>;
  }

  if (view === "list") {
    return (
      <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Bereavement Plan of Care (POC)</h2>
            <p style={{ color: COLORS.dim, fontSize: 13, margin: 0 }}>
              Risk-tiered goals, interventions, and the 13-month bereavement follow-up contact schedule required by CMS COPs §418.64(d).
            </p>
          </div>
          <button type="button" style={S.btn(COLORS.teal)} onClick={openNew}>
            + Add New POC
          </button>
        </div>

        {error && (
          <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={S.card}>
          {pocs.length === 0 ? (
            <div style={{ color: COLORS.dim, fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No bereavement POCs on file yet.
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={S.tableHeader}>Created</th>
                  <th style={S.tableHeader}>Date of Death</th>
                  <th style={S.tableHeader}>Risk Level</th>
                  <th style={S.tableHeader}>Contacts Completed</th>
                  <th style={S.tableHeader}>Status</th>
                  <th style={S.tableHeader} />
                </tr>
              </thead>
              <tbody>
                {pocs.map((p) => (
                  <tr key={p.id}>
                    <td style={S.tableCell}>{p.created_at?.slice(0, 10)}</td>
                    <td style={S.tableCell}>{p.date_of_death || "—"}</td>
                    <td style={S.tableCell}>
                      {p.risk_level ? (
                        <span style={S.badge(`${RISK_LEVEL_COLOR[p.risk_level]}22`, RISK_LEVEL_COLOR[p.risk_level])}>
                          {p.risk_level}
                        </span>
                      ) : "—"}
                      {p.risk_level && (
                        <span style={{ marginLeft: 6, fontSize: 10, color: p.risk_source === "SCORED" ? COLORS.teal : COLORS.dim }}>
                          {p.risk_source === "SCORED" ? "Scored" : "Manual"}
                        </span>
                      )}
                    </td>
                    <td style={S.tableCell}>
                      {p.action_plan.filter((a) => (a.required !== false || a.included) && a.completed_date).length}
                      {" / "}
                      {p.action_plan.filter((a) => a.required !== false || a.included).length}
                    </td>
                    <td style={S.tableCell}>
                      <span style={S.badge(p.status === "SIGNED" ? `${COLORS.teal}22` : `${COLORS.dim}22`, p.status === "SIGNED" ? COLORS.teal : COLORS.dim)}>
                        {p.status}
                      </span>
                    </td>
                    <td style={S.tableCell}>
                      <button type="button" style={S.btnOutline} onClick={() => openExisting(p)}>
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
        <h2 style={{ color: COLORS.white, fontSize: 18, margin: 0 }}>Bereavement Plan of Care</h2>
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
          Electronically signed{activePOC?.signed_at ? ` on ${new Date(activePOC.signed_at).toLocaleDateString()}` : ""}. This POC is locked.
        </div>
      )}

      {/* Plan basis */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Plan Basis</h3>
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
            <label style={label}>Date of Death</label>
            <input type="date" style={input} disabled={isLocked} value={form.date_of_death || ""} onChange={(e) => updateField("date_of_death", e.target.value)} />
          </div>
          <div style={formGroup}>
            <label style={label}>Risk Level</label>
            <select style={input} disabled={isLocked} value={form.risk_level || "LOW"} onChange={(e) => updateField("risk_level", e.target.value)}>
              <option value="LOW">Low</option>
              <option value="MODERATE">Moderate</option>
              <option value="HIGH">High</option>
            </select>
          </div>
        </div>
        {form.bereavement_assessment_id && (
          <div style={{ fontSize: 12, color: COLORS.dim, marginTop: 4 }}>
            Linked to a Comprehensive Bereavement Assessment on file.
          </div>
        )}
        {form.risk_source === "SCORED" ? (
          <div style={{ fontSize: 12, color: COLORS.teal, marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={S.badge(`${COLORS.teal}22`, COLORS.teal)}>✓ Scored</span>
            Risk level derived from linked assessment (score: {form.risk_score ?? "—"}/10). Not a subjective staff guess.
          </div>
        ) : form.risk_source === "MANUAL" ? (
          <div style={{ fontSize: 12, color: COLORS.orange, marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={S.badge(`${COLORS.orange}22`, COLORS.orange)}>⚠ Manual</span>
            Risk level was hand-picked, not derived from a scored Bereavement Assessment. Link or complete an assessment for an objective score.
          </div>
        ) : null}
        {!isLocked && (
          <button type="button" style={{ ...S.btnOutline, marginTop: 12 }} disabled={regenerating} onClick={regeneratePlan}>
            {regenerating ? "Regenerating…" : "Reset to Standard Plan for This Risk Level"}
          </button>
        )}
      </div>

      {/* Primary bereaved contact */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 4px" }}>Primary Bereaved Contact</h3>
        {form.bereavement_assessment_id && (
          <p style={{ fontSize: 11, color: COLORS.dim, margin: "0 0 12px" }}>
            Synced from the linked Comprehensive Bereavement Assessment. Editing here overrides this POC only.
          </p>
        )}
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: "pointer", marginBottom: 12 }}>
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
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.white, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={Boolean(form.primary_was_caregiver)}
                disabled={isLocked}
                onChange={(e) => updateField("primary_was_caregiver", e.target.checked)}
              />
              <span>Was the primary bereaved patient's caregiver</span>
            </label>
          </>
        )}
      </div>

      {/* Goals */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Goals</h3>
        {form.goals.map((g, idx) => (
          <div key={g.key} style={{ marginBottom: 10 }}>
            <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: "pointer" }}>
              <input type="checkbox" checked={Boolean(g.selected)} disabled={isLocked} onChange={(e) => toggleGoal(idx, e.target.checked)} style={{ marginTop: 2 }} />
              <span>{g.label}</span>
            </label>
            {g.selected && (
              <div style={{ ...grid2, marginTop: 6, marginLeft: 24, width: "calc(100% - 24px)" }}>
                <input
                  type="date"
                  style={input}
                  disabled={isLocked}
                  value={g.target_date || ""}
                  onChange={(e) => updateGoalField(idx, "target_date", e.target.value)}
                  placeholder="Target date"
                />
                <input
                  style={input}
                  disabled={isLocked}
                  value={g.notes || ""}
                  onChange={(e) => updateGoalField(idx, "notes", e.target.value)}
                  placeholder="Notes…"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Interventions */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Interventions</h3>
        {form.interventions.map((iv, idx) => (
          <label key={iv.key} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: "pointer", marginBottom: 8 }}>
            <input type="checkbox" checked={Boolean(iv.selected)} disabled={isLocked} onChange={(e) => toggleIntervention(idx, e.target.checked)} style={{ marginTop: 2 }} />
            <span>{iv.label}</span>
          </label>
        ))}
        <div style={{ ...formGroup, marginTop: 8 }}>
          <label style={label}>Other Interventions (specify)</label>
          <textarea
            style={textarea}
            disabled={isLocked}
            value={form.other_interventions || ""}
            onChange={(e) => updateField("other_interventions", e.target.value)}
            placeholder="Describe any additional intervention not listed above…"
          />
        </div>
      </div>

      {/* 13-month action plan */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>13-Month Bereavement Contact Schedule</h3>
          <span style={S.badge(`${COLORS.teal}22`, COLORS.teal)}>
            {completedCount} / {activePlanEntries.length} completed
          </span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 640 }}>
            <thead>
              <tr>
                <th style={S.tableHeader}>Contact</th>
                <th style={S.tableHeader}>Type</th>
                <th style={S.tableHeader}>Planned Date</th>
                <th style={S.tableHeader}>Completed Date</th>
                <th style={S.tableHeader}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {form.action_plan.map((a, idx) =>
                a.required === false ? null : (
                  <tr key={idx}>
                    <td style={S.tableCell}>{a.label}</td>
                    <td style={S.tableCell}>
                      <select
                        style={{ ...input, padding: "6px 8px" }}
                        disabled={isLocked}
                        value={a.contact_type || "PHONE"}
                        onChange={(e) => updateContact(idx, "contact_type", e.target.value)}
                      >
                        <option value="PHONE">Phone</option>
                        <option value="LETTER">Letter/Card</option>
                        <option value="VISIT">In-Person Visit</option>
                      </select>
                    </td>
                    <td style={S.tableCell}>
                      <input
                        type="date"
                        style={{ ...input, padding: "6px 8px" }}
                        disabled={isLocked}
                        value={a.planned_date || ""}
                        onChange={(e) => updateContact(idx, "planned_date", e.target.value)}
                      />
                    </td>
                    <td style={S.tableCell}>
                      <input
                        type="date"
                        style={{ ...input, padding: "6px 8px" }}
                        disabled={isLocked}
                        value={a.completed_date || ""}
                        onChange={(e) => updateContact(idx, "completed_date", e.target.value)}
                      />
                    </td>
                    <td style={S.tableCell}>
                      <input
                        style={{ ...input, padding: "6px 8px" }}
                        disabled={isLocked}
                        value={a.notes || ""}
                        onChange={(e) => updateContact(idx, "notes", e.target.value)}
                        placeholder="Notes…"
                      />
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>

        {form.action_plan.some((a) => a.required === false) && (
          <>
            <h4 style={{ fontSize: 12, color: COLORS.dim, textTransform: "uppercase", margin: "18px 0 8px" }}>
              Optional / As-Needed Contacts
            </h4>
            <p style={{ fontSize: 11, color: COLORS.dim, margin: "0 0 10px" }}>
              Not part of the standard schedule. Check "Include" to activate a contact for this specific plan (e.g. a condolence call or extra check-in).
            </p>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 640 }}>
                <thead>
                  <tr>
                    <th style={S.tableHeader}>Include</th>
                    <th style={S.tableHeader}>Contact</th>
                    <th style={S.tableHeader}>Type</th>
                    <th style={S.tableHeader}>Planned Date</th>
                    <th style={S.tableHeader}>Completed Date</th>
                    <th style={S.tableHeader}>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {form.action_plan.map((a, idx) =>
                    a.required === false ? (
                      <tr key={idx} style={{ opacity: a.included ? 1 : 0.55 }}>
                        <td style={S.tableCell}>
                          <input
                            type="checkbox"
                            checked={Boolean(a.included)}
                            disabled={isLocked}
                            onChange={(e) => updateContact(idx, "included", e.target.checked)}
                          />
                        </td>
                        <td style={S.tableCell}>{a.label}</td>
                        <td style={S.tableCell}>
                          <select
                            style={{ ...input, padding: "6px 8px" }}
                            disabled={isLocked || !a.included}
                            value={a.contact_type || "PHONE"}
                            onChange={(e) => updateContact(idx, "contact_type", e.target.value)}
                          >
                            <option value="PHONE">Phone</option>
                            <option value="LETTER">Letter/Card</option>
                            <option value="VISIT">In-Person Visit</option>
                          </select>
                        </td>
                        <td style={S.tableCell}>
                          <input
                            type="date"
                            style={{ ...input, padding: "6px 8px" }}
                            disabled={isLocked || !a.included}
                            value={a.planned_date || ""}
                            onChange={(e) => updateContact(idx, "planned_date", e.target.value)}
                          />
                        </td>
                        <td style={S.tableCell}>
                          <input
                            type="date"
                            style={{ ...input, padding: "6px 8px" }}
                            disabled={isLocked || !a.included}
                            value={a.completed_date || ""}
                            onChange={(e) => updateContact(idx, "completed_date", e.target.value)}
                          />
                        </td>
                        <td style={S.tableCell}>
                          <input
                            style={{ ...input, padding: "6px 8px" }}
                            disabled={isLocked || !a.included}
                            value={a.notes || ""}
                            onChange={(e) => updateContact(idx, "notes", e.target.value)}
                            placeholder="Notes…"
                          />
                        </td>
                      </tr>
                    ) : null
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* Narrative */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Narrative</h3>
        <textarea
          style={{ ...textarea, minHeight: 120 }}
          disabled={isLocked}
          value={form.narrative || ""}
          onChange={(e) => updateField("narrative", e.target.value)}
          placeholder="Additional context, referrals made, closure notes…"
        />
      </div>

      {!isLocked && (
        <div style={{ display: "flex", gap: 10 }}>
          <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={handleSave}>
            {saving ? "Saving…" : "Save"}
          </button>
          {activePOC && (
            <button type="button" style={S.btn(COLORS.purple)} disabled={signing} onClick={handleSign}>
              {signing ? "Signing…" : "Sign & Lock"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
