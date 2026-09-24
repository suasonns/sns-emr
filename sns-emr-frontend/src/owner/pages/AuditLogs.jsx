import React, { useCallback, useEffect, useRef, useState } from 'react';
import { fetchOwnerAuditLogs, fetchOwnerTenants } from '../../api/ownerAdmin';
import { CATEGORY_META, SEVERITY_META } from '../auditCategories';
import AuditEventDrawer from '../components/AuditEventDrawer';
import { IconChevronDown } from '../shell/icons';

const DATE_RANGE_OPTIONS = [
  { label: 'Last 24h', hours: 24 },
  { label: 'Last 7 days', hours: 24 * 7 },
  { label: 'Last 30 days', hours: 24 * 30 },
  { label: 'Last 90 days', hours: 24 * 90 },
];

const PAGE_SIZE = 25;

function formatTimestamp(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

function toCsvValue(value) {
  const str = value === null || value === undefined ? '' : String(value);
  if (/[",\n]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
  return str;
}

function downloadCsv(rows) {
  const header = ['Timestamp', 'Category', 'Risk', 'Action', 'Actor', 'Tenant', 'Target', 'IP Address', 'Event ID', 'Request ID'];
  const lines = [header.map(toCsvValue).join(',')];
  rows.forEach((l) => {
    lines.push(
      [l.created_at, l.category, l.severity, l.action, l.user_display, l.tenant_name, l.description || '', l.ip_address || '', l.log_id, l.request_id || '']
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

function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

function CategoryBadge({ category }) {
  const meta = CATEGORY_META.find((c) => c.key === category);
  if (!meta) return <span className="text-text-tertiary text-[11px]">{category || '—'}</span>;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide font-mono uppercase"
      style={{ background: meta.bg, color: meta.color }}
    >
      {category}
    </span>
  );
}

function SeverityBadge({ severity }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.INFO;
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold ${meta.className}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
      {meta.label}
    </span>
  );
}

function SummaryChips({ counts, activeCategory, onToggle }) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {CATEGORY_META.map((c) => {
        const active = activeCategory === c.key;
        return (
          <button
            key={c.key}
            type="button"
            onClick={() => onToggle(active ? null : c.key)}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border text-[11px] font-semibold transition-colors ${
              active ? 'border-ai bg-ai/10 text-text-primary' : 'border-sns-border bg-sns-elevated text-text-secondary hover:border-ai/40'
            }`}
          >
            <span>{c.icon}</span>
            <span>{c.label}:</span>
            <span className="font-mono font-bold text-text-primary">{counts[c.key] ?? 0}</span>
          </button>
        );
      })}
    </div>
  );
}

function FilterDropdown({ label, value, onChange, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none pr-8 pl-3 py-2 h-9 rounded-lg border border-sns-border bg-sns-elevated text-[12px] text-text-primary cursor-pointer focus:outline-none focus:border-ai/50 transition-colors"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{`${label}: ${o.label}`}</option>
        ))}
      </select>
      <IconChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-tertiary" />
    </div>
  );
}

/**
 * SNS Audit Logs -- platform-wide activity/security/compliance/governance
 * trail. Renders inside OwnerShell (same sidebar/topbar/theme as every
 * other owner-portal page) using real data from GET /api/owner/audit-logs
 * -- no mock data, no standalone app shell. Category and Risk are the
 * backend's centralized, authoritative classifications; see
 * auditCategories.js and AuditEventDrawer.jsx for exactly which fields are
 * real audit_logs columns vs. derived from event_metadata (including
 * Affected Permissions, a role-capability diff reusing SNS Staff &
 * Access's authoritative RBAC source).
 */
export default function AuditLogs() {
  const [tenants, setTenants] = useState([]);
  const [logs, setLogs] = useState([]);
  const [categoryCounts, setCategoryCounts] = useState({});
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

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

  const handleClearFilters = () => {
    setSearchInput('');
    setSearch('');
    setCategory(null);
    setTenantId('');
    setRangeIdx(0);
    setOffset(0);
  };

  const rangeStart = totalCount === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, totalCount);
  const hasActiveFilters = Boolean(search || category || tenantId || rangeIdx !== 0);

  // Keep the Event Details workspace populated by default (mirrors the
  // persistent detail panel pattern used elsewhere in the Owner Platform,
  // e.g. Tenant Management's "Selected Tenant" panel) instead of only
  // appearing after a click.
  useEffect(() => {
    if (!loading && logs.length > 0 && !logs.some((l) => l.log_id === selectedEvent?.log_id)) {
      setSelectedEvent(logs[0]);
    }
    if (!loading && logs.length === 0 && selectedEvent) {
      setSelectedEvent(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, logs]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Audit Logs</h1>
          <p className="text-sm text-text-secondary mt-1">
            Platform-wide activity, security, compliance, and governance trail.
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || totalCount === 0}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-sns-border bg-sns-elevated text-text-secondary text-xs font-semibold hover:border-ai/40 hover:text-text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            📄 {exporting ? 'Exporting…' : 'Export Report'}
          </button>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-ai text-ai-on text-xs font-bold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            🔄 {loading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="px-3 py-2.5 rounded-lg bg-status-critical/10 border border-status-critical/20 text-status-critical text-xs">
          {error}
        </div>
      )}

      {/* Command-center layout: investigation table on the left, a
          permanent Event Details workspace on the right -- matching the
          persistent detail-panel pattern used elsewhere in the Owner
          Platform (e.g. Tenant Management's "Selected Tenant" panel)
          instead of an on-click-only overlay. */}
      <div className="flex items-start gap-6">
        <div className="flex-1 min-w-0 flex flex-col gap-4">
          <SummaryChips counts={categoryCounts} activeCategory={category} onToggle={(v) => { setCategory(v); setOffset(0); }} />

          {/* Toolbar */}
          <div className="flex flex-wrap items-center gap-2 px-4 py-3 rounded-xl border border-sns-border bg-sns-card">
            <div className="relative flex-1 min-w-[220px] max-w-[340px]">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary text-sm">🔍</span>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search events, users, actions, IPs..."
                className="w-full h-9 pl-9 pr-3 rounded-lg border border-sns-border bg-sns-elevated text-[12px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-ai/50 transition-colors"
              />
            </div>
            <FilterDropdown
              label="Category"
              value={category || ''}
              onChange={(v) => { setCategory(v || null); setOffset(0); }}
              options={[{ value: '', label: 'All' }, ...CATEGORY_META.map((c) => ({ value: c.key, label: c.label }))]}
            />
            <FilterDropdown
              label="Tenant"
              value={tenantId}
              onChange={(v) => { setTenantId(v); setOffset(0); }}
              options={[{ value: '', label: 'All' }, ...tenants.map((t) => ({ value: t.tenant_id, label: t.display_name }))]}
            />
            <FilterDropdown
              label="Date Range"
              value={rangeIdx}
              onChange={(v) => { setRangeIdx(Number(v)); setOffset(0); }}
              options={DATE_RANGE_OPTIONS.map((r, i) => ({ value: i, label: r.label }))}
            />
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="text-xs font-semibold text-ai hover:underline ml-1"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Table -- semantic <table> with fixed column widths via <colgroup>.
              (A CSS-grid div layout with arbitrary grid-cols-[...] classes was
              tried first but produced unreliable column tracks; a real table
              is the stable, standards-based layout the browser guarantees.) */}
          <div className="rounded-xl border border-sns-border bg-sns-card overflow-hidden overflow-x-auto">
            <table className="w-full border-collapse table-fixed text-text-primary">
              <colgroup>
                <col style={{ width: '150px' }} />
                <col style={{ width: '160px' }} />
                <col />
                <col style={{ width: '200px' }} />
                <col style={{ width: '110px' }} />
                <col style={{ width: '90px' }} />
                <col style={{ width: '32px' }} />
              </colgroup>
              <thead>
                <tr className="bg-sns-elevated border-b border-sns-border">
                  {['Timestamp', 'Actor', 'Action', 'Target', 'Category', 'Risk', ''].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="text-[10px] font-bold uppercase tracking-wider text-text-tertiary font-mono text-left px-4 py-2.5"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading && logs.length === 0 ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="bg-sns-card">
                      <td colSpan={7} className="px-4 py-1.5">
                        <div className="h-8 rounded-md bg-sns-elevated animate-pulse" style={{ animationDelay: `${i * 50}ms` }} />
                      </td>
                    </tr>
                  ))
                ) : logs.length === 0 ? (
                  <tr className="bg-sns-card">
                    <td colSpan={7} className="text-center py-16 px-6">
                      <div className="flex flex-col items-center">
                        <div className="text-4xl mb-3 opacity-50">🔍</div>
                        <h3 className="text-base font-bold text-text-primary mb-1">No audit events found</h3>
                        <p className="text-xs text-text-secondary max-w-xs mb-4">
                          Try adjusting your filters or date range to find audit events.
                        </p>
                        {hasActiveFilters && (
                          <button
                            type="button"
                            onClick={handleClearFilters}
                            className="px-4 py-2 rounded-lg bg-ai text-ai-on text-xs font-bold hover:opacity-90 transition-opacity"
                          >
                            Clear Filters
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  logs.map((l) => {
                    const selected = selectedEvent?.log_id === l.log_id;
                    return (
                      <tr
                        key={l.log_id}
                        tabIndex={0}
                        role="button"
                        aria-selected={selected}
                        onClick={() => setSelectedEvent(l)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedEvent(l);
                          }
                        }}
                        className={`cursor-pointer border-b border-sns-border-subtle transition-colors focus:outline-none ${
                          selected
                            ? 'bg-ai/10 border-l-[3px] border-l-ai'
                            : 'bg-sns-card hover:bg-sns-border-subtle/40'
                        }`}
                      >
                        <td className="px-4 py-2.5 text-[11px] font-mono text-text-tertiary whitespace-nowrap">
                          {formatTimestamp(l.created_at)}
                        </td>
                        <td className="px-4 py-2.5 text-[12px] font-semibold text-text-primary truncate max-w-0">
                          {l.user_display}
                        </td>
                        <td className="px-4 py-2.5 text-[11px] font-mono text-text-primary truncate max-w-0" title={l.action}>
                          {labelize(l.action)}
                        </td>
                        <td
                          className="px-4 py-2.5 text-[12px] text-text-secondary truncate max-w-0"
                          title={l.description || ''}
                        >
                          {l.description || `${l.entity_type || ''} ${l.entity_id || ''}`.trim() || '—'}
                        </td>
                        <td className="px-4 py-2.5">
                          <CategoryBadge category={l.category} />
                        </td>
                        <td className="px-4 py-2.5">
                          <SeverityBadge severity={l.severity} />
                        </td>
                        <td className="px-4 py-2.5 text-text-tertiary">›</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>

            <div className="flex items-center justify-between px-4 py-3 border-t border-sns-border">
              <span className="text-xs text-text-tertiary">
                {totalCount === 0
                  ? 'Showing 0 of 0 platform logs'
                  : `Showing ${rangeStart}-${rangeEnd} of ${totalCount.toLocaleString()} platform logs`}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0 || loading}
                  className="px-3 py-1.5 rounded-lg border border-sns-border text-text-secondary text-[11px] font-semibold disabled:opacity-40 hover:border-ai/40 transition-colors"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={rangeEnd >= totalCount || loading}
                  className="px-3 py-1.5 rounded-lg bg-ai text-ai-on text-[11px] font-bold disabled:opacity-40 transition-opacity"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="w-[420px] shrink-0 sticky top-6 h-[calc(100vh-140px)]">
          <AuditEventDrawer
            event={selectedEvent}
            onClose={() => setSelectedEvent(null)}
            onSelectRelated={(evt) => setSelectedEvent(evt)}
          />
        </div>
      </div>
    </div>
  );
}
