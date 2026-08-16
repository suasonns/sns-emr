import React from 'react';
import { COLORS, S } from '../design';

const SERVICES = [
  { name: 'API Gateway', dot: COLORS.green, latency: '14ms', uptime: '99.99%' },
  { name: 'Auth Service', dot: COLORS.green, latency: '28ms', uptime: '100.0%' },
  { name: 'Claims Engine', dot: COLORS.green, latency: '112ms', uptime: '99.95%' },
  { name: 'Billing Service', dot: COLORS.green, latency: '84ms', uptime: '99.92%' },
  { name: 'Notification Service', dot: COLORS.green, latency: '42ms', uptime: '100.0%' },
  { name: 'AI Analytics Model', dot: COLORS.purple, latency: '340ms', uptime: '99.88%' },
  { name: 'File Storage S3', dot: COLORS.green, latency: '18ms', uptime: '100.0%' },
  { name: 'PDF Generator', dot: COLORS.green, latency: '195ms', uptime: '99.74%' },
];

const ALERTS = [
  { time: '09:12:11', source: 'Valley Palliative Care', action: 'API Rate Limit Triggered', detail: 'Exceeded tier allotment of 500req/sec. Escalating limit protocol.', severity: 'Warning', sevColor: COLORS.orange },
  { time: '08:34:02', source: 'Serenity Hospice Group', action: 'F2F Sync Mismatch', detail: 'CDPH validation pipeline skipped 2 unsigned medical face-to-face documents.', severity: 'Warning', sevColor: COLORS.orange },
  { time: '05:00:14', source: 'Billing Daemon', action: 'Reconciliation Error', detail: 'RA integration parser flagged 1 claim with mismatch pricing index.', severity: 'Critical', sevColor: COLORS.red },
];

export default function SystemHealth() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>System Health</h1>
          <p style={S.pageSubtitle}>Orchestrate server statuses, pipeline performance, and API SLAs in real time</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.green, display: 'inline-block' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.green }}>All Systems Operational</span>
        </div>
      </div>

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'PLATFORM UPTIME', value: '99.97%', sub: 'Healthy SLA', subColor: COLORS.green, desc: 'Meets SLA limits', dot: COLORS.green },
          { label: 'AVG RESPONSE TIME', value: '142ms', sub: 'Fast', subColor: COLORS.green, desc: 'Edge delivery metrics', dot: COLORS.green },
          { label: 'API CALLS (24H)', value: '847K', sub: 'Normal', subColor: COLORS.green, desc: 'SaaS volume bandwidth', dot: COLORS.green },
          { label: 'ERROR RATE', value: '0.02%', sub: '', subColor: '', desc: 'Zero critical crashes', dot: COLORS.red },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <p style={S.statValue}>{s.value}</p>
              {s.sub && <span style={S.statSub(s.subColor)}>{s.sub}</span>}
            </div>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Service Status + DB & Infrastructure */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Service Status */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 20px' }}>SERVICE STATUS</h3>
          {SERVICES.map((s, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', padding: '12px 0', borderBottom: i < SERVICES.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.dot, marginRight: 12 }} />
              <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: COLORS.white }}>{s.name}</span>
              <span style={{ fontSize: 13, color: COLORS.muted, marginRight: 20, minWidth: 50, textAlign: 'right' }}>{s.latency}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.green, minWidth: 60, textAlign: 'right' }}>{s.uptime}</span>
            </div>
          ))}
        </div>

        {/* Database & Infrastructure */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 20px' }}>DATABASE & INFRASTRUCTURE</h3>
          {[
            { label: 'Average Query Latency', value: '23ms' },
            { label: 'Connection Pool Utilization', value: '67%' },
            { label: 'Replication Lag (Replica A)', value: '12ms' },
          ].map((d, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: COLORS.muted }}>{d.label}</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.white }}>{d.value}</span>
            </div>
          ))}

          {/* Storage bar */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: COLORS.muted }}>Platform Storage Used</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>2.4TB / 5TB</span>
            </div>
            <div style={{ height: 8, background: COLORS.border, borderRadius: 4 }}>
              <div style={{ width: '48%', height: '100%', background: COLORS.blue, borderRadius: 4 }} />
            </div>
          </div>

          {/* AI Engine Status */}
          <h4 style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>AI Engine Status</h4>
          {[
            { label: 'Predictions Generated', value: '847' },
            { label: 'Inference Time (Avg)', value: '340ms' },
            { label: 'Model Confidence', value: '94.2%' },
            { label: 'Queue Depth', value: '0' },
            { label: 'Model Version', value: 'v2.4.0' },
          ].map((d, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 12, color: COLORS.muted }}>{d.label}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.white }}>{d.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System Alerts */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>SYSTEM ALERTS</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {ALERTS.map((a, i) => (
              <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                <td style={{ ...S.tableCell, width: 90 }}>{a.time}</td>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{a.source}</td>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{a.action}</td>
                <td style={{ ...S.tableCell, maxWidth: 340 }}>{a.detail}</td>
                <td style={{ ...S.tableCell, textAlign: 'right' }}>
                  <span style={S.badge(a.sevColor + '22', a.sevColor)}>{a.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
