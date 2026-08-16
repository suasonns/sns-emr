import React, { useState } from 'react';
import {
  DashboardOverview,
  PatientCensus,
  Admissions,
  Clinical,
  Scheduling,
  Billing,
  StaffManagement,
  QAPICompliance,
  Reports,
  SecureInbox,
  Settings,
} from './pages';

export const COLORS = {
  bg: '#0f172a',
  card: '#1e293b',
  border: '#334155',
  teal: '#10b7a2',
  white: '#ffffff',
  offWhite: '#f8fafc',
  textPrimary: '#f1f5f9',
  muted: '#94a3b8',
  dim: '#64748b',
  green: '#10b981',
  red: '#ef4444',
  orange: '#f59e0b',
  blue: '#3b82f6',
  purple: '#a855f7',
  pink: '#f43f5e',
  yellow: '#eab308',
};

export const S = {
  pageTitle: { fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 },
  pageSubtitle: { fontSize: 13, fontWeight: 400, color: COLORS.muted, margin: '4px 0 0' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 },
  statCard: { background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: '20px 18px', position: 'relative' },
  statValue: { fontSize: 28, fontWeight: 700, color: COLORS.white, margin: '6px 0 4px' },
  statDot: (color) => ({ width: 8, height: 8, borderRadius: '50%', background: color, position: 'absolute', top: 14, right: 14 }),
  statSub: (color) => ({ fontSize: 11, fontWeight: 600, color }),
  card: { background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 24, marginBottom: 24 },
  tableHeader: { padding: '10px 12px', fontSize: 11, fontWeight: 600, color: COLORS.dim, borderBottom: `1px solid ${COLORS.border}`, textTransform: 'uppercase' },
  tableCell: { padding: '12px 12px', fontSize: 13, fontWeight: 400, color: COLORS.muted, borderBottom: `1px solid ${COLORS.border}` },
  badge: (bg, color) => ({ display: 'inline-block', padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: bg, color }),
  btn: (bg) => ({ padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, background: bg, color: COLORS.white }),
  btnOutline: { padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`, cursor: 'pointer', fontSize: 13, fontWeight: 600, background: 'transparent', color: COLORS.muted },
  searchBar: { width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.muted, fontSize: 13, outline: 'none' },
  select: { padding: '10px 12px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.muted, fontSize: 13, outline: 'none', cursor: 'pointer' },
};

const NAV_ITEMS = [
  'Dashboard', 'Patient Census', 'Admissions', 'Clinical', 'Scheduling',
  'Billing', 'Staff', 'QAPI & Compliance', 'Reports', 'Inbox', 'Settings',
];

const PAGES = [
  DashboardOverview, PatientCensus, Admissions, Clinical, Scheduling,
  Billing, StaffManagement, QAPICompliance, Reports, SecureInbox, Settings,
];

export default function TenantDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  const ActivePage = PAGES[activeTab];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: COLORS.bg, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ width: 220, background: COLORS.card, borderRight: `1px solid ${COLORS.border}`, padding: '24px 0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0 20px', marginBottom: 32 }}>
          <p style={{ fontSize: 18, fontWeight: 700, color: COLORS.teal, margin: 0 }}>SNS Hospice</p>
          <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: '4px 0 0' }}>Grace Hospice Care</p>
        </div>

        <nav style={{ flex: 1 }}>
          {NAV_ITEMS.map((item, i) => (
            <div
              key={item}
              onClick={() => setActiveTab(i)}
              style={{
                padding: '10px 20px',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: activeTab === i ? 600 : 500,
                color: activeTab === i ? COLORS.teal : COLORS.muted,
                background: activeTab === i ? `${COLORS.teal}12` : 'transparent',
                borderLeft: activeTab === i ? `3px solid ${COLORS.teal}` : '3px solid transparent',
              }}
            >
              {item}
            </div>
          ))}
        </nav>

        <div style={{ padding: '16px 20px', borderTop: `1px solid ${COLORS.border}`, display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: COLORS.white }}>SJ</div>
          <div>
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.white, margin: 0 }}>Sarah Jenkins</p>
            <p style={{ fontSize: 10, fontWeight: 400, color: COLORS.dim, margin: 0 }}>Agency Admin</p>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
        <ActivePage />
      </div>
    </div>
  );
}
