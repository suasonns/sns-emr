import { useCallback, useEffect, useMemo, useState } from "react";
import { useThemeMode } from "../theme/theme";
import { getRnicaColors, getRnicaStyles } from "../theme/clinicalDesign";
import { getCurrentUser } from "../api/session";
import { ContinuousCareLogSection } from "./RNICA";
import {
  VISIT_NOTE_FORM_TYPES,
  VISIT_NOTE_CARE_LEVELS,
  VISIT_NOTE_BODY_SYSTEMS,
  isFullBodyFormType,
  createVisitNote,
  getVisitNote,
  updateVisitNote,
  finalizeVisitNote,
  listVisitNotesForPatient,
} from "../api/visitNotes";

// ════════════════════════════════════════════════════════════════
// RN / LVN "Visit Notes" module — Add New Visit / My Visit Notes /
// History of Visit Notes. Modeled on the legacy HospiceMD Visit Notes
// screen, restyled with SNS EMR's shared clinical design system
// (getRnicaColors/getRnicaStyles). RN ICA / MSW ICA / SC ICA and the CHHA
// visit note are separate, pre-existing modules — this file does not
// import or modify any of their form logic, only the shared
// ContinuousCareLogSection (which already exists specifically so it can
// be reused here when Care Level = Continuous Care).
// ════════════════════════════════════════════════════════════════

const SEVERITY_OPTIONS = [
  { value: "NONE", label: "None (0)" },
  { value: "MILD", label: "Mild (1-3)" },
  { value: "MODERATE", label: "Moderate (4-6)" },
  { value: "SEVERE", label: "Severe (7-10)" },
];

const ADL_ACTIVITIES = [
  { key: "bathing", label: "Bathing" },
  { key: "dressing", label: "Dressing" },
  { key: "toileting", label: "Toileting" },
  { key: "transferring", label: "Transferring" },
  { key: "feeding", label: "Feeding" },
  { key: "grooming", label: "Grooming" },
];

const DEFAULT_CONTENT = {
  correction: false,
  type_of_visit: "",
  visit_kind: "",
  form_type: "ASSESS",
  care_level: "",
  visit_date: "",
  time_in: "",
  time_out: "",
  duration: "",
  entered_by: "",
  staff_assigned: "",
  pain: { controlled: "", pain_level: null, other_observation: "" },
  vitals: {
    temperature: "",
    temperature_position: "",
    pulse: "",
    respirations: "",
    bp_systolic: "",
    bp_diastolic: "",
    bp_position: "",
    height: "",
    weight: "",
    mac: "",
    bmi: "",
    o2_sat: "",
    o2_delivery: "",
    unable_to_assess: false,
  },
  signs_symptoms: {},
  care_provided: {
    physical_comfort_support: false,
    structural_functional_activity_support: false,
    emotional_support: false,
    spiritual_support: false,
    safety_instructions: false,
    interpersonal_relationship_support: false,
    environmental_needs: false,
    self_determination_preference_needs: false,
    knowledge_related_needs: false,
    language_communication_related_needs: false,
    other_needs: false,
    other_needs_text: "",
  },
  visit_checklist: {
    updated_family_pcg: null,
    updated_cm_md: null,
    comfort_pack_med_checked: null,
    dme_inspected: null,
    foley_cath_checked: null,
    foley_cath_last_changed: "",
    gi_tube_checked: null,
    next_visit_confirmed: null,
  },
  death_disposal_notes: "",
  narrative: "",
};

function FormInput({ label, value, onChange, type = "text", disabled, styles, COLORS, required }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required && <span style={{ color: COLORS.error }}>*</span>}
      </label>
      <input
        style={{ ...styles.input, ...(disabled ? { opacity: 0.6, cursor: "not-allowed" } : {}) }}
        type={type}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options, disabled, styles, placeholder = "— Select One —" }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <select
        style={{ ...styles.select, ...(disabled ? { opacity: 0.6, cursor: "not-allowed" } : {}) }}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={typeof opt === "string" ? opt : opt.value} value={typeof opt === "string" ? opt : opt.value}>
            {typeof opt === "string" ? opt : opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function FormTextarea({ label, value, onChange, rows = 4, disabled, styles }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <textarea
        style={{ ...styles.textarea, minHeight: rows * 24, ...(disabled ? { opacity: 0.6, cursor: "not-allowed" } : {}) }}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
    </div>
  );
}

function Card({ title, subtitle, children, styles, actions }) {
  return (
    <div style={styles.card}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
        <div style={styles.cardTitle}>{title}</div>
        {actions}
      </div>
      {subtitle && <p style={styles.sectionSubtitle}>{subtitle}</p>}
      {children}
    </div>
  );
}

// ---------------------------------------------------------------
// Visit Details bar — always renders first / topmost, per requirement.
// ---------------------------------------------------------------
function VisitDetailsCard({ content, onChange, disabled, styles, COLORS, discipline }) {
  const set = (key, value) => onChange({ ...content, [key]: value });
  return (
    <Card title="Visit Details" styles={styles}>
      <div style={styles.fieldsGrid}>
        <FormInput label="Entered By" value={content.entered_by} onChange={(v) => set("entered_by", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Staff Assigned" value={content.staff_assigned} onChange={(v) => set("staff_assigned", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <div style={styles.formGroup}>
          <label style={styles.label}>Discipline</label>
          <input style={{ ...styles.input, opacity: 0.7 }} value={discipline || ""} disabled readOnly />
        </div>
        <FormSelect label="Care Level" value={content.care_level} onChange={(v) => set("care_level", v)} options={VISIT_NOTE_CARE_LEVELS} disabled={disabled} styles={styles} />
        <FormSelect label="Type Of" value={content.type_of_visit} onChange={(v) => set("type_of_visit", v)} options={["In-Person", "Telephone", "Video"]} disabled={disabled} styles={styles} />
        <FormSelect label="Visit" value={content.visit_kind} onChange={(v) => set("visit_kind", v)} options={["Scheduled", "Unscheduled"]} disabled={disabled} styles={styles} />
        <FormSelect
          label="Form Type"
          value={content.form_type}
          onChange={(v) => set("form_type", v)}
          options={VISIT_NOTE_FORM_TYPES.map((f) => ({ value: f.value, label: f.label }))}
          disabled={disabled}
          styles={styles}
        />
        <FormInput label="Visit Date" type="date" value={content.visit_date} onChange={(v) => set("visit_date", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Time In" type="time" value={content.time_in} onChange={(v) => set("time_in", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Time Out" type="time" value={content.time_out} onChange={(v) => set("time_out", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Duration" value={content.duration} onChange={(v) => set("duration", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <label style={{ ...styles.formGroup, display: "flex", alignItems: "center", gap: 6, marginTop: 18 }}>
          <input type="checkbox" checked={!!content.correction} onChange={(e) => set("correction", e.target.checked)} disabled={disabled} style={{ width: 16, height: 16 }} />
          <span style={{ ...styles.label, marginBottom: 0 }}>Correction</span>
        </label>
      </div>
    </Card>
  );
}

function PainCard({ pain, onChange, disabled, styles, COLORS }) {
  const set = (key, value) => onChange({ ...pain, [key]: value });
  return (
    <Card title="Pain" styles={styles}>
      <div style={styles.fieldsGrid}>
        <FormSelect label="Pain Controlled" value={pain.controlled} onChange={(v) => set("controlled", v)} options={["Y", "N", "Unable", "N/A"]} disabled={disabled} styles={styles} />
        <FormInput label="Pain Level (0-10)" type="number" value={pain.pain_level ?? ""} onChange={(v) => set("pain_level", v === "" ? null : Number(v))} disabled={disabled} styles={styles} COLORS={COLORS} />
        <div style={{ ...styles.formGroup, gridColumn: "1 / -1" }}>
          <label style={styles.label}>Other Observation</label>
          <input style={styles.input} value={pain.other_observation ?? ""} onChange={(e) => set("other_observation", e.target.value)} disabled={disabled} />
        </div>
      </div>
    </Card>
  );
}

function VitalsCard({ vitals, onChange, disabled, styles, COLORS }) {
  const set = (key, value) => onChange({ ...vitals, [key]: value });
  return (
    <Card title="Vitals & Measurements" styles={styles}>
      <div style={styles.fieldsGrid}>
        <FormInput label="Temp" value={vitals.temperature} onChange={(v) => set("temperature", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="Temp Position" value={vitals.temperature_position} onChange={(v) => set("temperature_position", v)} options={["Oral", "Axillary", "Tympanic", "Rectal"]} disabled={disabled} styles={styles} />
        <FormInput label="Pulse" value={vitals.pulse} onChange={(v) => set("pulse", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Resp" value={vitals.respirations} onChange={(v) => set("respirations", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BP Systolic" value={vitals.bp_systolic} onChange={(v) => set("bp_systolic", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BP Diastolic" value={vitals.bp_diastolic} onChange={(v) => set("bp_diastolic", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="BP Position" value={vitals.bp_position} onChange={(v) => set("bp_position", v)} options={["Sitting", "Standing", "Lying"]} disabled={disabled} styles={styles} />
        <FormInput label="Height" value={vitals.height} onChange={(v) => set("height", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Weight" value={vitals.weight} onChange={(v) => set("weight", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="MAC" value={vitals.mac} onChange={(v) => set("mac", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BMI" value={vitals.bmi} onChange={(v) => set("bmi", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="O2 Sat %" value={vitals.o2_sat} onChange={(v) => set("o2_sat", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="O2 Delivery" value={vitals.o2_delivery} onChange={(v) => set("o2_delivery", v)} options={["Room Air", "Nasal Cannula", "Non-Rebreather", "Ventilator", "Other"]} disabled={disabled} styles={styles} />
        <label style={{ ...styles.formGroup, display: "flex", alignItems: "center", gap: 6, marginTop: 18 }}>
          <input type="checkbox" checked={!!vitals.unable_to_assess} onChange={(e) => set("unable_to_assess", e.target.checked)} disabled={disabled} style={{ width: 16, height: 16 }} />
          <span style={{ ...styles.label, marginBottom: 0 }}>Unable to Assess</span>
        </label>
      </div>
    </Card>
  );
}

function BodySystemRow({ systemKey, label, value, onChange, disabled, styles, COLORS }) {
  const row = value || {};
  const set = (key, val) => onChange(systemKey, { ...row, [key]: val });
  const showNutrition = systemKey === "nutrition";
  const showGu = systemKey === "gu_reproductive";
  const showMobility = systemKey === "mobility";
  const showAdl = systemKey === "adl_assessment";

  const calculateAdlScore = () => {
    const scores = row.adl_scores || {};
    const total = ADL_ACTIVITIES.reduce((sum, a) => sum + (Number(scores[a.key]) || 0), 0);
    set("adl_total_score", total);
  };

  return (
    <div style={{ borderTop: `1px solid ${COLORS.border || "#e2e8f0"}`, padding: "10px 0" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <strong style={{ fontSize: 12.5, color: COLORS.dark }}>{label}</strong>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5, cursor: disabled ? "default" : "pointer" }}>
          <input
            type="checkbox"
            checked={!!row.assessed_no_issues}
            onChange={(e) => set("assessed_no_issues", e.target.checked)}
            disabled={disabled}
            style={{ width: 15, height: 15 }}
          />
          Assessed / No Issues Reported
        </label>
      </div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 6 }}>
        {SEVERITY_OPTIONS.map((opt) => (
          <label key={opt.value} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5, cursor: disabled ? "default" : "pointer" }}>
            <input
              type="radio"
              name={`${systemKey}_severity`}
              checked={row.severity === opt.value}
              onChange={() => set("severity", opt.value)}
              disabled={disabled}
            />
            {opt.label}
          </label>
        ))}
      </div>
      <div style={{ ...styles.fieldsGrid, marginTop: 6 }}>
        <FormInput label="Other Symptom" value={row.other_symptom} onChange={(v) => set("other_symptom", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Other Observation" value={row.other_observation} onChange={(v) => set("other_observation", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        {showNutrition && (
          <>
            <FormSelect label="Diet" value={row.diet} onChange={(v) => set("diet", v)} options={["Regular", "Mechanical Soft", "Pureed", "Liquid", "NPO", "Other"]} disabled={disabled} styles={styles} />
            <FormInput label="Diet Specify" value={row.diet_specify} onChange={(v) => set("diet_specify", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        )}
        {showGu && (
          <>
            <FormSelect label="Incontinent" value={row.incontinent} onChange={(v) => set("incontinent", v)} options={["None", "Bowel", "Bladder", "Both"]} disabled={disabled} styles={styles} />
            <FormInput label="Last BM" type="date" value={row.last_bm} onChange={(v) => set("last_bm", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        )}
        {showMobility && (
          <>
            <FormSelect label="Ambulatory Status" value={row.ambulatory_status} onChange={(v) => set("ambulatory_status", v)} options={["Ambulatory", "Non-Ambulatory"]} disabled={disabled} styles={styles} />
            <FormInput label="Endurance #" value={row.endurance} onChange={(v) => set("endurance", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        )}
      </div>
      {showAdl && (
        <div style={{ marginTop: 8 }}>
          <div style={{ ...styles.fieldsGrid }}>
            {ADL_ACTIVITIES.map((a) => (
              <FormSelect
                key={a.key}
                label={a.label}
                value={row.adl_scores?.[a.key] != null ? String(row.adl_scores[a.key]) : ""}
                onChange={(v) => set("adl_scores", { ...(row.adl_scores || {}), [a.key]: v === "" ? null : Number(v) })}
                options={["0", "1", "2", "3"]}
                disabled={disabled}
                styles={styles}
              />
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
            {!disabled && (
              <button type="button" onClick={calculateAdlScore} style={{ ...styles.btnSecondary, padding: "4px 10px", fontSize: 11.5 }}>
                Calculate ADL Score
              </button>
            )}
            <span style={{ fontSize: 12, color: COLORS.dark }}>
              Total Score: <strong>{row.adl_total_score ?? "—"}</strong>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function SignsSymptomsCard({ signsSymptoms, onChange, disabled, styles, COLORS }) {
  const setSystem = (key, value) => onChange({ ...signsSymptoms, [key]: value });
  return (
    <Card title="Signs & Symptoms / Alteration in Status" subtitle="One row per body system — severity, other symptom/observation, and system-specific detail." styles={styles}>
      {VISIT_NOTE_BODY_SYSTEMS.map((sys) => (
        <BodySystemRow
          key={sys.key}
          systemKey={sys.key}
          label={sys.label}
          value={signsSymptoms[sys.key]}
          onChange={setSystem}
          disabled={disabled}
          styles={styles}
          COLORS={COLORS}
        />
      ))}
    </Card>
  );
}

const CARE_PROVIDED_ITEMS = [
  ["physical_comfort_support", "Physical Comfort Support"],
  ["structural_functional_activity_support", "Structural/Functional/Activity Support"],
  ["emotional_support", "Emotional Support"],
  ["spiritual_support", "Spiritual Support"],
  ["safety_instructions", "Safety Instructions"],
  ["interpersonal_relationship_support", "Interpersonal Relationship Support"],
  ["environmental_needs", "Environmental Needs"],
  ["self_determination_preference_needs", "Self-Determination/Preference Needs"],
  ["knowledge_related_needs", "Knowledge Related Needs"],
  ["language_communication_related_needs", "Language/Communication Related Needs"],
];

function CareProvidedCard({ careProvided, onChange, disabled, styles, COLORS }) {
  const set = (key, value) => onChange({ ...careProvided, [key]: value });
  return (
    <Card title="Care Provided" styles={styles}>
      <div style={styles.checkboxGroup}>
        {CARE_PROVIDED_ITEMS.map(([key, label]) => (
          <label key={key} style={styles.checkboxLabel}>
            <input type="checkbox" checked={!!careProvided[key]} onChange={(e) => set(key, e.target.checked)} disabled={disabled} />
            {label}
          </label>
        ))}
        <label style={styles.checkboxLabel}>
          <input type="checkbox" checked={!!careProvided.other_needs} onChange={(e) => set("other_needs", e.target.checked)} disabled={disabled} />
          Other Needs
        </label>
      </div>
      {careProvided.other_needs && (
        <FormInput label="Other Needs — Specify" value={careProvided.other_needs_text} onChange={(v) => set("other_needs_text", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
      )}
    </Card>
  );
}

const CHECKLIST_ITEMS = [
  ["updated_family_pcg", "Update Family/PCG"],
  ["updated_cm_md", "Update CM/MD"],
  ["comfort_pack_med_checked", "Comfort Pack/Med Checked"],
  ["dme_inspected", "DME Inspected"],
  ["gi_tube_checked", "Check GI Tube"],
  ["next_visit_confirmed", "Confirmed Schedule of Next Visit"],
];

function VisitChecklistCard({ checklist, onChange, disabled, styles, COLORS }) {
  const set = (key, value) => onChange({ ...checklist, [key]: value });
  return (
    <Card title="Visit Check List" styles={styles}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {CHECKLIST_ITEMS.map(([key, label]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 12, color: COLORS.dark, minWidth: 240 }}>{label}</span>
            {["Yes", "No"].map((opt) => (
              <label key={opt} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5, cursor: disabled ? "default" : "pointer" }}>
                <input
                  type="radio"
                  name={key}
                  checked={checklist[key] === (opt === "Yes")}
                  onChange={() => set(key, opt === "Yes")}
                  disabled={disabled}
                />
                {opt}
              </label>
            ))}
          </div>
        ))}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 12, color: COLORS.dark, minWidth: 240 }}>Check Foley Cath</span>
          {["Yes", "No"].map((opt) => (
            <label key={opt} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5, cursor: disabled ? "default" : "pointer" }}>
              <input
                type="radio"
                name="foley_cath_checked"
                checked={checklist.foley_cath_checked === (opt === "Yes")}
                onChange={() => set("foley_cath_checked", opt === "Yes")}
                disabled={disabled}
              />
              {opt}
            </label>
          ))}
          {checklist.foley_cath_checked && (
            <FormInput label="Last Changed" type="date" value={checklist.foley_cath_last_changed} onChange={(v) => set("foley_cath_last_changed", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
          )}
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------
// The editor for a single visit note (new or existing).
// ---------------------------------------------------------------
function VisitNoteEditor({ visitId, discipline, patientId, onSaved, onCancel, styles, COLORS }) {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [visitStatus, setVisitStatus] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError("");
    getVisitNote(visitId)
      .then((record) => {
        const currentUser = getCurrentUser();
        setContent({
          ...DEFAULT_CONTENT,
          ...record.content,
          entered_by: record.content?.entered_by || currentUser?.full_name || currentUser?.name || "",
          pain: { ...DEFAULT_CONTENT.pain, ...(record.content?.pain || {}) },
          vitals: { ...DEFAULT_CONTENT.vitals, ...(record.content?.vitals || {}) },
          care_provided: { ...DEFAULT_CONTENT.care_provided, ...(record.content?.care_provided || {}) },
          visit_checklist: { ...DEFAULT_CONTENT.visit_checklist, ...(record.content?.visit_checklist || {}) },
          signs_symptoms: record.content?.signs_symptoms || {},
          form_type: record.form_type || record.content?.form_type || "ASSESS",
        });
        setVisitStatus(record.visit_status);
      })
      .catch((err) => setError(err.message || "Unable to load this visit note."))
      .finally(() => setLoading(false));
  }, [visitId]);

  const isFinalized = (visitStatus || "").toUpperCase() === "FINALIZED";
  const isCC = (content.care_level || "").trim().toLowerCase() === "continuous care";
  const isFullBody = isFullBodyFormType(content.form_type);
  const isDeathVisit = content.form_type === "DEATH_VISIT";

  const handleSave = () => {
    setSaving(true);
    setError("");
    setMessage("");
    updateVisitNote(visitId, content)
      .then((record) => {
        setContent({ ...DEFAULT_CONTENT, ...record.content });
        setMessage("Visit note saved.");
        onSaved?.();
      })
      .catch((err) => setError(err.message || "Unable to save this visit note."))
      .finally(() => setSaving(false));
  };

  const handleSignAndSubmit = () => {
    setFinalizing(true);
    setError("");
    updateVisitNote(visitId, content)
      .then(() => finalizeVisitNote(visitId))
      .then(() => {
        setVisitStatus("FINALIZED");
        setMessage("Visit note signed and submitted.");
        onSaved?.();
      })
      .catch((err) => setError(err.message || "Unable to sign and submit this visit note."))
      .finally(() => setFinalizing(false));
  };

  if (loading) {
    return <div style={{ fontSize: 12, color: COLORS.gray, padding: 12 }}>Loading visit note…</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {error && <div style={{ color: "#ef4444", fontSize: 12.5 }}>{error}</div>}
      {message && <div style={{ color: "#0d9488", fontSize: 12.5 }}>{message}</div>}
      {isFinalized && <div style={styles.infoBox}>This visit note has been signed and submitted and can no longer be edited.</div>}

      <VisitDetailsCard content={content} onChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} discipline={discipline} />

      {isCC ? (
        <ContinuousCareLogSection
          visitId={visitId}
          discipline={discipline}
          enteredBy={content.entered_by}
          styles={styles}
          COLORS={COLORS}
          disabled={isFinalized}
        />
      ) : isFullBody ? (
        <>
          <PainCard pain={content.pain} onChange={(v) => setContent((p) => ({ ...p, pain: v }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          <VitalsCard vitals={content.vitals} onChange={(v) => setContent((p) => ({ ...p, vitals: v }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          <SignsSymptomsCard signsSymptoms={content.signs_symptoms} onChange={(v) => setContent((p) => ({ ...p, signs_symptoms: v }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          <CareProvidedCard careProvided={content.care_provided} onChange={(v) => setContent((p) => ({ ...p, care_provided: v }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          <VisitChecklistCard checklist={content.visit_checklist} onChange={(v) => setContent((p) => ({ ...p, visit_checklist: v }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
        </>
      ) : (
        <div style={styles.infoBox}>
          This Form Type only requires a narrative — the full clinical documentation body is hidden, matching the standard workflow for non-Assess visit types.
        </div>
      )}

      {isDeathVisit && (
        <Card title="Death Disposal" styles={styles}>
          <FormTextarea label="Death Disposal Notes" value={content.death_disposal_notes} onChange={(v) => setContent((p) => ({ ...p, death_disposal_notes: v }))} disabled={isFinalized} styles={styles} rows={3} />
        </Card>
      )}

      <Card title="Narrative" styles={styles}>
        <FormTextarea label="Narrative" value={content.narrative} onChange={(v) => setContent((p) => ({ ...p, narrative: v }))} disabled={isFinalized} styles={styles} rows={6} />
      </Card>

      {!isFinalized && (
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button type="button" onClick={onCancel} style={styles.btnSecondary}>
            Close
          </button>
          <button type="button" onClick={handleSave} disabled={saving || finalizing} style={{ ...styles.btnSecondary, opacity: saving ? 0.6 : 1 }}>
            {saving ? "Saving…" : "Save Draft"}
          </button>
          <button type="button" onClick={handleSignAndSubmit} disabled={saving || finalizing} style={{ ...styles.btnPrimary, opacity: finalizing ? 0.6 : 1 }}>
            {finalizing ? "Submitting…" : "Sign & Submit"}
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------
// "Add New Visit" — creates the Visit + primary ClinicalNote, then hands
// off to the editor above.
// ---------------------------------------------------------------
function AddNewVisitCard({ patientId, onCreated, styles, COLORS }) {
  const currentUser = getCurrentUser();
  const [discipline, setDiscipline] = useState("RN");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = () => {
    setCreating(true);
    setError("");
    createVisitNote({
      patient_id: patientId,
      visit_type: discipline,
      service_type: "SN",
      form_type: "ASSESS",
      visit_schedule_type: "SCHEDULED",
      clinical_note: {
        entered_by: currentUser?.full_name || currentUser?.name || "",
        staff_assigned: currentUser?.full_name || currentUser?.name || "",
        visit_date: new Date().toISOString().slice(0, 10),
      },
    })
      .then((res) => onCreated(res.visit_id, discipline))
      .catch((err) => setError(err.message || "Unable to create this visit."))
      .finally(() => setCreating(false));
  };

  return (
    <Card title="Add New Visit" subtitle="RN and LVN visit documentation — Visit Details, Pain/Vitals/Signs & Symptoms (or the Continuous Care Hourly Narrative when Care Level is Continuous Care), Care Provided, Visit Check List, and Narrative." styles={styles}>
      {error && <div style={{ color: "#ef4444", fontSize: 12.5, marginBottom: 8 }}>{error}</div>}
      <div style={styles.fieldsGrid}>
        <FormSelect label="Discipline" value={discipline} onChange={setDiscipline} options={["RN", "LVN"]} styles={styles} />
      </div>
      <button type="button" onClick={handleCreate} disabled={creating} style={{ ...styles.btnPrimary, opacity: creating ? 0.6 : 1, marginTop: 8 }}>
        {creating ? "Creating…" : "Start Visit Note"}
      </button>
    </Card>
  );
}

// ---------------------------------------------------------------
// Timeline — "My Visit Notes" / "History of Visit Notes", merged with
// MSW ICA / SC ICA per product requirement.
// ---------------------------------------------------------------
function VisitNoteTimeline({ entries, onSelect, styles, COLORS }) {
  if (entries.length === 0) {
    return <div style={{ fontSize: 12, color: COLORS.gray }}>No visit notes recorded yet for this patient.</div>;
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {entries.map((entry) => {
        const isEditable = entry.source === "VISIT_NOTE";
        const dateLabel = entry.visit_date ? new Date(entry.visit_date).toLocaleString() : "—";
        return (
          <div
            key={`${entry.source}-${entry.id}`}
            onClick={() => isEditable && entry.visit_id && onSelect(entry)}
            style={{
              border: `1px solid ${COLORS.border || "#e2e8f0"}`,
              borderRadius: 8,
              padding: 10,
              fontSize: 12,
              cursor: isEditable && entry.visit_id ? "pointer" : "default",
              background: entry.status === "FINALIZED" ? "transparent" : COLORS.infoBoxBg,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 6 }}>
              <strong>
                {entry.discipline} · {entry.form_type || "—"} {entry.care_level ? `· ${entry.care_level}` : ""}
              </strong>
              <span style={{ color: COLORS.gray, fontSize: 11 }}>{dateLabel}</span>
            </div>
            <div style={{ marginTop: 4, color: COLORS.dark, display: "flex", justifyContent: "space-between", gap: 8 }}>
              <span>{entry.narrative_preview || "(no narrative yet)"}</span>
              <span style={{ fontSize: 10.5, textTransform: "uppercase", fontWeight: 700, color: COLORS.gray }}>
                {entry.status || "DRAFT"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------
// Top-level board — wires timeline + add-new + editor together. This is
// the real replacement for the previously-mocked VisitNotesBoard in
// PatientChart.jsx.
// ---------------------------------------------------------------
export default function VisitNoteBoard({ patientId }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);

  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeVisit, setActiveVisit] = useState(null); // { visit_id, discipline }

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    listVisitNotesForPatient(patientId)
      .then((rows) => setEntries(Array.isArray(rows) ? rows : []))
      .catch((err) => setError(err.message || "Unable to load this patient's visit notes."))
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleCreated = (visitId, discipline = "RN") => {
    setActiveVisit({ visit_id: visitId, discipline });
  };

  const handleSelect = (entry) => {
    setActiveVisit({ visit_id: entry.visit_id, discipline: entry.discipline });
  };

  if (!patientId) {
    return <div style={{ fontSize: 12, color: COLORS.gray, padding: 12 }}>Select a patient to view Visit Notes.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {activeVisit ? (
        <VisitNoteEditor
          visitId={activeVisit.visit_id}
          discipline={activeVisit.discipline}
          patientId={patientId}
          onSaved={reload}
          onCancel={() => {
            setActiveVisit(null);
            reload();
          }}
          styles={styles}
          COLORS={COLORS}
        />
      ) : (
        <>
          <AddNewVisitCard patientId={patientId} onCreated={handleCreated} styles={styles} COLORS={COLORS} />
          <Card title="Visit Notes" subtitle="RN/LVN visit notes plus MSW and SC assessment visits, most recent first." styles={styles}>
            {error && <div style={{ color: "#ef4444", fontSize: 12.5, marginBottom: 8 }}>{error}</div>}
            {loading ? (
              <div style={{ fontSize: 12, color: COLORS.gray }}>Loading visit notes…</div>
            ) : (
              <VisitNoteTimeline entries={entries} onSelect={handleSelect} styles={styles} COLORS={COLORS} />
            )}
          </Card>
        </>
      )}
    </div>
  );
}
