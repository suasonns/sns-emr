import React from 'react';
import { COLORS, S } from '../design';

const MRR_DATA = [
  { month: 'Jun', value: '$128.4K', height: 100 },
  { month: 'Jul', value: '$131.2K', height: 112 },
  { month: 'Aug', value: '$134.5K', height: 124 },
  { month: 'Sep', value: '$139K', height: 140 },
  { month: 'Oct', value: '$143.2K', height: 156 },
  { month: 'Nov', value: '$147.2K', height: 172 },
];

const DENIAL_REASONS = [
  { reason: 'Missing F2F', cases: '34 cases (27.9%)', width: '100%', color: COLORS.teal },
  { reason: 'Expired POC', cases: '28 cases (23%)', width: '82%', color: COLORS.teal },
  { reason: 'Eligibility', cases: '22 cases (18%)', width: '65%', color: COLORS.purple },
  { reason: 'Missing NOE', cases: '14 cases (11.5%)', width: '41%', color: COLORS.purple },
  { reason: 'Other Reasons', cases: '24 cases (19.7%)', width: '71%', color: COLORS.dim },
];

const ADOPTION = [
  { feature: 'ICA Assessments', pct: '94%', width: '94%' },
  { feature: 'Billing Readiness', pct: '87%', width: '87%' },
  { feature: 'Scheduling', pct: '82%', width: '82%' },
  { feature: 'Analytics Hub', pct: '71%', width: '71%' },
  { feature: 'Secure Inbox', pct: '63%', width: '63%' },
  { feature: 'AI Assistant', pct: '45%', width: '45%' },
];

const USAGE = [
  { label: 'Daily Active Users (DAU)', value: '198 leads' },
  { label: 'Weekly Active Users (WAU)', value: '287 leads' },
  { label: 'Monthly Active Users (MAU)', value: '342 users' },
  { label: 'Platform Active Tenancies', value: '24 Hospice Domains' },
  { label: 'Avg Sessions per User', value: '4.2 sessions / day' },
  { label: 'Avg Session Duration', value: '18.5 minutes' },
];

export default function Analytics() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Analytics</h1>
          <p style={S.pageSubtitle}>Deep statistical overviews of platform revenue, active patient load, and system metrics</p>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {['7D', '30D', '90D', 'YTD'].map((t, i) => (
            <button key={t} style={{
              padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 700,
              background: i === 1 ? COLORS.teal : COLORS.card,
              color: i === 1 ? COLORS.white : COLORS.muted,
            }}>{t}</button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'TOTAL PLATFORM MRR', change: '+4.2%', changeColor: COLORS.teal, value: '$147,200', desc: 'Current Monthly Recurring Revenue', dot: COLORS.green },
          { label: 'ACTIVE HOSPICE PATIENTS', change: '+8.1%', changeColor: COLORS.teal, value: '1,847', desc: 'Registered active census load', dot: COLORS.green },
          { label: 'DAILY ACTIVE USERS', change: '-2.4%', changeColor: COLORS.red, value: '198', desc: 'Active super-admins & clinic leads', dot: COLORS.green },
          { label: 'CLEAN CLAIM RATE', change: '+1.2%', changeColor: COLORS.teal, value: '92.1%', desc: 'Average first-submission validation rate', dot: COLORS.green },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <p style={{ fontSize: 10, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
              <span style={{ fontSize: 11, fontWeight: 700, color: s.changeColor }}>{s.change}</span>
            </div>
            <p style={S.statValue}>{s.value}</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Revenue Trend + Denial Rate */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Revenue Trend Chart */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>REVENUE TREND (MRR OVERVIEW)</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 24px' }}>6-month incremental development scale ($ Thousands)</p>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: 180, padding: '0 8px' }}>
            {MRR_DATA.map((d, i) => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 11, color: COLORS.muted }}>{d.value}</span>
                <div style={{ width: 36, height: d.height, background: COLORS.teal, borderRadius: 4 }} />
                <span style={{ fontSize: 12, color: COLORS.muted }}>{d.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Denial Rate */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>DENIAL RATE BY REASON</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 24px' }}>Claim rejections grouped by critical clinical validation gaps</p>
          {DENIAL_REASONS.map((d, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 13, color: COLORS.muted }}>{d.reason}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{d.cases}</span>
              </div>
              <div style={{ height: 8, background: COLORS.border, borderRadius: 4 }}>
                <div style={{ width: d.width, height: '100%', background: d.color, borderRadius: 4 }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Adoption + Usage Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Feature Adoption */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>FEATURE ADOPTION LEVEL</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>Platform features usage percentage by clinical users</p>
          {ADOPTION.map((a, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
              <span style={{ fontSize: 13, color: COLORS.muted, minWidth: 130 }}>{a.feature}</span>
              <div style={{ flex: 1, height: 8, background: COLORS.border, borderRadius: 4 }}>
                <div style={{ width: a.width, height: '100%', background: COLORS.teal, borderRadius: 4 }} />
              </div>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white, minWidth: 36, textAlign: 'right' }}>{a.pct}</span>
            </div>
          ))}
        </div>

        {/* Platform Usage */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>PLATFORM USAGE METRICS</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>DAU/MAU dynamics and session durations</p>
          {USAGE.map((u, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: i < USAGE.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <span style={{ fontSize: 13, color: COLORS.muted }}>{u.label}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{u.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
