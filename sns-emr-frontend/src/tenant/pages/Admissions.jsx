import React from 'react';
import { COLORS, S } from '../TenantDashboard';

const COLUMNS = [
  {
    title: 'New Referrals', count: '4', cards: [
      { name: 'Thomas Sterling', urgency: 'HIGH', urgColor: COLORS.orange, source: 'Mercy Hospital', dx: 'COPD', assigned: 'John Higgins', date: 'Sep 29' },
      { name: 'George Higgins', urgency: 'URGENT', urgColor: COLORS.red, source: 'Physician Direct', dx: 'Lung Cancer', assigned: 'David Vance', date: 'Sep 28' },
      { name: 'Lillian Vance', urgency: 'MEDIUM', urgColor: COLORS.teal, source: 'Heritage SNF', dx: 'Dementia', assigned: 'Sarah Cole', date: 'Sep 28' },
      { name: 'William Davis', urgency: 'MEDIUM', urgColor: COLORS.teal, source: 'Hospital Direct', dx: 'CHF', assigned: 'Sarah Cole', date: 'Sep 27' },
    ],
  },
  {
    title: 'Evaluation In Progress', count: '3', cards: [
      { name: 'Alice Brady', urgency: 'URGENT', urgColor: COLORS.red, source: 'St Jude Medical', dx: 'Renal Failure', assigned: 'John Higgins', date: 'Sep 25' },
      { name: 'Samuel Carter', urgency: 'HIGH', urgColor: COLORS.orange, source: 'Heritage SNF', dx: 'ALS', assigned: 'Sarah Cole', date: 'Sep 24' },
      { name: 'Emily Watson', urgency: 'MEDIUM', urgColor: COLORS.teal, source: 'Physician Direct', dx: 'Heart Failure', assigned: 'David Vance', date: 'Sep 23' },
    ],
  },
  {
    title: 'Approved Pending Admission', count: '2', cards: [
      { name: 'Franklin Rose', urgency: 'HIGH', urgColor: COLORS.orange, source: 'Mercy Hospital', dx: 'Pancreatic Ca', assigned: 'John Higgins', date: 'Sep 22' },
      { name: 'Clara Bow', urgency: 'MEDIUM', urgColor: COLORS.teal, source: 'Self Direct', dx: 'End Stage Alz', assigned: 'Sarah Cole', date: 'Sep 21' },
    ],
  },
  {
    title: 'Admitted', count: '3', cards: [
      { name: 'Martha Stevens', urgency: 'COMPLETED', urgColor: COLORS.green, source: 'Physician Direct', dx: 'CHF', assigned: 'John Higgins', date: 'Sep 15' },
      { name: 'James Wilson', urgency: 'COMPLETED', urgColor: COLORS.green, source: 'Hospital Direct', dx: 'COPD', assigned: 'Sarah Cole', date: 'Sep 12' },
      { name: 'Betty Thomas', urgency: 'COMPLETED', urgColor: COLORS.green, source: 'Heritage SNF', dx: 'Cancer', assigned: 'David Vance', date: 'Sep 10' },
    ],
  },
];

const ACTIVITY = [
  { date: '09/29/2024', name: 'George Higgins', source: 'Physician Direct', dx: 'Lung Cancer', evaluator: 'David Vance', pipeline: '1 day', status: 'Evaluation In Progress', statusColor: COLORS.teal },
  { date: '09/28/2024', name: 'Thomas Sterling', source: 'Mercy Hospital', dx: 'COPD', evaluator: 'John Higgins', pipeline: '2 days', status: 'New Referral', statusColor: COLORS.muted },
  { date: '09/27/2024', name: 'Lillian Vance', source: 'Heritage SNF', dx: 'Dementia', evaluator: 'Sarah Cole', pipeline: '3 days', status: 'New Referral', statusColor: COLORS.muted },
  { date: '09/26/2024', name: 'Franklin Rose', source: 'Mercy Hospital', dx: 'Pancreatic Ca', evaluator: 'John Higgins', pipeline: '5 days', status: 'Approved', statusColor: COLORS.green },
  { date: '09/25/2024', name: 'Alice Brady', source: 'St Jude Medical', dx: 'Renal Failure', evaluator: 'John Higgins', pipeline: '5 days', status: 'Evaluation In Progress', statusColor: COLORS.teal },
  { date: '09/24/2024', name: 'Samuel Carter', source: 'Heritage SNF', dx: 'ALS', evaluator: 'Sarah Cole', pipeline: '6 days', status: 'Evaluation In Progress', statusColor: COLORS.teal },
];

export default function Admissions() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Admissions & Referrals</h1>
          <p style={S.pageSubtitle}>Manage incoming referrals and process new patient intakes</p>
        </div>
        <button style={S.btn(COLORS.teal)}>New Referral</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Pending Referrals', value: '12' },
          { label: 'In Evaluation', value: '5' },
          { label: 'Approved for Admission', value: '3' },
          { label: 'Admitted This Month', value: '8' },
          { label: 'Conversion Rate', value: '67%' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {COLUMNS.map((col, ci) => (
          <div key={ci} style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.white }}>{col.title}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted }}>{col.count}</span>
            </div>
            {col.cards.map((card, i) => (
              <div key={i} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 12, marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{card.name}</span>
                  <span style={{ fontSize: 9, fontWeight: 700, color: card.urgColor }}>{card.urgency}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{ fontSize: 11, color: COLORS.dim }}>Source:</span>
                    <span style={{ fontSize: 11, color: COLORS.muted }}>{card.source}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{ fontSize: 11, color: COLORS.dim }}>Diagnosis:</span>
                    <span style={{ fontSize: 11, color: COLORS.muted }}>{card.dx}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{ fontSize: 11, color: COLORS.dim }}>Assigned:</span>
                    <span style={{ fontSize: 11, color: COLORS.muted }}>{card.assigned}</span>
                  </div>
                </div>
                <p style={{ fontSize: 10, color: COLORS.dim, margin: '8px 0 0', textAlign: 'right' }}>{card.date}</p>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div style={S.card}>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Recent Admission Activity</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['DATE', 'REFERRAL NAME', 'SOURCE', 'DIAGNOSIS', 'EVALUATOR', 'IN PIPELINE', 'STATUS', 'ACTION'].map((h) => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ACTIVITY.map((a, i) => (
              <tr key={i}>
                <td style={S.tableCell}>{a.date}</td>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.textPrimary }}>{a.name}</td>
                <td style={S.tableCell}>{a.source}</td>
                <td style={S.tableCell}>{a.dx}</td>
                <td style={S.tableCell}>{a.evaluator}</td>
                <td style={S.tableCell}>{a.pipeline}</td>
                <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: a.statusColor }}>{a.status}</span></td>
                <td style={S.tableCell}><span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>Review</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
