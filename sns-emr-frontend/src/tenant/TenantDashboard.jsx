import React, { useEffect, useState } from 'react';
import {
  DashboardOverview,
  PatientCensus,
  Clinical,
  Analytics,
  HelpSupport,
  AgencySettings,
  SecureInbox,
  Settings,
} from './pages';
import { fetchTenantDashboard } from '../api/dashboard';
import { fetchCensusWorkspace } from '../api/census';
import { getCurrentUser } from '../api/session';
import { hasRouteAccess } from '../utils/authorization';
import { useThemeMode } from '../theme/theme';
import { COLORS, S } from './design';

export { COLORS, S } from './design';

const ADMIN_SETTING_ROLES = ['ADMIN', 'ADMINISTRATOR', 'CLINICALADMIN', 'DPCS', 'DPCSADMIN', 'SUPERADMIN'];

function normalizeRole(value) {
  return String(value ?? '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function getTenantNav(currentUser) {
  const normalizedRole = normalizeRole(currentUser?.role);
  const canViewAgencySettings = ADMIN_SETTING_ROLES.some((role) => normalizedRole.includes(role));

  const items = ['Dashboard', 'Patient Census', 'Clinical', 'Insights', 'Help & Support'];
  if (canViewAgencySettings) {
    items.push('Agency Settings');
  }
  items.push('Inbox', 'Settings');

  return items;
}

function getTenantPages(currentUser) {
  const normalizedRole = normalizeRole(currentUser?.role);
  const canViewAgencySettings = ADMIN_SETTING_ROLES.some((role) => normalizedRole.includes(role));

  const pages = [DashboardOverview, PatientCensus, Clinical, Analytics, HelpSupport];
  if (canViewAgencySettings) {
    pages.push(AgencySettings);
  }
  pages.push(SecureInbox, Settings);
  return pages;
}

export default function TenantDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  const [workspace, setWorkspace] = useState(null);
  const [census, setCensus] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const currentUser = getCurrentUser();
  const isRestricted = !hasRouteAccess(currentUser, 'tenant');
  const navItems = getTenantNav(currentUser);
  const pages = getTenantPages(currentUser);
  const ActivePage = pages[activeTab] || pages[0];
  const { mode, toggleMode } = useThemeMode();
  const tenantName = workspace?.tenant_name || currentUser?.tenant_name || 'Tenant Workspace';
  const displayName = currentUser?.full_name || currentUser?.email || 'Signed-in User';
  const displayRole = currentUser?.role || 'Staff';
  const agencyLabel = currentUser?.tenant_name || tenantName || 'Current Agency';
  const initials = (displayName.match(/\b\w/g) || []).slice(0, 2).join('').toUpperCase() || 'SU';

  useEffect(() => {
    if (isRestricted) {
      setLoading(false);
      return undefined;
    }
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
  }, [isRestricted]);

  if (isRestricted) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', background: COLORS.bg, fontFamily: 'Inter, sans-serif' }}>
        <div style={{ maxWidth: 480, textAlign: 'center', color: COLORS.white, padding: 24 }}>
          <h2>Tenant workspace not available</h2>
          <p>
            Your current role does not have access to patient census or clinical data.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: COLORS.bg, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ width: 220, background: COLORS.card, borderRight: `1px solid ${COLORS.border}`, padding: '24px 0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0 20px', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img
              src="/brand/sns-logo-light.svg"
              alt="SNS logo"
              onError={(event) => {
                const target = event.currentTarget;
                if (!target.src.endsWith('/brand/sns-logo-icon.svg')) {
                  target.src = '/brand/sns-logo-icon.svg';
                }
              }}
              style={{ width: 220, height: 'auto', display: 'block' }}
            />
          </div>
        </div>

        <div style={{ padding: '0 16px 14px' }}>
          <button
            type="button"
            onClick={toggleMode}
            style={{
              width: '100%',
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              background: COLORS.bg,
              color: COLORS.white,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 700,
              padding: '10px 12px',
            }}
          >
            {mode === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>
        </div>

        <nav style={{ flex: 1 }}>
          {navItems.map((item, i) => (
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
          <div style={{ minWidth: 0 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.white, margin: 0 }}>{displayName}</p>
            <p style={{ fontSize: 10, fontWeight: 400, color: COLORS.dim, margin: '2px 0 0' }}>{displayRole}</p>
            <p style={{ fontSize: 9, fontWeight: 600, color: COLORS.teal, margin: '4px 0 0', letterSpacing: '0.04em', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              Agency: {agencyLabel}
            </p>
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
