import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

const USERS = [
  { name: 'Sarah Jenkins', email: 'sarah.j@gracehospice.com', role: 'Super Admin', roleColor: COLORS.purple, tenant: 'Grace Hospice Care', status: 'Active', statusColor: COLORS.green, lastLogin: '3m ago' },
  { name: 'Dr. Robert Chen', email: 'r.chen@comfortcare.org', role: 'Physician', roleColor: COLORS.blue, tenant: 'Comfort Care Services', status: 'Active', statusColor: COLORS.green, lastLogin: '1h ago' },
  { name: 'Emily Watson, RN', email: 'e.watson@sunrisehh.com', role: 'RN', roleColor: COLORS.teal, tenant: 'Sunrise Home Health', status: 'Active', statusColor: COLORS.green, lastLogin: 'Just Now' },
  { name: 'Marcus Brody', email: 'm.brody@serenityhospice.com', role: 'Biller', roleColor: COLORS.orange, tenant: 'Serenity Hospice Group', status: 'Inactive', statusColor: COLORS.dim, lastLogin: '12d ago' },
  { name: 'Platform Admin', email: 'platform@snshospice.com', role: 'Super Admin', roleColor: COLORS.purple, tenant: 'Platform Owner', status: 'Active', statusColor: COLORS.green, lastLogin: 'Just Now' },
  { name: 'Linda Morrison, RN', email: 'linda.m@valleypalliative.com', role: 'RN', roleColor: COLORS.teal, tenant: 'Valley Palliative Care', status: 'Disabled', statusColor: COLORS.orange, lastLogin: '3mo ago' },
  { name: 'James Callahan', email: 'j.callahan@apexnursing.com', role: 'Agency Admin', roleColor: COLORS.green, tenant: 'Apex Nursing Agency', status: 'Active', statusColor: COLORS.green, lastLogin: '2h ago' },
  { name: 'Dr. Amanda Ross', email: 'a.ross@sacredheart.com', role: 'Physician', roleColor: COLORS.blue, tenant: 'Sacred Heart Hospice', status: 'Active', statusColor: COLORS.green, lastLogin: '4d ago' },
];

export default function UserManagement() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>User Management</h1>
          <p style={S.pageSubtitle}>Orchestrate personnel access, security permissions, and roles across active agencies</p>
        </div>
        <button style={{ ...S.btn(COLORS.teal), display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 16 }}>+</span> ADD NEW USER
        </button>
      </div>

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'TOTAL USERS', value: '342', sub: 'Normal', subColor: COLORS.green, desc: 'Registered active directories', dot: COLORS.green },
          { label: 'ACTIVE NOW', value: '198', sub: 'High Activity', subColor: COLORS.teal, desc: 'Live active sessions (24h)', dot: COLORS.green },
          { label: 'AGENCY ADMINS', value: '24', sub: '', subColor: '', desc: 'One admin per active tenant', dot: COLORS.green },
          { label: 'DISABLED USERS', value: '3', sub: '', subColor: '', desc: 'Revoked credentials', dot: COLORS.red },
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
          <input style={S.searchBar} placeholder="Search users by name, email, or database record..." readOnly />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Role:</span>
          <select style={S.select}><option>All Roles</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Agency:</span>
          <select style={S.select}><option>All Agencies</option></select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Status:</span>
          <select style={S.select}><option>Active Only</option></select>
        </div>
      </div>

      {/* Table */}
      <div style={S.card}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Name', 'Email', 'Role', 'Tenant/Agency', 'Status', 'Last Login', 'Actions'].map(h => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {USERS.map((u, i) => (
              <tr key={i}>
                <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{u.name}</td>
                <td style={S.tableCell}>{u.email}</td>
                <td style={{ ...S.tableCell }}>
                  <span style={S.badge(u.roleColor + '22', u.roleColor)}>{u.role}</span>
                </td>
                <td style={S.tableCell}>{u.tenant}</td>
                <td style={{ ...S.tableCell }}>
                  <span style={S.badge(u.statusColor + '22', u.statusColor)}>{u.status}</span>
                </td>
                <td style={S.tableCell}>{u.lastLogin}</td>
                <td style={{ ...S.tableCell }}>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <span style={{ fontSize: 11, fontWeight: 500, color: COLORS.muted, cursor: 'pointer' }}>Reset</span>
                    <span style={{ fontSize: 11, fontWeight: 500, color: COLORS.muted, cursor: 'pointer' }}>Disable</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>Edit</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
