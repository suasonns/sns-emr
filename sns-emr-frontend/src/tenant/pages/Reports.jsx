import React from 'react';
import { COLORS, S } from '../design';

const TABS = [
  { label: 'Clinical', active: true },
  { label: 'Financial' },
  { label: 'Operational' },
  { label: 'Compliance' },
  { label: 'Custom Builder' },
];

const REPORTS = [
  { title: 'Patient Census Report', lastRun: 'Last Run: Yesterday', freq: 'Daily', desc: 'Detailed breakdown of admissions, discharges, active census, and length of stay analytics.' },
  { title: 'Visit Frequency Report', lastRun: 'Last Run: 3 days ago', freq: 'Weekly', desc: 'Monitors clinician check-in rates and matches actual visits against current patient Plans of Care.' },
  { title: 'Missed Visit Report', lastRun: 'Last Run: Today, 8:00 AM', freq: 'Daily', desc: 'Flags missed clinical assessments with documentation logs, causes, and alert status tracking.' },
  { title: 'POC Timeliness Report', lastRun: 'Last Run: Oct 01, 2024', freq: 'Monthly', desc: 'Tracks Plan of Care creation, physician signature turnaround, and statutory submission windows.' },
  { title: 'Clinician Productivity Report', lastRun: 'Last Run: Last Week', freq: 'Weekly', desc: 'Performance tracking, case visits, mileage, documentation speed, and caseload utilization indices.' },
  { title: 'Referral Conversion Report', lastRun: 'Last Run: Oct 01, 2024', freq: 'Monthly', desc: 'Funnels conversion analysis from inquiry through medical assessment to active admission status.' },
  { title: 'Quality Indicator Trend Report', lastRun: 'Last Run: Sep 30, 2024', freq: 'Monthly', desc: 'Aggregated performance on main QAPI quality measures over historical quarters.' },
  { title: 'Infection Control Report', lastRun: 'Last Run: 5 days ago', freq: 'Weekly', desc: 'Tracks reported patient or staff infections, antibiotic usage logs, and containment adherence.' },
];

const RECENT = [
  { name: 'September CMS HQRP Quality Data Export', by: 'Sarah Jenkins, RN', date: 'Oct 02, 2024', format: 'CSV', size: '4.2 MB' },
  { name: 'September Admissions & Discharges Summary', by: 'Sarah Jenkins, RN', date: 'Oct 01, 2024', format: 'PDF', size: '1.8 MB' },
  { name: 'Clinician Visit Compliance Audit Q3', by: 'David Miller, PT', date: 'Sep 28, 2024', format: 'Excel', size: '12.4 MB' },
  { name: 'Bereavement Contact Outreach Monthly Log', by: 'Sarah Higgins, MSW', date: 'Sep 25, 2024', format: 'PDF', size: '940 KB' },
  { name: 'Adverse Drug Event Log YTD', by: 'Marcus Chen, MD', date: 'Sep 18, 2024', format: 'CSV', size: '125 KB' },
  { name: 'Missed Visits and Action Exception Log', by: 'Sarah Jenkins, RN', date: 'Sep 15, 2024', format: 'Excel', size: '3.1 MB' },
];

export default function Reports() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>Reports</h1>
          <p style={{ fontSize: 14, fontWeight: 400, color: COLORS.muted, margin: '4px 0 0' }}>Generate clinical, financial, and operational reports with custom date ranges and export options.</p>
        </div>
        <button style={S.btnOutline}>Scheduled Exports</button>
      </div>

      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: `1px solid ${COLORS.border}` }}>
        {TABS.map((tab) => (
          <button key={tab.label} style={{
            padding: '12px 20px', border: 'none', cursor: 'pointer',
            fontSize: 14, fontWeight: tab.active ? 600 : 500,
            color: tab.active ? COLORS.teal : COLORS.muted,
            background: 'transparent',
            borderBottom: tab.active ? `2px solid ${COLORS.teal}` : '2px solid transparent',
          }}>{tab.label}</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 32 }}>
        {REPORTS.map((r, i) => (
          <div key={i} style={S.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.offWhite, margin: 0 }}>{r.title}</h3>
              <span style={S.badge(COLORS.blue + '22', COLORS.blue)}>{r.freq}</span>
            </div>
            <p style={{ fontSize: 11, color: COLORS.dim, margin: '0 0 8px' }}>{r.lastRun}</p>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 16px', lineHeight: 1.5 }}>{r.desc}</p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 16 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.muted, cursor: 'pointer' }}>Download PDF</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.muted, cursor: 'pointer' }}>Export CSV</span>
              </div>
              <button style={{ ...S.btn(COLORS.teal), padding: '8px 16px', fontSize: 12 }}>Generate Now</button>
            </div>
          </div>
        ))}
      </div>

      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>Recently Generated Logs</h3>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Showing past 6 downloads</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Report Name', 'Generated By', 'Date Generated', 'Format', 'File Size', 'Action'].map((h) => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {RECENT.map((r, i) => (
              <tr key={i}>
                <td style={{ ...S.tableCell, fontWeight: 500, color: COLORS.offWhite }}>{r.name}</td>
                <td style={S.tableCell}>{r.by}</td>
                <td style={S.tableCell}>{r.date}</td>
                <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted }}>{r.format}</span></td>
                <td style={S.tableCell}>{r.size}</td>
                <td style={S.tableCell}><span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>Download</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
