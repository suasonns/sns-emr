import React, { useCallback, useEffect, useRef, useState } from 'react';
import { COLORS, S } from '../design';
import { fetchOwnerAuditLogs, fetchOwnerTenants } from '../../api/ownerAdmin';

const CATEGORY_META = [
  { key: 'AUTH', icon: '🔐', label: 'AUTH EVENT TYPES', bg: '#3b82f622', color: COLORS.blue },
  { key: 'DATA', icon: '📂', label: 'DATA ACCESS', bg: '#8b5cf622', color: COLORS.purple },
  { key: 'ADMIN', icon: '⚙️', label: 'ADMIN ACTIONS', bg: '#10b7a222', color: COLORS.teal },
  { key: 'BILLING', icon: '💳', label: 'BILLING TRANSACTIONS', bg: '#ec489922', color: COLORS.pink },
  { key: 'COMPLIANCE', icon: '⚠️', label: 'COMPLIANCE AUDITS', bg: '#f9731622', color: COLORS.orange },
];

const CAT_COLORS = Object.fromEntries(CATEGORY_META.map((c) => [c.key, { bg: c.bg, color: c.color }]));

const DATE_RANGE_OPTIONS = [
  { label: 'Last 24 Hours', hours: 24 },
  { label: 'Last 7 Days', hours: 24 * 7 },
  { label: 'Last 30 Days', hours: 24 * 30 },
  { label: 'Last 90 Days', hours: 24 * 90 },
];

const PAGE_SIZE = 25;

function formatTimestamp(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    month: 'short',
    day: 'numeric',
  });
}

function toCsvValue(value) {
  const str = value === null || value === undefined ? '' : String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function downloadCsv(rows) {
  const header = ['Timestamp', 'Category', 'Action', 'User', 'Tenant', 'Detail', 'IP Address'];
  const lines = [header.map(toCsvValue).join(',')];
  rows.forEach((l) => {
    lines.push(
      [l.created_at, l.category, l.action, l.user_display, l.tenant_name, l.description || '', l.ip_address || '']
        .map(toCsvValue)
        .join(',')
    );
  });
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `platform-audit-log-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function AuditLogs() {
  const [tenants, setTenants] = useState([]);
  const [logs, setLogs] = useState([]);
  const [categoryCounts, setCategoryCounts] = useState({});
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState(null);
  const [tenantId, setTenantId] = useState('');
  const [rangeIdx, setRangeIdx] = useState(0);
  const [offset, setOffset] = useState(0);

  const debounceRef = useRef(null);

  useEffect(() => {
    fetchOwnerTenants()
      .then((res) => setTenants(res.tenants || []))
      .catch(() => setTenants([]));
  }, []);

  // Debounce free-text search -> committed `search` state (resets pagination).
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setOffset(0);
      setSearch(searchInput.trim());
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  const hours = DATE_RANGE_OPTIONS[rangeIdx].hours;

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    fetchOwnerAuditLogs({
      search: search || undefined,
      category: category || undefined,
      tenantId: tenantId || undefined,
      hours,
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => {
        setLogs(res.logs);
        setTotalCount(res.total_count);
        setCategoryCounts(res.category_counts);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load audit logs'))
      .finally(() => setLoading(false));
  }, [search, category, tenantId, hours, offset]);

  useEffect(() => {
    load();
  }, [load]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await fetchOwnerAuditLogs({
        search: search || undefined,
        category: category || undefined,
        tenantId: tenantId || undefined,
        hours,
        limit: 5000,
        offset: 0,
      });
      downloadCsv(res.logs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const rangeStart = totalCount === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, totalCount);

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Audit Logs</h1>
          <p style={S.pageSubtitle}>Platform-wide activity trail — all user actions, system events, and compliance records</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button style={S.btnOutline} onClick={handleExport} disabled={exporting || totalCount === 0}>
            📋 {exporting ? 'EXPORTING…' : 'EXPORT REPORT'}
          </button>
          <button style={S.btn(COLORS.teal)} onClick={load} disabled={loading}>
            {loading ? 'REFRESHING…' : 'REFRESH ENGINE'}
          </button>
        </div>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13 }}>{error}</div>
      ) : null}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input
            style={S.searchBar}
            placeholder="Search user names, actions, IP addresses..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Category:</span>
          <select
            style={S.select}
            value={category || ''}
            onChange={(e) => {
              setCategory(e.target.value || null);
              setOffset(0);
            }}
          >
            <option value="">All Categories</option>
            {CATEGORY_META.map((c) => (
              <option key={c.key} value={c.key}>{c.label}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Tenant:</span>
          <select
            style={S.select}
            value={tenantId}
            onChange={(e) => {
              setTenantId(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All Active Tenants</option>
            {tenants.map((t) => (
              <option key={t.tenant_id} value={t.tenant_id}>{t.display_name}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Date Range:</span>
          <select
            style={S.select}
            value={rangeIdx}
            onChange={(e) => {
              setRangeIdx(Number(e.target.value));
              setOffset(0);
            }}
          >
            {DATE_RANGE_OPTIONS.map((r, i) => (
              <option key={r.label} value={i}>{r.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Pills */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        {CATEGORY_META.map((c) => {
          const active = category === c.key;
          const count = categoryCounts[c.key] ?? 0;
          return (
            <div
              key={c.key}
              onClick={() => {
                setCategory(active ? null : c.key);
                setOffset(0);
              }}
              style={{
                flex: 1,
                background: COLORS.card,
                border: `1px solid ${active ? c.color : COLORS.border}`,
                borderRadius: 10,
                padding: '14px 16px',
                textAlign: 'center',
                cursor: 'pointer',
                boxShadow: active ? `0 0 0 1px ${c.color}` : 'none',
              }}
            >
              <span style={{ fontSize: 18 }}>{c.icon}</span>
              <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, margin: '6px 0 4px', letterSpacing: 0.3 }}>{c.label}</p>
              <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.white, margin: 0 }}>{count}</p>
            </div>
          );
        })}
      </div>

      {/* Logs Table */}
      <div style={S.card}>
        {loading && logs.length === 0 ? (
          <p style={{ fontSize: 13, color: COLORS.muted, padding: '20px 0', textAlign: 'center' }}>Loading audit trail…</p>
        ) : logs.length === 0 ? (
          <p style={{ fontSize: 13, color: COLORS.muted, padding: '20px 0', textAlign: 'center' }}>
            No audit events match these filters in the selected window.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['TIMESTAMP', 'CATEGORY', 'ACTION', 'USER', 'TENANT', 'DETAIL DESCRIPTION', 'IP ADDRESS'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => {
                const catStyle = CAT_COLORS[l.category] || CAT_COLORS.ADMIN;
                return (
                  <tr key={l.log_id}>
                    <td style={S.tableCell}>{formatTimestamp(l.created_at)}</td>
                    <td style={{ ...S.tableCell }}>
                      <span style={S.badge(catStyle.bg, catStyle.color)}>{l.category}</span>
                    </td>
                    <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{l.action}</td>
                    <td style={S.tableCell}>{l.user_display}</td>
                    <td style={S.tableCell}>{l.tenant_name}</td>
                    <td style={{ ...S.tableCell, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={l.description || ''}>
                      {l.description || `${l.entity_type || ''} ${l.entity_id || ''}`.trim() || '—'}
                    </td>
                    <td style={S.tableCell}>{l.ip_address || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ fontSize: 12, color: COLORS.muted }}>
            {totalCount === 0
              ? 'Showing 0 of 0 platform logs'
              : `Showing ${rangeStart}-${rangeEnd} of ${totalCount.toLocaleString()} platform logs`}
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              style={{ ...S.btnOutline, padding: '6px 14px', fontSize: 11, opacity: offset === 0 ? 0.5 : 1 }}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={offset === 0 || loading}
            >
              Previous
            </button>
            <button
              style={{ ...S.btn(COLORS.teal), padding: '6px 14px', fontSize: 11, opacity: rangeEnd >= totalCount ? 0.5 : 1 }}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              disabled={rangeEnd >= totalCount || loading}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
