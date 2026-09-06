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
import { fetchOwnerTenants, fetchOwnerBillingLicensing } from '../../api/ownerAdmin';

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

export default function BillingLicensing() {
  const [tenantOptions, setTenantOptions] = useState([]);
  const [selectedTenantId, setSelectedTenantId] = useState('');
  const [billingData, setBillingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');

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
    </div>
  );
}
