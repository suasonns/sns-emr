import React, { useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import VendorManagement from './VendorManagement';
import OrderPackManagement from './OrderPackManagement';
import { getAgencyProfile } from '../../api/agencyProfile';
import { listStaff } from '../../api/staff';

// Honest placeholder for settings domains that have no backend persistence
// yet (Notifications / Clinical templates / Billing config / Integrations).
// Per this project's "never fabricate data" policy, these must not show
// invented toggle states, fake integration statuses, or fake API keys.
function NotAvailableCard({ title, note }) {
  return (
    <div style={{ ...S.card, marginBottom: 0, padding: 24, border: `1px dashed ${COLORS.border}` }}>
      <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 13, color: COLORS.muted, lineHeight: 1.6 }}>{note}</div>
    </div>
  );
}

const settingsTabs = [
  { label: 'General' },
  { label: 'Notifications' },
  { label: 'Clinical' },
  { label: 'Billing' },
  { label: 'Vendors' },
  { label: 'Order Packs' },
  { label: 'Integrations' },
  { label: 'Users & Permissions' },
];

function GeneralTab() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getAgencyProfile()
      .then((data) => { if (!cancelled) setProfile(data); })
      .catch((err) => { if (!cancelled) setError(err?.message || 'Failed to load agency profile'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const agencyInfo = profile ? [
    { label: 'Agency Name', value: profile.display_name || '—' },
    { label: 'Legal Name', value: profile.legal_name || '—' },
    { label: 'NPI Number', value: profile.npi || '—' },
    { label: 'EIN', value: profile.ein || '—' },
    { label: 'PTAN', value: profile.ptan || '—' },
    { label: 'Tenant Type', value: profile.tenant_type || '—' },
    { label: 'CBSA Code', value: profile.cbsa_code || '—' },
    { label: 'Status', value: profile.status || '—' },
  ] : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Agency Information</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Core agency identity fields on record.</div>
        {loading && <div style={{ fontSize: 13, color: COLORS.muted }}>Loading…</div>}
        {error && <div style={{ fontSize: 13, color: COLORS.red }}>{error}</div>}
        {!loading && !error && agencyInfo.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < agencyInfo.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.muted }}>{item.label}</span>
            <span style={{ fontSize: 13, color: COLORS.white, fontWeight: 500 }}>{item.value}</span>
          </div>
        ))}
      </div>

      <NotAvailableCard
        title="Address, Operating Hours &amp; Service Areas"
        note="Not configured yet — these fields aren't part of the agency record in this release. Editing here would not persist anywhere, so nothing is shown until real fields and an edit endpoint exist."
      />

      <NotAvailableCard
        title="Access Level Visibility"
        note="Role-based access to Agency Settings is enforced by the backend and is not user-configurable in this release."
      />
    </div>
  );
}

function NotificationsTab() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <NotAvailableCard
        title="Email Notifications"
        note="Not available yet — there is no notification-preference backend, so alert toggles shown here would not actually change what gets sent."
      />
      <NotAvailableCard
        title="SMS / Text Notifications"
        note="Not available yet — no SMS delivery integration exists in this release."
      />
      <NotAvailableCard
        title="Quiet Hours"
        note="Not available yet — quiet-hours scheduling isn't wired to any backend preference."
      />
    </div>
  );
}

function ClinicalTab() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <NotAvailableCard
        title="Documentation Templates"
        note="Not available yet — clinical note templates are hardcoded per note type in this release; there is no configurable template library or backend model for it."
      />
      <NotAvailableCard
        title="Assessment Schedules"
        note="Not available yet — assessment cadence isn't backed by a configurable schedule; it's driven by the fixed clinical workflows already built."
      />
      <NotAvailableCard
        title="Clinical Protocols"
        note="Not available yet — standing orders and protocol documents aren't stored or manageable here."
      />
    </div>
  );
}

function BillingTab() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <NotAvailableCard
        title="Billing Configuration"
        note="Not available yet — default payer, billing cycle, and submission-mode preferences aren't stored per agency; billing runs use the real claims/EDI pipeline directly."
      />
      <NotAvailableCard
        title="Medicare Rate Schedule"
        note="Not available yet — this page won't show a rate table until it reads the real CMS per-diem rate service, so it can't drift from what billing actually uses."
      />
      <NotAvailableCard
        title="Auto-Billing Rules"
        note="Not available yet — these switches aren't wired to any backend rule engine, so toggling them would not change how claims are generated."
      />
    </div>
  );
}

function IntegrationsTab() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <NotAvailableCard
        title="Third-Party Integrations"
        note="Not available yet — this agency has no connected Medicare MAC, quality benchmarking, e-signature, accounting, e-prescribing, or FHIR integrations configured. Nothing here is actually connected."
      />
      <NotAvailableCard
        title="API Access"
        note="Not available yet — there is no API key issuance for third-party integrations in this release."
      />
    </div>
  );
}

function UsersTab() {
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    listStaff({ status: 'active' })
      .then((data) => { if (!cancelled) setStaffList(data); })
      .catch((err) => { if (!cancelled) setError(err?.message || 'Failed to load staff'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const total = staffList.length;
  const roleCount = new Set(staffList.map((u) => u.role).filter(Boolean)).size;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
        {[
          { label: 'Total Active Staff', value: String(total) },
          { label: 'Roles Represented', value: String(roleCount) },
        ].map((stat, i) => (
          <div key={i} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '14px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.muted }}>{stat.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, marginTop: 4 }}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 13, fontWeight: 600, color: COLORS.white }}>
          Staff Roster
        </div>
        {loading && <div style={{ padding: 20, fontSize: 13, color: COLORS.muted }}>Loading…</div>}
        {error && <div style={{ padding: 20, fontSize: 13, color: COLORS.red }}>{error}</div>}
        {!loading && !error && staffList.length === 0 && (
          <div style={{ padding: 20, fontSize: 13, color: COLORS.muted }}>No active staff on record.</div>
        )}
        {!loading && !error && staffList.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {['Name', 'Email', 'Role', 'Status'].map((h) => (
                  <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {staffList.map((u) => (
                <tr key={u.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: '12px 20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 30, height: 30, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 11 }}>
                        {(u.full_name || u.email || '?').split(' ').map((n) => n[0]).slice(0, 2).join('')}
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.white }}>{u.full_name || '—'}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 20px', fontSize: 12, color: COLORS.muted }}>{u.email}</td>
                  <td style={{ padding: '12px 20px' }}><span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.teal}22`, color: COLORS.teal }}>{u.role}</span></td>
                  <td style={{ padding: '12px 20px' }}><span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: u.active ? `${COLORS.green}22` : `${COLORS.orange}22`, color: u.active ? COLORS.green : COLORS.orange }}>{u.active ? 'Active' : 'Inactive'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <NotAvailableCard
        title="Role Permissions"
        note="Not available yet — role permission matrices aren't user-configurable here; access is enforced by the backend's fixed role definitions."
      />
    </div>
  );
}

export default function AgencySettings() {
  const [activeTab, setActiveTab] = useState('General');

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: COLORS.white, margin: 0 }}>Agency Settings</h1>
        <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>
          Configure agency preferences, integrations, notifications, and compliance parameters.
          <span style={{ color: '#f59e0b', marginLeft: 8, fontSize: 11, fontWeight: 600 }}>Administrator / DPCS Access Only</span>
        </p>
      </div>

      <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 24 }}>
        {settingsTabs.map((tab) => (
          <button key={tab.label} onClick={() => setActiveTab(tab.label)} style={{
            padding: '12px 20px', background: 'transparent', border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 600,
            color: activeTab === tab.label ? COLORS.teal : COLORS.muted,
            borderBottom: activeTab === tab.label ? `2px solid ${COLORS.teal}` : '2px solid transparent',
          }}>{tab.label}</button>
        ))}
      </div>

      {activeTab === 'General' && <GeneralTab />}
      {activeTab === 'Notifications' && <NotificationsTab />}
      {activeTab === 'Clinical' && <ClinicalTab />}
      {activeTab === 'Billing' && <BillingTab />}
      {activeTab === 'Vendors' && <VendorManagement />}
      {activeTab === 'Order Packs' && <OrderPackManagement />}
      {activeTab === 'Integrations' && <IntegrationsTab />}
      {activeTab === 'Users & Permissions' && <UsersTab />}
    </div>
  );
}
