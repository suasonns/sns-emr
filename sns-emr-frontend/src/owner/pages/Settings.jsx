import React, { useMemo, useState } from 'react';
import { COLORS, S } from '../design';
import { getCurrentUser, isPlatformSuperUser, setCurrentUser } from '../../api/session';

const TABS = ['General', 'Security', 'Notifications', 'Billing', 'AI Config', 'Integrations'];

const INTEGRATIONS = [
  { name: 'Medicare DDE Sync Engine', status: 'Connected', statusColor: COLORS.teal, lastSync: 'Last sync: 2m ago', action: 'Disconnect', actionColor: COLORS.teal },
  { name: 'Palmetto GBA Billing Gateway', status: 'Connected', statusColor: COLORS.teal, lastSync: 'Last sync: 15m ago', action: 'Disconnect', actionColor: COLORS.teal },
  { name: 'CGS Administrators Portal', status: 'Connected', statusColor: COLORS.teal, lastSync: 'Last sync: 1h ago', action: 'Disconnect', actionColor: COLORS.teal },
  { name: 'Availity Cleared Claims Engine', status: 'Connected', statusColor: COLORS.teal, lastSync: 'Last sync: 3h ago', action: 'Disconnect', actionColor: COLORS.teal },
  { name: 'Surescripts RX Hub', status: 'Disconnected', statusColor: COLORS.red, lastSync: 'Last sync: 3d ago', action: 'Connect', actionColor: COLORS.teal },
];

export default function Settings() {
  const currentUser = getCurrentUser();
  const canManageTenantPreference = isPlatformSuperUser(currentUser);

  const tenantOptions = useMemo(() => [
    { id: '01271980-0000-0000-0000-000005101977', name: 'Love & Faith Hospice Services, Inc.' },
    { id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', name: 'Angela Hospice (Training)' },
    { id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', name: 'Silva Hospice (Training)' },
    { id: '5224ceb6-e29d-4841-858e-e77f1b67fe65', name: 'Dev Tenant A' },
    { id: '85282f8b-fd5b-45e6-bb82-45394ef7a2f8', name: 'Dev Tenant B' },
  ], []);

  const [activeTenantId, setActiveTenantId] = useState(() => {
    const stored = localStorage.getItem('sns-active-agency');
    const fallback = currentUser?.tenant_id || tenantOptions[0].id;
    const nextValue = stored && tenantOptions.some((tenant) => tenant.id === stored) ? stored : fallback;
    localStorage.setItem('sns-active-agency', nextValue);
    return nextValue;
  });

  const handleTenantPreferenceChange = (event) => {
    const nextTenantId = event.target.value;
    setActiveTenantId(nextTenantId);
    localStorage.setItem('sns-active-agency', nextTenantId);

    const nextTenant = tenantOptions.find((tenant) => tenant.id === nextTenantId) || tenantOptions[0];
    const updatedUser = currentUser ? {
      ...currentUser,
      tenant_id: nextTenant.id,
      tenant_name: nextTenant.name,
    } : null;

    if (updatedUser) {
      setCurrentUser(updatedUser);
    }
  };

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Settings</h1>
          <p style={S.pageSubtitle}>Global SaaS instance configurations, billing limits, MFA security systems and Medicare API integrations</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 32, borderBottom: `1px solid ${COLORS.border}` }}>
        {TABS.map((tab, i) => (
          <button key={tab} style={{
            padding: '12px 20px', border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 700,
            color: i === 0 ? COLORS.teal : COLORS.muted,
            background: 'transparent',
            borderBottom: i === 0 ? `2px solid ${COLORS.teal}` : '2px solid transparent',
          }}>{tab}</button>
        ))}
      </div>

      {canManageTenantPreference ? (
        <div style={{ ...S.card, marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>TENANT PREFERENCE</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'end' }}>
            <div>
              <p style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px' }}>ACTIVE AGENCY</p>
              <select value={activeTenantId} onChange={handleTenantPreferenceChange} style={{ ...S.select, width: '100%' }}>
                {tenantOptions.map((tenant) => (
                  <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                ))}
              </select>
            </div>
            <div>
              <p style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px' }}>TENANT CONTEXT</p>
              <input
                style={{ ...S.searchBar, paddingLeft: 12, width: '100%', boxSizing: 'border-box' }}
                value={tenantOptions.find((tenant) => tenant.id === activeTenantId)?.name || 'Love & Faith Hospice Services, Inc.'}
                readOnly
              />
            </div>
          </div>
        </div>
      ) : null}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Left Column */}
        <div>
          {/* General Platform Parameters */}
          <div style={S.card}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 24px' }}>GENERAL PLATFORM PARAMETERS</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {[
                { label: 'PLATFORM NAME', value: 'SNS Hospice Solutions Control Panel' },
                { label: 'SUPPORT DEPT EMAIL', value: 'sysops@snshospicesolutions.com' },
                { label: 'DEFAULT TIMEZONE', value: 'America/New_York (EST)', isSelect: true },
                { label: 'DATE FORMAT', value: 'MM/DD/YYYY', isSelect: true },
                { label: 'AUTO SESSION TIMEOUT (MIN)', value: '30 minutes' },
                { label: 'MAX LOGIN ATTEMPTS BEFORE LOCKOUT', value: '5 attempts' },
              ].map((f, i) => (
                <div key={i}>
                  <p style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px' }}>{f.label}</p>
                  {f.isSelect ? (
                    <select style={{ ...S.select, width: '100%' }}><option>{f.value}</option></select>
                  ) : (
                    <input style={{ ...S.searchBar, paddingLeft: 12, width: '100%', boxSizing: 'border-box' }} value={f.value} readOnly />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Security & Access Controls */}
          <div style={S.card}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 24px' }}>SECURITY & ACCESS CONTROLS</h3>
            {[
              { label: 'Multi-Factor Authentication Required', desc: 'Enforce platform-wide 2FA for all tenancy logins', on: true },
              { label: 'HIPAA Compliance Safe-Harbor Encryption', desc: 'All local SQLite cache stores strictly encrypted on-device', on: true },
              { label: 'Telemetry & Clinical Audit Auto-upload', desc: 'Stream active audit-logs to AWS compliance repository', on: false },
            ].map((toggle, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                  <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.white, margin: '0 0 4px' }}>{toggle.label}</p>
                  <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{toggle.desc}</p>
                </div>
                <div style={{
                  width: 44, height: 24, borderRadius: 12,
                  background: toggle.on ? COLORS.teal : COLORS.border,
                  position: 'relative', cursor: 'pointer',
                }}>
                  <div style={{
                    width: 18, height: 18, borderRadius: '50%', background: COLORS.white,
                    position: 'absolute', top: 3,
                    left: toggle.on ? 23 : 3,
                    transition: 'left 0.2s',
                  }} />
                </div>
              </div>
            ))}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 12 }}>
              <div>
                <p style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px' }}>PASSWORD EXPIRATION SCHEDULE</p>
                <input style={{ ...S.searchBar, paddingLeft: 12, width: '100%', boxSizing: 'border-box' }} value="90 Days" readOnly />
              </div>
              <div>
                <p style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, margin: '0 0 8px' }}>AUDIT LOG RETENTION</p>
                <input style={{ ...S.searchBar, paddingLeft: 12, width: '100%', boxSizing: 'border-box' }} value="365 Days" readOnly />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column — Integrations */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>ACTIVE CLEARINGHOUSE INTEGRATIONS</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>Platform API gateways configured for active state processing</p>
          {INTEGRATIONS.map((intg, i) => (
            <div key={i} style={{ padding: '16px 0', borderBottom: i < INTEGRATIONS.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>{intg.name}</p>
                  <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{intg.lastSync}</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: intg.statusColor }}>{intg.status}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: intg.actionColor, cursor: 'pointer' }}>{intg.action}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Warning + Save */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 32 }}>
        <p style={{ fontSize: 13, color: COLORS.muted, margin: 0 }}>Be careful. Modifications to general parameters immediately trigger container restarts.</p>
        <button style={{ ...S.btn(COLORS.teal), padding: '14px 32px', fontSize: 13, fontWeight: 700 }}>SAVE INSTANCE CONFIGURATIONS</button>
      </div>
    </div>
  );
}
