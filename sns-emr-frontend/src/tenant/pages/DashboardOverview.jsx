import React from 'react';
import { COLORS, S } from '../design';

function metricValue(metrics, key) {
  return metrics?.find((metric) => metric.key === key)?.value ?? 0;
}

const TONE_COLORS = { red: COLORS.red, orange: COLORS.orange, blue: COLORS.blue };

const PRIORITY_TIERS = [
  { key: 'priority_1', title: 'Priority 1 · Compliance & Signatures', icon: '\u{1F534}' },
  { key: 'priority_2', title: 'Priority 2 · Clinical Follow-up', icon: '\u{1F7E0}' },
  { key: 'priority_3', title: 'Priority 3 · Pipeline & Growth', icon: '\u{1F535}' },
];

function ComplianceWidgetCard({ widget }) {
  const tone = TONE_COLORS[widget.tone] || COLORS.muted;
  const unavailable = widget.data_available === false;
  return (
    <div
      title={unavailable ? widget.note : undefined}
      style={{
        background: COLORS.bg,
        border: `1px solid ${COLORS.border}`,
        borderLeft: `3px solid ${tone}`,
        borderRadius: 10,
        padding: '14px 16px',
        minWidth: 0,
      }}
    >
      <div style={{ color: COLORS.muted, fontSize: 12, fontWeight: 600, marginBottom: 8 }}>{widget.label}</div>
      {unavailable ? (
        <div style={{ fontSize: 13, color: COLORS.dim, fontStyle: 'italic' }}>Not yet tracked</div>
      ) : (
        <div style={{ fontSize: 26, fontWeight: 800, color: COLORS.white }}>{widget.value}</div>
      )}
      {widget.note && !unavailable && (
        <div style={{ fontSize: 11, color: COLORS.dim, marginTop: 4 }}>{widget.note}</div>
      )}
      {widget.action_label && !unavailable && (
        <button
          type="button"
          style={{
            marginTop: 10,
            fontSize: 12,
            fontWeight: 600,
            color: tone,
            background: 'transparent',
            border: `1px solid ${tone}`,
            borderRadius: 6,
            padding: '4px 10px',
            cursor: 'pointer',
          }}
        >
          {widget.action_label}
        </button>
      )}
      {Array.isArray(widget.breakdown) && widget.breakdown.some((b) => b.count > 0) && (
        <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {widget.breakdown.filter((b) => b.count > 0).map((b) => (
            <span key={b.status} style={{ ...S.badge('rgba(148,163,184,0.12)', COLORS.muted), fontSize: 10 }}>
              {b.status.replaceAll('_', ' ')}: {b.count}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DashboardOverview({ workspace, census, loading }) {
  const dashboard = workspace?.dashboard;
  const tenantDisplayName = workspace?.tenant_name || 'Love & Faith Hospice Services, Inc.';
  const metrics = dashboard?.metrics ?? [];
  const complianceQueue = dashboard?.compliance_queue ?? {};
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
  const visibleTiers = PRIORITY_TIERS.map((tier) => ({ ...tier, widgets: complianceQueue[tier.key] ?? [] }))
    .filter((tier) => tier.widgets.length > 0);

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

      {visibleTiers.length > 0 ? (
        visibleTiers.map((tier) => (
          <div key={tier.key} style={{ marginTop: 24 }}>
            <div style={S.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>
                  {tier.icon} {tier.title}
                </h3>
                <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.teal), fontSize: 11 }}>Live compliance</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                {tier.widgets.map((widget) => (
                  <ComplianceWidgetCard key={widget.key} widget={widget} />
                ))}
              </div>
            </div>
          </div>
        ))
      ) : (
        <div style={{ marginTop: 24 }}>
          <div style={S.card}>
            <div style={{ color: COLORS.muted, fontSize: 13 }}>
              No compliance widgets are visible for your current role.
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: 24 }}>
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
      </div>
    </div>
  );
}
