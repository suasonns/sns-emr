import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

export default function DashboardOverview() {
  const stats = [
    { label: 'Tenants', value: '18', tone: COLORS.teal },
    { label: 'Active Users', value: '342', tone: COLORS.blue },
    { label: 'Open Tasks', value: '27', tone: COLORS.orange },
    { label: 'System Uptime', value: '99.98%', tone: COLORS.green },
  ];

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Dashboard</h1>
          <p style={S.pageSubtitle}>Operational snapshot across tenants, users, billing, and system health.</p>
        </div>
        <button type="button" style={S.btn(COLORS.teal)}>New Report</button>
      </div>

      <div style={S.statsRow}>
        {stats.map((stat) => (
          <div key={stat.label} style={S.statCard}>
            <span style={S.statDot(stat.tone)} />
            <p style={S.statLabel}>{stat.label}</p>
            <div style={S.statValue}>{stat.value}</div>
            <div style={S.statSub(COLORS.teal)}>Updated 5m ago</div>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3 style={S.cardTitle}>Top tenant health</h3>
          <span style={{ fontSize: 12, color: COLORS.muted }}>Last 24 hours</span>
        </div>

        <div style={{ display: 'grid', gap: 12 }}>
          {[
            ['Sunrise Hospice', 'Healthy', '93%'],
            ['North Valley Care', 'Needs attention', '81%'],
            ['Evergreen Health', 'Healthy', '96%'],
            ['Summit Hospice', 'Review', '72%'],
          ].map(([name, status, pct], index) => (
            <div
              key={name}
              style={{
                display: 'grid',
                gridTemplateColumns: '1.7fr 1fr 0.8fr',
                gap: 12,
                alignItems: 'center',
                padding: '10px 0',
                borderBottom: index < 3 ? `1px solid ${COLORS.border}` : 'none',
              }}
            >
              <div style={{ color: COLORS.white, fontWeight: 600 }}>{name}</div>
              <span style={{ ...S.badge(status === 'Healthy' ? 'rgba(34,197,94,0.12)' : 'rgba(249,115,22,0.12)', status === 'Healthy' ? COLORS.green : COLORS.orange), display: 'inline-flex', width: 'fit-content' }}>{status}</span>
              <div style={{ color: COLORS.muted, textAlign: 'right', fontWeight: 600 }}>{pct}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
