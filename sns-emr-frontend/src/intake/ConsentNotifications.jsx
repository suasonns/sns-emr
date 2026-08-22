import React, { useState } from 'react';
import { useThemeMode } from '../theme/theme';
import { getChartColors } from '../theme/chartColors';
import PatientNotificationNonCovered from './PatientNotificationNonCovered';

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
    <div style={{ display: 'flex', gap: 24, marginTop: 12 }}>
      <div>
        <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block' }}>SOC DATE</span>
        <span style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>{patient.socDate}</span>
      </div>
      <div>
        <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block' }}>BENEFIT PERIOD</span>
        <span style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>{patient.benefitPeriod}</span>
      </div>
    </div>
  </div>
);

export const defaultPatient = {
  firstName: 'LOREN B', lastName: 'SHIELDS', mrn: '054/782',
  dob: '03/15/1948', age: 78, sex: 'M', payer: 'Medicare',
  primaryPayerType: 'MEDICARE', secondaryPayerType: '',
  status: 'ACTIVE', socDate: '01/15/2026',
  benefitPeriod: '01/15/2026 – 07/14/2026',
};

const consentDocuments = [
  { key: 'hospice_eval', label: 'Hospice Eval Order', defaultChecked: true },
  { key: 'informed_consent', label: 'Informed Consent', defaultChecked: true },
  { key: 'election', label: 'Election of Hospice', defaultChecked: true },
  { key: 'polst_dnr', label: 'POLST / DNR', defaultChecked: true },
  { key: 'change_hospice', label: 'Change of Hospice (if applicable)', defaultChecked: false },
  { key: 'poa_directive', label: 'POA / Advance Directive', defaultChecked: true },
  { key: 'bill_of_rights', label: 'Bill of Rights', defaultChecked: true },
  { key: 'telehealth', label: 'Telehealth Consent', defaultChecked: true },
  { key: 'bedside_charts', label: 'Sent Bedside Charts', defaultChecked: true },
  { key: 'cahps_decline', label: 'Family / PCG declines CAHPS Survey', defaultChecked: false },
  { key: 'bereavement_decline', label: 'Family / PCG declines Bereavement Letters / Support', defaultChecked: false },
  { key: 'veteran', label: 'Patient / Spouse is a Veteran', defaultChecked: false },
  { key: 'non_covered', label: 'Non-Covered Items (check if requested by patient)', defaultChecked: false },
];

const ConsentNotifications = ({ patient = defaultPatient }) => {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);

  const [showNonCovered, setShowNonCovered] = useState(false);
  const [checkedItems, setCheckedItems] = useState(
    consentDocuments.reduce((acc, doc) => ({ ...acc, [doc.key]: doc.defaultChecked }), {})
  );
  const [cprPreference] = useState('DNR');
  const [dnrDate, setDnrDate] = useState('01/15/2026');
  const [socDate, setSocDate] = useState('01/15/2026');
  const [reviewDate, setReviewDate] = useState('01/15/2026');
  const [uploadCount] = useState(0);

  if (showNonCovered) {
    return <PatientNotificationNonCovered patient={patient} onBack={() => setShowNonCovered(false)} />;
  }

  const toggleCheck = (key) => {
    setCheckedItems((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const inputStyle = {
    backgroundColor: colors.bg, border: `1px solid ${colors.border}`,
    borderRadius: 6, padding: '8px 12px', color: colors.white,
    fontSize: 13, fontFamily: "'Inter', sans-serif", outline: 'none', width: '100%',
  };

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      {/* Breadcrumb */}
      <div style={{ color: colors.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{patient.firstName} {patient.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>Intake & Admission</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: colors.white }}>Consent & Notifications</span>
      </div>

      <PatientBanner patient={patient} colors={colors} />

      {/* Main Card */}
      <div style={cardStyle(colors)}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            Consent & Notifications
          </div>
          <div style={{ color: colors.label, fontSize: 13 }}>
            Review required admission documents, verify signatures, and certify hard copies on file.
          </div>
        </div>

        {/* Upload Documents */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Section 1 — Upload Patient Consent Documents
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
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <span style={{
                backgroundColor: colors.teal, color: colors.white, fontSize: 11,
                fontWeight: 600, padding: '4px 12px', borderRadius: 4,
              }}>{uploadCount} Files Attached</span>
              <span style={{ color: colors.teal, fontSize: 12, cursor: 'pointer' }}>Show Details...</span>
            </div>
          </div>
        </div>

        {/* Document Verification Checklist */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>
            Section 2 — Document Verification Checklist
          </div>
          <div style={{ color: colors.label, fontSize: 12, marginBottom: 16 }}>
            Check all completed documents on file (Documents available on hard copy)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 32px' }}>
            {consentDocuments.map((doc) => (
              <div key={doc.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                <label
                  style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', padding: '6px 0', flex: 1 }}
                  onClick={() => toggleCheck(doc.key)}
                >
                  <div style={{
                    width: 20, height: 20, borderRadius: 4, flexShrink: 0,
                    border: checkedItems[doc.key] ? 'none' : `2px solid ${colors.border}`,
                    backgroundColor: checkedItems[doc.key] ? colors.teal : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {checkedItems[doc.key] && (
                      <span style={{ color: colors.white, fontSize: 12, fontWeight: 700 }}>✓</span>
                    )}
                  </div>
                  <span style={{ color: colors.text, fontSize: 13 }}>{doc.label}</span>
                </label>
              </div>
            ))}
          </div>

          {/* Prominent call-out for the Non-Covered Items Notification screen */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: 16, marginTop: 20, padding: '16px 20px',
            backgroundColor: colors.amberBg, border: `2px solid ${colors.amber}`, borderRadius: 8,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <span style={{ fontSize: 26 }}>⚠️</span>
              <div>
                <div style={{ color: colors.white, fontSize: 15, fontWeight: 700 }}>
                  Patient Notification of Non-Covered Items
                </div>
                <div style={{ color: colors.text, fontSize: 12.5 }}>
                  Required if the patient has requested non-covered items, medications, or services.
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowNonCovered(true)}
              style={{
                padding: '12px 24px', backgroundColor: colors.amber, color: colors.white,
                border: 'none', borderRadius: 6, fontSize: 14, fontWeight: 700,
                cursor: 'pointer', fontFamily: "'Inter', sans-serif", whiteSpace: 'nowrap',
              }}
            >
              Open Notification →
            </button>
          </div>
        </div>

        {/* CPR Preference & SOC Notification Side by Side */}
        <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
          {/* CPR Preference */}
          <div style={{
            flex: 1, backgroundColor: colors.bg, borderRadius: 8, padding: 20,
            border: `1px solid ${colors.border}`,
          }}>
            <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16 }}>
              Section 3 — CPR Preference & Code Status
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <span style={{ color: colors.text, fontSize: 13 }}>CPR Status preference on file:</span>
              <Badge variant="red" colors={colors}>{cprPreference} (Do Not Resuscitate)</Badge>
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  DNR Verification Date
                </span>
                <input type="text" value={dnrDate} onChange={(e) => setDnrDate(e.target.value)} style={inputStyle} />
              </div>
              <div style={{ flex: 1 }}>
                <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  Effective Start of Care
                </span>
                <input type="text" value={socDate} onChange={(e) => setSocDate(e.target.value)} style={inputStyle} />
              </div>
            </div>
          </div>

          {/* SOC Patient Notifications */}
          <div style={{
            flex: 1, backgroundColor: colors.bg, borderRadius: 8, padding: 20,
            border: `1px solid ${colors.border}`,
          }}>
            <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16 }}>
              Section 4 — SOC Patient Notifications
            </div>
            <div style={{ color: colors.text, fontSize: 13, lineHeight: '1.6', marginBottom: 16 }}>
              I certify that the patient/family was furnished with written copies of the Hospice Bill
              of Rights, Patient Privacy Protection Act, and after-hours emergency contact
              instructions at the start of care.
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <div style={{
                width: 20, height: 20, borderRadius: 4, backgroundColor: colors.teal,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ color: colors.white, fontSize: 12, fontWeight: 700 }}>✓</span>
              </div>
              <span style={{ color: colors.text, fontSize: 13 }}>Written notifications provided and explained to representative</span>
            </label>
          </div>
        </div>

        {/* Staff Confirmation */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16 }}>
            Section 5 — Staff Confirmation Statement
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 20, height: 20, borderRadius: 10, backgroundColor: colors.green,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ color: colors.white, fontSize: 10, fontWeight: 700 }}>✓</span>
              </div>
              <span style={{ color: colors.text, fontSize: 13 }}>
                I have reviewed the checked items and have original hard copies on file.
              </span>
            </label>
            <div>
              <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                Review Date
              </span>
              <input type="text" value={reviewDate} onChange={(e) => setReviewDate(e.target.value)} style={{ ...inputStyle, width: 160 }} />
            </div>
          </div>
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
        }}>Submit Verification File</button>
      </div>
    </div>
  );
};

export default ConsentNotifications;
