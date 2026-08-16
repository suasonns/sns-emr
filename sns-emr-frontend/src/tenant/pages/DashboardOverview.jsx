import React from 'react';
import { COLORS, S } from '../design';

const STATS = [
  { label: 'Active Patients', value: '247', tone: COLORS.teal },
  { label: 'Visit Completion', value: '96.4%', tone: COLORS.green },
  { label: 'Open Alerts', value: '14', tone: COLORS.orange },
  { label: 'Risk Flags', value: '03', tone: COLORS.red },
];

const CARE_BUNDLES = [
  ['Routine Visits', '92%', 'On schedule'],
  ['Continuous Care', '76%', 'Monitoring'],
  ['Clinical Documentation', '88%', 'Signed'],
  ['Billing & Claims', '81%', 'Review needed'],
];

export default function DashboardOverview() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Agency Dashboard</h1>
          <p style={S.pageSubtitle}>Operational overview across admissions, clinical care, scheduling, and billing.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>Run Daily Report</button>
      </div>

      <div style={S.statsRow}>
        {STATS.map((stat) => (
          <div key={stat.label} style={S.statCard}>
            <span style={S.statDot(stat.tone)} />
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: 0 }}>{stat.label}</p>
            <div style={S.statValue}>{stat.value}</div>
            <div style={S.statSub(COLORS.teal)}>Updated 10 min ago</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 24 }}>
        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Care delivery overview</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {CARE_BUNDLES.map(([name, pct, status]) => (
              <div key={name} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 0.8fr', gap: 12, alignItems: 'center', borderBottom: `1px solid ${COLORS.border}`, paddingBottom: 8 }}>
                <div style={{ color: COLORS.textPrimary, fontWeight: 600 }}>{name}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 110, height: 6, background: COLORS.border, borderRadius: 999 }}>
                    <div style={{ width: pct, height: '100%', background: COLORS.teal, borderRadius: 999 }} />
                  </div>
                  <span style={{ color: COLORS.muted, fontSize: 12 }}>{pct}</span>
                </div>
                <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.teal), display: 'inline-flex', width: 'fit-content' }}>{status}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Priority actions</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {[
              { label: 'Pending cosignatures', value: '6', tone: COLORS.red },
              { label: 'Scheduled visits today', value: '18', tone: COLORS.teal },
              { label: 'Claims needing review', value: '08', tone: COLORS.orange },
            ].map((item) => (
              <div key={item.label} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: COLORS.muted, fontSize: 12 }}>{item.label}</span>
                  <span style={{ fontSize: 18, fontWeight: 700, color: item.tone }}>{item.value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
