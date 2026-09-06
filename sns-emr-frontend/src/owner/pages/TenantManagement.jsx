import React, { useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import {
  fetchOwnerTenants,
  createOwnerTenant,
  setOwnerTenantStatus,
  setOwnerTenantFinancials,
} from '../../api/ownerAdmin';

const STATUS_COLOR = {
  ACTIVE: COLORS.green,
  INACTIVE: COLORS.muted,
  SUSPENDED: COLORS.red,
};

const EMPTY_FORM = {
  legal_name: '',
  display_name: '',
  npi: '',
  ein: '',
  ptan: '',
  tenant_type: 'TRAINING',
  admin_email: '',
  admin_full_name: '',
  admin_password: '',
  admin_role: 'DPCS_ADMINISTRATOR',
};

function OnboardModal({ onClose, onCreated }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        ein: form.ein.trim() || undefined,
        ptan: form.ptan.trim() || undefined,
        display_name: form.display_name.trim() || undefined,
      };
      const result = await createOwnerTenant(payload);
      onCreated(result);
    } catch (err) {
      setError(err?.message || 'Failed to onboard tenant');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <form onSubmit={submit} style={{ ...S.card, width: 480, maxHeight: '85vh', overflowY: 'auto' }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>New Tenant Onboarding</h3>

        {error && (
          <div style={{ background: COLORS.red + '22', border: `1px solid ${COLORS.red}44`, borderRadius: 8, padding: '8px 12px', marginBottom: 12, color: COLORS.red, fontSize: 12 }}>
            {error}
          </div>
        )}

        <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: '12px 0 6px' }}>AGENCY</p>
        <input style={S.searchBar} placeholder="Legal name (required)" required value={form.legal_name} onChange={update('legal_name')} />
        <div style={{ height: 8 }} />
        <input style={S.searchBar} placeholder="Display name (optional)" value={form.display_name} onChange={update('display_name')} />
        <div style={{ height: 8 }} />
        <input style={S.searchBar} placeholder="NPI (10 digits, required)" required maxLength={10} value={form.npi} onChange={update('npi')} />
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <input style={S.searchBar} placeholder="EIN (9 digits, optional)" maxLength={9} value={form.ein} onChange={update('ein')} />
          <input style={S.searchBar} placeholder="PTAN (optional)" value={form.ptan} onChange={update('ptan')} />
        </div>
        <div style={{ height: 8 }} />
        <select style={{ ...S.select, width: '100%' }} value={form.tenant_type} onChange={update('tenant_type')}>
          <option value="TRAINING">Training (field testing)</option>
          <option value="PRODUCTION">Production</option>
          <option value="DEV">Dev</option>
        </select>

        <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: '16px 0 6px' }}>INITIAL ADMINISTRATOR</p>
        <input style={S.searchBar} type="email" placeholder="Admin email (required)" required value={form.admin_email} onChange={update('admin_email')} />
        <div style={{ height: 8 }} />
        <input style={S.searchBar} placeholder="Admin full name (required)" required value={form.admin_full_name} onChange={update('admin_full_name')} />
        <div style={{ height: 8 }} />
        <input style={S.searchBar} type="password" placeholder="Temporary password (min 12 chars, required)" required minLength={12} value={form.admin_password} onChange={update('admin_password')} />
        <div style={{ height: 8 }} />
        <select style={{ ...S.select, width: '100%' }} value={form.admin_role} onChange={update('admin_role')}>
          <option value="DPCS_ADMINISTRATOR">DPCS / Administrator</option>
          <option value="ADMINISTRATOR">Administrator</option>
          <option value="DPCS">DPCS</option>
        </select>

        <div style={{ display: 'flex', gap: 10, marginTop: 20, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose} style={{ ...S.btn(COLORS.border), color: COLORS.white }} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" style={S.btn(COLORS.teal)} disabled={submitting}>
            {submitting ? 'Onboarding…' : 'Onboard Tenant'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function TenantManagement() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState(null);
  const [statusBusy, setStatusBusy] = useState(false);
  const [statusError, setStatusError] = useState('');
  const [financialsBusy, setFinancialsBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchOwnerTenants();
      setTenants(data.tenants || []);
      setSelected((prev) => {
        if (!prev) return data.tenants?.[0] ?? null;
        return data.tenants?.find((t) => t.tenant_id === prev.tenant_id) ?? data.tenants?.[0] ?? null;
      });
    } catch (err) {
      setError(err?.message || 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const changeStatus = async (tenant, status) => {
    if (!tenant) return;
    const verb = status === 'SUSPENDED' ? 'suspend' : status === 'ACTIVE' ? 'reactivate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${verb} "${tenant.display_name}"? This changes their platform access immediately.`)) {
      return;
    }
    setStatusBusy(true);
    setStatusError('');
    try {
      await setOwnerTenantStatus(tenant.tenant_id, status);
      await load();
    } catch (err) {
      setStatusError(err?.message || `Failed to ${verb} tenant`);
    } finally {
      setStatusBusy(false);
    }
  };

  const active = tenants.filter((t) => t.status === 'ACTIVE').length;
  const suspended = tenants.filter((t) => t.status === 'SUSPENDED').length;
  const inactive = tenants.filter((t) => t.status === 'INACTIVE').length;
  const financialsEnabled = tenants.filter((t) => t.financials_enabled).length;

  const changeFinancials = async (tenant, enabled) => {
    if (!tenant) return;
    const action = enabled ? 'enable' : 'disable';
    if (!window.confirm(`Are you sure you want to ${action} managed Financials access for "${tenant.display_name}"? This only affects external billing-provider access.`)) {
      return;
    }
    setFinancialsBusy(true);
    setStatusError('');
    try {
      await setOwnerTenantFinancials(tenant.tenant_id, enabled);
      await load();
    } catch (err) {
      setStatusError(err?.message || `Failed to ${action} Financials`);
    } finally {
      setFinancialsBusy(false);
    }
  };

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Tenant Management</h1>
          <p style={S.pageSubtitle}>Onboard and manage all agency tenants on the platform</p>
        </div>
        <button style={S.btn(COLORS.teal)} onClick={() => setShowModal(true)}>NEW TENANT ONBOARDING</button>
      </div>

      {error && (
        <div style={{ background: COLORS.red + '22', border: `1px solid ${COLORS.red}44`, borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'TOTAL TENANTS', value: String(tenants.length), desc: 'Registered hospice agencies', dot: COLORS.blue },
          { label: 'ACTIVE', value: String(active), desc: 'Currently operating', dot: COLORS.green },
          { label: 'INACTIVE', value: String(inactive), desc: 'Not yet in active use', dot: COLORS.orange },
          { label: 'SUSPENDED', value: String(suspended), desc: 'Access disabled', dot: COLORS.red },
          { label: 'FINANCIALS ON', value: String(financialsEnabled), desc: 'Managed billing allowed', dot: COLORS.teal },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Table + Detail Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
        <div style={S.card}>
          {loading ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading tenants…</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Agency Name', 'Status', 'Type', 'Patients', 'Users', 'Billing', 'Financials'].map((h) => (
                    <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tenants.map((t) => (
                  <tr
                    key={t.tenant_id}
                    onClick={() => setSelected(t)}
                    style={{ cursor: 'pointer', background: selected?.tenant_id === t.tenant_id ? 'rgba(16,183,162,0.06)' : undefined }}
                  >
                    <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{t.display_name}</td>
                    <td style={S.tableCell}>
                      <span style={S.badge((STATUS_COLOR[t.status] || COLORS.muted) + '22', STATUS_COLOR[t.status] || COLORS.muted)}>{t.status}</span>
                    </td>
                    <td style={S.tableCell}>{t.tenant_type}</td>
                    <td style={S.tableCell}>{t.patient_count}</td>
                    <td style={S.tableCell}>{t.user_count}</td>
                    <td style={S.tableCell}>{t.billing_enabled ? 'Enabled' : 'Pending EIN/PTAN'}</td>
                    <td style={S.tableCell}>{t.financials_enabled ? 'On' : 'Off'}</td>
                  </tr>
                ))}
                {tenants.length === 0 && (
                  <tr>
                    <td style={S.tableCell} colSpan={7}>No tenants yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail Panel */}
        <div style={S.card}>
          <p style={{ fontSize: 12, fontWeight: 700, color: COLORS.muted, margin: '0 0 4px', letterSpacing: 0.5 }}>SELECTED TENANT</p>
          {selected ? (
            <>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>{selected.display_name}</h3>
              <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 24px', wordBreak: 'break-all' }}>ID: {selected.tenant_id}</p>

              <h4 style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '0 0 12px' }}>Details</h4>
              {[
                { label: 'Status', value: selected.status },
                { label: 'Type', value: selected.tenant_type },
                { label: 'AI Enabled', value: selected.ai_enabled ? 'Yes' : 'No' },
                { label: 'Billing Enabled', value: selected.billing_enabled ? 'Yes' : 'No (needs EIN/PTAN)' },
                { label: 'Financials', value: selected.financials_enabled ? 'On' : 'Off' },
                { label: 'Patients', value: selected.patient_count },
                { label: 'Users', value: selected.user_count },
              ].map((d, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, color: COLORS.muted }}>{d.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{d.value}</span>
                </div>
              ))}

              {statusError && (
                <div style={{ background: COLORS.red + '22', border: `1px solid ${COLORS.red}44`, borderRadius: 8, padding: '8px 10px', margin: '4px 0 12px', color: COLORS.red, fontSize: 12 }}>
                  {statusError}
                </div>
              )}

              <h4 style={{ fontSize: 13, fontWeight: 700, color: COLORS.white, margin: '16px 0 12px' }}>Access Control</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button
                  type="button"
                  style={selected.financials_enabled ? { ...S.btn(COLORS.border), color: COLORS.white } : S.btn(COLORS.teal)}
                  disabled={financialsBusy}
                  onClick={() => changeFinancials(selected, !selected.financials_enabled)}
                >
                  {financialsBusy
                    ? 'Working…'
                    : selected.financials_enabled
                      ? 'Turn Financials Off'
                      : 'Turn Financials On'}
                </button>
                {selected.status !== 'ACTIVE' && (
                  <button
                    type="button"
                    style={S.btn(COLORS.green)}
                    disabled={statusBusy}
                    onClick={() => changeStatus(selected, 'ACTIVE')}
                  >
                    {statusBusy ? 'Working…' : 'Reactivate Tenant'}
                  </button>
                )}
                {selected.status !== 'SUSPENDED' && (
                  <button
                    type="button"
                    style={S.btn(COLORS.red)}
                    disabled={statusBusy}
                    onClick={() => changeStatus(selected, 'SUSPENDED')}
                  >
                    {statusBusy ? 'Working…' : 'Suspend Access'}
                  </button>
                )}
                {selected.status !== 'INACTIVE' && (
                  <button
                    type="button"
                    style={{ ...S.btn(COLORS.border), color: COLORS.white }}
                    disabled={statusBusy}
                    onClick={() => changeStatus(selected, 'INACTIVE')}
                  >
                    {statusBusy ? 'Working…' : 'Mark Inactive'}
                  </button>
                )}
              </div>
            </>
          ) : (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>No tenant selected.</p>
          )}
        </div>
      </div>

      {showModal && (
        <OnboardModal
          onClose={() => setShowModal(false)}
          onCreated={() => {
            setShowModal(false);
            load();
          }}
        />
      )}
    </div>
  );
}
