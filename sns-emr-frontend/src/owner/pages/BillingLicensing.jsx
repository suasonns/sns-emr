/**
 * Owner Portal — Billing & Licensing Management
 *
 * Layout/structure translated from the approved Figma design package
 * (Owner Portal — Billing & Licensing Management, FINAL APPROVED baseline).
 * Per that approval: the design is approved, the example data is not.
 * Every metric below is sourced from `fetchOwnerBillingLicensing()` and
 * falls back to an honest "not available yet" state rather than the
 * Figma mockup's placeholder figures -- there is no platform-billing
 * backend service behind this page yet (see app.api.ownerAdmin.ts).
 */
import React, { useEffect, useMemo, useState } from 'react';
import { COLORS, S } from '../design';
import {
  BILLING_PROVIDER_SERVICE_SCOPES,
  createBillingProviderAssignment,
  createBillingProviderOrganization,
  fetchBillingProviderAssignments,
  fetchBillingProviderOrganizations,
  fetchOwnerTenants,
  fetchOwnerBillingLicensing,
  updateBillingProviderAssignment,
  updateBillingProviderOrganization,
} from '../../api/ownerAdmin';

const FILTER_TABS = [
  { key: 'ALL', label: 'All Clients' },
  { key: 'ACTIVE', label: 'Active' },
  { key: 'TRIAL', label: 'Trial' },
  { key: 'SUSPENDED', label: 'Suspended' },
  { key: 'PAYMENT_DUE', label: 'Payment Due' },
];

const CLIENT_STATUS_COLOR = {
  PAID: COLORS.green,
  OVERDUE: COLORS.red,
  PENDING: COLORS.orange,
  TRIAL: COLORS.teal,
};

const PAYMENT_STATUS_COLOR = {
  SUCCESS: COLORS.green,
  PENDING: COLORS.orange,
  OVERDUE: COLORS.red,
};

const OUTSTANDING_STATUS_COLOR = {
  UPCOMING: COLORS.blue,
  OVERDUE: COLORS.red,
};

const EMPTY_ORG_FORM = {
  name: '',
  organization_type: 'MANAGED_BILLING_PROVIDER',
  status: 'ACTIVE',
  notes: '',
};

function defaultAssignmentForm(tenantId = '') {
  return {
    billing_provider_organization_id: '',
    tenant_id: tenantId,
    relationship_status: 'PENDING',
    effective_start_at: new Date().toISOString().slice(0, 16),
    effective_end_at: '',
    financials_enabled: false,
    service_scope: [],
  };
}

function fmtMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtCompactMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function fmtDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit', year: 'numeric' });
}

function matchesFilter(client, filterKey) {
  if (filterKey === 'ALL') return true;
  if (filterKey === 'PAYMENT_DUE') return client.status === 'OVERDUE' || client.status === 'PENDING';
  return client.status === filterKey;
}

function fmtDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function humanizeScope(scope) {
  return (scope || '')
    .split('_')
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(' ');
}

export default function BillingLicensing() {
  const [tenantOptions, setTenantOptions] = useState([]);
  const [selectedTenantId, setSelectedTenantId] = useState('');
  const [billingData, setBillingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [providerOrganizations, setProviderOrganizations] = useState([]);
  const [providerAssignments, setProviderAssignments] = useState([]);
  const [providerLoading, setProviderLoading] = useState(true);
  const [providerError, setProviderError] = useState('');
  const [organizationForm, setOrganizationForm] = useState(EMPTY_ORG_FORM);
  const [organizationBusy, setOrganizationBusy] = useState(false);
  const [editingOrganizationId, setEditingOrganizationId] = useState('');
  const [assignmentForm, setAssignmentForm] = useState(defaultAssignmentForm());
  const [assignmentBusy, setAssignmentBusy] = useState(false);
  const [editingAssignmentId, setEditingAssignmentId] = useState('');

  useEffect(() => {
    let mounted = true;
    fetchOwnerTenants()
      .then((res) => {
        if (mounted) setTenantOptions(res?.tenants ?? []);
      })
      .catch(() => {
        // Agency filter is a convenience control; failing to load it
        // should never block the billing/licensing view itself.
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError('');
    fetchOwnerBillingLicensing({ tenantId: selectedTenantId || undefined })
      .then((res) => {
        if (mounted) setBillingData(res);
      })
      .catch((err) => {
        if (mounted) {
          setError(
            err?.message ||
              'Billing & Licensing data is not available yet. This page is not backed by a platform-billing service in this release.'
          );
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [selectedTenantId]);

  const loadProviderData = async () => {
    setProviderLoading(true);
    setProviderError('');
    try {
      const [orgs, assignments] = await Promise.all([
        fetchBillingProviderOrganizations(),
        fetchBillingProviderAssignments(),
      ]);
      setProviderOrganizations(orgs.organizations || []);
      setProviderAssignments(assignments.assignments || []);
    } catch (err) {
      setProviderError(err?.message || 'Failed to load billing-provider assignments.');
    } finally {
      setProviderLoading(false);
    }
  };

  useEffect(() => {
    loadProviderData();
  }, []);

  useEffect(() => {
    setAssignmentForm((previous) => ({
      ...previous,
      tenant_id: previous.tenant_id || selectedTenantId || '',
    }));
  }, [selectedTenantId]);

  const kpis = billingData?.kpis || {};
  const clients = billingData?.clients || [];
  const revenueByAgency = billingData?.revenue_by_agency || [];
  const recentPayments = billingData?.recent_payments || [];
  const upcomingOutstandings = billingData?.upcoming_outstandings || [];
  const licenseAllocations = billingData?.license_allocations || [];

  const filteredClients = useMemo(
    () => clients.filter((c) => matchesFilter(c, activeFilter)),
    [clients, activeFilter]
  );

  const maxRevenue = useMemo(
    () => revenueByAgency.reduce((max, r) => Math.max(max, Number(r.amount) || 0), 0),
    [revenueByAgency]
  );

  const visibleAssignments = useMemo(
    () => (
      selectedTenantId
        ? providerAssignments.filter((assignment) => assignment.tenant_id === selectedTenantId)
        : providerAssignments
    ),
    [providerAssignments, selectedTenantId]
  );

  const resetOrganizationForm = () => {
    setOrganizationForm(EMPTY_ORG_FORM);
    setEditingOrganizationId('');
  };

  const resetAssignmentEditor = () => {
    setAssignmentForm(defaultAssignmentForm(selectedTenantId || ''));
    setEditingAssignmentId('');
  };

  const handleOrganizationSubmit = async (e) => {
    e.preventDefault();
    setOrganizationBusy(true);
    setProviderError('');
    const payload = {
      ...organizationForm,
      name: organizationForm.name.trim(),
      organization_type: organizationForm.organization_type.trim(),
      notes: organizationForm.notes.trim() || undefined,
    };
    try {
      if (editingOrganizationId) {
        await updateBillingProviderOrganization(editingOrganizationId, payload);
      } else {
        await createBillingProviderOrganization(payload);
      }
      resetOrganizationForm();
      await loadProviderData();
    } catch (err) {
      setProviderError(err?.message || 'Failed to save billing-provider organization.');
    } finally {
      setOrganizationBusy(false);
    }
  };

  const handleAssignmentSubmit = async (e) => {
    e.preventDefault();
    setAssignmentBusy(true);
    setProviderError('');
    const payload = {
      ...assignmentForm,
      effective_start_at: new Date(assignmentForm.effective_start_at).toISOString(),
      effective_end_at: assignmentForm.effective_end_at ? new Date(assignmentForm.effective_end_at).toISOString() : null,
      service_scope: assignmentForm.service_scope,
    };
    try {
      if (editingAssignmentId) {
        await updateBillingProviderAssignment(editingAssignmentId, payload);
      } else {
        await createBillingProviderAssignment(payload);
      }
      resetAssignmentEditor();
      await loadProviderData();
    } catch (err) {
      setProviderError(err?.message || 'Failed to save billing-provider assignment.');
    } finally {
      setAssignmentBusy(false);
    }
  };

  const beginEditOrganization = (organization) => {
    setEditingOrganizationId(organization.id);
    setOrganizationForm({
      name: organization.name || '',
      organization_type: organization.organization_type || '',
      status: organization.status || 'ACTIVE',
      notes: organization.notes || '',
    });
  };

  const beginEditAssignment = (assignment) => {
    setEditingAssignmentId(assignment.id);
    setAssignmentForm({
      billing_provider_organization_id: assignment.billing_provider_organization_id,
      tenant_id: assignment.tenant_id,
      relationship_status: assignment.relationship_status || 'PENDING',
      effective_start_at: assignment.effective_start_at ? assignment.effective_start_at.slice(0, 16) : new Date().toISOString().slice(0, 16),
      effective_end_at: assignment.effective_end_at ? assignment.effective_end_at.slice(0, 16) : '',
      financials_enabled: Boolean(assignment.financials_enabled),
      service_scope: assignment.service_scope || [],
    });
  };

  const kpiCards = [
    {
      label: 'Total Monthly Revenue',
      value: fmtMoney(kpis.total_monthly_revenue),
      dot: COLORS.green,
    },
    {
      label: 'Outstanding Invoices',
      value:
        kpis.outstanding_invoice_count === null || kpis.outstanding_invoice_count === undefined
          ? '—'
          : `${kpis.outstanding_invoice_count} invoices`,
      sub: fmtMoney(kpis.outstanding_invoice_total) !== '—' ? `${fmtMoney(kpis.outstanding_invoice_total)} unresolved` : null,
      dot: COLORS.red,
    },
    {
      label: 'Active Agencies',
      value:
        kpis.active_agencies === null || kpis.active_agencies === undefined
          ? '—'
          : `${kpis.active_agencies} / ${kpis.licensed_agencies ?? '—'} Licensed`,
      dot: COLORS.teal,
    },
    {
      label: 'Avg. Rev Per Agency',
      value: fmtMoney(kpis.avg_revenue_per_agency),
      dot: COLORS.purple,
    },
  ];

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Billing &amp; Licensing Management</h1>
          <p style={S.pageSubtitle}>Manage subscriptions, invoicing, and payment status across all tenant agencies.</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select
            style={{ ...S.select }}
            value={selectedTenantId}
            onChange={(e) => setSelectedTenantId(e.target.value)}
          >
            <option value="">All Agencies</option>
            {tenantOptions.map((t) => (
              <option key={t.tenant_id} value={t.tenant_id}>{t.display_name || t.legal_name}</option>
            ))}
          </select>
          <button type="button" style={S.btn(COLORS.teal)} disabled title="Not available yet">
            + Generate Invoice
          </button>
        </div>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginBottom: 16 }}>
          {error}
        </div>
      ) : null}

      {/* KPI Row */}
      <div style={S.statsRow}>
        {kpiCards.map((k) => (
          <div key={k.label} style={S.statCard}>
            <div style={S.statDot(k.dot)} />
            <p style={S.statLabel}>{k.label}</p>
            <p style={S.statValue}>{loading ? '…' : k.value}</p>
            {k.sub ? <span style={S.statSub(k.dot)}>{k.sub}</span> : null}
          </div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveFilter(tab.key)}
            style={
              activeFilter === tab.key
                ? { ...S.btn(COLORS.teal), padding: '8px 16px', fontSize: 12 }
                : { ...S.btnOutline, padding: '8px 16px', fontSize: 12 }
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Client Billing Overview */}
      <div style={{ ...S.card, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={S.cardTitle}>Client Billing Overview</h3>
          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal }}>{filteredClients.length} agencies</span>
        </div>
        {loading ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading client billing overview…</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Agency Name', 'Plan Type', 'License Seats', 'Monthly Rate', 'Last Payment', 'Status', 'Balance Due', 'Actions'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredClients.map((c) => (
                <tr key={c.tenant_id}>
                  <td style={S.tableCellBold}>{c.agency_name}</td>
                  <td style={S.tableCell}>{c.plan_type}</td>
                  <td style={S.tableCell}>{c.seats_used ?? '—'} / {c.seats_licensed ?? '—'}</td>
                  <td style={S.tableCell}>{c.monthly_rate ? `${fmtMoney(c.monthly_rate)}/mo` : '—'}</td>
                  <td style={S.tableCell}>{fmtDate(c.last_payment_date)}</td>
                  <td style={{ ...S.tableCell, padding: '12px 0' }}>
                    <span style={S.badge((CLIENT_STATUS_COLOR[c.status] || COLORS.muted) + '22', CLIENT_STATUS_COLOR[c.status] || COLORS.muted)}>
                      {c.status}
                    </span>
                  </td>
                  <td style={S.tableCell}>{fmtMoney(c.balance_due)}</td>
                  <td style={S.tableCell}>
                    <span style={{ color: COLORS.teal, fontWeight: 600, cursor: 'pointer' }}>View</span>
                    {' · '}
                    <span style={{ color: COLORS.teal, fontWeight: 600, cursor: 'pointer' }}>
                      {c.status === 'TRIAL' ? 'Convert' : 'Invoice'}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredClients.length === 0 && (
                <tr>
                  <td style={S.tableCell} colSpan={8}>No billing data available yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Revenue Contribution by Agency */}
        <div style={S.card}>
          <h3 style={S.cardTitle}>Revenue Contribution by Agency</h3>
          {loading ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
          ) : revenueByAgency.length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>No revenue data available yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {revenueByAgency.map((r) => (
                <div key={r.tenant_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: COLORS.white }}>{r.agency_name}</span>
                    <span style={{ color: COLORS.muted, fontWeight: 600 }}>{fmtCompactMoney(r.amount)}</span>
                  </div>
                  <div style={{ background: COLORS.bg, borderRadius: 6, height: 6, overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${maxRevenue > 0 ? Math.round((Number(r.amount) / maxRevenue) * 100) : 0}%`,
                        background: COLORS.teal,
                        height: '100%',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent History & Upcoming Outstandings */}
        <div style={S.card}>
          <h3 style={S.cardTitle}>Recent History &amp; Upcoming Outstandings</h3>
          {loading ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
          ) : (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: recentPayments.length ? 16 : 0 }}>
                {recentPayments.map((p, i) => (
                  <div key={`${p.tenant_id}-${i}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: COLORS.white }}>{p.agency_name}</p>
                      <p style={{ margin: 0, fontSize: 11, color: COLORS.muted }}>{fmtDate(p.occurred_at)}</p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{fmtMoney(p.amount)}</span>
                      <span style={S.badge((PAYMENT_STATUS_COLOR[p.status] || COLORS.muted) + '22', PAYMENT_STATUS_COLOR[p.status] || COLORS.muted)}>
                        {p.status}
                      </span>
                    </div>
                  </div>
                ))}
                {recentPayments.length === 0 && (
                  <p style={{ color: COLORS.muted, fontSize: 13, margin: 0 }}>No recent payment history available yet.</p>
                )}
              </div>

              {upcomingOutstandings.length > 0 && (
                <>
                  <p style={S.sectionLabel}>Upcoming Outstandings</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
                    {upcomingOutstandings.map((o, i) => (
                      <div key={`${o.tenant_id}-${i}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: COLORS.white }}>{o.agency_name}</p>
                          <p style={{ margin: 0, fontSize: 11, color: COLORS.muted }}>Due: {fmtDate(o.due_date)}</p>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{fmtMoney(o.amount)}</span>
                          <span style={S.badge((OUTSTANDING_STATUS_COLOR[o.status] || COLORS.muted) + '22', OUTSTANDING_STATUS_COLOR[o.status] || COLORS.muted)}>
                            {o.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* License Allocation Summary */}
      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={S.cardTitle}>License Allocation Summary</h3>
          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal }}>
            {billingData?.total_seats_used ?? '—'} / {billingData?.total_seats_allocated ?? '—'} Seats Used
          </span>
        </div>
        {loading ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
        ) : (
          <>
            <div style={{ background: COLORS.bg, borderRadius: 6, height: 8, overflow: 'hidden', marginBottom: 20 }}>
              <div
                style={{
                  width:
                    billingData?.total_seats_allocated
                      ? `${Math.round((Number(billingData.total_seats_used || 0) / Number(billingData.total_seats_allocated)) * 100)}%`
                      : '0%',
                  background: COLORS.teal,
                  height: '100%',
                }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.max(licenseAllocations.length, 1)}, minmax(0, 1fr))`, gap: 16 }}>
              {licenseAllocations.length === 0 ? (
                <p style={{ color: COLORS.muted, fontSize: 13, gridColumn: '1 / -1' }}>No license allocation data available yet.</p>
              ) : (
                licenseAllocations.map((plan) => (
                  <div key={plan.plan_label} style={{ ...S.card, marginBottom: 0 }}>
                    <p style={S.statLabel}>{plan.plan_label}</p>
                    <p style={{ ...S.statValue, fontSize: 22 }}>{plan.seats_used} / {plan.seats_total} Seats</p>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>

      {providerError ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginTop: 24 }}>
          {providerError}
        </div>
      ) : null}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={S.cardTitle}>Billing Provider Organizations</h3>
            {providerLoading ? <span style={{ color: COLORS.muted, fontSize: 12 }}>Loading…</span> : null}
          </div>

          <form onSubmit={handleOrganizationSubmit} style={{ display: 'grid', gap: 10, marginBottom: 18 }}>
            <input
              style={S.searchBar}
              placeholder="Organization name"
              required
              value={organizationForm.name}
              onChange={(e) => setOrganizationForm((previous) => ({ ...previous, name: e.target.value }))}
            />
            <input
              style={S.searchBar}
              placeholder="Organization type"
              required
              value={organizationForm.organization_type}
              onChange={(e) => setOrganizationForm((previous) => ({ ...previous, organization_type: e.target.value }))}
            />
            <select
              style={S.select}
              value={organizationForm.status}
              onChange={(e) => setOrganizationForm((previous) => ({ ...previous, status: e.target.value }))}
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>
            <textarea
              style={{ ...S.searchBar, minHeight: 84, resize: 'vertical' }}
              placeholder="Notes (optional)"
              value={organizationForm.notes}
              onChange={(e) => setOrganizationForm((previous) => ({ ...previous, notes: e.target.value }))}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" style={S.btn(COLORS.teal)} disabled={organizationBusy}>
                {organizationBusy ? 'Saving…' : editingOrganizationId ? 'Update Organization' : 'Create Organization'}
              </button>
              {editingOrganizationId ? (
                <button type="button" style={{ ...S.btn(COLORS.border), color: COLORS.white }} onClick={resetOrganizationForm}>
                  Cancel Edit
                </button>
              ) : null}
            </div>
          </form>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {providerOrganizations.map((organization) => (
              <div key={organization.id} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div>
                    <div style={{ color: COLORS.white, fontWeight: 700 }}>{organization.name}</div>
                    <div style={{ color: COLORS.muted, fontSize: 12 }}>{organization.organization_type}</div>
                  </div>
                  <button type="button" style={{ ...S.btn(COLORS.border), color: COLORS.white }} onClick={() => beginEditOrganization(organization)}>
                    Edit
                  </button>
                </div>
                <div style={{ marginTop: 10, fontSize: 12, color: COLORS.muted }}>
                  Status: {organization.status} {organization.notes ? `• ${organization.notes}` : ''}
                </div>
              </div>
            ))}
            {!providerLoading && providerOrganizations.length === 0 ? (
              <p style={{ color: COLORS.muted, fontSize: 13, margin: 0 }}>No billing-provider organizations configured yet.</p>
            ) : null}
          </div>
        </div>

        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={S.cardTitle}>Agency Assignments</h3>
            <span style={{ color: COLORS.muted, fontSize: 12 }}>
              {selectedTenantId ? 'Filtered to selected agency' : 'All agencies'}
            </span>
          </div>

          <form onSubmit={handleAssignmentSubmit} style={{ display: 'grid', gap: 10, marginBottom: 18 }}>
            <select
              style={S.select}
              required
              value={assignmentForm.billing_provider_organization_id}
              onChange={(e) => setAssignmentForm((previous) => ({ ...previous, billing_provider_organization_id: e.target.value }))}
            >
              <option value="">Select billing provider</option>
              {providerOrganizations.map((organization) => (
                <option key={organization.id} value={organization.id}>{organization.name}</option>
              ))}
            </select>
            <select
              style={S.select}
              required
              value={assignmentForm.tenant_id}
              onChange={(e) => setAssignmentForm((previous) => ({ ...previous, tenant_id: e.target.value }))}
            >
              <option value="">Select agency</option>
              {tenantOptions.map((tenant) => (
                <option key={tenant.tenant_id} value={tenant.tenant_id}>{tenant.display_name || tenant.legal_name}</option>
              ))}
            </select>
            <select
              style={S.select}
              value={assignmentForm.relationship_status}
              onChange={(e) => setAssignmentForm((previous) => ({ ...previous, relationship_status: e.target.value }))}
            >
              <option value="PENDING">Pending</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="TERMINATED">Terminated</option>
            </select>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <input
                style={S.searchBar}
                type="datetime-local"
                required
                value={assignmentForm.effective_start_at}
                onChange={(e) => setAssignmentForm((previous) => ({ ...previous, effective_start_at: e.target.value }))}
              />
              <input
                style={S.searchBar}
                type="datetime-local"
                value={assignmentForm.effective_end_at}
                onChange={(e) => setAssignmentForm((previous) => ({ ...previous, effective_end_at: e.target.value }))}
              />
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: COLORS.white, fontSize: 13 }}>
              <input
                type="checkbox"
                checked={assignmentForm.financials_enabled}
                onChange={(e) => setAssignmentForm((previous) => ({ ...previous, financials_enabled: e.target.checked }))}
              />
              Assignment financials enabled
            </label>

            <div>
              <p style={{ ...S.sectionLabel, marginBottom: 8 }}>Service Scope</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {BILLING_PROVIDER_SERVICE_SCOPES.map((scope) => (
                  <label key={scope} style={{ display: 'flex', alignItems: 'center', gap: 8, color: COLORS.white, fontSize: 12 }}>
                    <input
                      type="checkbox"
                      checked={assignmentForm.service_scope.includes(scope)}
                      onChange={(e) => setAssignmentForm((previous) => ({
                        ...previous,
                        service_scope: e.target.checked
                          ? [...previous.service_scope, scope]
                          : previous.service_scope.filter((value) => value !== scope),
                      }))}
                    />
                    {humanizeScope(scope)}
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" style={S.btn(COLORS.teal)} disabled={assignmentBusy}>
                {assignmentBusy ? 'Saving…' : editingAssignmentId ? 'Update Assignment' : 'Create Assignment'}
              </button>
              {editingAssignmentId ? (
                <button type="button" style={{ ...S.btn(COLORS.border), color: COLORS.white }} onClick={resetAssignmentEditor}>
                  Cancel Edit
                </button>
              ) : null}
            </div>
          </form>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {visibleAssignments.map((assignment) => (
              <div key={assignment.id} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div>
                    <div style={{ color: COLORS.white, fontWeight: 700 }}>
                      {assignment.billing_provider_organization_name || 'Unknown Provider'} → {assignment.tenant_display_name || assignment.tenant_legal_name || 'Unknown Agency'}
                    </div>
                    <div style={{ color: COLORS.muted, fontSize: 12 }}>
                      {assignment.relationship_status} • Financials {assignment.financials_enabled ? 'ON' : 'OFF'}
                    </div>
                  </div>
                  <button type="button" style={{ ...S.btn(COLORS.border), color: COLORS.white }} onClick={() => beginEditAssignment(assignment)}>
                    Edit
                  </button>
                </div>
                <div style={{ marginTop: 10, fontSize: 12, color: COLORS.muted }}>
                  {fmtDateTime(assignment.effective_start_at)} → {assignment.effective_end_at ? fmtDateTime(assignment.effective_end_at) : 'Open-ended'}
                </div>
                <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {(assignment.service_scope || []).map((scope) => (
                    <span key={`${assignment.id}-${scope}`} style={S.badge(COLORS.teal + '22', COLORS.teal)}>
                      {humanizeScope(scope)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {!providerLoading && visibleAssignments.length === 0 ? (
              <p style={{ color: COLORS.muted, fontSize: 13, margin: 0 }}>No agency assignments configured yet.</p>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
