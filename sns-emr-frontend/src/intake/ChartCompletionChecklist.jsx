import React, { useState } from 'react';
import { useThemeMode } from '../theme/theme';
import { getChartColors } from '../theme/chartColors';
import { defaultPatient } from './ConsentNotifications';

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

const sections = [
  {
    key: 'admission', label: 'Admission Documents', items: [
      { label: 'Hospice Eval Order', status: 'complete', by: 'Dr. Reyes', date: '01/15/2026' },
      { label: 'Informed Consent', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'Election of Hospice', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'POLST / DNR', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'POA / Advance Directive', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'Bill of Rights', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'Telehealth Consent', status: 'pending', by: null, date: null },
      { label: 'Non-Covered Items Notification', status: 'overdue', by: null, date: null },
    ]
  },
  {
    key: 'clinical', label: 'Clinical Assessments', items: [
      { label: 'Initial RN Assessment', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'HHA Care Plan', status: 'complete', by: 'R. Ortiz, HHA', date: '01/16/2026' },
      { label: 'MSW Psychosocial Assessment', status: 'complete', by: 'J. Blake, LCSW', date: '01/17/2026' },
      { label: 'Spiritual Assessment', status: 'pending', by: null, date: null },
      { label: 'Bereavement Risk Assessment', status: 'pending', by: null, date: null },
      { label: 'Nutritional Assessment', status: 'overdue', by: null, date: null },
    ]
  },
  {
    key: 'orders', label: 'Physician Orders', items: [
      { label: 'Certification of Terminal Illness (CTI)', status: 'complete', by: 'Romel Suason, RN (reviewed) · signed by Dr. Reyes, MD', date: '01/15/2026' },
      { label: 'Face-to-Face Encounter (F2F)', status: 'complete', by: 'Dr. Samuel Okafor, NP (PCP/covering MD)', date: '01/14/2026' },
      { label: 'Plan of Care (485)', status: 'complete', by: 'Romel Suason, RN', date: '01/16/2026' },
      { label: 'Medication Orders', status: 'complete', by: 'Angela Suason, LVN', date: '01/16/2026' },
      { label: 'DME Orders', status: 'pending', by: null, date: null },
    ]
  },
  {
    key: 'coordination', label: 'Care Coordination', items: [
      { label: 'IDG Meeting Notes', status: 'complete', by: 'J. Blake, LCSW', date: '01/18/2026' },
      { label: 'Staff Assignment Confirmed', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
      { label: 'Volunteer Coordination', status: 'pending', by: null, date: null },
    ]
  },
  {
    key: 'compliance', label: 'Compliance & HOPE', items: [
      { label: 'HOPE Assessment', status: 'pending', by: null, date: null },
      { label: 'CAHPS Survey Eligibility', status: 'complete', by: 'M. Whitfield, RN', date: '01/15/2026' },
    ]
  },
];

const statusMeta = (status, colors) => {
  if (status === 'complete') return { variant: 'green', label: 'Complete', icon: '✓' };
  if (status === 'overdue') return { variant: 'red', label: 'Overdue', icon: '!' };
  return { variant: 'amber', label: 'Pending', icon: '•' };
};

const ChecklistItem = ({ item, colors }) => {
  const meta = statusMeta(item.status, colors);
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      backgroundColor: colors.bg, borderRadius: 8, padding: '10px 16px',
      border: `1px solid ${colors.border}`, marginBottom: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 22, height: 22, borderRadius: 11,
          backgroundColor: meta.variant === 'green' ? colors.green : meta.variant === 'red' ? colors.red : colors.amber,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: colors.white, fontSize: 12, fontWeight: 700, flexShrink: 0,
        }}>{meta.icon}</div>
        <span style={{ color: colors.text, fontSize: 13 }}>{item.label}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {item.by && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase' }}>Completed By</div>
            <div style={{ color: colors.white, fontSize: 12 }}>{item.by} · {item.date}</div>
          </div>
        )}
        <Badge variant={meta.variant} colors={colors}>{meta.label}</Badge>
        <span style={{ color: colors.label, fontSize: 14, cursor: 'pointer' }} title="Notes">📝</span>
      </div>
    </div>
  );
};

const SectionCard = ({ section, colors }) => {
  const total = section.items.length;
  const complete = section.items.filter((i) => i.status === 'complete').length;
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ color: colors.white, fontSize: 14, fontWeight: 700 }}>{section.label}</span>
        <Badge variant={complete === total ? 'green' : 'amber'} colors={colors}>{complete}/{total} Complete</Badge>
      </div>
      {section.items.map((item, i) => (
        <ChecklistItem key={i} item={item} colors={colors} />
      ))}
    </div>
  );
};

const ChartCompletionChecklist = ({ patient = defaultPatient }) => {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);

  const allItems = sections.flatMap((s) => s.items);
  const totalItems = allItems.length;
  const completeItems = allItems.filter((i) => i.status === 'complete').length;
  const pendingItems = allItems.filter((i) => i.status === 'pending').length;
  const overdueItems = allItems.filter((i) => i.status === 'overdue').length;
  const percentComplete = Math.round((completeItems / totalItems) * 100);

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ color: colors.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{patient.firstName} {patient.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>Intake & Admission</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: colors.white }}>Chart Completion Checklist</span>
      </div>

      <PatientBanner patient={patient} colors={colors} />

      <div style={cardStyle(colors)}>
        <div style={{ marginBottom: 20 }}>
          <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            Chart Completion Checklist
          </div>
          <div style={{ color: colors.label, fontSize: 13 }}>
            Track completion of all required admission, clinical, and compliance documentation.
          </div>
        </div>

        {/* Overall progress */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ color: colors.text, fontSize: 13, fontWeight: 600 }}>Overall Progress</span>
            <span style={{ color: colors.teal, fontSize: 13, fontWeight: 700 }}>{percentComplete}%</span>
          </div>
          <div style={{ height: 10, backgroundColor: colors.bg, borderRadius: 5, border: `1px solid ${colors.border}`, overflow: 'hidden' }}>
            <div style={{
              width: `${percentComplete}%`, height: '100%',
              backgroundColor: percentComplete === 100 ? colors.green : colors.teal,
              borderRadius: 5, transition: 'width 0.3s ease',
            }} />
          </div>
        </div>

        {/* Summary row */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 28 }}>
          <div style={{ flex: 1, backgroundColor: colors.bg, borderRadius: 8, padding: 14, border: `1px solid ${colors.border}`, textAlign: 'center' }}>
            <div style={{ color: colors.white, fontSize: 22, fontWeight: 700 }}>{totalItems}</div>
            <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase' }}>Total Items</div>
          </div>
          <div style={{ flex: 1, backgroundColor: colors.greenBg, borderRadius: 8, padding: 14, border: `1px solid ${colors.green}33`, textAlign: 'center' }}>
            <div style={{ color: colors.green, fontSize: 22, fontWeight: 700 }}>{completeItems}</div>
            <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase' }}>Complete</div>
          </div>
          <div style={{ flex: 1, backgroundColor: colors.amberBg, borderRadius: 8, padding: 14, border: `1px solid ${colors.amber}33`, textAlign: 'center' }}>
            <div style={{ color: colors.amber, fontSize: 22, fontWeight: 700 }}>{pendingItems}</div>
            <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase' }}>Pending</div>
          </div>
          <div style={{ flex: 1, backgroundColor: colors.redBg, borderRadius: 8, padding: 14, border: `1px solid ${colors.red}33`, textAlign: 'center' }}>
            <div style={{ color: colors.red, fontSize: 22, fontWeight: 700 }}>{overdueItems}</div>
            <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase' }}>Overdue</div>
          </div>
        </div>

        {sections.map((s) => (
          <SectionCard key={s.key} section={s} colors={colors} />
        ))}
      </div>

      {/* Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        <button style={{
          padding: '10px 24px', backgroundColor: 'transparent', color: colors.teal,
          border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 13,
          fontWeight: 600, cursor: 'pointer', fontFamily: "'Inter', sans-serif",
        }}>Print Checklist</button>
        <button style={{
          padding: '10px 24px', backgroundColor: 'transparent', color: colors.teal,
          border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 13,
          fontWeight: 600, cursor: 'pointer', fontFamily: "'Inter', sans-serif",
        }}>Export PDF</button>
        <button style={{
          padding: '10px 24px', backgroundColor: colors.teal, color: colors.white,
          border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600,
          cursor: 'pointer', fontFamily: "'Inter', sans-serif",
        }}>Mark All Complete</button>
      </div>
    </div>
  );
};

export default ChartCompletionChecklist;
