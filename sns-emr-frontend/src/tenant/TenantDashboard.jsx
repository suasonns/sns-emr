import React, { useEffect, useState } from 'react';
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
import { fetchTenantDashboard } from '../api/dashboard';
import { fetchCensusWorkspace } from '../api/census';
import { getCurrentUser } from '../api/session';
import { COLORS, S } from './design';

export { COLORS, S } from './design';

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
  const [workspace, setWorkspace] = useState(null);
  const [census, setCensus] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const ActivePage = PAGES[activeTab];
  const currentUser = getCurrentUser();
  const tenantName = workspace?.tenant_name || currentUser?.tenant_name || 'Tenant Workspace';
  const displayName = currentUser?.full_name || currentUser?.email || 'Signed-in User';
  const displayRole = currentUser?.role || 'Staff';
  const initials = (displayName.match(/\b\w/g) || []).slice(0, 2).join('').toUpperCase() || 'SU';

  useEffect(() => {
    let active = true;
    Promise.all([fetchTenantDashboard(), fetchCensusWorkspace()])
      .then(([dashboardResponse, censusResponse]) => {
        if (!active) return;
        setWorkspace(dashboardResponse);
        setCensus(censusResponse);
      })
      .catch((requestError) => {
        if (active) setError(requestError instanceof Error ? requestError.message : 'Tenant data failed to load');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: COLORS.bg, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ width: 220, background: COLORS.card, borderRight: `1px solid ${COLORS.border}`, padding: '24px 0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0 20px', marginBottom: 32 }}>
          <p style={{ fontSize: 18, fontWeight: 700, color: COLORS.teal, margin: 0 }}>SNS Hospice</p>
          <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: '4px 0 0' }}>{tenantName}</p>
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
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: COLORS.white }}>{initials}</div>
          <div>
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.white, margin: 0 }}>{displayName}</p>
            <p style={{ fontSize: 10, fontWeight: 400, color: COLORS.dim, margin: 0 }}>{displayRole}</p>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
        {error ? <div style={{ ...S.card, color: COLORS.red }}>{error}</div> : null}
        <ActivePage workspace={workspace} census={census} loading={loading} />
      </div>
    </div>
  );
}
