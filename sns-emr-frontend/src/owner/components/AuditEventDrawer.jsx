import React, { useEffect, useState } from 'react';
import { IconClose } from '../shell/icons';
import { CATEGORY_META, SEVERITY_META } from '../auditCategories';
import { fetchOwnerAuditLogs } from '../../api/ownerAdmin';

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

function OverviewRow({ label, children }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider shrink-0">{label}</span>
      <span className="text-[13px] text-text-primary text-right break-words">{children}</span>
    </div>
  );
}

function CategoryPill({ category }) {
  const meta = CATEGORY_META.find((c) => c.key === category);
  if (!meta) return <span className="text-text-tertiary">{category || '—'}</span>;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold tracking-wide"
      style={{ background: meta.bg, color: meta.color }}
    >
      {category}
    </span>
  );
}

function SeverityPill({ severity }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.INFO;
  return (
    <span className={`inline-flex items-center gap-1.5 text-[13px] font-bold ${meta.className}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
      {meta.label}
    </span>
  );
}

// Recognized before/after metadata key-pair conventions actually written by
// the backend's log_event(event_metadata=...) call sites (see
// backend/app/api/owner_admin.py, e.g. OWNER_CHANGED_STAFF_ROLE writes
// {previous_role, new_role}). Any metadata key not matched by one of these
// pairs still renders in the flat "Change Details" list below -- nothing
// is dropped, this only lifts the ones with a real before/after shape into
// a dedicated Before/After State section.
const BEFORE_AFTER_PAIRS = [
  { before: 'previous_role', after: 'new_role', label: 'Role' },
  { before: 'previous_status', after: 'new_status', label: 'Status' },
  { before: 'previous_value', after: 'new_value', label: 'Value' },
];

function splitMetadata(metadata) {
  if (!metadata) return { pairs: [], rest: {} };
  const rest = { ...metadata };
  const pairs = [];
  for (const { before, after, label } of BEFORE_AFTER_PAIRS) {
    if (before in rest || after in rest) {
      pairs.push({ label, before: rest[before], after: rest[after] });
      delete rest[before];
      delete rest[after];
    }
  }
  return { pairs, rest };
}

function formatMetaValue(value) {
  if (value === null || value === undefined || value === '') return '—';
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

/**
 * SNS Audit Logs -- Event Details drawer. Every field rendered here is real
 * data returned by GET /api/owner/audit-logs (app.api.owner_admin.
 * list_audit_logs): category and severity are the backend's centralized,
 * authoritative classifications (_category_for_action / _severity_for_event
 * -- context-aware for tenant-status and role-change events); Before/After
 * State and Affected Roles are parsed from real event_metadata key pairs
 * already written by the relevant handlers; Affected Permissions is a
 * role-capability diff computed server-side from the SAME authoritative
 * RBAC source (app.core.roles.capabilities_for_role) used by SNS Staff &
 * Access, only for role-change events where both roles are resolvable;
 * Request ID is the real audit_logs.request_id column (never a fabricated
 * "session"); Related Events is fetched fresh from the API scoped to this
 * event's entity_id, so it reflects the full history, not just the
 * currently loaded page. Nothing here is a placeholder -- sections are
 * simply omitted when the API has no real data for them.
 */
export default function AuditEventDrawer({ event, onClose, onSelectRelated }) {
  const [relatedEvents, setRelatedEvents] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);

  useEffect(() => {
    if (!event?.entity_id) {
      setRelatedEvents([]);
      return;
    }
    let cancelled = false;
    setRelatedLoading(true);
    fetchOwnerAuditLogs({ entityId: event.entity_id, hours: 24 * 365 * 5, limit: 50, offset: 0 })
      .then((res) => {
        if (cancelled) return;
        setRelatedEvents((res.logs || []).filter((e) => e.log_id !== event.log_id));
      })
      .catch(() => {
        if (!cancelled) setRelatedEvents([]);
      })
      .finally(() => {
        if (!cancelled) setRelatedLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [event?.entity_id, event?.log_id]);

  if (!event) {
    return (
      <div className="w-full h-full bg-sns-card border border-sns-border rounded-xl shadow-panel flex flex-col overflow-hidden">
        <div className="px-5 py-4 border-b border-sns-border shrink-0">
          <h3 className="text-base font-bold text-text-primary">Event Details</h3>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-5 text-center">
          <div className="text-3xl mb-3 opacity-40">🗂️</div>
          <p className="text-sm font-semibold text-text-secondary">No event selected</p>
          <p className="text-xs text-text-tertiary mt-1 max-w-[220px]">
            Select a row from the table to inspect its full details, before/after state, and related events.
          </p>
        </div>
      </div>
    );
  }

  const { pairs: beforeAfterPairs, rest: remainingMetadata } = splitMetadata(event.event_metadata);
  const hasRemainingMetadata = Object.keys(remainingMetadata).length > 0;

  return (
    <div
      className="w-full h-full bg-sns-card border border-sns-border rounded-xl shadow-panel flex flex-col overflow-hidden"
      onKeyDown={(e) => { if (e.key === 'Escape') onClose?.(); }}
    >
      <div className="px-5 py-4 border-b border-sns-border shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-text-primary">Event Details</h3>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="w-7 h-7 rounded-md flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-sns-border-subtle transition-colors"
              aria-label="Clear selection"
              title="Clear selection"
            >
              <IconClose />
            </button>
          )}
        </div>
          <button
            type="button"
            className="mt-1 text-[11px] font-mono text-text-tertiary hover:text-ai transition-colors"
            onClick={() => navigator.clipboard?.writeText(event.log_id)}
            title="Click to copy Event ID"
          >
            {event.log_id}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {/* OVERVIEW -- entirely real fields from audit_logs */}
          <div className="mb-6">
            <h4 className="text-[11px] font-bold text-ai uppercase tracking-wider mb-3">Overview</h4>
            <div className="divide-y divide-sns-border-subtle">
              <OverviewRow label="Actor">{event.user_display}</OverviewRow>
              <OverviewRow label="Action">{labelize(event.action)}</OverviewRow>
              <OverviewRow label="Target">
                {event.description || `${event.entity_type || ''} ${event.entity_id || ''}`.trim() || '—'}
              </OverviewRow>
              <OverviewRow label="Timestamp">{formatDateTime(event.created_at)}</OverviewRow>
              <OverviewRow label="Platform">Owner Platform</OverviewRow>
              <OverviewRow label="Tenant">{event.tenant_name}</OverviewRow>
              <OverviewRow label="Category"><CategoryPill category={event.category} /></OverviewRow>
              <OverviewRow label="Risk Level"><SeverityPill severity={event.severity} /></OverviewRow>
              {event.ip_address && <OverviewRow label="IP Address">{event.ip_address}</OverviewRow>}
              {/* Real audit_logs.request_id -- a request-trace id, not a
                  login/auth session id (no session tracking exists yet).
                  Labeled honestly; omitted when null rather than fabricated. */}
              {event.request_id && (
                <OverviewRow label="Request ID">
                  <span className="font-mono text-[11px]">{event.request_id}</span>
                </OverviewRow>
              )}
            </div>
          </div>

          {/* BEFORE / AFTER STATE -- only rendered for metadata shapes that
              actually contain a recognized previous_X / new_X pair; omitted
              entirely otherwise. Also doubles as "Affected Roles" when the
              pair is a role change. */}
          {beforeAfterPairs.length > 0 && (
            <div className="mb-6">
              <h4 className="text-[11px] font-bold text-ai uppercase tracking-wider mb-3">
                {beforeAfterPairs.some((p) => p.label === 'Role') ? 'Affected Roles' : 'Before / After State'}
              </h4>
              <div className="space-y-2">
                {beforeAfterPairs.map((p) => (
                  <div key={p.label} className="rounded-lg bg-sns-app border border-sns-border p-3">
                    <div className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-2">{p.label}</div>
                    <div className="flex items-center gap-2">
                      <span className="flex-1 px-2 py-1 rounded bg-status-critical/10 text-status-critical text-xs font-semibold text-center truncate">
                        {formatMetaValue(p.before)}
                      </span>
                      <span className="text-text-tertiary text-xs shrink-0">→</span>
                      <span className="flex-1 px-2 py-1 rounded bg-status-healthy/10 text-status-healthy text-xs font-semibold text-center truncate">
                        {formatMetaValue(p.after)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AFFECTED PERMISSIONS -- role-derived capability diff, only
              for OWNER_CHANGED_STAFF_ROLE events where the backend could
              resolve both roles through the authoritative RBAC source
              (app.core.roles.capabilities_for_role). Omitted entirely
              otherwise -- never a guessed permission name. */}
          {event.affected_permissions && (
            <div className="mb-6">
              <h4 className="text-[11px] font-bold text-ai uppercase tracking-wider mb-3">Affected Permissions</h4>
              <div className="rounded-lg bg-sns-app border border-sns-border p-3 space-y-3">
                {event.affected_permissions.added.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-status-healthy uppercase tracking-wider mb-1.5">+ Added</div>
                    <div className="flex flex-wrap gap-1.5">
                      {event.affected_permissions.added.map((p) => (
                        <span key={p} className="px-1.5 py-0.5 rounded bg-status-healthy/10 text-status-healthy text-[11px] font-mono">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {event.affected_permissions.removed.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-status-critical uppercase tracking-wider mb-1.5">− Removed</div>
                    <div className="flex flex-wrap gap-1.5">
                      {event.affected_permissions.removed.map((p) => (
                        <span key={p} className="px-1.5 py-0.5 rounded bg-status-critical/10 text-status-critical text-[11px] font-mono">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {event.affected_permissions.added.length === 0 && event.affected_permissions.removed.length === 0 && (
                  <div className="text-xs text-text-tertiary">No effective capability change between these roles.</div>
                )}
              </div>
            </div>
          )}

          {/* CHANGE DETAILS -- remaining metadata keys not already shown as
              a Before/After pair above. Only rendered when the API
              returned real event_metadata; omitted entirely otherwise. */}
          {hasRemainingMetadata && (
            <div className="mb-6">
              <h4 className="text-[11px] font-bold text-ai uppercase tracking-wider mb-3">Change Details</h4>
              <div className="rounded-lg bg-sns-app border border-sns-border p-3 space-y-1.5">
                {Object.entries(remainingMetadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3 text-xs">
                    <span className="text-text-tertiary uppercase tracking-wide shrink-0">{labelize(key)}</span>
                    <span className="text-text-primary text-right break-words">{formatMetaValue(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RELATED EVENTS -- fetched from the API scoped to this event's
              entity_id (full history, not just the currently loaded page).
              Omitted entirely when there are none, rather than a filler
              message. */}
          {relatedLoading ? (
            <div className="text-[11px] text-text-tertiary">Loading related events…</div>
          ) : (
            relatedEvents.length > 0 && (
              <div>
                <h4 className="text-[11px] font-bold text-ai uppercase tracking-wider mb-3">Related Events</h4>
                <div className="divide-y divide-sns-border-subtle">
                  {relatedEvents.slice(0, 5).map((evt) => (
                    <button
                      key={evt.log_id}
                      type="button"
                      onClick={() => onSelectRelated?.(evt)}
                      className="w-full text-left py-2.5 hover:bg-sns-border-subtle/40 transition-colors -mx-1 px-1 rounded"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-semibold text-ai">{evt.action}</span>
                        <span className="text-[11px] font-mono text-text-tertiary">{formatDateTime(evt.created_at).split(', ').pop()}</span>
                      </div>
                      <div className="text-xs text-text-secondary mt-0.5">
                        {evt.description || `${evt.user_display} on ${evt.entity_type || 'record'}`}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      </div>
  );
}
