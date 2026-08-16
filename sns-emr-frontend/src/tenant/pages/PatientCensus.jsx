import React from 'react';
import { COLORS, S } from '../TenantDashboard';

const PATIENTS = [
  { name: 'Martha Stevens', mrn: '22938', dx: 'CHF', level: 'Routine', rn: 'John Higgins', poc: '3 days', pocColor: COLORS.red, status: 'Active', statusColor: COLORS.green, highlight: true },
  { name: 'James Wilson', mrn: '22941', dx: 'COPD', level: 'Continuous', rn: 'Sarah Cole', poc: '12 days', pocColor: COLORS.orange, status: 'Active', statusColor: COLORS.green },
  { name: 'Betty Thomas', mrn: '22945', dx: 'Cancer', level: 'Respite', rn: 'David Vance', poc: 'Expired', pocColor: COLORS.red, status: 'Active', statusColor: COLORS.green },
  { name: 'Arthur Miller', mrn: '22950', dx: 'Alzheimers', level: 'GIP', rn: 'John Higgins', poc: '45 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
  { name: 'Eleanor Vance', mrn: '22953', dx: 'CHF', level: 'Routine', rn: 'John Higgins', poc: '28 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
  { name: 'Robert Lee', mrn: '22958', dx: 'COPD', level: 'Routine', rn: 'Sarah Cole', poc: '19 days', pocColor: COLORS.muted, status: 'On Hold', statusColor: COLORS.orange },
  { name: 'Harold Green', mrn: '22961', dx: 'Cancer', level: 'Routine', rn: 'David Vance', poc: '62 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
  { name: 'Mildred Cox', mrn: '22965', dx: 'Alzheimers', level: 'Routine', rn: 'John Higgins', poc: '8 days', pocColor: COLORS.orange, status: 'Active', statusColor: COLORS.green },
  { name: 'Grace Kelly', mrn: '22970', dx: 'CHF', level: 'Routine', rn: 'Sarah Cole', poc: '14 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
  { name: 'Frank Sinatra', mrn: '22975', dx: 'COPD', level: 'Routine', rn: 'John Higgins', poc: '32 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
  { name: 'John Wayne', mrn: '22980', dx: 'Cancer', level: 'Continuous', rn: 'David Vance', poc: 'Expired', pocColor: COLORS.red, status: 'Pending DC', statusColor: COLORS.red },
  { name: 'Dean Martin', mrn: '22985', dx: 'CHF', level: 'Routine', rn: 'Sarah Cole', poc: '54 days', pocColor: COLORS.muted, status: 'Active', statusColor: COLORS.green },
];

const QUICK_LINKS = ['View Full Chart', 'Visit History', 'Medications & Orders', 'Care Plan & Goals', 'Billing Ledger'];

const ACTIVITY = [
  { title: 'RN Visit Completed', sub: 'John Higgins RN • 10:15 AM' },
  { title: 'Medication Renewal Signed', sub: 'Dr Albert Chen • Yesterday' },
  { title: 'MSW Evaluation Updated', sub: 'Sarah Cole MSW • 2 days ago' },
];

export default function PatientCensus() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Patient Census</h1>
          <p style={S.pageSubtitle}>Complete active patient registry with care plans and clinical status</p>
        </div>
        <button style={S.btn(COLORS.teal)}>Add New Patient</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Census', value: '47' },
          { label: 'Routine Care', value: '38' },
          { label: 'Continuous Care', value: '4' },
          { label: 'Respite Care', value: '3' },
          { label: 'GIP', value: '2' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input style={S.searchBar} placeholder="Search by name, MRN, clinician..." readOnly />
        </div>
        {['Dx Group', 'Care Level', 'Assigned RN', 'Status'].map((f) => (
          <select key={f} style={S.select}><option>{f}</option></select>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, margin: 0 }}>Active Registry</h3>
            <span style={{ fontSize: 12, fontWeight: 400, color: COLORS.dim }}>Showing 12 of 47 Patients</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['PATIENT NAME', 'MRN', 'PRIMARY DX', 'CARE LEVEL', 'ASSIGNED RN', 'POC EXPIRY', 'STATUS'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {PATIENTS.map((p, i) => (
                <tr key={i}>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: p.highlight ? COLORS.teal : COLORS.textPrimary }}>{p.name}</td>
                  <td style={S.tableCell}>{p.mrn}</td>
                  <td style={S.tableCell}>{p.dx}</td>
                  <td style={S.tableCell}>{p.level}</td>
                  <td style={S.tableCell}>{p.rn}</td>
                  <td style={{ ...S.tableCell, fontWeight: 500, color: p.pocColor }}>{p.poc}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: p.statusColor }}>{p.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={S.card}>
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', fontSize: 18, fontWeight: 700, color: COLORS.white }}>
              <span>MS</span>
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Martha Stevens</h3>
            <p style={{ fontSize: 12, fontWeight: 400, color: COLORS.muted, margin: '6px 0 0' }}>MRN 22938 • DOB: 11/12/1942 (81 y/o)</p>
          </div>

          {[
            { label: 'Primary Diagnosis', value: 'Congestive Heart Failure (CHF)' },
            { label: 'Attending Physician', value: 'Dr. Albert Chen, MD' },
            { label: 'Admission Date', value: '04/12/2023' },
            { label: 'Current Care Level', value: 'Routine Home Care' },
            { label: 'POC Period', value: '08/10/2024 - 11/08/2024' },
          ].map((f, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 11, fontWeight: 400, color: COLORS.dim, margin: '0 0 2px' }}>{f.label}</p>
              <p style={{ fontSize: 13, fontWeight: 400, color: COLORS.textPrimary, margin: 0 }}>{f.value}</p>
            </div>
          ))}

          <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.dim, margin: '20px 0 10px' }}>QUICK CHART ACTIONS</p>
          {QUICK_LINKS.map((l, i) => (
            <div key={i} style={{ padding: '8px 12px', background: COLORS.bg, borderRadius: 6, marginBottom: 6, fontSize: 13, fontWeight: 600, color: COLORS.white, cursor: 'pointer', border: `1px solid ${COLORS.border}` }}>{l}</div>
          ))}

          <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.dim, margin: '20px 0 10px' }}>RECENT ACTIVITY</p>
          {ACTIVITY.map((a, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary, margin: 0 }}>{a.title}</p>
              <p style={{ fontSize: 11, fontWeight: 400, color: COLORS.dim, margin: '2px 0 0' }}>{a.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
