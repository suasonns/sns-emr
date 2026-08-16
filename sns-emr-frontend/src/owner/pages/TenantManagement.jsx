import React from 'react';
import { COLORS, S } from '../design';

const TENANTS = [
  { name: 'Grace Hospice Care', status: 'Active', statusColor: COLORS.green, health: '98%', healthColor: COLORS.green, patients: 312, users: 48, mrr: '$4,200', plan: 'Pro' },
  { name: 'Comfort Care Services', status: 'At Risk', statusColor: COLORS.orange, health: '74%', healthColor: COLORS.orange, patients: 145, users: 22, mrr: '$1,800', plan: 'Starter' },
  { name: 'Sunrise Home Health', status: 'Active', statusColor: COLORS.green, health: '94%', healthColor: COLORS.green, patients: 567, users: 92, mrr: '$6,500', plan: 'Enterprise' },
  { name: 'Serenity Hospice Group', status: 'Critical', statusColor: COLORS.red, health: '45%', healthColor: COLORS.red, patients: 240, users: 34, mrr: '$3,800', plan: 'Pro' },
  { name: 'Valley Palliative Care', status: 'Active', statusColor: COLORS.green, health: '91%', healthColor: COLORS.green, patients: 189, users: 31, mrr: '$2,900', plan: 'Pro' },
  { name: 'Apex Nursing Agency', status: 'Active', statusColor: COLORS.green, health: '88%', healthColor: COLORS.green, patients: 88, users: 14, mrr: '$1,200', plan: 'Starter' },
  { name: 'Beacon Health & Hospice', status: 'At Risk', statusColor: COLORS.orange, health: '79%', healthColor: COLORS.orange, patients: 210, users: 29, mrr: '$3,100', plan: 'Pro' },
  { name: 'Sacred Heart Hospice', status: 'Active', statusColor: COLORS.green, health: '96%', healthColor: COLORS.green, patients: 112, users: 18, mrr: '$1,800', plan: 'Starter' },
  { name: 'Golden Gate Palliative', status: 'Active', statusColor: COLORS.green, health: '92%', healthColor: COLORS.green, patients: 345, users: 54, mrr: '$4,500', plan: 'Pro' },
  { name: 'Horizon Care Systems', status: 'Critical', statusColor: COLORS.red, health: '58%', healthColor: COLORS.red, patients: 405, users: 61, mrr: '$5,200', plan: 'Enterprise' },
  { name: 'Evergreen Hospice', status: 'Active', statusColor: COLORS.green, health: '97%', healthColor: COLORS.green, patients: 175, users: 26, mrr: '$2,900', plan: 'Pro' },
  { name: 'Legacy Home & Health', status: 'Active', statusColor: COLORS.green, health: '90%', healthColor: COLORS.green, patients: 95, users: 12, mrr: '$1,200', plan: 'Starter' },
];

export default function TenantManagement() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Tenant Management</h1>
          <p style={S.pageSubtitle}>Monitor and manage all agency tenants across the platform</p>
        </div>
        <button style={S.btn(COLORS.teal)}>NEW TENANT ONBOARDING</button>
      </div>

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'TOTAL TENANTS', value: '24', sub: '▲ 2 new', subColor: COLORS.teal, desc: 'Registered hospice domains', dot: COLORS.blue },
          { label: 'ACTIVE', value: '18', sub: 'Healthy SLA', subColor: COLORS.green, desc: 'Consistent daily activity logs', dot: COLORS.green },
          { label: 'AT RISK', value: '4', sub: '', subColor: '', desc: 'Dipping compliance telemetry', dot: COLORS.orange },
          { label: 'CRITICAL', value: '2', sub: '', subColor: '', desc: 'Immediate action required', dot: COLORS.red },
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

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input style={S.searchBar} placeholder="Search agencies by name, region, or database ID..." readOnly />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Status:</span>
          <select style={S.select}><option>All Statuses</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Plan:</span>
          <select style={S.select}><option>All Plans</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Region:</span>
          <select style={S.select}><option>All Regions</option></select>
        </div>
      </div>

      {/* Table + Detail Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
        {/* Table */}
        <div style={S.card}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Agency Name', 'Status', 'Health Score', 'Patients', 'Users', 'MRR', 'Plan'].map(h => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TENANTS.map((t, i) => (
                <tr key={i} style={i === 0 ? { background: 'rgba(16,183,162,0.06)' } : {}}>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{t.name}</td>
                  <td style={{ ...S.tableCell }}><span style={S.badge(t.statusColor + '22', t.statusColor)}>{t.status}</span></td>
                  <td style={S.tableCell}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 50, height: 4, background: COLORS.border, borderRadius: 2 }}>
                        <div style={{ width: t.health, height: '100%', background: t.healthColor, borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.white }}>{t.health}</span>
                    </div>
                  </td>
                  <td style={S.tableCell}>{t.patients}</td>
                  <td style={S.tableCell}>{t.users}</td>
                  <td style={S.tableCell}>{t.mrr}</td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: t.plan === 'Enterprise' ? COLORS.teal : t.plan === 'Pro' ? COLORS.blue : COLORS.muted }}>{t.plan}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Detail Panel */}
        <div style={S.card}>
          <p style={{ fontSize: 12, fontWeight: 700, color: COLORS.muted, margin: '0 0 4px', letterSpacing: 0.5 }}>SELECTED TENANT</p>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>Grace Hospice Care</h3>
          <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 24px' }}>ID: tenant_grace_991b2</p>

          <h4 style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '0 0 12px' }}>Quick Diagnostics</h4>
          {[
            { label: 'Clean Claim Rate', value: '96.4%' },
            { label: 'NOE Compliance', value: '99.1%' },
            { label: 'Denial Rate', value: '2.1%' },
          ].map((d, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 13, color: COLORS.muted }}>{d.label}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{d.value}</span>
            </div>
          ))}

          <h4 style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '24px 0 12px' }}>Administrative Actions</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: COLORS.bg, borderRadius: 8 }}>
              <span>⚙️</span>
              <span style={{ fontSize: 13, color: COLORS.muted }}>SaaS Billing Configuration</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: COLORS.bg, borderRadius: 8 }}>
              <span>📄</span>
              <span style={{ fontSize: 13, color: COLORS.muted }}>Export Compliance Audit</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: COLORS.red + '22', borderRadius: 8, border: `1px solid ${COLORS.red}44` }}>
              <span>⚠️</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.red }}>Suspend Tenant Account</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
