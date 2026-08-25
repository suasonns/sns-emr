import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useThemeMode } from "../theme/theme";
import { getRnicaColors, getRnicaStyles } from "../theme/clinicalDesign";
import { getCurrentUser } from "../api/session";
import { getSupervisorySchedule } from "../api/supervisorySchedule";
import { ContinuousCareLogSection } from "./RNICA";
import {
  VISIT_NOTE_FORM_TYPES,
  VISIT_NOTE_CARE_LEVELS,
  createVisitNote,
  getVisitNote,
  updateVisitNote,
  finalizeVisitNote,
  listVisitNotesForPatient,
} from "../api/visitNotes";
import {
  ADL_ACTIVITIES,
  AMBULATORY_STATUS_OPTIONS,
  ASSISTANCE_LEVEL_OPTIONS,
  VISIT_NOTE_BODY_SYSTEM_CARD_DEFINITIONS,
  BODY_SYSTEM_LOOKUP,
  CONCERN_OPTIONS,
  FAST_OPTIONS,
  FOLLOW_UP_OPTIONS,
  FUNCTIONAL_SCORE_OPTIONS,
  NYHA_OPTIONS,
  ORAL_INTAKE_OPTIONS,
  PRESENT_OPTIONS,
  RESPONSE_OPTIONS,
  SEVERITY_OPTIONS,
  VISIT_NOTE_SECTION_ITEMS,
  buildVisitNoteNavItems,
  buildVisitNoteComparisonState,
  createEmptySupervisoryReview,
  formatComparableDate,
  hasStartedSupervisoryReview,
  validateSupervisoryReview,
} from "./visitNoteHelpers";

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
  functional_decline: {
    kps: null,
    pps: null,
    fast: "",
    nyha: "",
  },
  signs_symptoms: {},
  supervisory_review: createEmptySupervisoryReview(),
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
  death_disposal: {
    hospice_received_call_at: "",
    pronounced_death_at: "",
    pronounced_by: "",
    pronounced_by_name: "",
    evidenced_by: [],
    mortuary_notified_at: "",
    mortuary_name: "",
    physician_idg_notified_at: "",
    family_instructed_on_narcotic_disposal: false,
    narcotics: [],
    witnessed_or_stated_by: "",
  },
  narrative: "",
  psychosocial_symptoms: "",
  spiritual_symptoms: "",
};

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

const CHECKLIST_ITEMS = [
  ["updated_family_pcg", "Update Family/PCG"],
  ["updated_cm_md", "Update CM/MD"],
  ["comfort_pack_med_checked", "Comfort Pack/Med Checked"],
  ["dme_inspected", "DME Inspected"],
  ["gi_tube_checked", "Check GI Tube"],
  ["next_visit_confirmed", "Confirmed Schedule of Next Visit"],
];

function safeString(value) {
  return value == null ? "" : String(value);
}

function isFullBodyFormType(formType) {
  if (!formType) return true;
  const match = VISIT_NOTE_FORM_TYPES.find((item) => item.value === formType);
  return match ? match.fullBody : false;
}

function mergeContent(recordContent = {}) {
  return {
    ...DEFAULT_CONTENT,
    ...recordContent,
    pain: { ...DEFAULT_CONTENT.pain, ...(recordContent.pain || {}) },
    vitals: { ...DEFAULT_CONTENT.vitals, ...(recordContent.vitals || {}) },
    functional_decline: { ...DEFAULT_CONTENT.functional_decline, ...(recordContent.functional_decline || {}) },
    care_provided: { ...DEFAULT_CONTENT.care_provided, ...(recordContent.care_provided || {}) },
    visit_checklist: { ...DEFAULT_CONTENT.visit_checklist, ...(recordContent.visit_checklist || {}) },
    supervisory_review: {
      ...createEmptySupervisoryReview(),
      ...(recordContent.supervisory_review || {}),
      hha: { ...(recordContent.supervisory_review?.hha || {}) },
      lvn_lpn: { ...(recordContent.supervisory_review?.lvn_lpn || {}) },
    },
    signs_symptoms: { ...(recordContent.signs_symptoms || {}) },
    death_disposal: {
      ...DEFAULT_CONTENT.death_disposal,
      ...(recordContent.death_disposal || {}),
      evidenced_by: [...(recordContent.death_disposal?.evidenced_by || [])],
      narcotics: (recordContent.death_disposal?.narcotics || []).map((item) => ({ ...item })),
    },
  };
}

function FormInput({ label, value, onChange, type = "text", disabled, styles, COLORS, required, min, max, step }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required ? <span style={{ color: COLORS.error }}>*</span> : null}
      </label>
      <input
        style={{ ...styles.input, ...(disabled ? { opacity: 0.65, cursor: "not-allowed" } : {}) }}
        type={type}
        value={value ?? ""}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options, disabled, styles, placeholder = "— Select One —", required }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required ? "*" : ""}
      </label>
      <select
        style={{ ...styles.select, ...(disabled ? { opacity: 0.65, cursor: "not-allowed" } : {}) }}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => {
          const item = typeof option === "string" ? { value: option, label: option } : option;
          return (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          );
        })}
      </select>
    </div>
  );
}

function FormTextarea({ label, value, onChange, rows = 4, disabled, styles }) {
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <textarea
        style={{ ...styles.textarea, minHeight: rows * 24, ...(disabled ? { opacity: 0.65, cursor: "not-allowed" } : {}) }}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      />
    </div>
  );
}

function Card({ title, subtitle, actions, children, styles }) {
  return (
    <div style={styles.card}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <div style={styles.cardTitle}>{title}</div>
        {actions}
      </div>
      {subtitle ? <p style={styles.sectionSubtitle}>{subtitle}</p> : null}
      {children}
    </div>
  );
}

function ComparisonBadge({ label, COLORS }) {
  const colors = {
    Improved: { color: COLORS.success || "#16a34a", background: "rgba(22,163,74,0.12)" },
    Stable: { color: COLORS.dark, background: "rgba(148,163,184,0.14)" },
    Worsened: { color: COLORS.error || "#dc2626", background: "rgba(220,38,38,0.12)" },
    "Not comparable": { color: COLORS.warning || "#d97706", background: "rgba(245,158,11,0.12)" },
    "No previous documented value": { color: COLORS.gray, background: "rgba(148,163,184,0.12)" },
  };
  const tone = colors[label] || colors["Not comparable"];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, borderRadius: 999, padding: "3px 9px", fontSize: 11, fontWeight: 700, color: tone.color, background: tone.background }}>
      {label}
    </span>
  );
}

function ComparisonGrid({ items, styles, COLORS, onJump }) {
  if (!items?.length) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 8, marginBottom: 10 }}>
      {items.map((item) => (
        <button
          key={item.key}
          type="button"
          onClick={() => onJump?.(item.sectionId)}
          style={{
            border: `1px solid ${COLORS.border || "#334155"}`,
            borderRadius: 8,
            background: "transparent",
            color: COLORS.dark,
            padding: "8px 10px",
            textAlign: "left",
            cursor: onJump ? "pointer" : "default",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <strong style={{ fontSize: 12.5 }}>{item.label}</strong>
            <ComparisonBadge label={item.statusLabel} COLORS={COLORS} />
          </div>
          <div style={{ marginTop: 4, fontSize: 11.5, color: COLORS.gray }}>
            Previous: {item.previousDisplay || "—"} {item.previousDate ? `· ${formatComparableDate(item.previousDate)}` : ""}
          </div>
          <div style={{ marginTop: 4, fontSize: 12 }}>{item.currentDisplay || "Current not documented"}</div>
          {item.changeText ? <div style={{ marginTop: 2, fontSize: 11.5, color: COLORS.gray }}>{item.changeText}</div> : null}
        </button>
      ))}
    </div>
  );
}

function ValidationErrorSummary({ errors, onJump, COLORS }) {
  if (!errors.length) return null;
  return (
    <div style={{ border: `1px solid ${COLORS.error || "#ef4444"}`, borderRadius: 10, padding: 12, background: "rgba(239,68,68,0.08)" }}>
      <div style={{ fontSize: 12.5, fontWeight: 800, color: COLORS.error || "#ef4444", marginBottom: 8 }}>Complete these items before signing:</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {errors.map((error, index) => (
          <button
            key={`${error.sectionId}-${index}`}
            type="button"
            onClick={() => onJump(error.sectionId)}
            style={{ background: "transparent", border: "none", color: COLORS.dark, textAlign: "left", padding: 0, cursor: "pointer", fontSize: 12.5 }}
          >
            • {error.message}
          </button>
        ))}
      </div>
    </div>
  );
}

function StickySectionNav({ items, activeSectionId, onJump, COLORS, compact }) {
  const narrativeButton = (
    <button
      type="button"
      onClick={() => onJump("narrative")}
      style={{
        borderRadius: 999,
        border: `1px solid ${COLORS.accent || COLORS.primary || "#0f766e"}`,
        background: "rgba(13,148,136,0.14)",
        color: COLORS.accent || COLORS.primary || "#0f766e",
        padding: "6px 12px",
        fontSize: 11.5,
        fontWeight: 800,
        cursor: "pointer",
        whiteSpace: "nowrap",
      }}
    >
      Jump to Narrative
    </button>
  );

  if (compact) {
    return (
      <div style={{ position: "sticky", top: 12, zIndex: 4, marginBottom: 8 }}>
        <div style={{ display: "grid", gap: 8, padding: 10, borderRadius: 10, border: `1px solid ${COLORS.border || "#334155"}`, background: COLORS.card, boxShadow: "0 10px 24px rgba(15, 23, 42, 0.08)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: "0.04em", textTransform: "uppercase", color: COLORS.gray }}>Visit note navigation</div>
              <div style={{ fontSize: 12, color: COLORS.dark }}>Jump between sections without losing your place.</div>
            </div>
            {narrativeButton}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label style={{ fontSize: 11.5, fontWeight: 700, color: COLORS.gray }}>Section</label>
            <select
              value={activeSectionId}
              onChange={(event) => onJump(event.target.value)}
              style={{ flex: 1, minHeight: 34, borderRadius: 8, border: `1px solid ${COLORS.border || "#334155"}`, background: "transparent", color: COLORS.dark }}
            >
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: "sticky", top: 12, zIndex: 4, marginBottom: 8 }}>
      <div style={{ display: "grid", gap: 10, padding: 10, borderRadius: 10, border: `1px solid ${COLORS.border || "#334155"}`, background: COLORS.card, boxShadow: "0 10px 24px rgba(15, 23, 42, 0.08)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: "0.04em", textTransform: "uppercase", color: COLORS.gray }}>Visit note navigation</div>
            <div style={{ fontSize: 12, color: COLORS.dark }}>{items.length} sections in documented order.</div>
          </div>
          {narrativeButton}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {items.map((item) => {
            const active = item.id === activeSectionId;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onJump(item.id)}
                style={{
                  borderRadius: 999,
                  border: `1px solid ${active ? COLORS.accent || COLORS.primary || "#0f766e" : COLORS.border || "#334155"}`,
                  background: active ? "rgba(13,148,136,0.14)" : "transparent",
                  color: active ? COLORS.accent || COLORS.primary || "#0f766e" : COLORS.dark,
                  padding: "6px 10px",
                  fontSize: 11.5,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function FloatingNarrativeButton({ onJump, COLORS }) {
  return (
    <button
      type="button"
      onClick={() => onJump("narrative")}
      style={{
        position: "fixed",
        right: 24,
        bottom: 24,
        zIndex: 5,
        borderRadius: 999,
        border: `1px solid ${COLORS.border || "#334155"}`,
        background: COLORS.card,
        color: COLORS.dark,
        padding: "10px 14px",
        fontSize: 12,
        fontWeight: 800,
        cursor: "pointer",
        boxShadow: "0 10px 20px rgba(15, 23, 42, 0.22)",
      }}
    >
      Jump to Narrative
    </button>
  );
}

function Section({ anchorId, children }) {
  return (
    <section id={anchorId} style={{ scrollMarginTop: 120 }}>
      {children}
    </section>
  );
}

function BodySystemFields({ systemKey, value, onChange, disabled, styles, COLORS }) {
  const definition = BODY_SYSTEM_LOOKUP[systemKey];
  const row = value || {};
  const set = (key, nextValue) => onChange(systemKey, { ...row, [key]: nextValue });
  const toggleFinding = (finding) => {
    const current = Array.isArray(row.selected_findings) ? row.selected_findings : [];
    const next = current.includes(finding) ? current.filter((item) => item !== finding) : [...current, finding];
    set("selected_findings", next);
  };

  return (
    <div style={{ borderTop: `1px solid ${COLORS.border || "#334155"}`, padding: "12px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <strong style={{ fontSize: 13 }}>{definition.label}</strong>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5 }}>
          <input type="checkbox" checked={!!row.assessed_no_issues} disabled={disabled} onChange={(event) => set("assessed_no_issues", event.target.checked)} />
          Assessed / No issues reported
        </label>
      </div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
        {SEVERITY_OPTIONS.map((option) => (
          <label key={option.value} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5 }}>
            <input type="radio" name={`${systemKey}_severity`} checked={row.severity === option.value} disabled={disabled} onChange={() => set("severity", option.value)} />
            {option.label}
          </label>
        ))}
      </div>
      {definition.findings.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
          {definition.findings.map(([findingValue, findingLabel]) => (
            <label key={findingValue} style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "5px 8px", borderRadius: 999, border: `1px solid ${COLORS.border || "#334155"}`, fontSize: 11.5 }}>
              <input type="checkbox" checked={(row.selected_findings || []).includes(findingValue)} disabled={disabled} onChange={() => toggleFinding(findingValue)} />
              {findingLabel}
            </label>
          ))}
        </div>
      ) : null}
      <div style={{ ...styles.fieldsGrid, marginTop: 10 }}>
        {systemKey === "nutrition" ? (
          <>
            <FormSelect label="Oral Intake" value={row.oral_intake} onChange={(nextValue) => set("oral_intake", nextValue)} options={ORAL_INTAKE_OPTIONS} disabled={disabled} styles={styles} />
            <FormSelect label="Diet" value={row.diet} onChange={(nextValue) => set("diet", nextValue)} options={["Regular", "Mechanical Soft", "Pureed", "Liquid", "NPO", "Other"]} disabled={disabled} styles={styles} />
            <FormInput label="Diet Detail" value={row.diet_specify} onChange={(nextValue) => set("diet_specify", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        ) : null}
        {systemKey === "gu_reproductive" ? (
          <>
            <FormSelect label="Incontinent" value={row.incontinent} onChange={(nextValue) => set("incontinent", nextValue)} options={["None", "Bowel", "Bladder", "Both"]} disabled={disabled} styles={styles} />
            <FormInput label="Last BM" type="date" value={row.last_bm} onChange={(nextValue) => set("last_bm", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        ) : null}
        {systemKey === "mobility" ? (
          <>
            <FormSelect label="Ambulatory Status" value={row.ambulatory_status} onChange={(nextValue) => set("ambulatory_status", nextValue)} options={AMBULATORY_STATUS_OPTIONS} disabled={disabled} styles={styles} />
            <FormInput label="Assistive Device" value={row.assistive_device} onChange={(nextValue) => set("assistive_device", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
            <FormSelect label="Assistance Level" value={row.assistance_level} onChange={(nextValue) => set("assistance_level", nextValue)} options={ASSISTANCE_LEVEL_OPTIONS} disabled={disabled} styles={styles} />
            <FormInput label="Endurance" value={row.endurance} onChange={(nextValue) => set("endurance", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
            <FormInput label="Bedbound Status" value={row.bedbound_status} onChange={(nextValue) => set("bedbound_status", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
          </>
        ) : null}
        <FormInput label="Other Symptom" value={row.other_symptom} onChange={(nextValue) => set("other_symptom", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Other Observation" value={row.other_observation} onChange={(nextValue) => set("other_observation", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>
    </div>
  );
}

function AdlSection({ value, onChange, disabled, styles, COLORS }) {
  const row = value || {};
  const set = (key, nextValue) => onChange("adl_assessment", { ...row, [key]: nextValue });
  const calculate = () => {
    const scores = row.adl_scores || {};
    const total = ADL_ACTIVITIES.reduce((sum, item) => sum + (Number(scores[item.key]) || 0), 0);
    set("adl_total_score", total);
  };

  return (
    <div style={{ marginTop: 10 }}>
      <div style={styles.fieldsGrid}>
        {ADL_ACTIVITIES.map((activity) => (
          <FormSelect
            key={activity.key}
            label={activity.label}
            value={row.adl_scores?.[activity.key] != null ? String(row.adl_scores[activity.key]) : ""}
            onChange={(nextValue) => {
              const scores = { ...(row.adl_scores || {}) };
              scores[activity.key] = nextValue === "" ? null : Number(nextValue);
              set("adl_scores", scores);
            }}
            options={["0", "1", "2", "3"]}
            disabled={disabled}
            styles={styles}
          />
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8 }}>
        {!disabled ? (
          <button type="button" onClick={calculate} style={{ ...styles.btnSecondary, padding: "5px 10px", fontSize: 11.5 }}>
            Calculate ADL Score
          </button>
        ) : null}
        <span style={{ fontSize: 12.5, color: COLORS.dark }}>
          Total Score: <strong>{row.adl_total_score ?? "—"}</strong>
        </span>
      </div>
    </div>
  );
}

function VisitDetailsCard({ content, onChange, disabled, styles, COLORS, discipline }) {
  const set = (key, nextValue) => onChange({ ...content, [key]: nextValue });
  return (
    <Card title="Visit Details" styles={styles}>
      <div style={styles.fieldsGrid}>
        <FormInput label="Entered By" value={content.entered_by} onChange={(nextValue) => set("entered_by", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Staff Assigned" value={content.staff_assigned} onChange={(nextValue) => set("staff_assigned", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <div style={styles.formGroup}>
          <label style={styles.label}>Discipline</label>
          <input style={{ ...styles.input, opacity: 0.7 }} value={discipline || ""} disabled readOnly />
        </div>
        <FormSelect label="Care Level" value={content.care_level} onChange={(nextValue) => set("care_level", nextValue)} options={VISIT_NOTE_CARE_LEVELS} disabled={disabled} styles={styles} />
        <FormSelect label="Type Of" value={content.type_of_visit} onChange={(nextValue) => set("type_of_visit", nextValue)} options={["In-Person", "Telephone", "Video"]} disabled={disabled} styles={styles} />
        <FormSelect label="Visit" value={content.visit_kind} onChange={(nextValue) => set("visit_kind", nextValue)} options={["Scheduled", "Unscheduled"]} disabled={disabled} styles={styles} />
        <FormSelect label="Form Type" value={content.form_type} onChange={(nextValue) => set("form_type", nextValue)} options={VISIT_NOTE_FORM_TYPES.map((item) => ({ value: item.value, label: item.label }))} disabled={disabled} styles={styles} />
        <FormInput label="Visit Date" type="date" value={content.visit_date} onChange={(nextValue) => set("visit_date", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Time In" type="time" value={content.time_in} onChange={(nextValue) => set("time_in", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Time Out" type="time" value={content.time_out} onChange={(nextValue) => set("time_out", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Duration" value={content.duration} onChange={(nextValue) => set("duration", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <label style={{ ...styles.formGroup, display: "flex", alignItems: "center", gap: 6, marginTop: 18 }}>
          <input type="checkbox" checked={!!content.correction} onChange={(event) => set("correction", event.target.checked)} disabled={disabled} />
          <span style={{ ...styles.label, marginBottom: 0 }}>Correction</span>
        </label>
      </div>
    </Card>
  );
}

function SinceLastComparableVisitCard({ comparisonState, onJump, styles, COLORS }) {
  const previousLabel = comparisonState.previousEntry
    ? `${formatComparableDate(comparisonState.previousEntry.visit_date || comparisonState.previousEntry.visit_datetime)}${comparisonState.previousEntry.form_type ? ` · ${comparisonState.previousEntry.form_type}` : ""}`
    : "";

  return (
    <Card
      title="Since Last Comparable Visit"
      subtitle={comparisonState.previousEntry ? `Using the most recent prior finalized comparable visit: ${previousLabel}` : "No prior finalized comparable RN visit was found for the currently selected visit date."}
      styles={styles}
    >
      {comparisonState.summaryItems.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {comparisonState.summaryItems.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onJump(item.sectionId)}
              style={{ borderRadius: 999, border: `1px solid ${COLORS.border || "#334155"}`, background: "transparent", color: COLORS.dark, padding: "7px 12px", fontSize: 11.5, fontWeight: 700, cursor: "pointer" }}
            >
              {item.label}: {item.text} · {item.statusLabel}
            </button>
          ))}
        </div>
      ) : (
        <div style={styles.infoBox}>No supported previous/current comparison pairs are documented yet for this visit note.</div>
      )}
    </Card>
  );
}

function PainCard({ pain, comparisons, onChange, disabled, styles, COLORS, onJump }) {
  const set = (key, nextValue) => onChange({ ...pain, [key]: nextValue });
  return (
    <Card title="Pain" styles={styles}>
      <ComparisonGrid items={comparisons} styles={styles} COLORS={COLORS} onJump={onJump} />
      <div style={styles.fieldsGrid}>
        <FormSelect label="Pain Controlled" value={pain.controlled} onChange={(nextValue) => set("controlled", nextValue)} options={["Y", "N", "Unable", "N/A"]} disabled={disabled} styles={styles} />
        <FormInput label="Pain Level (0-10)" type="number" value={pain.pain_level ?? ""} min={0} max={10} onChange={(nextValue) => set("pain_level", nextValue === "" ? null : Number(nextValue))} disabled={disabled} styles={styles} COLORS={COLORS} />
        <div style={{ ...styles.formGroup, gridColumn: "1 / -1" }}>
          <label style={styles.label}>Other Observation</label>
          <input style={styles.input} value={pain.other_observation ?? ""} disabled={disabled} onChange={(event) => set("other_observation", event.target.value)} />
        </div>
      </div>
    </Card>
  );
}

function VitalsMeasurementsCard({ vitals, comparisons, onChange, disabled, styles, COLORS, onJump }) {
  const set = (key, nextValue) => onChange({ ...vitals, [key]: nextValue });
  return (
    <Card title="Vitals and Measurements" styles={styles}>
      <ComparisonGrid items={comparisons} styles={styles} COLORS={COLORS} onJump={onJump} />
      <div style={styles.fieldsGrid}>
        <FormInput label="Temp" value={vitals.temperature} onChange={(nextValue) => set("temperature", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="Temp Position" value={vitals.temperature_position} onChange={(nextValue) => set("temperature_position", nextValue)} options={["Oral", "Axillary", "Tympanic", "Rectal"]} disabled={disabled} styles={styles} />
        <FormInput label="Pulse" value={vitals.pulse} onChange={(nextValue) => set("pulse", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Resp" value={vitals.respirations} onChange={(nextValue) => set("respirations", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BP Systolic" value={vitals.bp_systolic} onChange={(nextValue) => set("bp_systolic", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BP Diastolic" value={vitals.bp_diastolic} onChange={(nextValue) => set("bp_diastolic", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="BP Position" value={vitals.bp_position} onChange={(nextValue) => set("bp_position", nextValue)} options={["Sitting", "Standing", "Lying"]} disabled={disabled} styles={styles} />
        <FormInput label="Height" value={vitals.height} onChange={(nextValue) => set("height", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="O2 Sat %" value={vitals.o2_sat} onChange={(nextValue) => set("o2_sat", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="O2 Delivery" value={vitals.o2_delivery} onChange={(nextValue) => set("o2_delivery", nextValue)} options={["Room Air", "Nasal Cannula", "Non-Rebreather", "Ventilator", "Other"]} disabled={disabled} styles={styles} />
        <label style={{ ...styles.formGroup, display: "flex", alignItems: "center", gap: 6, marginTop: 18 }}>
          <input type="checkbox" checked={!!vitals.unable_to_assess} onChange={(event) => set("unable_to_assess", event.target.checked)} disabled={disabled} />
          <span style={{ ...styles.label, marginBottom: 0 }}>Unable to Assess</span>
        </label>
      </div>
    </Card>
  );
}

function FunctionalDeclineCard({ content, comparisons, onContentChange, disabled, styles, COLORS, onJump, buildAnchor }) {
  const mobility = content.signs_symptoms.mobility || {};
  const adl = content.signs_symptoms.adl_assessment || {};
  const functional = content.functional_decline || {};
  const setSystem = (key, nextValue) => onContentChange((current) => ({ ...current, signs_symptoms: { ...current.signs_symptoms, [key]: nextValue } }));
  const setFunctional = (key, nextValue) => onContentChange((current) => ({ ...current, functional_decline: { ...current.functional_decline, [key]: nextValue } }));

  return (
    <Card title="Functional and Decline Indicators" subtitle="Mobility, ADL, and decline scores remain independently documented while prior values stay read-only." styles={styles}>
      <ComparisonGrid items={comparisons} styles={styles} COLORS={COLORS} onJump={onJump} />
      <Section anchorId={buildAnchor("mobility")}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 800, color: COLORS.dark, marginBottom: 6 }}>Mobility</div>
          <BodySystemFields systemKey="mobility" value={mobility} onChange={setSystem} disabled={disabled} styles={styles} COLORS={COLORS} />
        </div>
      </Section>
      <Section anchorId={buildAnchor("adl")}>
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: COLORS.dark, marginBottom: 6 }}>ADL</div>
          <AdlSection value={adl} onChange={setSystem} disabled={disabled} styles={styles} COLORS={COLORS} />
        </div>
      </Section>
      <div style={{ ...styles.fieldsGrid, marginTop: 12 }}>
        <FormSelect label="KPS" value={functional.kps != null ? String(functional.kps) : ""} onChange={(nextValue) => setFunctional("kps", nextValue === "" ? null : Number(nextValue))} options={FUNCTIONAL_SCORE_OPTIONS} disabled={disabled} styles={styles} />
        <FormSelect label="PPS" value={functional.pps != null ? String(functional.pps) : ""} onChange={(nextValue) => setFunctional("pps", nextValue === "" ? null : Number(nextValue))} options={FUNCTIONAL_SCORE_OPTIONS} disabled={disabled} styles={styles} />
        <FormSelect label="FAST" value={functional.fast || ""} onChange={(nextValue) => setFunctional("fast", nextValue)} options={FAST_OPTIONS} disabled={disabled} styles={styles} />
        <FormSelect label="NYHA" value={functional.nyha || ""} onChange={(nextValue) => setFunctional("nyha", nextValue)} options={NYHA_OPTIONS} disabled={disabled} styles={styles} />
      </div>
    </Card>
  );
}

function NutritionCard({ content, comparisons, onContentChange, disabled, styles, COLORS, onJump }) {
  const nutrition = content.signs_symptoms.nutrition || {};
  const vitals = content.vitals || {};
  const setNutrition = (systemKey, nextValue) => onContentChange((current) => ({ ...current, signs_symptoms: { ...current.signs_symptoms, [systemKey]: nextValue } }));
  const setVitals = (key, nextValue) => onContentChange((current) => ({ ...current, vitals: { ...current.vitals, [key]: nextValue } }));

  return (
    <Card title="Nutrition" subtitle="Nutrition findings, intake, and weight-related measurements stay grouped together for quicker hospice decline review." styles={styles}>
      <ComparisonGrid items={comparisons} styles={styles} COLORS={COLORS} onJump={onJump} />
      <BodySystemFields systemKey="nutrition" value={nutrition} onChange={setNutrition} disabled={disabled} styles={styles} COLORS={COLORS} />
      <div style={{ ...styles.fieldsGrid, marginTop: 10 }}>
        <FormInput label="Weight" value={vitals.weight} onChange={(nextValue) => setVitals("weight", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="MAC" value={vitals.mac} onChange={(nextValue) => setVitals("mac", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="BMI" value={vitals.bmi} onChange={(nextValue) => setVitals("bmi", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>
    </Card>
  );
}

function BodySystemsCard({ content, comparisonsBySection, onContentChange, disabled, styles, COLORS, onJump, buildAnchor }) {
  const setSystem = (systemKey, nextValue) => onContentChange((current) => ({ ...current, signs_symptoms: { ...current.signs_symptoms, [systemKey]: nextValue } }));
  return (
    <Card title="Signs and Symptoms / Body Systems" subtitle="Structured findings are centralized by body system while preserving the existing severity and free-text observations." styles={styles}>
      {VISIT_NOTE_BODY_SYSTEM_CARD_DEFINITIONS.map((definition) => (
        <Section key={definition.key} anchorId={buildAnchor(definition.sectionId)}>
          <ComparisonGrid items={comparisonsBySection[definition.sectionId] || []} styles={styles} COLORS={COLORS} onJump={onJump} />
          <BodySystemFields systemKey={definition.key} value={content.signs_symptoms[definition.key]} onChange={setSystem} disabled={disabled} styles={styles} COLORS={COLORS} />
        </Section>
      ))}
    </Card>
  );
}

function FallSafetyCard({ content, comparisons, onContentChange, disabled, styles, COLORS, onJump }) {
  const setSystem = (systemKey, nextValue) => onContentChange((current) => ({ ...current, signs_symptoms: { ...current.signs_symptoms, [systemKey]: nextValue } }));
  return (
    <Card title="Fall / Incident and Safety" styles={styles}>
      <ComparisonGrid items={comparisons} styles={styles} COLORS={COLORS} onJump={onJump} />
      <BodySystemFields systemKey="fall_incidence" value={content.signs_symptoms.fall_incidence} onChange={setSystem} disabled={disabled} styles={styles} COLORS={COLORS} />
      <BodySystemFields systemKey="safety_issues" value={content.signs_symptoms.safety_issues} onChange={setSystem} disabled={disabled} styles={styles} COLORS={COLORS} />
    </Card>
  );
}

function SupervisorySubform({ title, form, onChange, assignments, disabled, styles, COLORS, questionConfig }) {
  const set = (key, nextValue) => onChange({ ...form, [key]: nextValue });
  const assignmentOptions = assignments.map((assignment) => ({
    value: assignment.user_id,
    label: `${assignment.name} · ${assignment.discipline}${assignment.is_primary ? " · Primary" : ""}`,
  }));
  return (
    <div style={{ border: `1px solid ${COLORS.border || "#334155"}`, borderRadius: 10, padding: 12, marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
        <strong style={{ fontSize: 13 }}>{title}</strong>
        <span style={{ fontSize: 11.5, color: COLORS.gray }}>{assignments.length ? "Assignments sourced from active patient assignments." : "No active assignment documented."}</span>
      </div>
      <div style={{ ...styles.fieldsGrid, marginTop: 10 }}>
        <FormSelect label={`Assigned ${title}`} value={form.assigned_staff_user_id} onChange={(nextValue) => {
          const match = assignments.find((assignment) => assignment.user_id === nextValue);
          set("assigned_staff_user_id", nextValue);
          set("assigned_staff_name", match?.name || "");
        }} options={assignmentOptions} disabled={disabled || !assignments.length} styles={styles} />
        <FormSelect label="Supervision Type" value={form.supervision_type} onChange={(nextValue) => set("supervision_type", nextValue)} options={PRESENT_OPTIONS} disabled={disabled} styles={styles} />
        <FormInput label="Observation Date/Time" type="datetime-local" value={form.observation_datetime || ""} onChange={(nextValue) => set("observation_datetime", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="RN Supervisor" value={form.rn_supervisor_name || ""} onChange={(nextValue) => set("rn_supervisor_name", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>
      {form.supervision_type === "NOT_PRESENT" ? (
        <div style={{ ...styles.infoBox, marginTop: 8 }}>
          Staff not present: complete findings from record review or patient/family report only. Use “Unable to determine” rather than implying direct observation.
        </div>
      ) : null}
      <div style={{ ...styles.fieldsGrid, marginTop: 10 }}>
        {questionConfig.map((question) => (
          <FormSelect key={question.key} label={question.label} value={form[question.key] || ""} onChange={(nextValue) => set(question.key, nextValue)} options={RESPONSE_OPTIONS} disabled={disabled} styles={styles} />
        ))}
        <FormSelect label="Patient / Family Concerns" value={form.patient_family_concerns || ""} onChange={(nextValue) => set("patient_family_concerns", nextValue)} options={CONCERN_OPTIONS} disabled={disabled} styles={styles} />
        <FormTextarea label="Concern Details" value={form.concern_details || ""} onChange={(nextValue) => set("concern_details", nextValue)} disabled={disabled} rows={3} styles={styles} />
        <FormSelect label="Corrective Action or Follow-up Required" value={form.corrective_action_required || ""} onChange={(nextValue) => set("corrective_action_required", nextValue)} options={FOLLOW_UP_OPTIONS} disabled={disabled} styles={styles} />
        <FormTextarea label="Corrective Action / Follow-up Details" value={form.corrective_action_details || ""} onChange={(nextValue) => set("corrective_action_details", nextValue)} disabled={disabled} rows={3} styles={styles} />
        <FormSelect label="Notification Documented" value={form.notification_documented || ""} onChange={(nextValue) => set("notification_documented", nextValue)} options={FOLLOW_UP_OPTIONS} disabled={disabled} styles={styles} />
        <FormInput label="Person Notified" value={form.person_notified || ""} onChange={(nextValue) => set("person_notified", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Notification Date/Time" type="datetime-local" value={form.notification_datetime || ""} onChange={(nextValue) => set("notification_datetime", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormSelect label="Follow-up Required" value={form.follow_up_required || ""} onChange={(nextValue) => set("follow_up_required", nextValue)} options={FOLLOW_UP_OPTIONS} disabled={disabled} styles={styles} />
        <FormInput label="Follow-up Due Date" type="date" value={form.follow_up_due_date || ""} onChange={(nextValue) => set("follow_up_due_date", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>
      <FormTextarea label="Supervisor Comments" value={form.supervisor_comments || ""} onChange={(nextValue) => set("supervisor_comments", nextValue)} disabled={disabled} rows={3} styles={styles} />
      {form.audit?.updated_at ? (
        <div style={{ marginTop: 8, fontSize: 11.5, color: COLORS.gray }}>
          Last saved {formatComparableDate(form.audit.updated_at)}{form.audit.finalized_at ? ` · finalized ${formatComparableDate(form.audit.finalized_at)}` : ""}
        </div>
      ) : null}
    </div>
  );
}

function RNReviewCard({ content, supervisoryContext, onContentChange, disabled, styles, COLORS }) {
  if (!supervisoryContext?.visible) return null;
  const review = content.supervisory_review || createEmptySupervisoryReview();
  const setReview = (key, nextValue) => onContentChange((current) => ({ ...current, supervisory_review: { ...(current.supervisory_review || createEmptySupervisoryReview()), [key]: nextValue } }));
  const locked = disabled || !supervisoryContext.can_edit;

  return (
    <Card title="RN Supervisory Review" subtitle={supervisoryContext.derivation_note || "Separate HHA and LVN/LPN supervisory documentation is stored independently."} styles={styles}>
      {!supervisoryContext.can_edit && !disabled ? (
        <div style={styles.infoBox}>You may view saved RN supervisory documentation here, but only authorized RN/supervisory roles may edit it.</div>
      ) : null}
      <div style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 12, color: COLORS.gray }}>
          HHA: {supervisoryContext.hha.service_status} · Last completed: {supervisoryContext.hha.last_completed?.visit_date ? formatComparableDate(supervisoryContext.hha.last_completed.visit_date) : "Not documented"} · {supervisoryContext.hha.status_label}
        </div>
        <div style={{ fontSize: 12, color: COLORS.gray }}>
          LVN/LPN: {supervisoryContext.lvn_lpn.service_status} · Last completed: {supervisoryContext.lvn_lpn.last_completed?.visit_date ? formatComparableDate(supervisoryContext.lvn_lpn.last_completed.visit_date) : "Not documented"} · {supervisoryContext.lvn_lpn.status_label}
        </div>
      </div>
      {supervisoryContext.hha.applicable || hasStartedSupervisoryReview(review.hha) ? (
        <SupervisorySubform
          title="HHA"
          form={review.hha || {}}
          onChange={(nextValue) => setReview("hha", nextValue)}
          assignments={supervisoryContext.hha.assignments || []}
          disabled={locked}
          styles={styles}
          COLORS={COLORS}
          questionConfig={[
            { key: "services_meet_patient_needs", label: "HHA services meet patient needs" },
            { key: "follows_care_plan", label: "HHA follows current aide care plan" },
            { key: "demonstrates_competency", label: "HHA demonstrates competency" },
            { key: "communication_appropriate", label: "HHA communication appropriate" },
            { key: "infection_control_safety", label: "HHA infection-control and safety practices followed" },
          ]}
        />
      ) : null}
      {supervisoryContext.lvn_lpn.applicable || hasStartedSupervisoryReview(review.lvn_lpn) ? (
        <SupervisorySubform
          title="LVN/LPN"
          form={review.lvn_lpn || {}}
          onChange={(nextValue) => setReview("lvn_lpn", nextValue)}
          assignments={supervisoryContext.lvn_lpn.assignments || []}
          disabled={locked}
          styles={styles}
          COLORS={COLORS}
          questionConfig={[
            { key: "services_meet_patient_needs", label: "LVN/LPN services meet patient needs" },
            { key: "follows_care_plan", label: "Current plan of care followed" },
            { key: "ordered_interventions_completed", label: "Ordered interventions completed appropriately" },
            { key: "documentation_consistent", label: "Documentation reviewed and consistent" },
            { key: "demonstrates_competency", label: "Skills/tasks performed competently" },
            { key: "communication_appropriate", label: "Communication appropriate" },
            { key: "infection_control_safety", label: "Infection-control and safety practices followed" },
          ]}
        />
      ) : null}
      {!supervisoryContext.hha.applicable && !supervisoryContext.lvn_lpn.applicable && !hasStartedSupervisoryReview(review.hha) && !hasStartedSupervisoryReview(review.lvn_lpn) ? (
        <div style={styles.infoBox}>No active HHA or LVN/LPN patient assignment is documented for this patient.</div>
      ) : null}
    </Card>
  );
}

// Structured After-Death Visit + Medication/Narcotic Disposal section (see
// visit_notes_scheduling_spec.md section 2). Real reference fields taken
// from HospiceMD's standalone "Report of Death and Disposal of Controlled
// Drugs" form, folded into the visit note itself so the two are never
// disconnected records.
const PRONOUNCED_BY_OPTIONS = [
  ["FACILITY_STAFF", "Facility Staff"],
  ["FAMILY_PCG", "Family / PCG"],
  ["HOSPICE_STAFF", "Hospice Staff"],
  ["PHYSICIAN", "Physician"],
  ["PARAMEDIC_AMBULANCE", "Paramedic / Ambulance"],
];
const EVIDENCED_BY_OPTIONS = [
  ["VITAL_SIGNS_ABSENT", "Absence of Vital Signs"],
  ["TACTILE_VERBAL_PUPIL_RESPONSE_ABSENT", "Absence of Tactile, Verbal, or Pupil Response"],
];

function DeathDisposalCard({ value, onChange, disabled, styles, COLORS }) {
  const set = (key, nextValue) => onChange({ ...value, [key]: nextValue });
  const toggleEvidencedBy = (key) => {
    const current = value.evidenced_by || [];
    set("evidenced_by", current.includes(key) ? current.filter((k) => k !== key) : [...current, key]);
  };
  const narcotics = value.narcotics || [];
  const setNarcotic = (index, field, nextValue) => {
    const next = narcotics.map((item, i) => (i === index ? { ...item, [field]: nextValue } : item));
    set("narcotics", next);
  };
  const addNarcotic = () => set("narcotics", [...narcotics, { drug_name: "", quantity: "", disposal_method: "" }]);
  const removeNarcotic = (index) => set("narcotics", narcotics.filter((_, i) => i !== index));

  return (
    <Card title="After-Death Visit — Medication/Narcotic Disposal" styles={styles}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
        <FormInput label="Hospice Received Call" type="datetime-local" value={value.hospice_received_call_at} onChange={(v) => set("hospice_received_call_at", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Date/Time of Pronounced Death" type="datetime-local" value={value.pronounced_death_at} onChange={(v) => set("pronounced_death_at", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Mortuary Notified Date/Time" type="datetime-local" value={value.mortuary_notified_at} onChange={(v) => set("mortuary_notified_at", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Mortuary Name" value={value.mortuary_name} onChange={(v) => set("mortuary_name", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
        <FormInput label="Physician/IDG Notified Date/Time" type="datetime-local" value={value.physician_idg_notified_at} onChange={(v) => set("physician_idg_notified_at", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>

      <div style={{ marginTop: 10 }}>
        <div style={styles.label}>Pronounced/Attended By</div>
        <div style={styles.checkboxGroup}>
          {PRONOUNCED_BY_OPTIONS.map(([key, label]) => (
            <label key={key} style={styles.checkboxLabel}>
              <input type="radio" name="pronounced_by" checked={value.pronounced_by === key} disabled={disabled} onChange={() => set("pronounced_by", key)} />
              {label}
            </label>
          ))}
        </div>
        <FormInput label="Pronounced/Attended By — Name" value={value.pronounced_by_name} onChange={(v) => set("pronounced_by_name", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>

      <div style={{ marginTop: 10 }}>
        <div style={styles.label}>As Evidenced by Absence of</div>
        <div style={styles.checkboxGroup}>
          {EVIDENCED_BY_OPTIONS.map(([key, label]) => (
            <label key={key} style={styles.checkboxLabel}>
              <input type="checkbox" checked={(value.evidenced_by || []).includes(key)} disabled={disabled} onChange={() => toggleEvidencedBy(key)} />
              {label}
            </label>
          ))}
        </div>
      </div>

      <label style={{ ...styles.checkboxLabel, marginTop: 10, display: "flex" }}>
        <input type="checkbox" checked={!!value.family_instructed_on_narcotic_disposal} disabled={disabled} onChange={(event) => set("family_instructed_on_narcotic_disposal", event.target.checked)} />
        Family/PCG instructed on proper disposal of narcotics
      </label>

      <div style={{ marginTop: 12 }}>
        <div style={styles.label}>Narcotic / Controlled Drug Disposal</div>
        {narcotics.map((item, index) => (
          <div key={index} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 2fr auto", gap: 8, marginBottom: 6, alignItems: "end" }}>
            <FormInput label="Drug Name" value={item.drug_name} onChange={(v) => setNarcotic(index, "drug_name", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
            <FormInput label="Quantity" value={item.quantity} onChange={(v) => setNarcotic(index, "quantity", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
            <FormInput label="Disposal Method" value={item.disposal_method} onChange={(v) => setNarcotic(index, "disposal_method", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
            {!disabled ? (
              <button type="button" onClick={() => removeNarcotic(index)} style={{ ...styles.btnSecondary, height: 34 }}>Remove</button>
            ) : null}
          </div>
        ))}
        {!disabled ? (
          <button type="button" onClick={addNarcotic} style={styles.btnSecondary}>+ Add Drug</button>
        ) : null}
      </div>

      <div style={{ marginTop: 10 }}>
        <FormInput label="Witnessed or Stated By" value={value.witnessed_or_stated_by} onChange={(v) => set("witnessed_or_stated_by", v)} disabled={disabled} styles={styles} COLORS={COLORS} />
      </div>
    </Card>
  );
}

function CareProvidedCard({ value, onChange, disabled, styles, COLORS }) {
  const set = (key, nextValue) => onChange({ ...value, [key]: nextValue });
  return (
    <Card title="Care Provided" styles={styles}>
      <div style={styles.checkboxGroup}>
        {CARE_PROVIDED_ITEMS.map(([key, label]) => (
          <label key={key} style={styles.checkboxLabel}>
            <input type="checkbox" checked={!!value[key]} disabled={disabled} onChange={(event) => set(key, event.target.checked)} />
            {label}
          </label>
        ))}
        <label style={styles.checkboxLabel}>
          <input type="checkbox" checked={!!value.other_needs} disabled={disabled} onChange={(event) => set("other_needs", event.target.checked)} />
          Other Needs
        </label>
      </div>
      {value.other_needs ? (
        <FormInput label="Other Needs — Specify" value={value.other_needs_text} onChange={(nextValue) => set("other_needs_text", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
      ) : null}
    </Card>
  );
}

// Shared narrative-style symptoms section for SC (Spiritual) and MSW
// (Psychosocial) visits. Kept as free narrative text rather than a checklist
// because we don't have a confirmed real checkbox list for either section —
// this avoids fabricating clinical fields that aren't backed by a real form.
function SymptomsCard({ title, value, onChange, disabled, styles }) {
  return (
    <Card title={title} styles={styles}>
      <FormTextarea label={title} value={value} onChange={onChange} disabled={disabled} styles={styles} rows={4} />
    </Card>
  );
}

function VisitChecklistCard({ checklist, onChange, disabled, styles, COLORS }) {
  const set = (key, nextValue) => onChange({ ...checklist, [key]: nextValue });
  return (
    <Card title="Visit Checklist" styles={styles}>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {CHECKLIST_ITEMS.map(([key, label]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontSize: 12.5, color: COLORS.dark, minWidth: 240 }}>{label}</span>
            {["Yes", "No"].map((option) => (
              <label key={option} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5 }}>
                <input type="radio" name={key} checked={checklist[key] === (option === "Yes")} disabled={disabled} onChange={() => set(key, option === "Yes")} />
                {option}
              </label>
            ))}
          </div>
        ))}
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <span style={{ fontSize: 12.5, color: COLORS.dark, minWidth: 240 }}>Check Foley Cath</span>
          {["Yes", "No"].map((option) => (
            <label key={option} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5 }}>
              <input type="radio" name="foley_cath_checked" checked={checklist.foley_cath_checked === (option === "Yes")} disabled={disabled} onChange={() => set("foley_cath_checked", option === "Yes")} />
              {option}
            </label>
          ))}
          {checklist.foley_cath_checked ? (
            <FormInput label="Last Changed" type="date" value={checklist.foley_cath_last_changed} onChange={(nextValue) => set("foley_cath_last_changed", nextValue)} disabled={disabled} styles={styles} COLORS={COLORS} />
          ) : null}
        </div>
      </div>
    </Card>
  );
}

function VisitNoteEditor({ visitId, discipline, patientId, onSaved, onCancel, styles, COLORS }) {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [visitStatus, setVisitStatus] = useState(null);
  const [comparableHistory, setComparableHistory] = useState([]);
  const [supervisoryContext, setSupervisoryContext] = useState({ visible: false, can_edit: false, hha: { applicable: false, assignments: [] }, lvn_lpn: { applicable: false, assignments: [] } });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [validationErrors, setValidationErrors] = useState([]);
  const [activeSectionId, setActiveSectionId] = useState("top");
  const [compactNav, setCompactNav] = useState(typeof window !== "undefined" ? window.innerWidth < 1080 : false);

  const currentUser = useMemo(() => getCurrentUser(), []);

  const anchor = useCallback((sectionId) => `visit-note-${visitId}-${sectionId}`, [visitId]);
  const scrollToSection = useCallback((sectionId) => {
    const element = document.getElementById(anchor(sectionId));
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveSectionId(sectionId);
    }
  }, [anchor]);

  useEffect(() => {
    const onResize = () => setCompactNav(window.innerWidth < 1080);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    getVisitNote(visitId)
      .then((record) => {
        setContent(mergeContent({
          ...record.content,
          entered_by: record.content?.entered_by || currentUser?.full_name || currentUser?.name || "",
        }));
        setVisitStatus(record.visit_status);
        setComparableHistory(record.comparable_history || []);
        setSupervisoryContext(record.supervisory_context || { visible: false, can_edit: false, hha: { applicable: false, assignments: [] }, lvn_lpn: { applicable: false, assignments: [] } });
      })
      .catch((reason) => setError(reason.message || "Unable to load this visit note."))
      .finally(() => setLoading(false));
  }, [currentUser, visitId]);

  const isFinalized = (visitStatus || "").toUpperCase() === "FINALIZED";
  const isCC = safeString(content.care_level).trim().toLowerCase() === "continuous care";
  const isFullBody = isFullBodyFormType(content.form_type);
  const isDeathVisit = content.form_type === "DEATH_VISIT" || content.form_type === "AFTER_DEATH";
  const normalizedDiscipline = safeString(discipline).trim().toUpperCase();
  const isSpiritualVisit = normalizedDiscipline === "SC" || normalizedDiscipline === "CHAPLAIN";
  const isMswVisit = normalizedDiscipline === "MSW" || normalizedDiscipline === "SW";
  const comparisonState = useMemo(() => buildVisitNoteComparisonState(content, comparableHistory), [content, comparableHistory]);
  const showSupervision = supervisoryContext.visible;
  const navItems = useMemo(
    () => buildVisitNoteNavItems({ isFullBody, isSpiritualVisit, isMswVisit, isContinuousCare: isCC, showSupervision, isDeathVisit }),
    [isFullBody, isSpiritualVisit, isMswVisit, isCC, showSupervision, isDeathVisit]
  );

  useEffect(() => {
    if (!navItems.length) return;
    if (!navItems.some((item) => item.id === activeSectionId)) {
      setActiveSectionId(navItems[0].id);
    }
  }, [activeSectionId, navItems]);

  useEffect(() => {
    const sections = navItems
      .map((item) => document.getElementById(anchor(item.id)))
      .filter(Boolean);
    if (!sections.length) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveSectionId(visible[0].target.id.replace(`visit-note-${visitId}-`, ""));
        }
      },
      { rootMargin: "-120px 0px -60% 0px", threshold: [0.15, 0.35, 0.6] }
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [anchor, navItems, visitId]);

  const persistResponse = (record, confirmationMessage) => {
    setContent(mergeContent(record.content || {}));
    setVisitStatus(record.visit_status || visitStatus);
    setComparableHistory(record.comparable_history || []);
    setSupervisoryContext(record.supervisory_context || supervisoryContext);
    setMessage(confirmationMessage);
    setValidationErrors([]);
    onSaved?.();
  };

  const handleSave = () => {
    setSaving(true);
    setError("");
    setMessage("");
    updateVisitNote(visitId, content)
      .then((record) => persistResponse(record, "Visit note saved."))
      .catch((reason) => setError(reason.message || "Unable to save this visit note."))
      .finally(() => setSaving(false));
  };

  const handleSignAndSubmit = () => {
    const errors = showSupervision ? validateSupervisoryReview(content, supervisoryContext) : [];
    if (errors.length) {
      setValidationErrors(errors);
      scrollToSection(errors[0].sectionId);
      return;
    }

    setFinalizing(true);
    setError("");
    setMessage("");
    updateVisitNote(visitId, content)
      .then(() => finalizeVisitNote(visitId))
      .then(() => {
        setVisitStatus("FINALIZED");
        setMessage("Visit note signed and submitted.");
        setValidationErrors([]);
        onSaved?.();
      })
      .catch((reason) => setError(reason.message || "Unable to sign and submit this visit note."))
      .finally(() => setFinalizing(false));
  };

  if (loading) {
    return <div style={{ fontSize: 12, color: COLORS.gray, padding: 12 }}>Loading visit note…</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <StickySectionNav items={navItems} activeSectionId={activeSectionId} onJump={scrollToSection} COLORS={COLORS} compact={compactNav} />
      {error ? <div style={{ color: COLORS.error || "#ef4444", fontSize: 12.5 }}>{error}</div> : null}
      {message ? <div style={{ color: COLORS.success || "#0d9488", fontSize: 12.5 }}>{message}</div> : null}
      <ValidationErrorSummary errors={validationErrors} onJump={scrollToSection} COLORS={COLORS} />
      {isFinalized ? <div style={styles.infoBox}>This visit note has been signed and submitted and can no longer be edited.</div> : null}

      <Section anchorId={anchor("top")}>
        <VisitDetailsCard content={content} onChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} discipline={discipline} />
      </Section>

      <Section anchorId={anchor("since-last")}>
        <SinceLastComparableVisitCard comparisonState={comparisonState} onJump={scrollToSection} styles={styles} COLORS={COLORS} />
      </Section>

      {isCC ? (
        <>
          <Section anchorId={anchor("continuous-care-log")}>
            <ContinuousCareLogSection visitId={visitId} discipline={discipline} enteredBy={content.entered_by} styles={styles} COLORS={COLORS} disabled={isFinalized} />
          </Section>
          {isDeathVisit ? (
            <Section anchorId={anchor("death-disposal")}>
              <DeathDisposalCard value={content.death_disposal} onChange={(nextValue) => setContent((current) => ({ ...current, death_disposal: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}
          <Section anchorId={anchor("narrative")}>
            <Card title="Narrative" styles={styles}>
              <FormTextarea label="Narrative" value={content.narrative} onChange={(nextValue) => setContent((current) => ({ ...current, narrative: nextValue }))} disabled={isFinalized} styles={styles} rows={6} />
            </Card>
          </Section>
        </>
      ) : isSpiritualVisit ? (
        <>
          <Section anchorId={anchor("pain")}>
            <PainCard pain={content.pain} comparisons={comparisonState.groups.pain} onChange={(nextValue) => setContent((current) => ({ ...current, pain: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <Section anchorId={anchor("symptoms")}>
            <SymptomsCard title="Spiritual Symptoms" value={content.spiritual_symptoms} onChange={(nextValue) => setContent((current) => ({ ...current, spiritual_symptoms: nextValue }))} disabled={isFinalized} styles={styles} />
          </Section>

          <Section anchorId={anchor("narrative")}>
            <Card title="Narrative" styles={styles}>
              <FormTextarea label="Narrative" value={content.narrative} onChange={(nextValue) => setContent((current) => ({ ...current, narrative: nextValue }))} disabled={isFinalized} styles={styles} rows={6} />
            </Card>
          </Section>

          <Section anchorId={anchor("care-provided")}>
            <CareProvidedCard value={content.care_provided} onChange={(nextValue) => setContent((current) => ({ ...current, care_provided: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          </Section>

          {isDeathVisit ? (
            <Section anchorId={anchor("death-disposal")}>
              <DeathDisposalCard value={content.death_disposal} onChange={(nextValue) => setContent((current) => ({ ...current, death_disposal: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}
        </>
      ) : isMswVisit ? (
        <>
          <Section anchorId={anchor("pain")}>
            <PainCard pain={content.pain} comparisons={comparisonState.groups.pain} onChange={(nextValue) => setContent((current) => ({ ...current, pain: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <Section anchorId={anchor("symptoms")}>
            <SymptomsCard title="Psychosocial Symptoms" value={content.psychosocial_symptoms} onChange={(nextValue) => setContent((current) => ({ ...current, psychosocial_symptoms: nextValue }))} disabled={isFinalized} styles={styles} />
          </Section>

          <Section anchorId={anchor("narrative")}>
            <Card title="Narrative" styles={styles}>
              <FormTextarea label="Narrative" value={content.narrative} onChange={(nextValue) => setContent((current) => ({ ...current, narrative: nextValue }))} disabled={isFinalized} styles={styles} rows={6} />
            </Card>
          </Section>

          <Section anchorId={anchor("care-provided")}>
            <CareProvidedCard value={content.care_provided} onChange={(nextValue) => setContent((current) => ({ ...current, care_provided: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          </Section>

          {isDeathVisit ? (
            <Section anchorId={anchor("death-disposal")}>
              <DeathDisposalCard value={content.death_disposal} onChange={(nextValue) => setContent((current) => ({ ...current, death_disposal: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}
        </>
      ) : isFullBody ? (
        <>
          <Section anchorId={anchor("vitals")}>
            <VitalsMeasurementsCard vitals={content.vitals} comparisons={comparisonState.groups.vitals} onChange={(nextValue) => setContent((current) => ({ ...current, vitals: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <Section anchorId={anchor("pain")}>
            <PainCard pain={content.pain} comparisons={comparisonState.groups.pain} onChange={(nextValue) => setContent((current) => ({ ...current, pain: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <Section anchorId={anchor("nutrition")}>
            <NutritionCard content={content} comparisons={comparisonState.groups.nutrition} onContentChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <BodySystemsCard content={content} comparisonsBySection={comparisonState.sectionMap} onContentChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} buildAnchor={anchor} />

          <Section anchorId={anchor("function")}>
            <FunctionalDeclineCard content={content} comparisons={comparisonState.groups.function} onContentChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} buildAnchor={anchor} />
          </Section>

          <Section anchorId={anchor("falls-safety")}>
            <FallSafetyCard content={content} comparisons={comparisonState.groups.fallsSafety} onContentChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} onJump={scrollToSection} />
          </Section>

          <Section anchorId={anchor("narrative")}>
            <Card title="Narrative" styles={styles}>
              <FormTextarea label="Narrative" value={content.narrative} onChange={(nextValue) => setContent((current) => ({ ...current, narrative: nextValue }))} disabled={isFinalized} styles={styles} rows={6} />
            </Card>
          </Section>

          <Section anchorId={anchor("care-provided")}>
            <CareProvidedCard value={content.care_provided} onChange={(nextValue) => setContent((current) => ({ ...current, care_provided: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          </Section>

          <Section anchorId={anchor("checklist")}>
            <VisitChecklistCard checklist={content.visit_checklist} onChange={(nextValue) => setContent((current) => ({ ...current, visit_checklist: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
          </Section>

          {showSupervision ? (
            <Section anchorId={anchor("rn-supervision")}>
              <RNReviewCard content={content} supervisoryContext={supervisoryContext} onContentChange={setContent} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}

          {isDeathVisit ? (
            <Section anchorId={anchor("death-disposal")}>
              <DeathDisposalCard value={content.death_disposal} onChange={(nextValue) => setContent((current) => ({ ...current, death_disposal: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}
        </>
      ) : (
        <div style={styles.infoBox}>This Form Type only requires a narrative. The full clinical body is hidden to match the standard workflow.</div>
      )}

      {!isCC && !isSpiritualVisit && !isMswVisit && !isFullBody ? (
        <>
          {isDeathVisit ? (
            <Section anchorId={anchor("death-disposal")}>
              <DeathDisposalCard value={content.death_disposal} onChange={(nextValue) => setContent((current) => ({ ...current, death_disposal: nextValue }))} disabled={isFinalized} styles={styles} COLORS={COLORS} />
            </Section>
          ) : null}

          <Section anchorId={anchor("narrative")}>
            <Card title="Narrative" styles={styles}>
              <FormTextarea label="Narrative" value={content.narrative} onChange={(nextValue) => setContent((current) => ({ ...current, narrative: nextValue }))} disabled={isFinalized} styles={styles} rows={6} />
            </Card>
          </Section>
        </>
      ) : null}

      {!isFinalized ? (
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button type="button" onClick={onCancel} style={styles.btnSecondary}>
            Close
          </button>
          <button type="button" onClick={handleSave} disabled={saving || finalizing} style={{ ...styles.btnSecondary, opacity: saving ? 0.65 : 1 }}>
            {saving ? "Saving…" : "Save Draft"}
          </button>
          <button type="button" onClick={handleSignAndSubmit} disabled={saving || finalizing} style={{ ...styles.btnPrimary, opacity: finalizing ? 0.65 : 1 }}>
            {finalizing ? "Submitting…" : "Sign & Submit"}
          </button>
        </div>
      ) : null}

      <FloatingNarrativeButton onJump={scrollToSection} COLORS={COLORS} />
    </div>
  );
}

// Discipline-specific defaults for a brand-new "Add New Visit". RN/LVN start
// as a full assessment-style visit (ASSESS); SC (Spiritual Counselor, maps to
// CHAPLAIN) and MSW only have a routine visit form configured, so they must
// start as ROUTINE_VISIT or the resolver rejects the request.
const VISIT_DISCIPLINE_DEFAULTS = {
  RN: { formType: "ASSESS", serviceType: "SN" },
  LVN: { formType: "ASSESS", serviceType: "SN" },
  SC: { formType: "ROUTINE_VISIT", serviceType: "CHAPLAIN" },
  MSW: { formType: "ROUTINE_VISIT", serviceType: "MSW" },
};

function AddNewVisitCard({ patientId, onCreated, styles, COLORS }) {
  const currentUser = getCurrentUser();
  const [discipline, setDiscipline] = useState("RN");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = () => {
    setCreating(true);
    setError("");
    const defaults = VISIT_DISCIPLINE_DEFAULTS[discipline] || VISIT_DISCIPLINE_DEFAULTS.RN;
    createVisitNote({
      patient_id: patientId,
      visit_type: discipline,
      service_type: defaults.serviceType,
      form_type: defaults.formType,
      visit_schedule_type: "SCHEDULED",
      clinical_note: {
        entered_by: currentUser?.full_name || currentUser?.name || "",
        staff_assigned: currentUser?.full_name || currentUser?.name || "",
        visit_date: new Date().toISOString().slice(0, 10),
      },
    })
      .then((response) => onCreated(response.visit_id, discipline))
      .catch((reason) => setError(reason.message || "Unable to create this visit."))
      .finally(() => setCreating(false));
  };

  return (
    <Card title="Add New Visit" subtitle="RN, LVN, SC, and MSW visit documentation — reorganized for faster clinical comparison, supervision review, and navigation." styles={styles}>
      {error ? <div style={{ color: COLORS.error || "#ef4444", fontSize: 12.5, marginBottom: 8 }}>{error}</div> : null}
      <div style={styles.fieldsGrid}>
        <FormSelect label="Discipline" value={discipline} onChange={setDiscipline} options={["RN", "LVN", "SC", "MSW"]} styles={styles} />
      </div>
      <button type="button" onClick={handleCreate} disabled={creating} style={{ ...styles.btnPrimary, opacity: creating ? 0.65 : 1, marginTop: 8 }}>
        {creating ? "Creating…" : "Start Visit Note"}
      </button>
    </Card>
  );
}

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
              border: `1px solid ${COLORS.border || "#334155"}`,
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

function SupervisoryComplianceBadge({ patientId, styles, COLORS }) {
  const [schedule, setSchedule] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    getSupervisorySchedule(patientId)
      .then((data) => { if (!cancelled) setSchedule(data); })
      .catch(() => { if (!cancelled) setError("Unable to load supervisory compliance status."); });
    return () => { cancelled = true; };
  }, [patientId]);

  if (error || !schedule) return null;

  const cadences = [
    { key: "chha_supervisory", label: "CHHA Supervisory (14-day)" },
    { key: "lvn_supervisory", label: "LVN Supervisory (28-day)" },
  ].map(({ key, label }) => ({ label, result: schedule[key] }));

  const active = cadences.filter((c) => c.result?.required);
  if (!active.length) return null;

  const statusColor = (status) => {
    if (status === "OVERDUE") return COLORS.error || "#ef4444";
    if (status === "DUE") return COLORS.orange || "#f59e0b";
    return COLORS.success || "#22c55e";
  };

  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 4 }}>
      {active.map(({ label, result }) => (
        <div
          key={label}
          style={{
            fontSize: 11.5,
            padding: "4px 10px",
            borderRadius: 999,
            border: `1px solid ${statusColor(result.status)}`,
            color: statusColor(result.status),
            background: "transparent",
            fontWeight: 600,
          }}
          title={
            result.last_satisfying_visit_date
              ? `Last satisfying RN supervisory visit: ${result.last_satisfying_visit_date}`
              : "No satisfying RN supervisory visit on record yet"
          }
        >
          {label}: {result.status.replace(/_/g, " ")} (due {result.due_date})
        </div>
      ))}
    </div>
  );
}

export default function VisitNoteBoard({ patientId }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeVisit, setActiveVisit] = useState(null);

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    listVisitNotesForPatient(patientId)
      .then((rows) => setEntries(Array.isArray(rows) ? rows : []))
      .catch((reason) => setError(reason.message || "Unable to load this patient's visit notes."))
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reload();
  }, [reload]);

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
          <AddNewVisitCard patientId={patientId} onCreated={(visit_id, createdDiscipline) => setActiveVisit({ visit_id, discipline: createdDiscipline })} styles={styles} COLORS={COLORS} />
          <SupervisoryComplianceBadge patientId={patientId} styles={styles} COLORS={COLORS} />
          <Card title="Visit Notes" subtitle="RN/LVN visit notes plus MSW and SC assessment visits, most recent first." styles={styles}>
            {error ? <div style={{ color: COLORS.error || "#ef4444", fontSize: 12.5, marginBottom: 8 }}>{error}</div> : null}
            {loading ? <div style={{ fontSize: 12, color: COLORS.gray }}>Loading visit notes…</div> : <VisitNoteTimeline entries={entries} onSelect={(entry) => setActiveVisit({ visit_id: entry.visit_id, discipline: entry.discipline })} styles={styles} COLORS={COLORS} />}
          </Card>
        </>
      )}
    </div>
  );
}
