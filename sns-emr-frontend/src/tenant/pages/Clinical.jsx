import React from 'react';
import { COLORS, S } from '../design';

const TABS = [
  { label: 'Visit Notes', count: '34', active: true },
  { label: 'Plans of Care', count: '12' },
  { label: 'Assessments', count: '8' },
  { label: 'Orders', count: '4' },
  { label: 'IDG Notes', count: '18' },
];

const DOCS = [
  { date: 'Oct 24, 2025', patient: 'Martha Stevens', alert: true, type: 'Visit Note', clinician: 'Sarah Jenkins, RN', status: 'Cosign Required', statusColor: COLORS.red, due: 'Oct 24, 2025' },
  { date: 'Oct 24, 2025', patient: 'James Miller', type: 'Assessment', clinician: 'Robert Chen, MSW', status: 'Draft', statusColor: COLORS.muted, due: 'Oct 25, 2025' },
  { date: 'Oct 23, 2025', patient: 'Eleanor Vance', type: 'Plan of Care', clinician: 'Sarah Jenkins, RN', status: 'Signed', statusColor: COLORS.green, due: 'Oct 23, 2025' },
  { date: 'Oct 23, 2025', patient: 'Thomas H. Wright', alert: true, type: 'Recertification', clinician: 'Dr. Allen Patel, MD', status: 'Pending Signature', statusColor: COLORS.yellow, due: 'Oct 23, 2025' },
  { date: 'Oct 22, 2025', patient: 'Lillian G.', type: 'Visit Note', clinician: 'A. Vance, Chaplain', status: 'Signed', statusColor: COLORS.green, due: 'Oct 22, 2025' },
  { date: 'Oct 22, 2025', patient: 'Frank Sinatra', type: 'Clinical Order', clinician: 'Dr. Allen Patel, MD', status: 'Signed', statusColor: COLORS.green, due: 'Oct 22, 2025' },
  { date: 'Oct 21, 2025', patient: 'Alice Cooper', type: 'Visit Note', clinician: 'Sarah Jenkins, RN', status: 'Draft', statusColor: COLORS.muted, due: 'Oct 22, 2025' },
  { date: 'Oct 21, 2025', patient: 'David Bowie', type: 'Assessment', clinician: 'Robert Chen, MSW', status: 'Signed', statusColor: COLORS.green, due: 'Oct 21, 2025' },
  { date: 'Oct 20, 2025', patient: 'Freddie Mercury', alert: true, type: 'Visit Note', clinician: 'M. Ramirez, Aide', status: 'Cosign Required', statusColor: COLORS.red, due: 'Oct 20, 2025' },
  { date: 'Oct 19, 2025', patient: 'Johnny Cash', type: 'Plan of Care', clinician: 'Sarah Jenkins, RN', status: 'Signed', statusColor: COLORS.green, due: 'Oct 19, 2025' },
];

export default function Clinical() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>Clinical Documentation</h1>
          <p style={S.pageSubtitle}>Manage plans of care, visit notes, assessments, and clinical orders for all active patients.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>New Documentation</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Unsigned Notes', value: '14' },
          { label: 'Pending Cosigns', value: '8' },
          { label: 'POCs Expiring 30 Days', value: '6' },
          { label: 'Overdue Assessments', value: '3' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.textPrimary, margin: '6px 0 0' }}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: `1px solid ${COLORS.border}` }}>
        {TABS.map((tab, i) => (
          <button key={tab.label} style={{
            padding: '12px 20px', border: 'none', cursor: 'pointer',
            fontSize: 14, fontWeight: 600,
            color: tab.active ? '#14b8a6' : COLORS.muted,
            background: 'transparent',
            borderBottom: tab.active ? '2px solid #14b8a6' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            {tab.label}
            <span style={{ fontSize: 11, fontWeight: 600, color: tab.active ? '#14b8a6' : COLORS.muted }}>{tab.count}</span>
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
        <div style={S.card}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Date', 'Patient Name', 'Type', 'Clinician', 'Status', 'Due Date'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.dim }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DOCS.map((d, i) => (
                <tr key={i}>
                  <td style={S.tableCell}>{d.date}</td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.textPrimary }}>
                    {d.alert && <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.red, marginRight: 6 }}>Alert</span>}
                    {d.patient}
                  </td>
                  <td style={S.tableCell}>{d.type}</td>
                  <td style={S.tableCell}>{d.clinician}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: d.statusColor }}>{d.status}</span></td>
                  <td style={S.tableCell}>{d.due}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={S.card}>
          <p style={{ fontSize: 11, fontWeight: 700, color: '#14b8a6', margin: '0 0 12px' }}>Active Preview</p>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 4px' }}>Martha Stevens</h3>
          <p style={{ fontSize: 12, fontWeight: 400, color: COLORS.muted, margin: '0 0 16px' }}>DOB: 12/04/1948 • DX: End-Stage COPD</p>

          {[
            { label: 'Document Type:', value: 'RN Skilled Nursing Visit', vColor: COLORS.textPrimary },
            { label: 'Visit Date:', value: 'Today, 10:15 AM', vColor: COLORS.textPrimary },
            { label: 'Status:', value: 'Cosign Required', vColor: COLORS.red },
          ].map((f, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: COLORS.dim }}>{f.label}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: f.vColor }}>{f.value}</span>
            </div>
          ))}

          <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary, margin: '20px 0 10px' }}>Vital Signs Summary</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
            {[
              { label: 'Blood Pressure', value: '128/82' },
              { label: 'Heart Rate', value: '74 bpm' },
              { label: 'Temperature', value: '98.4 °F' },
              { label: 'O2 Saturation', value: '96%', vColor: '#14b8a6' },
            ].map((v, i) => (
              <div key={i}>
                <p style={{ fontSize: 11, color: COLORS.dim, margin: '0 0 2px' }}>{v.label}</p>
                <p style={{ fontSize: 14, fontWeight: 700, color: v.vColor || COLORS.textPrimary, margin: 0 }}>{v.value}</p>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 12, color: COLORS.muted }}>Pain Assessment Scale</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.red }}>3/10</span>
          </div>

          <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary, margin: '16px 0 6px' }}>Clinical Narrative Snippet</p>
          <p style={{ fontSize: 12, fontWeight: 400, color: COLORS.muted, margin: '0 0 16px', lineHeight: 1.5 }}>Patient is comfortable but experiencing shortness of breath with mild exertion. Administered nebulizer treatment with mo...</p>

          <div style={{ display: 'flex', gap: 8 }}>
            <button style={S.btn(COLORS.teal)}>Sign Note</button>
            <button style={S.btnOutline}>Request Cosign</button>
          </div>
        </div>
      </div>
    </div>
  );
}
