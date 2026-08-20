import React from 'react';
import { COLORS } from '../../TenantDashboard';

const samplePatients = [
  { name: 'Martha Stevens', mrn: 'MRN-1849', diagnosis: 'Congestive Heart Failure', level: 'Routine', clinician: 'John Higgins, RN' },
  { name: 'James Wilson', mrn: 'MRN-2094', diagnosis: 'Cancer Pain Management', level: 'Complex', clinician: 'Sarah Patel, MSW' },
  { name: 'Betty Thomas', mrn: 'MRN-1188', diagnosis: 'End-Stage Renal Disease', level: 'Routine', clinician: 'Maria Lopez, LVN' },
  { name: 'Arthur Miller', mrn: 'MRN-3342', diagnosis: 'COPD', level: 'High Risk', clinician: 'Chloe Nguyen, RN' },
];

export default function CustomReportBuilder() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 20 }}>
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.text, marginBottom: 18, fontFamily: 'Inter, sans-serif' }}>
          Report Configuration
        </div>

        <div style={{ display: 'grid', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Report Name</label>
            <input
              value="Custom Clinical Summary"
              style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontFamily: 'Inter, sans-serif' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Date Range</label>
              <select style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontFamily: 'Inter, sans-serif' }}>
                <option>Patient Census</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Group By</label>
              <select style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontFamily: 'Inter, sans-serif' }}>
                <option>Assigned Clinician</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 8, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Configure Columns</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {['Patient Name', 'MRN', 'Diagnosis', 'Care Level', 'Assigned Clinician', 'Visit Last Date', 'Poc Status'].map((item) => (
                <span key={item} style={{ padding: '7px 10px', borderRadius: 999, fontSize: 12, border: `1px solid ${COLORS.border}`, color: COLORS.text, background: `${COLORS.primary}12`, fontFamily: 'Inter, sans-serif' }}>{item}</span>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 8, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Active Filters</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {['Status: Active', 'Admit: 30+ days', 'Care Type: Home Visit'].map((filter) => (
                <span key={filter} style={{ padding: '6px 10px', borderRadius: 999, fontSize: 11, background: `${COLORS.primary}18`, color: COLORS.primary, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{filter}</span>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 6 }}>
            <button style={{ padding: '10px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Save as Template</button>
            <button style={{ padding: '10px 16px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate Custom Report</button>
          </div>
        </div>
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Live Preview (Sample Rows)</div>
          <span style={{ fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>5 records</span>
        </div>

        <div style={{ overflow: 'hidden', borderRadius: 10, border: `1px solid ${COLORS.border}` }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: `${COLORS.primary}12` }}>
                {['Patient Name', 'MRN', 'Diagnosis', 'Care Level', 'Clinician'].map((header) => (
                  <th key={header} style={{ padding: '10px 12px', textAlign: 'left', color: COLORS.text, fontSize: 11, fontWeight: 700, fontFamily: 'Inter, sans-serif' }}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {samplePatients.map((row, idx) => (
                <tr key={idx} style={{ borderTop: idx === 0 ? 'none' : `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{row.name}</td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{row.mrn}</td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{row.diagnosis}</td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{row.level}</td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{row.clinician}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
