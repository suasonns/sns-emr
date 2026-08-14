import React, { useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";

const DEFAULT_PATIENT_ID = "5d31a53f-eebd-468f-bcb6-1b43771fe113";
const STORAGE_PREFIX = "sns-emr-sc-ica";

const INITIAL_FORM = {
  patientActiveInFaithTradition: false,
  patientFaith: "",
  caregiverActiveInFaithTradition: false,
  caregiverFaith: "",
  spiritualConcerns: [],
  spiritualDistressRating: "",
  chaplainNeeded: false,
  supportSystem: "Family",
  patientResponseToIllness: "Awake",
  familyResponseToIllness: "Accepting",
  supportPerson: "",
  supportPersonPhone: "",
  financialStress: "No",
  housingConcern: "No",
  transportationConcern: "No",
  referralNeeded: "N/A",
  referralType: "",
  narrative: "",
  notes: "",
  completion: {
    assessmentComplete: false,
    chaplainName: "",
    chaplainTitle: "",
    signatureDate: "",
  },
};

const concernOptions = [
  "Meaning of illness",
  "Forgiveness",
  "Hope",
  "Legacy",
  "Prayer requests",
  "Religious rituals",
  "Afterlife concerns",
  "Anger at God",
  "Spiritual distress",
];

const sidebarItems = [
  "Admission",
  "Assessment",
  "Psychosocial",
  "Tx / Med / DME",
  "IDG",
  "POC",
  "Issues / Outcome",
  "Physician",
  "Visit Notes",
  "Health Aide (HA)",
  "Volunteer",
  "Comm / Progress Log",
  "Document / Images",
  "Discharge",
  "Bereavement",
  "Compliance",
  "Incident / Occurrence",
  "Faxes",
  "Care Overview",
  "Monthly Schedule",
];

function Field({ label, children, compact = false }) {
  return (
    <div style={{ marginBottom: compact ? 8 : 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 4, color: "#334155" }}>{label}</div>
      {children}
    </div>
  );
}

function Card({ title, children, subtitle, id }) {
  return (
    <section id={id} style={{ border: "1px solid #dbe5ee", marginBottom: 12, background: "#fff", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ background: "#f8fafc", borderBottom: "1px solid #dbe5ee", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, fontStyle: "italic" }}>{title}</div>
          {subtitle ? <div style={{ fontSize: 10, color: "#64748b" }}>{subtitle}</div> : null}
        </div>
        <div style={{ fontSize: 10, color: "#0f766e", fontWeight: 700 }}>Add Issue</div>
      </div>
      <div style={{ padding: 12 }}>{children}</div>
    </section>
  );
}

function readStoredForm(patientId) {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
  if (!raw) return INITIAL_FORM;
  try {
    const parsed = JSON.parse(raw);
    return {
      ...INITIAL_FORM,
      ...parsed,
      completion: { ...INITIAL_FORM.completion, ...(parsed.completion || {}) },
    };
  } catch {
    return INITIAL_FORM;
  }
}

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function SectionLink({ active, label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        width: "100%",
        textAlign: "left",
        border: "none",
        background: active ? "linear-gradient(90deg, rgba(16,183,162,0.12), rgba(16,183,162,0.02))" : "transparent",
        color: "#0f172a",
        fontSize: 12,
        padding: "3px 4px",
        cursor: "pointer",
      }}
    >
      {label}
    </button>
  );
}

export default function SCICA({ patientId = DEFAULT_PATIENT_ID }) {
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  const [form, setForm] = useState(() => readStoredForm(patientId));
  const [activeSection, setActiveSection] = useState("faith");
  const [completed, setCompleted] = useState(false);
  const [completionError, setCompletionError] = useState("");

  useEffect(() => {
    let mounted = true;
    setPatientSummaryError("");
    fetchPatientSummary(patientId)
      .then((summary) => {
        if (mounted) setPatientSummary(summary);
      })
      .catch((error) => {
        console.error("Failed to load SC ICA patient summary:", error);
        if (mounted) setPatientSummaryError(error instanceof Error ? error.message : "Unable to load patient summary.");
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    setForm(readStoredForm(patientId));
    setCompleted(false);
    setCompletionError("");
  }, [patientId]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_PREFIX}:${patientId}`, JSON.stringify(form));
  }, [form, patientId]);

  const patientName = patientSummary?.patient?.full_name || "RNICA Runtime Test Patient";
  const patientOverview = useMemo(() => {
    if (!patientSummary) {
      return {
        diagnosis: "Hospice qualifying diagnosis",
        painSummary: "Loading patient context...",
        primaryProvider: "Unassigned",
        hnpStatus: "Pre-referral / Routine",
        lastVisit: "No visits recorded",
        disciplineHistory: [],
        careTeam: [],
      };
    }
    return {
      diagnosis: patientSummary.patient.primary_diagnosis,
      painSummary: `${patientSummary.communication_summary.total} communication entry(ies) on file.`,
      primaryProvider: patientSummary.care_team[0]?.staff_name || "Unassigned",
      hnpStatus: `${patientSummary.patient.admission_status} / ${patientSummary.patient.acuity_state}`,
      lastVisit: patientSummary.recent_visits[0]
        ? `${patientSummary.recent_visits[0].visit_type} — ${patientSummary.recent_visits[0].visit_datetime || "—"}`
        : "No visits recorded",
      disciplineHistory: [
        `${patientSummary.recent_visits.length} recent visit(s)`,
        `${patientSummary.communication_summary.total} communication entry(ies)`,
        `${patientSummary.incident_summary.total} incident report(s)`,
      ],
      careTeam: patientSummary.care_team.map((item) => item.discipline),
    };
  }, [patientSummary]);

  const summaryCount = [
    form.patientFaith,
    form.caregiverFaith,
    form.spiritualConcerns.length,
    form.spiritualDistressRating,
    form.chaplainNeeded,
    form.narrative,
  ].filter((value) => value !== false && value !== "" && value !== 0 && value !== null && value !== undefined).length;

  const progressLabel = completed ? "COMPLETED" : "IN PROGRESS";
  const progressTone = completed ? "#2563eb" : "#f59e0b";

  const sections = [
    { key: "faith", label: "1. Spiritual Assessment" },
    { key: "circumstances", label: "2. Spiritual Circumstances" },
    { key: "distress", label: "3. Patient — Distress / Concerns" },
    { key: "financial", label: "4. Financial / Legal Needs" },
    { key: "referrals", label: "5. Referrals" },
    { key: "narrative", label: "6. Narrative" },
    { key: "signature", label: "Signature" },
  ];

  const handleSelect = (section) => {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const update = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setCompleted(false);
    setCompletionError("");
  };

  const updateCompletion = (key, value) => {
    setForm((prev) => ({ ...prev, completion: { ...prev.completion, [key]: value } }));
    setCompleted(false);
    setCompletionError("");
  };

  const handleComplete = () => {
    if (!form.narrative && !form.notes && !form.chaplainNeeded && !form.spiritualConcerns.length) {
      setCompletionError("Document at least one concern or note before completing the assessment.");
      return;
    }
    setCompletionError("");
    setCompleted(true);
  };
  const assessmentChildren = [
    { label: "Nursing", target: "faith" },
    { label: "Spiritual", target: "faith" },
    { label: "Psychosocial", target: "circumstances" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#eef3f8" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto", padding: "24px 0" }}>
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 12 }}>
          <aside style={{ width: 260, minWidth: 260, paddingTop: 3 }}>
            <div style={{ fontSize: 13, color: "#0f172a", fontWeight: 700, marginBottom: 8, paddingLeft: 2 }}>Love & Faith Hospice Services, Inc.</div>
            <div style={{ border: "1px solid #dbe5ee", background: "#fff", fontSize: 11, borderRadius: 12, overflow: "hidden" }}>
              <div style={{ background: "linear-gradient(90deg, #1f4a78 0%, #10b7a2 100%)", color: "#fff", borderBottom: "1px solid #1f4a78", padding: "6px 10px", fontWeight: 700 }}>Patient</div>
              <div style={{ padding: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{patientName}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>{patientSummary?.patient?.mrn || "MRN not loaded"}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 6 }}>DOB: 11/15/1941 (84F)</div>
              </div>
            </div>

            <div style={{ marginTop: 8, border: "1px solid #dbe5ee", background: "#fff", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ background: "#eef6fb", borderBottom: "1px solid #dbe5ee", padding: "6px 10px", fontWeight: 700 }}>Navigation</div>
              <div style={{ padding: 8, maxHeight: 640, overflow: "auto" }}>
                {sidebarItems.map((item) => {
                  if (item === "Psychosocial") {
                    return null;
                  }
                  if (item === "Assessment") {
                    return (
                      <div key={item} style={{ marginBottom: 6 }}>
                        <div style={{ fontSize: 10, fontWeight: 800, color: "#64748b", letterSpacing: ".08em", textTransform: "uppercase", padding: "6px 4px 4px" }}>
                          Assessment
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 10 }}>
                          {assessmentChildren.map((child) => (
                            <button
                              key={child.label}
                              type="button"
                              onClick={() => handleSelect(child.target)}
                              style={{
                                width: "100%",
                                textAlign: "left",
                                border: "none",
                                background: "transparent",
                                color: "#0f172a",
                                fontSize: 12,
                                padding: "3px 4px",
                                cursor: "pointer",
                              }}
                            >
                              {child.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <SectionLink
                      key={item}
                      active={false}
                      label={item}
                      onClick={() => {
                        const target = item === "Admission" ? "faith" : "narrative";
                        handleSelect(target);
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </aside>

          <main style={{ background: "#f4f7f9", border: "1px solid #dbe5ee", boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)", borderRadius: 14, overflow: "hidden" }}>
            <div style={{ padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg, #1f4a78 0%, #10b7a2 100%)", color: "#fff" }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>Comprehensive Spiritual Assessment</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.88)" }}>Chaplain support needs, spiritual distress, and referral planning</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: progressTone }}>{progressLabel}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.8)" }}>Close</div>
              </div>
            </div>

            <div style={{ padding: 10, background: "#effaf8", borderBottom: "1px solid #dbe5ee", fontSize: 11 }}>
              Upload Documents (0)
            </div>

            {(patientSummaryError || completionError) && (
              <div style={{ margin: 10, padding: 10, border: "1px solid #f59e0b", background: "#fff7ed", color: "#9a3412", fontSize: 12, borderRadius: 10 }}>
                {patientSummaryError && <div>Patient summary: {patientSummaryError}</div>}
                {completionError && <div>SC ICA: {completionError}</div>}
              </div>
            )}

            <div style={{ padding: 12 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <Card title="1. Pain" subtitle="Spiritual distress and symptom context" id="faith">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Patient active in faith tradition">
                        <select value={form.patientActiveInFaithTradition ? "Yes" : "No"} onChange={(e) => update("patientActiveInFaithTradition", e.target.value === "Yes")} style={inputStyle}>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                      <Field label="Patient faith">
                        <input value={form.patientFaith} onChange={(e) => update("patientFaith", e.target.value)} style={inputStyle} placeholder="Faith tradition" />
                      </Field>
                    </div>
                    <Field label="Chaplain referral needed">
                      <label style={checkboxLabel}><input type="checkbox" checked={form.chaplainNeeded} onChange={(e) => update("chaplainNeeded", e.target.checked)} /> Needed</label>
                    </Field>
                    <Field label="Spiritual distress rating">
                      <select value={form.spiritualDistressRating} onChange={(e) => update("spiritualDistressRating", e.target.value)} style={inputStyle}>
                        <option value="">Select</option>
                        {Array.from({ length: 11 }).map((_, i) => <option key={i} value={String(i)}>{i}</option>)}
                      </select>
                    </Field>
                  </Card>

                  <Card title="2. Psychosocial Circumstances" subtitle="Support system and caregiver context" id="circumstances">
                    <Field label="Support system">
                      <select value={form.supportSystem} onChange={(e) => update("supportSystem", e.target.value)} style={inputStyle}>
                        <option>Family</option>
                        <option>Friends</option>
                        <option>Facility</option>
                        <option>Community</option>
                        <option>None</option>
                      </select>
                    </Field>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Support person">
                        <input value={form.supportPerson} onChange={(e) => update("supportPerson", e.target.value)} style={inputStyle} />
                      </Field>
                      <Field label="Support phone">
                        <input value={form.supportPersonPhone} onChange={(e) => update("supportPersonPhone", e.target.value)} style={inputStyle} />
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                      <Field label="Patient response to illness">
                        <select value={form.patientResponseToIllness} onChange={(e) => update("patientResponseToIllness", e.target.value)} style={inputStyle}>
                          <option>Awake</option>
                          <option>Accepting</option>
                          <option>Depressed</option>
                          <option>Fearful</option>
                          <option>Denial</option>
                        </select>
                      </Field>
                      <Field label="Family response to illness">
                        <select value={form.familyResponseToIllness} onChange={(e) => update("familyResponseToIllness", e.target.value)} style={inputStyle}>
                          <option>Accepting</option>
                          <option>Supportive</option>
                          <option>Overwhelmed</option>
                          <option>Fearful</option>
                          <option>Guilt</option>
                        </select>
                      </Field>
                      <Field label="Caregiver faith">
                        <input value={form.caregiverFaith} onChange={(e) => update("caregiverFaith", e.target.value)} style={inputStyle} />
                      </Field>
                    </div>
                  </Card>

                  <Card title="3. Patient — Psychosocial Distress/Concerns" subtitle="Select all that apply" id="distress">
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                      {concernOptions.map((option) => (
                        <label key={option} style={checkboxLabel}>
                          <input
                            type="checkbox"
                            checked={form.spiritualConcerns.includes(option)}
                            onChange={() => update("spiritualConcerns", toggleValue(form.spiritualConcerns, option))}
                          />
                          {option}
                        </label>
                      ))}
                    </div>
                  </Card>
                </div>

                <div>
                  <Card title="4. Financial/Legal Needs" subtitle="Basic social-risk review" id="financial">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Financial stress">
                        <select value={form.financialStress} onChange={(e) => update("financialStress", e.target.value)} style={inputStyle}>
                          <option>No</option>
                          <option>Yes</option>
                        </select>
                      </Field>
                      <Field label="Housing concern">
                        <select value={form.housingConcern} onChange={(e) => update("housingConcern", e.target.value)} style={inputStyle}>
                          <option>No</option>
                          <option>Yes</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Transportation concern">
                      <select value={form.transportationConcern} onChange={(e) => update("transportationConcern", e.target.value)} style={inputStyle}>
                        <option>No</option>
                        <option>Yes</option>
                      </select>
                    </Field>
                  </Card>

                  <Card title="5. Referrals" subtitle="Support services and follow-up" id="referrals">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Referral needed">
                        <select value={form.referralNeeded} onChange={(e) => update("referralNeeded", e.target.value)} style={inputStyle}>
                          <option>N/A</option>
                          <option>Yes</option>
                          <option>No</option>
                        </select>
                      </Field>
                      <Field label="Referral type">
                        <input value={form.referralType} onChange={(e) => update("referralType", e.target.value)} style={inputStyle} placeholder="Chaplain / MSW / Community" />
                      </Field>
                    </div>
                  </Card>

                  <Card title="6. Narrative (Include care provided items)" subtitle="Document visit summary and interventions" id="narrative">
                    <textarea
                      value={form.narrative}
                      onChange={(e) => update("narrative", e.target.value)}
                      style={textareaStyle}
                      placeholder="Document the spiritual assessment narrative and care provided."
                    />
                    <div style={{ marginTop: 8, fontSize: 11, color: "#64748b" }}>Comments (Char 500 Max)</div>
                    <textarea
                      value={form.notes}
                      onChange={(e) => update("notes", e.target.value)}
                      style={{ ...textareaStyle, minHeight: 70 }}
                      placeholder="Additional notes."
                    />
                  </Card>

                  <Card title="7. Signature" subtitle="Complete and sign" id="signature">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Chaplain name">
                        <input value={form.completion.chaplainName} onChange={(e) => updateCompletion("chaplainName", e.target.value)} style={inputStyle} />
                      </Field>
                      <Field label="Chaplain title">
                        <input value={form.completion.chaplainTitle} onChange={(e) => updateCompletion("chaplainTitle", e.target.value)} style={inputStyle} />
                      </Field>
                    </div>
                    <Field label="Signature date">
                      <input type="date" value={form.completion.signatureDate} onChange={(e) => updateCompletion("signatureDate", e.target.value)} style={inputStyle} />
                    </Field>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                      <label style={checkboxLabel}>
                        <input type="checkbox" checked={form.completion.assessmentComplete} onChange={(e) => updateCompletion("assessmentComplete", e.target.checked)} />
                        Assessment complete
                      </label>
                      <button type="button" onClick={handleComplete} style={buttonStyle}>
                        Mark Complete
                      </button>
                    </div>
                    <div style={{ marginTop: 10, fontSize: 11, color: completed ? "#166534" : "#475569" }}>
                      {completed ? "This form has been reviewed and signed." : "Draft not yet signed."}
                    </div>
                  </Card>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "4px 6px",
  border: "1px solid #9aa9b5",
  borderRadius: 2,
  background: "#fff",
  fontSize: 11,
};

const textareaStyle = {
  width: "100%",
  minHeight: 120,
  boxSizing: "border-box",
  padding: "6px",
  border: "1px solid #9aa9b5",
  borderRadius: 2,
  fontSize: 11,
  lineHeight: 1.3,
  resize: "vertical",
};

const checkboxLabel = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  fontSize: 11,
  color: "#111827",
};

const buttonStyle = {
  border: "1px solid #9aa9b5",
  background: "#f8fafc",
  color: "#111827",
  borderRadius: 2,
  padding: "4px 10px",
  fontSize: 11,
  cursor: "pointer",
};
