import React, { useState } from 'react';
import { useThemeMode } from '../theme/theme';
import { getChartColors } from '../theme/chartColors';

const cardStyle = (colors) => ({
  backgroundColor: colors.card,
  borderRadius: 8,
  padding: 24,
  borderLeft: `4px solid ${colors.teal}`,
  marginBottom: 24,
});

const Badge = ({ children, variant = 'green', colors }) => {
  const map = {
    green: { bg: colors.greenBg, color: colors.green },
    red: { bg: colors.redBg, color: colors.red },
    amber: { bg: colors.amberBg, color: colors.amber },
    teal: { bg: colors.tealBg, color: colors.teal },
  };
  const v = map[variant] || map.teal;
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 4,
      fontSize: 11, fontWeight: 600, backgroundColor: v.bg, color: v.color,
    }}>{children}</span>
  );
};

const PatientBanner = ({ patient, colors }) => (
  <div style={{ backgroundColor: colors.card, borderRadius: 8, padding: '16px 24px', marginBottom: 24 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ color: colors.white, fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
          {patient.lastName}, {patient.firstName}
        </div>
        <div style={{ color: colors.label, fontSize: 13 }}>
          MRN: {patient.mrn} &nbsp;|&nbsp; DOB: {patient.dob} ({patient.age}y) &nbsp;|&nbsp; Sex: {patient.sex} &nbsp;|&nbsp; Payer: {patient.payer}
        </div>
      </div>
      <Badge variant="green" colors={colors}>{patient.status}</Badge>
    </div>
  </div>
);

const relatedDiagnoses = [
  { code: 'C34.90', desc: 'Malignant neoplasm of lung, unspecified' },
  { code: 'R64', desc: 'Cachexia' },
];

const unrelatedDiagnoses = [
  { code: 'I10', desc: 'Essential (primary) hypertension' },
  { code: 'E11.9', desc: 'Type 2 diabetes mellitus without complications' },
];

const nonCoveredMeds = [
  { name: 'Metformin 500mg', reason: 'Unrelated to terminal diagnosis' },
  { name: 'Lisinopril 10mg', reason: 'Unrelated to terminal diagnosis' },
];

const nonCoveredSections = [
  { key: 'dme', label: 'Durable Medical Equipment (DME)', checked: false },
  { key: 'supplies', label: 'Medical Supplies', checked: false },
  { key: 'lab', label: 'Laboratory Services', checked: true },
  { key: 'treatment', label: 'Treatments / Procedures', checked: false },
  { key: 'diet', label: 'Dietary / Nutritional Supplements', checked: false },
  { key: 'respite', label: 'Respite Care (beyond covered days)', checked: false },
];

const PatientNotificationNonCovered = ({ patient, onBack }) => {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const [checkedSections] = useState(
    nonCoveredSections.reduce((acc, s) => ({ ...acc, [s.key]: s.checked }), {})
  );
  const [explanation, setExplanation] = useState(
    'Patient continues to take Metformin and Lisinopril for pre-existing, unrelated chronic conditions. These medications are not related to the terminal hospice diagnosis and are therefore not covered under the hospice benefit.'
  );

  const textAreaStyle = {
    backgroundColor: colors.bg, border: `1px solid ${colors.border}`,
    borderRadius: 6, padding: 12, color: colors.white, fontSize: 13,
    fontFamily: "'Inter', sans-serif", outline: 'none', width: '100%',
    minHeight: 90, resize: 'vertical', boxSizing: 'border-box',
  };

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      {/* Breadcrumb */}
      <div style={{ color: colors.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{patient.firstName} {patient.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span onClick={onBack} style={{ cursor: onBack ? 'pointer' : 'default' }}>Consent & Notifications</span>
        <span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: colors.white }}>Patient Notification</span>
      </div>

      {onBack && (
        <div
          onClick={onBack}
          style={{ color: colors.teal, fontSize: 13, fontWeight: 600, cursor: 'pointer', marginBottom: 16 }}
        >
          ← Back to Consent & Notifications
        </div>
      )}

      <PatientBanner patient={patient} colors={colors} />

      <div style={cardStyle(colors)}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            Patient Notification of Non-Covered Items
          </div>
          <div style={{ color: colors.label, fontSize: 13 }}>
            Documents items, medications, and services determined to be unrelated to the terminal
            diagnosis and therefore not covered under the hospice benefit.
          </div>
        </div>

        {/* Upload */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Upload Signed Notification
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            backgroundColor: colors.bg, borderRadius: 8, padding: '12px 16px',
            border: `1px dashed ${colors.border}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 16 }}>📎</span>
              <span style={{ color: colors.label, fontSize: 13 }}>Drag and drop files here, or click to browse</span>
            </div>
            <span style={{
              backgroundColor: colors.teal, color: colors.white, fontSize: 11,
              fontWeight: 600, padding: '4px 12px', borderRadius: 4,
            }}>0 Files Attached</span>
          </div>
        </div>

        {/* Meta fields */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={{ flex: 1 }}>
            <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Notification Date</span>
            <div style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>01/15/2026</div>
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Notified By</span>
            <div style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>RN Case Manager</div>
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Acknowledged By</span>
            <div style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>Patient / Representative</div>
          </div>
        </div>

        <div style={{ color: colors.text, fontSize: 13, lineHeight: '1.6', marginBottom: 24, backgroundColor: colors.bg, borderRadius: 8, padding: 16, border: `1px solid ${colors.border}` }}>
          The patient/representative has been informed that certain diagnoses, medications, and
          services listed below are considered unrelated to the terminal illness and its related
          conditions, and therefore are not covered by the hospice Medicare/Medicaid benefit.
        </div>

        {/* Diagnoses columns */}
        <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
          <div style={{ flex: 1 }}>
            <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
              Diagnoses Related to Terminal Illness
            </div>
            {relatedDiagnoses.map((d) => (
              <div key={d.code} style={{
                display: 'flex', gap: 10, padding: '8px 12px', marginBottom: 8,
                backgroundColor: colors.greenBg, borderRadius: 6, border: `1px solid ${colors.green}33`,
              }}>
                <span style={{ color: colors.green, fontWeight: 700, fontSize: 12 }}>{d.code}</span>
                <span style={{ color: colors.text, fontSize: 12.5 }}>{d.desc}</span>
              </div>
            ))}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
              Diagnoses Unrelated to Terminal Illness
            </div>
            {unrelatedDiagnoses.map((d) => (
              <div key={d.code} style={{
                display: 'flex', gap: 10, padding: '8px 12px', marginBottom: 8,
                backgroundColor: colors.amberBg, borderRadius: 6, border: `1px solid ${colors.amber}33`,
              }}>
                <span style={{ color: colors.amber, fontWeight: 700, fontSize: 12 }}>{d.code}</span>
                <span style={{ color: colors.text, fontSize: 12.5 }}>{d.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Reason key */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 24, fontSize: 12, color: colors.label }}>
          <span><Badge variant="green" colors={colors}>Related</Badge> Covered under hospice benefit</span>
          <span><Badge variant="amber" colors={colors}>Unrelated</Badge> Not covered — billed separately</span>
        </div>

        {/* Non-covered medications table */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Non-Covered Medications
          </div>
          <div style={{ border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ display: 'flex', backgroundColor: colors.bg, padding: '8px 16px', borderBottom: `1px solid ${colors.border}` }}>
              <span style={{ flex: 1, color: colors.label, fontSize: 11, textTransform: 'uppercase', fontWeight: 700 }}>Medication</span>
              <span style={{ flex: 2, color: colors.label, fontSize: 11, textTransform: 'uppercase', fontWeight: 700 }}>Reason Not Covered</span>
            </div>
            {nonCoveredMeds.map((m, i) => (
              <div key={m.name} style={{
                display: 'flex', padding: '10px 16px',
                borderBottom: i < nonCoveredMeds.length - 1 ? `1px solid ${colors.border}` : 'none',
              }}>
                <span style={{ flex: 1, color: colors.white, fontSize: 13 }}>{m.name}</span>
                <span style={{ flex: 2, color: colors.text, fontSize: 13 }}>{m.reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Non-covered sections list */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Non-Covered Services
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 32px' }}>
            {nonCoveredSections.map((s) => (
              <label key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 20, height: 20, borderRadius: 4, flexShrink: 0,
                  border: checkedSections[s.key] ? 'none' : `2px solid ${colors.border}`,
                  backgroundColor: checkedSections[s.key] ? colors.teal : 'transparent',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {checkedSections[s.key] && (
                    <span style={{ color: colors.white, fontSize: 12, fontWeight: 700 }}>✓</span>
                  )}
                </div>
                <span style={{ color: colors.text, fontSize: 13 }}>{s.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Clinical explanation */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Clinical Explanation
          </div>
          <textarea value={explanation} onChange={(e) => setExplanation(e.target.value)} style={textAreaStyle} />
        </div>
      </div>

      {/* Review section */}
      <div style={{ ...cardStyle(colors), marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 20, height: 20, borderRadius: 10, backgroundColor: colors.green,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ color: colors.white, fontSize: 10, fontWeight: 700 }}>✓</span>
            </div>
            <span style={{ color: colors.text, fontSize: 13 }}>
              I certify the patient/representative was notified of non-covered items and understands financial responsibility.
            </span>
          </label>
          <Badge variant="green" colors={colors}>Acknowledged</Badge>
        </div>
      </div>

      {/* Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        <button style={{
          padding: '10px 24px', backgroundColor: 'transparent', color: colors.teal,
          border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 13,
          fontWeight: 600, cursor: 'pointer', fontFamily: "'Inter', sans-serif",
        }}>Printer Friendly Version</button>
        <button style={{
          padding: '10px 24px', backgroundColor: colors.teal, color: colors.white,
          border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600,
          cursor: 'pointer', fontFamily: "'Inter', sans-serif",
        }}>Submit Notification</button>
      </div>
    </div>
  );
};

export default PatientNotificationNonCovered;
