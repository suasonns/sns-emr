import React from 'react';
import { COLORS } from '../../TenantDashboard';

/**
 * AnalyticsFinancial — Financial reports & cost reporting tab.
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │  BILLING ACCESS LOGIC — READ CAREFULLY BEFORE MODIFYING            │
 * │                                                                     │
 * │  This component receives a `billingType` prop from Analytics.jsx    │
 * │  which comes from the tenant's database configuration:              │
 * │                                                                     │
 * │  billingType="in_house"                                             │
 * │    ✅ Full billing reports: NOE/NOTR, Revenue Summary, Credit       │
 * │       Balance Audit, Billing Exception Log, Claims Aging,           │
 * │       Denial Analysis, Payer Mix Analysis                           │
 * │    ✅ Cost Reports (Worksheet S-1 Part II & III)                    │
 * │    ✅ Tenant ALSO has access to the full Billing Dashboard          │
 * │       (the separate billing module at src/billing/) because         │
 * │       SNS handles their billing in-house.                           │
 * │                                                                     │
 * │  billingType="external"                                             │
 * │    ✅ Billing Tracker: read-only status view showing claims         │
 * │       status from the external biller (view-only, no actions)       │
 * │    ✅ NOE/NOTR Tracking (agency still manages election notices)     │
 * │    ✅ Cost Reports (still needed for annual filing)                 │
 * │    ❌ NO claims management, denial analysis, payer mix,             │
 * │       credit balance tools, or billing exception log                │
 * │    ❌ NO access to the full Billing Dashboard module                │
 * │                                                                     │
 * │  DEFAULT: 'external' (least privilege). If billing_type is          │
 * │  missing from the tenant record, show limited view and prompt       │
 * │  admin to configure in Agency Settings → Billing → Billing Type.   │
 * │                                                                     │
 * │  The billingType value is set per-tenant in:                        │
 * │    - Database: tenants.billing_type ('in_house' | 'external')       │
 * │    - UI: Agency Settings → Billing tab → Billing Type dropdown      │
 * │    - API: PATCH /api/tenants/:id { billing_type: 'in_house' }       │
 * └─────────────────────────────────────────────────────────────────────┘
 */

const fullBillingReports = [
  { title: '835 Remittance Review', frequency: 'Daily', lastRun: 'Last Run: Today, 8:00 AM', desc: 'Electronic remittance advice (835) payments, adjustments, and posting variances across Medicare, Medicaid, and commercial payers.' },
  { title: 'NOE / NOTR Tracking', frequency: 'Daily', lastRun: 'Last Run: Today, 8:00 AM', desc: 'Notice of Election and Notice of Termination/Revocation submission timelines and CMS compliance.' },
  { title: 'Revenue Summary', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Monthly collections, adjustments, write-offs, and net revenue across all payers.' },
  { title: 'Credit Balance Audit', frequency: 'Weekly', lastRun: 'Last Run: Aug 14, 2026', desc: 'Patient accounts with credit balances requiring refund processing or reallocation.' },
  { title: 'Billing Exception Log', frequency: 'Daily', lastRun: 'Last Run: Yesterday', desc: 'Claims with missing documentation, unsigned orders, or incomplete F2F encounters.' },
  { title: 'Claims Aging Report', frequency: 'Weekly', lastRun: 'Last Run: Aug 14, 2026', desc: 'Outstanding claims by aging bucket — 0-30, 31-60, 61-90, and 90+ days with payer breakdown.' },
  { title: 'Denial Analysis', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Denial rates, core rejection reasons, and appeal outcomes by payer with trend tracking.' },
  { title: 'Payer Mix Analysis', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Revenue contribution breakdown — Medicare, Medicaid, Private Insurance, and other payers.' },
];

const externalBillerTracking = [
  { claimId: 'CLM-20260815-001', patient: 'Martha Stevens', payer: 'Medicare', amount: '$6,119.70', submitted: 'Aug 15, 2026', status: 'Submitted', daysOut: 2 },
  { claimId: 'CLM-20260812-003', patient: 'Arthur Pendelton', payer: 'Medicare', amount: '$6,119.70', submitted: 'Aug 12, 2026', daysOut: 5, status: 'In Review' },
  { claimId: 'CLM-20260810-002', patient: 'James Miller', payer: 'Medicaid', amount: '$5,890.20', submitted: 'Aug 10, 2026', daysOut: 7, status: 'Pending Payment' },
  { claimId: 'CLM-20260801-005', patient: 'Eleanor Vance', payer: 'Medicare', amount: '$6,119.70', submitted: 'Aug 01, 2026', daysOut: 16, status: 'Paid' },
  { claimId: 'CLM-20260728-004', patient: 'Thomas H. Wright', payer: 'BCBS', amount: '$5,450.00', submitted: 'Jul 28, 2026', daysOut: 20, status: 'Denied' },
  { claimId: 'CLM-20260725-001', patient: 'Dorothy Chen', payer: 'Medicare', amount: '$6,119.70', submitted: 'Jul 25, 2026', daysOut: 23, status: 'Paid' },
];

const freqColor = (f) => {
  switch (f) { case 'Daily': return COLORS.primary; case 'Weekly': return '#6366f1'; case 'Monthly': return COLORS.warning; default: return COLORS.textDim; }
};

const claimStatusColor = (s) => {
  switch (s) { case 'Submitted': return COLORS.primary; case 'In Review': return COLORS.warning; case 'Pending Payment': return '#8b5cf6'; case 'Paid': return COLORS.success; case 'Denied': return COLORS.danger; default: return COLORS.textDim; }
};

export default function AnalyticsFinancial({ billingType = 'external' }) {
  const isInHouse = billingType === 'in_house';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{
        background: isInHouse ? `${COLORS.primary}12` : `${COLORS.warning}12`,
        border: `1px solid ${isInHouse ? COLORS.primary + '44' : COLORS.warning + '44'}`,
        borderRadius: 12, padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: isInHouse ? COLORS.primary : COLORS.warning, fontFamily: 'Inter, sans-serif' }}>
            {isInHouse ? 'In-House Billing — Full Access' : 'External Biller — Billing Tracker View'}
          </div>
          <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 2, fontFamily: 'Inter, sans-serif' }}>
            {isInHouse
              ? 'Your agency manages billing through SNS. Full billing reports and Billing Dashboard access enabled.'
              : 'Your agency uses an outside biller. Showing read-only claims tracker and cost reports only.'
            }
          </div>
        </div>
        <span style={{ padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, background: isInHouse ? COLORS.primary : COLORS.warning, color: '#fff', fontFamily: 'Inter, sans-serif' }}>
          {isInHouse ? 'In-House' : 'External'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {isInHouse ? (
          <>
            {[
              { label: 'Total Revenue (Aug)', value: '$184,320', sub: '+8.2% vs Jul' },
              { label: 'Outstanding Claims', value: '$42,890', sub: '12 claims pending' },
              { label: 'Denial Rate', value: '3.2%', sub: 'National avg: 5.1%' },
              { label: 'Credit Balances', value: '$2,140', sub: '3 accounts' },
            ].map((s, i) => (
              <div key={i} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '16px 20px' }}>
                <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{s.label}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{s.value}</div>
                <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 2, fontFamily: 'Inter, sans-serif' }}>{s.sub}</div>
              </div>
            ))}
          </>
        ) : (
          <>
            {[
              { label: 'Claims Submitted', value: '18', sub: 'This month' },
              { label: 'Awaiting Payment', value: '6', sub: '$34,560 total' },
              { label: 'Paid This Month', value: '10', sub: '$61,197 collected' },
              { label: 'Denied', value: '2', sub: 'Escalated to biller' },
            ].map((s, i) => (
              <div key={i} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '16px 20px' }}>
                <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{s.label}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{s.value}</div>
                <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 2, fontFamily: 'Inter, sans-serif' }}>{s.sub}</div>
              </div>
            ))}
          </>
        )}
      </div>

      {isInHouse && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
          {fullBillingReports.map((r, i) => (
            <div key={i} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif', flex: 1 }}>{r.title}</div>
                <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, flexShrink: 0, background: `${freqColor(r.frequency)}18`, color: freqColor(r.frequency), fontFamily: 'Inter, sans-serif' }}>{r.frequency}</span>
              </div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 8, fontFamily: 'Inter, sans-serif' }}>{r.lastRun}</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.5, marginBottom: 16, fontFamily: 'Inter, sans-serif' }}>{r.desc}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate Now</button>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Download PDF</button>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Export CSV</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!isInHouse && (
        <>
          <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>NOE / NOTR Tracking</div>
              <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.primary}18`, color: COLORS.primary, fontFamily: 'Inter, sans-serif' }}>Daily</span>
            </div>
            <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.5, marginBottom: 16, fontFamily: 'Inter, sans-serif' }}>Notice of Election and Notice of Termination/Revocation submission timelines and CMS compliance. Your agency manages NOE/NOTR regardless of billing arrangement.</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate Now</button>
              <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Download PDF</button>
            </div>
          </div>

          <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Billing Tracker</span>
                <span style={{ fontSize: 11, color: COLORS.warning, marginLeft: 10, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>Read-Only — Managed by External Biller</span>
              </div>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  {['Claim ID', 'Patient', 'Payer', 'Amount', 'Submitted', 'Days Out', 'Status'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {externalBillerTracking.map((c, i) => (
                  <tr key={i} style={{ borderBottom: i < externalBillerTracking.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                    <td style={{ padding: '12px 16px', fontSize: 12, fontWeight: 600, color: COLORS.primary, fontFamily: 'monospace' }}>{c.claimId}</td>
                    <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 500, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{c.patient}</td>
                    <td style={{ padding: '12px 16px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{c.payer}</td>
                    <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{c.amount}</td>
                    <td style={{ padding: '12px 16px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{c.submitted}</td>
                    <td style={{ padding: '12px 16px', fontSize: 12, fontWeight: 600, color: c.daysOut > 14 ? COLORS.warning : COLORS.text, fontFamily: 'Inter, sans-serif' }}>{c.daysOut}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${claimStatusColor(c.status)}18`, color: claimStatusColor(c.status), fontFamily: 'Inter, sans-serif' }}>{c.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, marginBottom: 12, fontFamily: 'Inter, sans-serif' }}>Cost Reports</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
          {[
            { title: 'Cost Report — Worksheet S-1 (Part II)', desc: 'Medicare cost report worksheet for provider statistical and reimbursement data. Required for annual cost report filing with your Medicare Administrative Contractor (MAC).', lastFiled: 'Last Filed: Dec 2025' },
            { title: 'Cost Report — Worksheet S-1 (Part III)', desc: 'Supplemental worksheet covering hospice-specific statistical data including patient days by level of care, unduplicated census count, and total charges. Required for annual filing.', lastFiled: 'Last Filed: Dec 2025' },
          ].map((cr, i) => (
            <div key={i} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.text, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>{cr.title}</div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 10, fontFamily: 'Inter, sans-serif' }}>{cr.lastFiled}</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, marginBottom: 20, fontFamily: 'Inter, sans-serif' }}>{cr.desc}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={{ padding: '8px 18px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate</button>
                <button style={{ padding: '8px 18px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Download PDF</button>
                <button style={{ padding: '8px 18px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Export CSV</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
