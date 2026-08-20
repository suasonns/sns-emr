import React from 'react';
import { COLORS, S } from '../design';

function metricValue(metrics, key) {
  return metrics?.find((metric) => metric.key === key)?.value ?? 0;
}

export default function DashboardOverview({ workspace, census, loading }) {
  const dashboard = workspace?.dashboard;
  const tenantDisplayName = workspace?.tenant_name || 'Love & Faith Hospice Services, Inc.';
  const metrics = dashboard?.metrics ?? [];
  const stats = [
    { label: 'Active Patients', value: census?.patient_count ?? 0, tone: COLORS.teal },
    { label: 'Open Tasks', value: metricValue(metrics, 'open_tasks'), tone: COLORS.orange },
    { label: 'Pending Incidents', value: metricValue(metrics, 'pending_incidents'), tone: COLORS.red },
    { label: 'IDG Blocked Patients', value: metricValue(metrics, 'idg_blocked_patients'), tone: COLORS.purple },
  ];
  const careBundles = [
    ['Clinical notes requiring review', metricValue(metrics, 'flagged_notes'), 'Flagged'],
    ['Open regulatory tasks', metricValue(metrics, 'open_tasks'), 'Open'],
    ['Pending incidents', metricValue(metrics, 'pending_incidents'), 'Pending'],
    ['IDG readiness blockers', metricValue(metrics, 'idg_blocked_patients'), 'Blocked'],
  ];
  const priorityActions = [
    ...(dashboard?.open_tasks ?? []).slice(0, 4).map((task) => ({
      label: String(task.task_type || 'Task').replaceAll('_', ' '),
      value: task.status || 'OPEN',
      tone: COLORS.orange,
    })),
    ...(dashboard?.pending_incidents ?? []).slice(0, 3).map((incident) => ({
      label: String(incident.incident_type || 'Incident').replaceAll('_', ' '),
      value: incident.incident_severity || 'PENDING',
      tone: COLORS.red,
    })),
  ].slice(0, 5);

  const qiesTracker = [
    { label: 'HOPE Transmission', daysLeft: 9, status: 'On track', tone: '#34d399', deadline: 'Deadline: 07/26' },
    { label: 'QIES Reporting', daysLeft: 13, status: 'Needs review', tone: '#60a5fa', deadline: 'Deadline: 07/30' },
  ];

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>{tenantDisplayName}</h1>
          <p style={S.pageSubtitle}>Operational overview across admissions, clinical care, scheduling, and billing.</p>
        </div>
        <div style={{ color: COLORS.dim, fontSize: 12 }}>{loading ? 'Loading tenant data...' : 'Live tenant data'}</div>
      </div>

      <div style={S.statsRow}>
        {stats.map((stat) => (
          <div key={stat.label} style={S.statCard}>
            <span style={S.statDot(stat.tone)} />
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: 0 }}>{stat.label}</p>
            <div style={S.statValue}>{stat.value}</div>
            <div style={S.statSub(COLORS.teal)}>Updated 10 min ago</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>HOPE / QIES submission tracker</h3>
            <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.teal), fontSize: 11 }}>Live compliance</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
            {qiesTracker.map((item) => (
              <div key={item.label} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ color: COLORS.muted, fontSize: 12, fontWeight: 600 }}>{item.label}</span>
                  <span style={{ fontSize: 11, color: item.tone, fontWeight: 700 }}>{item.status}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 28, fontWeight: 800, color: COLORS.white }}>{item.daysLeft}</span>
                  <span style={{ color: COLORS.muted, fontSize: 12 }}>days left</span>
                </div>

                <div style={{ color: COLORS.dim, fontSize: 12, marginBottom: 12 }}>{item.deadline}</div>

                <div style={{ height: 8, borderRadius: 999, background: 'rgba(148,163,184,0.18)', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.max(18, Math.min(100, (item.daysLeft / 15) * 100))}%`, height: '100%', borderRadius: 999, background: item.tone }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 24, marginTop: 24 }}>
        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Care delivery overview</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {careBundles.map(([name, count, status]) => (
              <div key={name} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 0.8fr', gap: 12, alignItems: 'center', borderBottom: `1px solid ${COLORS.border}`, paddingBottom: 8 }}>
                <div style={{ color: COLORS.textPrimary, fontWeight: 600 }}>{name}</div>
                <strong style={{ color: COLORS.white }}>{count}</strong>
                <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.teal), display: 'inline-flex', width: 'fit-content' }}>{status}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Priority actions</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {priorityActions.length ? priorityActions.map((item) => (
              <div key={item.label} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: COLORS.muted, fontSize: 12 }}>{item.label}</span>
                  <span style={{ fontSize: 18, fontWeight: 700, color: item.tone }}>{item.value}</span>
                </div>
              </div>
            )) : <div style={{ color: COLORS.muted, fontSize: 13 }}>No open tasks or pending incidents.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
