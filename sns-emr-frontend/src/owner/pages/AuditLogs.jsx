import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

const CATEGORIES = [
  { icon: '🔐', label: 'AUTH EVENT TYPES', value: '2 Active' },
  { icon: '📂', label: 'DATA ACCESS', value: '1 Active' },
  { icon: '⚙️', label: 'ADMIN ACTIONS', value: '2 Active' },
  { icon: '💳', label: 'BILLING TRANSACTIONS', value: '2 Active' },
  { icon: '⚠️', label: 'COMPLIANCE AUDITS', value: '1 Active' },
];

const CAT_COLORS = {
  AUTH: { bg: '#3b82f622', color: COLORS.blue },
  DATA: { bg: '#8b5cf622', color: COLORS.purple },
  COMPLIANCE: { bg: '#f9731622', color: COLORS.orange },
  ADMIN: { bg: '#10b7a222', color: COLORS.teal },
  BILLING: { bg: '#ec489922', color: COLORS.pink },
};

const LOGS = [
  { time: '04:12:15 PM', cat: 'AUTH', action: 'User login success', user: 'sarah.j@gracehospice', tenant: 'Grace Hospice Care', detail: 'MFA Verified, Session #991b2', ip: '192.168.1.104' },
  { time: '04:09:44 PM', cat: 'DATA', action: 'Patient chart accessed', user: 'mark.t@comfortcare', tenant: 'Comfort Care Services', detail: 'Accessed medical records of Patient ID: #22938', ip: '10.0.4.82' },
  { time: '03:52:10 PM', cat: 'COMPLIANCE', action: 'Compliance alert triggered', user: 'system_ai', tenant: 'Valley Hospice', detail: 'Denial risk spike alert triggered automatically', ip: '127.0.0.1' },
  { time: '03:41:00 PM', cat: 'ADMIN', action: 'User profile created', user: 'admin_owner', tenant: 'Grace Hospice Care', detail: 'Created new Clinician profile: jane.doe@gracehospice', ip: '192.168.1.5' },
  { time: '03:15:32 PM', cat: 'BILLING', action: 'Claim submitted to Medicare', user: 'billing_service', tenant: 'Sunrise Home Health', detail: 'Batch submission ID: #9001A (14 claims)', ip: '44.201.22.14' },
  { time: '02:44:12 PM', cat: 'COMPLIANCE', action: 'Medicare DDE Sync Completed', user: 'system_sync', tenant: 'All Tenants', detail: 'Pulled 847 historical claim statuses', ip: '127.0.0.1' },
  { time: '02:10:05 PM', cat: 'ADMIN', action: 'Plan upgraded to Enterprise', user: 'owner_admin', tenant: 'Sunrise Home Health', detail: 'Automatic pricing migration triggered', ip: '192.168.1.1' },
  { time: '01:30:19 PM', cat: 'AUTH', action: 'MFA Disabled by Administrator', user: 'admin_owner', tenant: 'Comfort Care Services', detail: 'MFA overridden temporarily for clinical pilot testing', ip: '10.0.4.15' },
  { time: '11:15:00 AM', cat: 'COMPLIANCE', action: 'Tenant suspended', user: 'owner_admin', tenant: 'Legacy Home & Health', detail: 'System-wide lockout triggered for non-payment SLA', ip: '192.168.1.1' },
  { time: '10:02:44 AM', cat: 'DATA', action: 'Clinical note signed', user: 'nurse.steve@gracehospice', tenant: 'Grace Hospice Care', detail: 'Signed POC assessment for Patient ID: #10043', ip: '192.168.1.200' },
];

export default function AuditLogs() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Audit Logs</h1>
          <p style={S.pageSubtitle}>Platform-wide activity trail — all user actions, system events, and compliance records</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button style={S.btnOutline}>📋 EXPORT REPORT</button>
          <button style={S.btn(COLORS.teal)}>REFRESH ENGINE</button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input style={S.searchBar} placeholder="Search user names, actions, IP addresses..." readOnly />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Category:</span>
          <select style={S.select}><option>All Categories</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Tenant:</span>
          <select style={S.select}><option>All Active Tenants</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Date Range:</span>
          <select style={S.select}><option>Last 24 Hours</option></select>
        </div>
      </div>

      {/* Category Pills */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        {CATEGORIES.map((c, i) => (
          <div key={i} style={{ flex: 1, background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: '14px 16px', textAlign: 'center' }}>
            <span style={{ fontSize: 18 }}>{c.icon}</span>
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: '6px 0 4px', letterSpacing: 0.3 }}>{c.label}</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.white, margin: 0 }}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Logs Table */}
      <div style={S.card}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['TIMESTAMP', 'CATEGORY', 'ACTION', 'USER', 'TENANT', 'DETAIL DESCRIPTION', 'IP ADDRESS'].map(h => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LOGS.map((l, i) => {
              const catStyle = CAT_COLORS[l.cat] || CAT_COLORS.ADMIN;
              return (
                <tr key={i}>
                  <td style={S.tableCell}>{l.time}</td>
                  <td style={{ ...S.tableCell }}>
                    <span style={S.badge(catStyle.bg, catStyle.color)}>{l.cat}</span>
                  </td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{l.action}</td>
                  <td style={S.tableCell}>{l.user}</td>
                  <td style={S.tableCell}>{l.tenant}</td>
                  <td style={{ ...S.tableCell, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.detail}</td>
                  <td style={S.tableCell}>{l.ip}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ fontSize: 12, color: COLORS.muted }}>Showing 1-10 of 2,492 platform logs</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={{ ...S.btnOutline, padding: '6px 14px', fontSize: 11 }}>Previous</button>
            <button style={{ ...S.btn(COLORS.teal), padding: '6px 14px', fontSize: 11 }}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
