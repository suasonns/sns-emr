import React, { useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import { fetchOwnerTenants, fetchOwnerAuditLogs } from '../../api/ownerAdmin';

const STATUS_COLOR = {
  ACTIVE: COLORS.green,
  INACTIVE: COLORS.muted,
  SUSPENDED: COLORS.red,
};

const CATEGORY_COLOR = {
  AUTH: COLORS.blue,
  DATA: COLORS.purple,
  ADMIN: COLORS.teal,
  BILLING: COLORS.orange,
  COMPLIANCE: COLORS.green,
};

function formatTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function humanizeAction(action) {
  if (!action) return '—';
  return action
    .toLowerCase()
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export default function DashboardOverview({ data = null, loading = false, error = '' }) {
  const [tenants, setTenants] = useState([]);
  const [activity, setActivity] = useState([]);
  const [subError, setSubError] = useState('');
  const [subLoading, setSubLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setSubLoading(true);
      setSubError('');
      try {
        const [tenantRes, activityRes] = await Promise.all([
          fetchOwnerTenants(),
          fetchOwnerAuditLogs({ limit: 8 }),
        ]);
        if (!mounted) return;
        setTenants(tenantRes.tenants || []);
        setActivity(activityRes.logs || []);
      } catch (err) {
        if (mounted) setSubError(err instanceof Error ? err.message : 'Failed to load dashboard detail');
      } finally {
        if (mounted) setSubLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const fmt = (value) => (typeof value === 'number' ? value.toLocaleString() : '0');

  const liveStats = [
    { label: 'Active Tenants', value: fmt(data?.total_tenants), sub: 'Registered agencies', dot: COLORS.green },
    { label: 'Active Tasks', value: fmt(data?.active_tasks), sub: 'Across all agencies', dot: COLORS.blue },
    { label: 'System Incidents', value: fmt(data?.system_incidents), sub: 'Reported incidents', dot: data?.system_incidents ? COLORS.orange : COLORS.green },
    { label: 'Clinical Notes', value: fmt(data?.clinical_notes), sub: 'Recorded to date', dot: COLORS.purple },
  ];

  const taskCounts = new Map(
    (data?.tenant_summary || []).map((t) => [t.tenant_id, t])
  );

  const tenantRows = tenants.map((t) => {
    const extra = taskCounts.get(t.tenant_id);
    return {
      tenant_id: t.tenant_id,
      name: t.display_name || t.legal_name || '—',
      status: t.status,
      tenant_type: t.tenant_type,
      patients: t.patient_count,
      users: t.user_count,
      open_tasks: extra?.open_tasks ?? '—',
      incidents: extra?.incidents ?? '—',
    };
  });

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Control Center</h1>
          <p style={S.pageSubtitle}>Real-time monitoring across all tenant agencies.</p>
        </div>
        <span style={{ fontSize: 13, color: COLORS.muted }}>
          {loading ? 'SYS_STATUS: LOADING' : error ? 'SYS_STATUS: UNAVAILABLE' : 'SYS_STATUS: ACTIVE'}
        </span>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginBottom: 16 }}>
          {error}
        </div>
      ) : null}
      {subError ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginBottom: 16 }}>
          {subError}
        </div>
      ) : null}

      {/* Top Stats Row */}
      <div style={S.statsRow}>
        {liveStats.map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={S.statLabel}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
            <span style={S.statSub(COLORS.muted)}>{s.sub}</span>
          </div>
        ))}
      </div>

      {/* Tenant Overview */}
      <div style={{ ...S.card, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Tenant Overview</h3>
          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal }}>{tenantRows.length} agencies</span>
        </div>
        {subLoading ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading tenants…</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Agency Name', 'Status', 'Type', 'Patients', 'Users', 'Open Tasks', 'Incidents'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tenantRows.map((t) => (
                <tr key={t.tenant_id}>
                  <td style={S.tableCellBold}>{t.name}</td>
                  <td style={{ ...S.tableCell, padding: '12px 0' }}>
                    <span style={S.badge((STATUS_COLOR[t.status] || COLORS.muted) + '22', STATUS_COLOR[t.status] || COLORS.muted)}>{t.status}</span>
                  </td>
                  <td style={S.tableCell}>{t.tenant_type}</td>
                  <td style={S.tableCell}>{t.patients}</td>
                  <td style={S.tableCell}>{t.users}</td>
                  <td style={S.tableCell}>{t.open_tasks}</td>
                  <td style={S.tableCell}>{t.incidents}</td>
                </tr>
              ))}
              {tenantRows.length === 0 && (
                <tr>
                  <td style={S.tableCell} colSpan={7}>No tenants yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Recent Activity */}
      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Recent Activity</h3>
          <span style={{ fontSize: 11, color: COLORS.muted }}>Live from audit log</span>
        </div>
        {subLoading ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading activity…</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Time', 'Tenant', 'User', 'Action', 'Category'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activity.map((a) => (
                <tr key={a.log_id}>
                  <td style={S.tableCell}>{formatTime(a.created_at)}</td>
                  <td style={S.tableCellBold}>{a.tenant_name}</td>
                  <td style={S.tableCell}>{a.user_display}</td>
                  <td style={{ ...S.tableCell, fontWeight: 500, color: COLORS.white }}>{humanizeAction(a.action)}</td>
                  <td style={{ ...S.tableCell, padding: '12px 0' }}>
                    <span style={S.badge((CATEGORY_COLOR[a.category] || COLORS.muted) + '22', CATEGORY_COLOR[a.category] || COLORS.muted)}>{a.category}</span>
                  </td>
                </tr>
              ))}
              {activity.length === 0 && (
                <tr>
                  <td style={S.tableCell} colSpan={5}>No recent activity.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
