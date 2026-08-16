import React from 'react';
import { COLORS, S } from '../TenantDashboard';

const CLAIMS = [
  { id: 'CLM-88301', patient: 'Martha Stevens', date: 'Oct 24, 2025', amount: '$1,450.00', payer: 'Medicare', status: 'Submitted', statusColor: COLORS.blue, days: '1 Day' },
  { id: 'CLM-88300', patient: 'James Miller', date: 'Oct 22, 2025', amount: '$980.00', payer: 'Medicaid', status: 'Pending', statusColor: COLORS.yellow, days: '3 Days' },
  { id: 'CLM-88299', patient: 'Eleanor Vance', date: 'Oct 20, 2025', amount: '$2,100.00', payer: 'Medicare', status: 'Paid', statusColor: COLORS.green, days: '5 Days' },
  { id: 'CLM-88298', patient: 'Thomas Wright', date: 'Oct 18, 2025', amount: '$1,850.00', payer: 'Medicare', status: 'Denied', statusColor: COLORS.red, days: '7 Days' },
  { id: 'CLM-88297', patient: 'Lillian G.', date: 'Oct 15, 2025', amount: '$750.00', payer: 'Private Pay', status: 'Paid', statusColor: COLORS.green, days: '10 Days' },
  { id: 'CLM-88296', patient: 'Frank Sinatra', date: 'Oct 14, 2025', amount: '$3,200.00', payer: 'Medicare', status: 'Submitted', statusColor: COLORS.blue, days: '11 Days' },
  { id: 'CLM-88295', patient: 'Alice Cooper', date: 'Oct 12, 2025', amount: '$1,250.00', payer: 'Medicaid', status: 'Paid', statusColor: COLORS.green, days: '13 Days' },
  { id: 'CLM-88294', patient: 'David Bowie', date: 'Oct 10, 2025', amount: '$1,600.00', payer: 'Medicare', status: 'Pending', statusColor: COLORS.yellow, days: '15 Days' },
];

const AGING = [
  { label: 'Current', value: '$142,000', pct: '64%', width: '100%' },
  { label: '30-60 Days', value: '$48,000', pct: '22%', width: '34%' },
  { label: '60-90 Days', value: '$22,000', pct: '10%', width: '15%' },
  { label: '90+ Days', value: '$8,000', pct: '4%', width: '6%' },
];

const PAYMENTS = [
  { id: 'PMT-00481', patient: 'Eleanor Vance', date: 'Oct 23, 2025', amount: '$2,100.00', payer: 'Medicare', method: 'Electronic EFT' },
  { id: 'PMT-00480', patient: 'Lillian G.', date: 'Oct 21, 2025', amount: '$750.00', payer: 'Private Pay', method: 'Credit Card' },
  { id: 'PMT-00479', patient: 'Alice Cooper', date: 'Oct 20, 2025', amount: '$1,250.00', payer: 'Medicaid', method: 'Electronic EFT' },
  { id: 'PMT-00478', patient: 'Freddie Mercury', date: 'Oct 18, 2025', amount: '$1,100.00', payer: 'Medicare', method: 'Electronic EFT' },
  { id: 'PMT-00477', patient: 'Johnny Cash', date: 'Oct 17, 2025', amount: '$1,450.00', payer: 'Medicare', method: 'Electronic EFT' },
  { id: 'PMT-00476', patient: 'John Doe', date: 'Oct 15, 2025', amount: '$950.00', payer: 'Medicaid', method: 'Electronic EFT' },
];

export default function Billing() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>Billing Overview</h1>
          <p style={S.pageSubtitle}>Claims management, eligibility tracking, and revenue cycle analytics for Grace Hospice Care.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>+ Create Claim</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Claims Submitted', value: '142' },
          { label: 'Pending Claims', value: '23' },
          { label: 'Denied Claims', value: '8' },
          { label: 'Revenue This Month', value: '$287.4K' },
          { label: 'Clean Claim Rate', value: '91.8%' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.textPrimary, margin: '6px 0 0' }}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24, marginBottom: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>Claims Pipeline</h3>
            <span style={{ fontSize: 12, color: COLORS.muted }}>Updated today, 8:00 AM</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Claim ID', 'Patient', 'Svc Date', 'Amount', 'Payer', 'Status', 'Days in AR'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.dim }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CLAIMS.map((c, i) => (
                <tr key={i}>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.textPrimary }}>{c.id}</td>
                  <td style={{ ...S.tableCell, color: COLORS.textPrimary }}>{c.patient}</td>
                  <td style={S.tableCell}>{c.date}</td>
                  <td style={{ ...S.tableCell, color: COLORS.textPrimary }}>{c.amount}</td>
                  <td style={S.tableCell}>{c.payer}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: c.statusColor }}>{c.status}</span></td>
                  <td style={S.tableCell}>{c.days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <div style={S.card}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 16px' }}>Revenue by Payer</h3>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <div style={{ width: 100, height: 100, borderRadius: '50%', border: `8px solid ${COLORS.teal}`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' }}>
                <div>
                  <p style={{ fontSize: 16, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>72%</p>
                  <p style={{ fontSize: 9, color: COLORS.dim, margin: 0 }}>Medicare</p>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { label: 'Medicare (72%)', color: COLORS.teal },
                { label: 'Medicaid (18%)', color: COLORS.blue },
                { label: 'Private Pay (10%)', color: COLORS.purple },
              ].map((p, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: p.color }} />
                  <span style={{ fontSize: 12, color: COLORS.muted }}>{p.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={S.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>Aging Report</h3>
              <span style={{ fontSize: 11, color: COLORS.dim }}>Total: $220K</span>
            </div>
            {AGING.map((a, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>{a.label}</span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.textPrimary }}>{a.value}</span>
                    <span style={{ fontSize: 11, color: COLORS.dim }}>{a.pct}</span>
                  </div>
                </div>
                <div style={{ height: 6, background: COLORS.border, borderRadius: 3 }}>
                  <div style={{ width: a.width, height: '100%', background: COLORS.teal, borderRadius: 3 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>Recent Payment Activity</h3>
          <span style={{ fontSize: 12, color: '#14b8a6', cursor: 'pointer' }}>View All Payments</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Payment ID', 'Patient', 'Payment Date', 'Amount Received', 'Payer', 'Method'].map((h) => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.dim }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PAYMENTS.map((p, i) => (
              <tr key={i}>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.textPrimary }}>{p.id}</td>
                <td style={{ ...S.tableCell, color: COLORS.textPrimary }}>{p.patient}</td>
                <td style={S.tableCell}>{p.date}</td>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.green }}>{p.amount}</td>
                <td style={S.tableCell}>{p.payer}</td>
                <td style={{ ...S.tableCell, color: COLORS.dim }}>{p.method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
