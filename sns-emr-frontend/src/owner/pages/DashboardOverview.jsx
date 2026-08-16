import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

const TENANTS = [
  { name: 'Grace Hospice Care', plan: 'Pro', status: 'Active', statusColor: COLORS.green, patients: 312, users: 48, lastActive: '3m ago', health: 98, barColor: COLORS.green },
  { name: 'Sunrise Home Health', plan: 'Enterprise', status: 'Active', statusColor: COLORS.green, patients: 567, users: 92, lastActive: 'Just Now', health: 94, barColor: COLORS.green },
  { name: 'Comfort Care Services', plan: 'Starter', status: 'Trial', statusColor: COLORS.orange, patients: 45, users: 8, lastActive: '1h ago', health: 85, barColor: COLORS.orange },
  { name: 'Valley Palliative Care', plan: 'Pro', status: 'Active', statusColor: COLORS.green, patients: 189, users: 34, lastActive: '12m ago', health: 91, barColor: COLORS.green },
  { name: 'Serenity Hospice Group', plan: 'Enterprise', status: 'Suspended', statusColor: '#ef4444', patients: 240, users: 0, lastActive: '4d ago', health: 12, barColor: COLORS.red },
  { name: 'Apex Nursing Agency', plan: 'Starter', status: 'Active', statusColor: COLORS.green, patients: 88, users: 14, lastActive: '34m ago', health: 72, barColor: COLORS.orange },
];

const ACTIVITY = [
  { time: '09:22:15', tenant: 'Grace Hospice Care', user: 'sarah.j@gracehospice.com', action: 'New tenant onboarded', detail: 'SaaS trial started under Starter Tier.', status: 'SUCCESS', statusColor: COLORS.green },
  { time: '09:21:40', tenant: 'Sunrise Home Health', user: 'admin@sunrisehh.com', action: 'User role changed', detail: 'Elevated nurse.chief to clinical-manager.', status: 'MODIFIED', statusColor: COLORS.blue },
  { time: '09:18:02', tenant: 'Comfort Care Services', user: 'billing@comfortcare.org', action: 'Subscription upgraded', detail: 'Starter Tier moved to Premium monthly billing plan.', status: 'UPGRADED', statusColor: COLORS.teal },
  { time: '09:15:00', tenant: 'SYSTEM_DAEMON', user: 'cron-scheduler', action: 'System backup completed', detail: 'S3 multi-region cold snapshot completed.', status: 'COMPLETED', statusColor: COLORS.green },
  { time: '09:12:11', tenant: 'Valley Palliative Care', user: 'integrator-api-key', action: 'API rate limit triggered', detail: 'Exceeded tier allotment of 500req/sec.', status: 'WARNING', statusColor: COLORS.orange },
  { time: '09:05:45', tenant: 'Serenity Hospice Group', user: 'compliance-officer', action: 'Tenant data export requested', detail: 'Exporting clinical records for Audit ID 92144.', status: 'PENDING', statusColor: COLORS.purple },
];

const PERF = [
  { label: 'API Latency', value: '142ms', barWidth: '28%', color: COLORS.teal },
  { label: 'Database Load', value: '23%', barWidth: '23%', color: COLORS.blue },
  { label: 'Memory Usage', value: '67%', barWidth: '67%', color: COLORS.orange },
  { label: 'Storage Used', value: '2.1TB / 5TB', barWidth: '42%', color: COLORS.blue },
];

export default function DashboardOverview({ data = null, loading = false, error = '' }) {
  const fmt = (value, fallback) =>
    typeof value === 'number' ? value.toLocaleString() : fallback;

  // Real counts once /dashboard/owner returns them; placeholders until then.
  const liveStats = [
    { label: 'Active Tenants', value: fmt(data?.total_tenants, '24'), sub: '▲ 2 this month', subColor: COLORS.teal, dot: COLORS.green },
    { label: 'Active Tasks', value: fmt(data?.active_tasks, '3,847'), sub: 'Across all agencies', subColor: COLORS.blue, dot: COLORS.green },
    { label: 'System Incidents', value: fmt(data?.system_incidents, '0'), sub: 'Reported incidents', subColor: COLORS.green, dot: COLORS.green },
    { label: 'Clinical Notes', value: fmt(data?.clinical_notes, '186'), sub: 'Recorded to date', subColor: COLORS.purple, dot: COLORS.green },
  ];

  const tenantRows =
    Array.isArray(data?.tenant_summary) && data.tenant_summary.length > 0
      ? data.tenant_summary.map((t) => ({
          name: t.name ?? t.legal_name ?? t.display_name ?? '—',
          plan: t.plan ?? '—',
          status: t.status ?? '—',
          statusColor: t.status === 'ACTIVE' ? COLORS.green : COLORS.orange,
          patients: t.patients ?? '—',
          users: t.users ?? '—',
          lastActive: t.last_active ?? '—',
          health: typeof t.health === 'number' ? t.health : 0,
          barColor: COLORS.green,
        }))
      : TENANTS;

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Control Center</h1>
          <p style={S.pageSubtitle}>Real-time monitoring and multi-tenant performance orchestration.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>
            {loading ? 'SYS_STATUS: LOADING' : error ? 'SYS_STATUS: UNAVAILABLE' : 'SYS_STATUS: ACTIVE'}
          </span>
          <button style={S.btn(COLORS.teal)}>RE-SYNC OK</button>
        </div>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13 }}>
          {error}
        </div>
      ) : null}

      {/* Top Stats Row 1 */}
      <div style={S.statsRow}>
        {liveStats.map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={S.statLabel}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
            <span style={S.statSub(s.subColor)}>{s.sub}</span>
          </div>
        ))}
      </div>

      {/* Top Stats Row 2 */}
      <div style={S.statsRow}>
        {[
          { label: 'Monthly Recurring Revenue', value: '$48.2K', sub: 'MRR Growth', subColor: COLORS.blue, dot: COLORS.green },
          { label: 'Annual Recurring Revenue', value: '$578.4K', sub: 'ARR Projected', subColor: COLORS.teal, dot: COLORS.green },
          { label: 'Avg Response Time', value: '142ms', sub: 'Edge network', subColor: COLORS.green, dot: COLORS.green },
          { label: 'Support Tickets Open', value: '7', sub: 'Requires attention', subColor: COLORS.orange, dot: COLORS.orange },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={S.statLabel}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
            <span style={S.statSub(s.subColor)}>{s.sub}</span>
          </div>
        ))}
      </div>

      {/* Tenant Health + System Performance */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Tenant Health */}
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Tenant Health Overview</h3>
            <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>Manage Tenants →</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Agency Name', 'Plan', 'Status', 'Patients', 'Users', 'Last Active', 'Health Score'].map(h => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tenantRows.map((t, i) => (
                <tr key={i}>
                  <td style={S.tableCellBold}>{t.name}</td>
                  <td style={S.tableCell}>{t.plan}</td>
                  <td style={{ ...S.tableCell, padding: '12px 0' }}>
                    <span style={S.badge(t.statusColor + '22', t.statusColor)}>{t.status}</span>
                  </td>
                  <td style={S.tableCell}>{t.patients}</td>
                  <td style={S.tableCell}>{t.users}</td>
                  <td style={S.tableCell}>{t.lastActive}</td>
                  <td style={{ ...S.tableCell, padding: '12px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 6, background: COLORS.border, borderRadius: 3 }}>
                        <div style={{ width: `${t.health}%`, height: '100%', background: t.barColor, borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: 11, fontWeight: 600, color: COLORS.white, minWidth: 30 }}>{t.health}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* System Performance */}
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>System Performance</h3>
            <span style={{ fontSize: 14, color: COLORS.red, cursor: 'pointer' }}>🔴</span>
          </div>
          {PERF.map((p, i) => (
            <div key={i} style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted }}>{p.label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{p.value}</span>
              </div>
              <div style={{ height: 6, background: COLORS.border, borderRadius: 3 }}>
                <div style={{ width: p.barWidth, height: '100%', background: p.color, borderRadius: 3 }} />
              </div>
            </div>
          ))}

          {/* Terminal */}
          <div style={{ background: COLORS.bg, borderRadius: 8, padding: 16, marginTop: 16 }}>
            <p style={{ fontSize: 10, color: COLORS.teal, margin: '0 0 6px', fontFamily: 'monospace' }}>$ console.monitor --live</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 4px', fontFamily: 'monospace' }}>[09:21:44] Database backups verified.</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0, fontFamily: 'monospace' }}>[09:22:10] Cluster-US-East scales ok.</p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Recent activity</h3>
            <span style={{ fontSize: 11, color: COLORS.muted }}>LIVE TELEMETRY</span>
          </div>
          <span style={{ fontSize: 13, color: COLORS.muted, cursor: 'pointer' }}>Export Platform Log</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Time', 'Tenant', 'User', 'Action', 'Detail', 'Status'].map(h => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ACTIVITY.map((a, i) => (
              <tr key={i}>
                <td style={S.tableCell}>{a.time}</td>
                <td style={S.tableCellBold}>{a.tenant}</td>
                <td style={S.tableCell}>{a.user}</td>
                <td style={{ ...S.tableCell, fontWeight: 500, color: COLORS.white }}>{a.action}</td>
                <td style={{ ...S.tableCell, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.detail}</td>
                <td style={{ ...S.tableCell, padding: '12px 0' }}>
                  <span style={S.badge(a.statusColor + '22', a.statusColor)}>{a.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
