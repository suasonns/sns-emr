import React, { useEffect, useMemo, useState } from 'react';
import { COLORS, S } from '../design';
import { getCurrentUser, setCurrentUser } from '../../api/session';
import { hasRouteAccess } from '../../utils/authorization';
import { fetchOwnerTenants } from '../../api/ownerAdmin';

const TABS = ['General', 'Security', 'Notifications', 'Billing', 'AI Config', 'Integrations'];

function NotAvailableCard({ title, note }) {
  return (
    <div style={{ ...S.card, borderStyle: 'dashed' }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 8px' }}>{title}</h3>
      <p style={{ fontSize: 12, color: COLORS.muted, lineHeight: 1.6, margin: 0 }}>{note}</p>
    </div>
  );
}

export default function Settings() {
  const currentUser = getCurrentUser();
  const canManageTenantPreference = hasRouteAccess(currentUser, 'owner');

  const [tenantOptions, setTenantOptions] = useState([]);
  const [tenantsLoading, setTenantsLoading] = useState(true);
  const [tenantsError, setTenantsError] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetchOwnerTenants()
      .then((res) => {
        if (cancelled) return;
        const options = (res.tenants || []).map((t) => ({ id: t.tenant_id, name: t.display_name || t.legal_name }));
        setTenantOptions(options);
      })
      .catch((err) => { if (!cancelled) setTenantsError(err?.message || 'Failed to load agencies'); })
      .finally(() => { if (!cancelled) setTenantsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const [activeTenantId, setActiveTenantId] = useState(() => localStorage.getItem('sns-active-agency') || '');

  useEffect(() => {
    if (tenantOptions.length === 0) return;
    const stored = localStorage.getItem('sns-active-agency');
    const fallback = currentUser?.tenant_id || tenantOptions[0].id;
    const nextValue = stored && tenantOptions.some((tenant) => tenant.id === stored) ? stored : fallback;
    setActiveTenantId(nextValue);
    localStorage.setItem('sns-active-agency', nextValue);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantOptions]);

  const handleTenantPreferenceChange = (event) => {
    const nextTenantId = event.target.value;
    setActiveTenantId(nextTenantId);
    localStorage.setItem('sns-active-agency', nextTenantId);

    const nextTenant = tenantOptions.find((tenant) => tenant.id === nextTenantId) || tenantOptions[0];
    const updatedUser = currentUser && nextTenant ? {
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
          <p style={S.pageSubtitle}>Global SaaS instance configuration and agency context.</p>
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
          {tenantsLoading ? (
            <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>Loading agencies…</p>
          ) : tenantsError ? (
            <p style={{ fontSize: 12, color: '#fca5a5', margin: 0 }}>{tenantsError}</p>
          ) : (
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
                  value={tenantOptions.find((tenant) => tenant.id === activeTenantId)?.name || ''}
                  readOnly
                />
              </div>
            </div>
          )}
        </div>
      ) : null}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <NotAvailableCard
          title="GENERAL PLATFORM PARAMETERS"
          note="Not available yet — platform name, support email, timezone, date format, session timeout, and lockout thresholds aren't stored in a configurable settings table in this release."
        />
        <NotAvailableCard
          title="SECURITY &amp; ACCESS CONTROLS"
          note="Not available yet — MFA enforcement, encryption posture, and audit-upload toggles are fixed in the backend and aren't user-configurable here."
        />
        <NotAvailableCard
          title="ACTIVE CLEARINGHOUSE INTEGRATIONS"
          note="Not available yet — there are no Medicare DDE, Palmetto GBA, CGS, or clearinghouse integrations connected. Nothing here is actually connected."
        />
      </div>
    </div>
  );
}
