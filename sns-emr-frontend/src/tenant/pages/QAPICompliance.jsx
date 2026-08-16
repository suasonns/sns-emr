import React from 'react';
import { COLORS, S } from '../design';

const INDICATORS = [
  { measure: 'Pain Assessment Timeliness', target: '95.0%', actual: '96.2%', status: 'Met', statusColor: '#10b796' },
  { measure: 'Fall Prevention Protocol', target: '95.0%', actual: '94.8%', status: 'Near', statusColor: COLORS.orange },
  { measure: 'Medication Error Rate', target: '< 0.5%', actual: '0.3%', status: 'Met', statusColor: '#10b796' },
  { measure: 'Patient/Family Satisfaction', target: '4.5/5', actual: '4.7/5', status: 'Met', statusColor: '#10b796' },
  { measure: 'Hospice Visit Frequency Compliance', target: '90.0%', actual: '91.4%', status: 'Met', statusColor: '#10b796' },
  { measure: 'IDG Meeting Compliance', target: '100%', actual: '100%', status: 'Met', statusColor: '#10b796' },
  { measure: 'Bereavement Follow-up Compliance', target: '90.0%', actual: '88.2%', status: 'Below', statusColor: COLORS.red },
  { measure: 'Discharge Planning Timeliness', target: '95.0%', actual: '93.5%', status: 'Near', statusColor: COLORS.orange },
];

const PROJECTS = [
  { title: 'Pain Management Consistency', status: 'Review', statusColor: COLORS.orange, pct: '75%', lead: 'Lead: Dr. Elena Rostova' },
  { title: 'Infallible Fall Prevention', status: 'In Progress', statusColor: '#10b796', pct: '90%', lead: 'Lead: Marcus Chen, MD' },
  { title: 'IDG Documentation Workflow', status: 'Planning', statusColor: COLORS.blue, pct: '35%', lead: 'Lead: Emily Watson, RN' },
  { title: 'Bereavement Outreach Revamp', status: 'In Progress', statusColor: '#10b796', pct: '60%', lead: 'Lead: Sarah Higgins, MSW' },
];

const DEADLINES = [
  { month: 'Oct', day: '15', title: 'Medicare Cost Report Submission', priority: 'High Priority' },
  { month: 'Nov', day: '01', title: 'Annual Fire & Safety Audit', priority: 'Medium Priority' },
  { month: 'Nov', day: '15', title: 'HQRP Quality Data Transmission', priority: 'High Priority' },
  { month: 'Dec', day: '01', title: 'Staff TB Screenings Due', priority: 'Low Priority' },
  { month: 'Dec', day: '10', title: 'OIG Exclusion List Verification', priority: 'Medium Priority' },
];

const CAPAS = [
  { ref: 'CAP-2401', issue: 'Delayed Initial Bereavement Call', owner: 'S. Higgins', target: 'Oct 20, 2024', status: 'Open', statusColor: COLORS.red },
  { ref: 'CAP-2398', issue: 'Missing Signature on POC', owner: 'J. Carter', target: 'Oct 12, 2024', status: 'Resolved', statusColor: '#10b796' },
  { ref: 'CAP-2394', issue: 'Refrigerator Temp Log Gap', owner: 'T. Sterling', target: 'Sep 30, 2024', status: 'Resolved', statusColor: '#10b796' },
  { ref: 'CAP-2388', issue: 'Incomplete Initial Pain Assessment', owner: 'E. Watson', target: 'Sep 15, 2024', status: 'Resolved', statusColor: '#10b796' },
  { ref: 'CAP-2375', issue: 'IDG Attendance Record Deviation', owner: 'M. Chen', target: 'Aug 20, 2024', status: 'Resolved', statusColor: '#10b796' },
];

export default function QAPICompliance() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>QAPI & Compliance</h1>
          <p style={{ fontSize: 14, fontWeight: 400, color: COLORS.muted, margin: '4px 0 0' }}>Quality metrics, performance improvement initiatives, regulatory compliance tracking and survey readiness.</p>
        </div>
        <button style={S.btnOutline}>Export Board</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Overall Quality Score', value: '92.4%', desc: 'Target: 95.0%+' },
          { label: 'Active QAPI Projects', value: '6', desc: 'In progress trials' },
          { label: 'Open Corrective Actions', value: '3', desc: 'Action plans pending' },
          { label: 'Survey Readiness', value: '87%', desc: 'Calculated index' },
          { label: 'Infection Control Rate', value: '99.1%', desc: 'Goal: 100%' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.offWhite, margin: '6px 0 4px' }}>{s.value}</p>
            <p style={{ fontSize: 12, color: COLORS.dim, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, marginBottom: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>Quality Indicators</h3>
            <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>View Historical Trends</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Quality Performance Measure', 'Target', 'Actual', 'Trend', 'Status'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {INDICATORS.map((ind, i) => (
                <tr key={i}>
                  <td style={{ ...S.tableCell, fontWeight: 500, color: COLORS.offWhite }}>{ind.measure}</td>
                  <td style={S.tableCell}>{ind.target}</td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.offWhite }}>{ind.actual}</td>
                  <td style={S.tableCell}>{ind.status === 'Met' ? '↑' : ind.status === 'Below' ? '↓' : '→'}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: ind.statusColor }}>{ind.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <div style={S.card}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: '0 0 16px' }}>Active QAPI Projects</h3>
            {PROJECTS.map((p, i) => (
              <div key={i} style={{ padding: '12px 0', borderBottom: i < PROJECTS.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.offWhite }}>{p.title}</span>
                  <span style={{ fontSize: 10, fontWeight: 600, color: p.statusColor }}>{p.status}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: COLORS.dim }}>{p.lead}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted }}>{p.pct}</span>
                </div>
                <div style={{ height: 4, background: COLORS.border, borderRadius: 2 }}>
                  <div style={{ width: p.pct, height: '100%', background: COLORS.teal, borderRadius: 2 }} />
                </div>
              </div>
            ))}
          </div>

          <div style={S.card}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: '0 0 16px' }}>Compliance Deadlines</h3>
            {DEADLINES.map((d, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '10px 0', borderBottom: i < DEADLINES.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <div style={{ textAlign: 'center', minWidth: 40 }}>
                  <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{d.month}</p>
                  <p style={{ fontSize: 13, fontWeight: 700, color: COLORS.offWhite, margin: 0 }}>{d.day}</p>
                </div>
                <div>
                  <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.offWhite, margin: 0 }}>{d.title}</p>
                  <p style={{ fontSize: 11, color: COLORS.dim, margin: '2px 0 0' }}>{d.priority}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>Corrective Action Log (CAPA)</h3>
          <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.offWhite }}>Filter: All Actions</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['CAPA Ref', 'Identified Issue', 'Assigned Owner', 'Target Resolution', 'Status'].map((h) => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CAPAS.map((c, i) => (
              <tr key={i}>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.teal }}>{c.ref}</td>
                <td style={{ ...S.tableCell, color: COLORS.offWhite }}>{c.issue}</td>
                <td style={S.tableCell}>{c.owner}</td>
                <td style={S.tableCell}>{c.target}</td>
                <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: c.statusColor }}>{c.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
