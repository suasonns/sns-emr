import React, { useCallback, useEffect, useMemo, useState } from "react";
import { COLORS, S } from "../tenant/design";
import {
  fetchBereavementRiskCatalog,
  listBereavementAssessments,
  createBereavementAssessment,
  updateBereavementAssessment,
  signBereavementAssessment,
} from "../api/bereavement";

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
// Auto-fit/minmax grids reflow by available width alone -- no breakpoints
// needed. On a phone (~375px) each collapses to 1 column; iPad portrait
// (~768px) fits 2; a 13" laptop or wider fits the full 2/3 columns.
const grid2 = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 };
const grid3 = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 };

const RISK_LEVEL_COLOR = {
  LOW: COLORS.green,
  MODERATE: COLORS.orange,
  HIGH: COLORS.red,
};

const EMPTY_ADDITIONAL_CONTACT = { name: "", relationship_to_patient: "", address: "", phone: "", specific_concerns: "" };

function emptyForm(patientId) {
  return {
    patient_id: patientId,
    discipline: "MSW",
    care_level: "",
    visit_type: "IN_PERSON",
    visit_mode: "SCHEDULED",
    visit_date: new Date().toISOString().slice(0, 10),
    time_in: "",
    time_out: "",
    duration_minutes: null,
    no_family: false,
    primary_first_name: "",
    primary_last_name: "",
    primary_age: null,
    primary_gender: "",
    primary_address: "",
    primary_city: "",
    primary_state: "",
    primary_zip: "",
    primary_home_phone: "",
    primary_work_phone: "",
    primary_cell_phone: "",
    primary_email: "",
    primary_relationship_to_patient: "",
    primary_was_caregiver: null,
    risk_items: {},
    risk_other_note: "",
    additional_bereaved: [],
    narrative: "",
  };
}

const riskItemsGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "4px 20px" };

function RiskChecklistGroup({ title, points, items, riskItems, onToggle, onNote }) {
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
              <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 13, color: COLORS.white, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={Boolean(entry.checked)}
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

export default function BereavementBoard({ patientId }) {
  const [catalog, setCatalog] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [view, setView] = useState("list"); // "list" | "form"
  const [activeAssessment, setActiveAssessment] = useState(null); // null => new
  const [form, setForm] = useState(emptyForm(patientId));
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [catalogData, assessmentData] = await Promise.all([
        fetchBereavementRiskCatalog(),
        listBereavementAssessments(patientId),
      ]);
      setCatalog(catalogData);
      setAssessments(assessmentData);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load bereavement assessments.");
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

  const openNew = () => {
    setActiveAssessment(null);
    setForm(emptyForm(patientId));
    setMessage("");
    setError("");
    setView("form");
  };

  const openExisting = (assessment) => {
    setActiveAssessment(assessment);
    setForm({ ...assessment, patient_id: patientId });
    setMessage("");
    setError("");
    setView("form");
  };

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

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const addContact = () => setForm((prev) => ({ ...prev, additional_bereaved: [...prev.additional_bereaved, { ...EMPTY_ADDITIONAL_CONTACT }] }));
  const updateContact = (idx, field, value) =>
    setForm((prev) => {
      const next = [...prev.additional_bereaved];
      next[idx] = { ...next[idx], [field]: value };
      return { ...prev, additional_bereaved: next };
    });
  const removeContact = (idx) =>
    setForm((prev) => ({ ...prev, additional_bereaved: prev.additional_bereaved.filter((_, i) => i !== idx) }));

  const isLocked = activeAssessment?.status === "SIGNED";

  const buildPayload = () => ({
    discipline: form.discipline || null,
    care_level: form.care_level || null,
    visit_type: form.visit_type || null,
    visit_mode: form.visit_mode || null,
    visit_date: form.visit_date || null,
    time_in: form.time_in || null,
    time_out: form.time_out || null,
    duration_minutes: form.duration_minutes || null,
    no_family: Boolean(form.no_family),
    primary_first_name: form.primary_first_name || null,
    primary_last_name: form.primary_last_name || null,
    primary_age: form.primary_age || null,
    primary_gender: form.primary_gender || null,
    primary_address: form.primary_address || null,
    primary_city: form.primary_city || null,
    primary_state: form.primary_state || null,
    primary_zip: form.primary_zip || null,
    primary_home_phone: form.primary_home_phone || null,
    primary_work_phone: form.primary_work_phone || null,
    primary_cell_phone: form.primary_cell_phone || null,
    primary_email: form.primary_email || null,
    primary_relationship_to_patient: form.primary_relationship_to_patient || null,
    primary_was_caregiver: form.primary_was_caregiver,
    risk_items: form.risk_items,
    risk_other_note: form.risk_other_note || null,
    additional_bereaved: form.additional_bereaved.filter((c) => c.name?.trim()),
    narrative: form.narrative || null,
  });

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      if (activeAssessment) {
        const updated = await updateBereavementAssessment(activeAssessment.id, buildPayload());
        setActiveAssessment(updated);
        setForm({ ...updated, patient_id: patientId });
      } else {
        const created = await createBereavementAssessment({ patient_id: patientId, ...buildPayload() });
        setActiveAssessment(created);
        setForm({ ...created, patient_id: patientId });
      }
      setMessage("Bereavement assessment saved.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to save assessment.");
    } finally {
      setSaving(false);
    }
  };

  const handleSign = async () => {
    if (!activeAssessment) return;
    setSigning(true);
    setError("");
    try {
      const signed = await signBereavementAssessment(activeAssessment.id);
      setActiveAssessment(signed);
      setForm({ ...signed, patient_id: patientId });
      setMessage("Assessment electronically signed and locked.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to sign assessment.");
    } finally {
      setSigning(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 24, color: COLORS.dim, fontSize: 13 }}>Loading bereavement assessments…</div>;
  }

  if (view === "list") {
    return (
      <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Bereavement — Initial Assessment</h2>
            <p style={{ color: COLORS.dim, fontSize: 13, margin: 0 }}>
              Comprehensive Bereavement Assessment history for the primary bereaved and any additional family contacts.
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
          {assessments.length === 0 ? (
            <div style={{ color: COLORS.dim, fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No bereavement assessments on file yet.
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={S.tableHeader}>Date Assessed</th>
                  <th style={S.tableHeader}>Primary Bereaved</th>
                  <th style={S.tableHeader}>Discipline</th>
                  <th style={S.tableHeader}>Risk Level</th>
                  <th style={S.tableHeader}>Status</th>
                  <th style={S.tableHeader} />
                </tr>
              </thead>
              <tbody>
                {assessments.map((a) => (
                  <tr key={a.id}>
                    <td style={S.tableCell}>{a.visit_date || a.created_at?.slice(0, 10)}</td>
                    <td style={S.tableCell}>
                      {a.no_family ? "No family" : [a.primary_first_name, a.primary_last_name].filter(Boolean).join(" ") || "—"}
                    </td>
                    <td style={S.tableCell}>{a.discipline || "—"}</td>
                    <td style={S.tableCell}>
                      {a.risk_level ? (
                        <span style={S.badge(`${RISK_LEVEL_COLOR[a.risk_level]}22`, RISK_LEVEL_COLOR[a.risk_level])}>
                          {a.risk_level} ({a.risk_total_score})
                        </span>
                      ) : "—"}
                    </td>
                    <td style={S.tableCell}>
                      <span style={S.badge(a.status === "SIGNED" ? `${COLORS.teal}22` : `${COLORS.dim}22`, a.status === "SIGNED" ? COLORS.teal : COLORS.dim)}>
                        {a.status}
                      </span>
                    </td>
                    <td style={S.tableCell}>
                      <button type="button" style={S.btnOutline} onClick={() => openExisting(a)}>
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
        <h2 style={{ color: COLORS.white, fontSize: 18, margin: 0 }}>Comprehensive Bereavement Assessment</h2>
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
          Electronically signed{activeAssessment?.signed_at ? ` on ${new Date(activeAssessment.signed_at).toLocaleDateString()}` : ""}. This assessment is locked.
        </div>
      )}

      {/* Visit metadata */}
      <div style={{ ...S.card }}>
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
      </div>

      {/* Primary Bereaved */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>Primary Bereaved</h3>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: COLORS.dim }}>
            <input type="checkbox" disabled={isLocked} checked={Boolean(form.no_family)} onChange={(e) => updateField("no_family", e.target.checked)} />
            No family
          </label>
        </div>
        {!form.no_family && (
          <>
            <div style={grid2}>
              <div style={formGroup}>
                <label style={label}>First Name</label>
                <input style={input} disabled={isLocked} value={form.primary_first_name || ""} onChange={(e) => updateField("primary_first_name", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Last Name</label>
                <input style={input} disabled={isLocked} value={form.primary_last_name || ""} onChange={(e) => updateField("primary_last_name", e.target.value)} />
              </div>
            </div>
            <div style={grid3}>
              <div style={formGroup}>
                <label style={label}>Age</label>
                <input type="number" style={input} disabled={isLocked} value={form.primary_age ?? ""} onChange={(e) => updateField("primary_age", e.target.value ? Number(e.target.value) : null)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Gender</label>
                <input style={input} disabled={isLocked} value={form.primary_gender || ""} onChange={(e) => updateField("primary_gender", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Relationship to Patient</label>
                <input style={input} disabled={isLocked} value={form.primary_relationship_to_patient || ""} onChange={(e) => updateField("primary_relationship_to_patient", e.target.value)} />
              </div>
            </div>
            <div style={formGroup}>
              <label style={label}>Address</label>
              <input style={input} disabled={isLocked} value={form.primary_address || ""} onChange={(e) => updateField("primary_address", e.target.value)} />
            </div>
            <div style={grid3}>
              <div style={formGroup}>
                <label style={label}>City</label>
                <input style={input} disabled={isLocked} value={form.primary_city || ""} onChange={(e) => updateField("primary_city", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>State</label>
                <input style={input} disabled={isLocked} value={form.primary_state || ""} onChange={(e) => updateField("primary_state", e.target.value)} />
              </div>
              <div style={formGroup}>
                <label style={label}>Zip</label>
                <input style={input} disabled={isLocked} value={form.primary_zip || ""} onChange={(e) => updateField("primary_zip", e.target.value)} />
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
            <div style={formGroup}>
              <label style={label}>Was the bereaved patient's primary caregiver?</label>
              <select
                style={input}
                disabled={isLocked}
                value={form.primary_was_caregiver === null || form.primary_was_caregiver === undefined ? "" : String(form.primary_was_caregiver)}
                onChange={(e) => updateField("primary_was_caregiver", e.target.value === "" ? null : e.target.value === "true")}
              >
                <option value="">Select…</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
          </>
        )}
      </div>

      {/* Risk / Stressors */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>Risks/Stressors For This Bereavement</h3>
          <span style={S.badge(`${RISK_LEVEL_COLOR[riskLevel]}22`, RISK_LEVEL_COLOR[riskLevel])}>
            {riskLevel} RISK — Score {totalScore}
          </span>
        </div>
        <RiskChecklistGroup title="Score 10" points={10} items={grouped[10]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} />
        <RiskChecklistGroup title="Score 5" points={5} items={grouped[5]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} />
        <RiskChecklistGroup title="Score 2 (each)" points={2} items={grouped[2]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} />
        <RiskChecklistGroup title="Score 1 (each)" points={1} items={grouped[1]} riskItems={form.risk_items} onToggle={toggleRiskItem} onNote={noteRiskItem} />
      </div>

      {/* Additional Bereaved */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, color: COLORS.white, margin: 0 }}>Additional Bereaved (if applicable)</h3>
          {!isLocked && (
            <button type="button" style={S.btnOutline} onClick={addContact}>
              + Add Contact
            </button>
          )}
        </div>
        {form.additional_bereaved.length === 0 ? (
          <div style={{ color: COLORS.dim, fontSize: 13 }}>No additional bereaved contacts added.</div>
        ) : (
          form.additional_bereaved.map((c, idx) => (
            <div key={idx} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 12, marginBottom: 10 }}>
              <div style={grid2}>
                <div style={formGroup}>
                  <label style={label}>Name</label>
                  <input style={input} disabled={isLocked} value={c.name} onChange={(e) => updateContact(idx, "name", e.target.value)} />
                </div>
                <div style={formGroup}>
                  <label style={label}>Relationship to Patient</label>
                  <input style={input} disabled={isLocked} value={c.relationship_to_patient || ""} onChange={(e) => updateContact(idx, "relationship_to_patient", e.target.value)} />
                </div>
              </div>
              <div style={grid2}>
                <div style={formGroup}>
                  <label style={label}>Address</label>
                  <input style={input} disabled={isLocked} value={c.address || ""} onChange={(e) => updateContact(idx, "address", e.target.value)} />
                </div>
                <div style={formGroup}>
                  <label style={label}>Phone No.</label>
                  <input style={input} disabled={isLocked} value={c.phone || ""} onChange={(e) => updateContact(idx, "phone", e.target.value)} />
                </div>
              </div>
              <div style={formGroup}>
                <label style={label}>Specific Concerns</label>
                <input style={input} disabled={isLocked} value={c.specific_concerns || ""} onChange={(e) => updateContact(idx, "specific_concerns", e.target.value)} />
              </div>
              {!isLocked && (
                <button type="button" style={{ ...S.btnOutline, color: COLORS.red, borderColor: COLORS.red }} onClick={() => removeContact(idx)}>
                  Remove
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Narrative */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, color: COLORS.white, margin: "0 0 12px" }}>Narrative</h3>
        <textarea
          style={{ ...textarea, minHeight: 140 }}
          disabled={isLocked}
          value={form.narrative || ""}
          onChange={(e) => updateField("narrative", e.target.value)}
          placeholder="Social worker's assessment summary, referrals, and follow-up plan…"
        />
      </div>

      {!isLocked && (
        <div style={{ display: "flex", gap: 10 }}>
          <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={handleSave}>
            {saving ? "Saving…" : "Save"}
          </button>
          {activeAssessment && (
            <button type="button" style={S.btn(COLORS.purple)} disabled={signing} onClick={handleSign}>
              {signing ? "Signing…" : "Sign & Lock"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
