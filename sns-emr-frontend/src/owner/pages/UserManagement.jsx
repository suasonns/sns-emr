import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchOwnerPlatformUsers,
  fetchOwnerAuditLogs,
  resetOwnerPlatformUserPassword,
  setOwnerPlatformUserActive,
} from '../../api/ownerAdmin';
import { IconChevronDown, IconClose, IconPlus } from '../shell/icons';
import { accessLevelLabel } from '../accessLevels';
import AddStaffModal from '../components/AddStaffModal';
import StaffProfileDrawer from '../components/StaffProfileDrawer';

const SCOPES = [
  { key: 'HUMAN', label: 'Human Staff' },
  { key: 'SERVICE', label: 'Service Accounts' },
  { key: 'API', label: 'API Identities' },
  { key: 'AUDIT', label: 'Audit' },
];

/**
 * SNS Staff & Access — Platform Owner User Management (Phase UM-2A).
 *
 * SCOPE (authoritative): SNS Hospice Solutions platform staff ONLY
 * (app.core.roles.PLATFORM_ROLES on the backend). This page never lists,
 * enables/disables, or resets the password of a tenant-agency or
 * billing-organization user. The backend (/api/owner/users) enforces this
 * same scope server-side.
 *
 * Every KPI, filter, column, and action below is wired to the real
 * /api/owner/users backend (account_type, department, allowed_actions,
 * actor_capabilities, capabilities-per-role are all real, backend-derived
 * fields -- nothing here is fabricated). Sections not yet backed by a
 * real service (Service Account/API Client management workflows,
 * Invitation lifecycle, Security Monitoring, Workforce Analytics,
 * Privileged Access Review) are intentionally deferred to later phases
 * per the approved SNS Staff & Access roadmap and are not represented as
 * complete here.
 */

const PAGE_SIZE = 25;

// Real, backend-derived platform_staff_status (ACTIVE/SUSPENDED/
// DISABLED/REMOVED) -- never independently derived from `active` alone,
// so Suspended and Removed are visually distinct from a plain Disabled.
const STATUS_BADGE_CLASS = {
  ACTIVE: 'bg-status-healthy/15 text-status-healthy',
  SUSPENDED: 'bg-status-high/15 text-status-high',
  DISABLED: 'bg-status-critical/15 text-status-critical',
  REMOVED: 'bg-text-tertiary/15 text-text-tertiary',
};

function roleLabel(role) {
  if (!role) return 'Unknown';
  return role
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}


function formatLastLogin(iso) {
  if (!iso) return 'Never';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return 'Never';
  const diffMs = Date.now() - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'Just Now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 31) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

function KpiCard({ label, value, subtitle, subtitleClassName, dotClassName }) {
  return (
    <div className="rounded-xl border border-ai/30 bg-gradient-to-b from-ai-gradient-start to-ai-bg/60 p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono font-bold text-text-secondary tracking-wide">{label}</span>
        <span className={`w-1.5 h-1.5 rounded-full ${dotClassName}`} />
      </div>
      <p className="text-[28px] font-bold text-text-primary leading-tight">{value}</p>
      <p className={`text-xs ${subtitleClassName}`}>{subtitle}</p>
    </div>
  );
}

const EMPTY_STATS = {
  total_users: 0,
  active_users: 0,
  active_now: 0,
  privileged_accounts: 0,
  disabled_users: 0,
  active_owners: 0,
  service_accounts: 0,
  automation_accounts: 0,
  api_clients: 0,
};

export default function UserManagement() {
  const [scope, setScope] = useState('HUMAN'); // 'HUMAN' | 'SERVICE' | 'API' | 'AUDIT'

  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [accessLevelsByRole, setAccessLevelsByRole] = useState({});
  const [availableDepartments, setAvailableDepartments] = useState([]);
  const [availablePlatforms, setAvailablePlatforms] = useState(['SNS Hospice Solutions']);
  const [jobTitlesByDepartment, setJobTitlesByDepartment] = useState({});
  const [availableAccountTypes, setAvailableAccountTypes] = useState([]);
  const [actorCapabilities, setActorCapabilities] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [department, setDepartment] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const [actioningId, setActioningId] = useState(null);
  const [resetResult, setResetResult] = useState(null);

  const [modalMode, setModalMode] = useState(null); // 'add' | 'invite' | null
  const [drawerUserId, setDrawerUserId] = useState(null);

  // Identity-scoped audit feed for the Audit tab -- distinct from (and a
  // subset of) the platform-wide standalone Audit Logs page; scoped
  // server-side to entity_type='user' so it only ever shows SNS staff/
  // platform-identity lifecycle events.
  const [auditEvents, setAuditEvents] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState('');

  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setOffset(0);
      setSearch(searchInput.trim());
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  const load = useCallback(() => {
    if (scope === 'AUDIT') return;
    setLoading(true);
    setError('');
    fetchOwnerPlatformUsers({
      search: search || undefined,
      role: role || undefined,
      status: status || undefined,
      department: department || undefined,
      accountType: scope === 'HUMAN' ? 'HUMAN_STAFF' : scope === 'API' ? 'API_CLIENT' : undefined,
      accountTypes: scope === 'SERVICE' ? ['SERVICE_ACCOUNT', 'AUTOMATION_ACCOUNT'] : undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => {
        setUsers(res.users);
        setTotalCount(res.total_count);
        setStats(res.stats);
        setAvailableRoles(res.available_roles);
        setAccessLevelsByRole(res.access_levels_by_role || {});
        setAvailableDepartments(res.available_departments || []);
        setAvailablePlatforms(res.available_platforms || ['SNS Hospice Solutions']);
        setJobTitlesByDepartment(res.job_titles_by_department || {});
        setAvailableAccountTypes(res.available_account_types || []);
        setActorCapabilities(res.actor_capabilities || []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load SNS staff'))
      .finally(() => setLoading(false));
  }, [scope, search, role, status, offset, department]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (scope !== 'AUDIT') return;
    setAuditLoading(true);
    setAuditError('');
    fetchOwnerAuditLogs({ entityType: 'user', hours: 24 * 30, limit: 50 })
      .then((res) => setAuditEvents(res.logs))
      .catch((err) => setAuditError(err instanceof Error ? err.message : 'Failed to load audit history'))
      .finally(() => setAuditLoading(false));
  }, [scope]);

  useEffect(() => {
    setOffset(0);
  }, [scope]);

  const canCreateStaff = actorCapabilities.includes('staff.create');

  const handleToggleActive = async (targetUser) => {
    setActioningId(targetUser.user_id);
    setError('');
    try {
      await setOwnerPlatformUserActive(targetUser.user_id, !targetUser.active);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update account status');
    } finally {
      setActioningId(null);
    }
  };

  const handleResetPassword = async (targetUser) => {
    if (!window.confirm(`Reset password for ${targetUser.full_name} (${targetUser.email})? They will be required to set a new password on next login.`)) {
      return;
    }
    setActioningId(targetUser.user_id);
    setError('');
    try {
      const res = await resetOwnerPlatformUserPassword(targetUser.user_id);
      setResetResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setActioningId(null);
    }
  };

  const rangeStart = totalCount === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, totalCount);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between p-4 rounded-2xl bg-sns-card border border-sns-border shadow-panel">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-[22px] font-bold text-text-primary">SNS Staff &amp; Access</h1>
            <span className="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-ai/10 text-ai border border-ai/30">
              SNS HOSPICE SOLUTIONS ONLY
            </span>
          </div>
          <p className="text-sm text-text-secondary mt-1">Identity &amp; Access Management for SNS Hospice Solutions platform personnel and platform identities</p>
        </div>
        <div className="flex items-center gap-2.5">
          {canCreateStaff && (
            <>
              <button
                type="button"
                onClick={() => setModalMode('invite')}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary text-[13px] font-semibold hover:bg-[var(--owner-btn-secondary-hover)] transition-colors"
              >
                <IconPlus /> Invite Staff
              </button>
              <button
                type="button"
                onClick={() => setModalMode('add')}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 transition-colors"
              >
                <IconPlus /> Add Staff
              </button>
            </>
          )}
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary text-[13px] font-bold hover:bg-[var(--owner-btn-secondary-hover)] transition-colors disabled:opacity-60"
          >
            {loading ? 'Refreshing…' : '⟳'}
          </button>
        </div>
      </div>

      {error && (
        <div className="px-4 py-2.5 rounded-lg bg-status-critical/10 border border-status-critical/20 text-status-critical text-sm">
          {error}
        </div>
      )}

      {resetResult && (
        <div className="flex items-center justify-between px-4 py-2.5 rounded-lg bg-ai/10 border border-ai/20 text-sm text-text-primary">
          <span>
            Set-password link for <strong>{resetResult.email}</strong> (expires in 72h, share with the staff member):{' '}
            <code className="text-ai break-all">{resetResult.reset_link}</code>
          </span>
          <button type="button" className="text-text-tertiary hover:text-text-primary" onClick={() => setResetResult(null)}>
            <IconClose />
          </button>
        </div>
      )}

      {/* KPI row -- 6 cards, all real backend-derived counts */}
      <div className="grid grid-cols-6 gap-3">
        <KpiCard label="TOTAL STAFF" value={String(stats.total_users)} subtitle="Platform-authorized personnel" subtitleClassName="text-ai" dotClassName="bg-ai" />
        <KpiCard label="PLATFORM OWNERS" value={String(stats.active_owners)} subtitle="Active owner accounts" subtitleClassName="text-ai" dotClassName="bg-ai" />
        <KpiCard label="ACTIVE STAFF" value={String(stats.active_users)} subtitle="Currently enabled" subtitleClassName="text-status-healthy" dotClassName="bg-status-healthy" />
        <KpiCard label="SUSPENDED STAFF" value={String(stats.disabled_users)} subtitle="Disabled credentials" subtitleClassName="text-status-high" dotClassName="bg-status-high" />
        <KpiCard label="SERVICE ACCOUNTS" value={String(stats.service_accounts)} subtitle="Non-human identities" subtitleClassName="text-status-monitor" dotClassName="bg-status-monitor" />
        <KpiCard label="API IDENTITIES" value={String(stats.api_clients)} subtitle="Integration clients" subtitleClassName="text-status-monitor" dotClassName="bg-status-monitor" />
      </div>

      {/* Identity scope -- Human Staff, Service Accounts, and API
          Identities are deliberately separate tabs (never one merged
          "employee" list) per the approved SNS Staff & Access IAM
          requirement that non-human platform identities never be
          presented as ordinary employees. Audit is a 4th, identity-scoped
          tab, distinct from the platform-wide standalone Audit Logs page. */}
      <div className="flex gap-1 p-1 rounded-xl bg-sns-app border border-sns-border w-fit">
        {SCOPES.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setScope(s.key)}
            className={`px-4 py-2 text-[13px] font-semibold rounded-lg transition-colors ${
              scope === s.key ? 'bg-ai text-ai-on' : 'text-text-secondary hover:text-text-primary hover:bg-sns-border-subtle'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {scope !== 'AUDIT' && (
      <>
      {/* Search & filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex-1 min-w-[200px] flex items-center gap-2 px-3 h-[38px] rounded-lg bg-sns-app border border-sns-border">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-tertiary shrink-0">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            placeholder="Search SNS staff by name or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1 bg-transparent text-[13px] text-text-primary placeholder:text-text-tertiary outline-none"
          />
        </div>
        <div className="relative">
          <select
            value={department}
            onChange={(e) => { setDepartment(e.target.value); setOffset(0); }}
            className="appearance-none w-44 pr-8 pl-3 h-[38px] rounded-lg bg-sns-app border border-sns-border text-[13px] text-text-primary"
          >
            <option value="">All Departments</option>
            {availableDepartments.map((d) => (
              <option key={d} value={d}>{labelize(d)}</option>
            ))}
          </select>
          <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        </div>
        <div className="relative">
          <select
            value={role}
            onChange={(e) => { setRole(e.target.value); setOffset(0); }}
            className="appearance-none w-44 pr-8 pl-3 h-[38px] rounded-lg bg-sns-app border border-sns-border text-[13px] text-text-primary"
          >
            <option value="">All Platform Roles</option>
            {availableRoles.map((r) => (
              <option key={r} value={r}>{roleLabel(r)}</option>
            ))}
          </select>
          <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        </div>
        <div className="relative">
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setOffset(0); }}
            className="appearance-none w-36 pr-8 pl-3 h-[38px] rounded-lg bg-sns-app border border-sns-border text-[13px] text-text-primary"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active Only</option>
            <option value="SUSPENDED">Suspended Only</option>
            <option value="DISABLED">Disabled Only</option>
            <option value="REMOVED">Removed / Former Staff</option>
          </select>
          <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        </div>
      </div>

      {/* Staff directory */}
      <div className="rounded-2xl border border-sns-border bg-sns-card overflow-hidden">
        {loading && users.length === 0 ? (
          <p className="text-sm text-text-secondary p-6 text-center">Loading SNS staff roster…</p>
        ) : users.length === 0 ? (
          <p className="text-sm text-text-secondary p-6 text-center">No SNS staff accounts match these filters.</p>
        ) : (
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-sns-app border-b border-sns-border">
                {(scope === 'HUMAN'
                  ? ['Name', 'Email', 'Department', 'Job Title', 'Platform Role', 'Access Level', 'Status', 'Last Login', 'Actions']
                  : scope === 'SERVICE'
                  ? ['Name', 'Account Type', 'Responsible Owner', 'Purpose', 'Platform', 'Platform Role', 'Status', 'Actions']
                  : ['Client Name', 'Responsible Owner', 'Purpose', 'Scope', 'Platform', 'Platform Role', 'Status', 'Actions']
                ).map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[11px] font-bold text-text-tertiary uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.user_id}
                  className="border-b border-sns-border last:border-b-0 hover:bg-sns-border-subtle transition-colors cursor-pointer"
                  onClick={() => setDrawerUserId(u.user_id)}
                >
                  <td className="px-4 py-3 text-sm font-semibold text-text-primary">{u.full_name}</td>
                  {scope === 'HUMAN' && <td className="px-4 py-3 text-[13px] font-mono text-text-secondary">{u.email}</td>}
                  {scope === 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{labelize(u.department)}</td>}
                  {scope === 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{u.job_title || '—'}</td>}
                  {scope === 'SERVICE' && <td className="px-4 py-3 text-[13px] text-text-secondary">{labelize(u.account_type)}</td>}
                  {scope !== 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{u.responsible_owner_name || 'Unassigned'}</td>}
                  {scope !== 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary max-w-[220px] truncate" title={u.purpose || ''}>{u.purpose || '—'}</td>}
                  {scope === 'API' && <td className="px-4 py-3 text-[13px] font-mono text-text-secondary">{u.scope || '—'}</td>}
                  {scope !== 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{u.platform || '—'}</td>}
                  <td className={`px-4 py-3 text-[13px] ${u.role === 'OWNER' ? 'text-ai font-semibold' : 'text-text-primary'}`}>{roleLabel(u.role)}</td>
                  {scope === 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{accessLevelLabel(u.access_level)}</td>}
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded font-mono font-bold text-[11px] ${STATUS_BADGE_CLASS[u.platform_staff_status] || (u.active ? 'bg-status-healthy/15 text-status-healthy' : 'bg-status-critical/15 text-status-critical')}`}>
                      {labelize(u.platform_staff_status) || (u.active ? 'Active' : 'Disabled')}
                    </span>
                  </td>
                  {scope === 'HUMAN' && <td className="px-4 py-3 text-[13px] text-text-secondary">{formatLastLogin(u.last_login)}</td>}
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-3">
                      {u.allowed_actions?.reset_password && (
                        <button
                          type="button"
                          disabled={actioningId === u.user_id}
                          onClick={() => handleResetPassword(u)}
                          className="text-[11px] font-medium text-text-secondary hover:text-text-primary disabled:opacity-50 disabled:cursor-default"
                        >
                          Reset
                        </button>
                      )}
                      {(u.allowed_actions?.disable || u.allowed_actions?.suspend) && (
                        <button
                          type="button"
                          disabled={actioningId === u.user_id}
                          onClick={() => handleToggleActive(u)}
                          className={`text-[11px] font-semibold disabled:opacity-50 disabled:cursor-default ${u.active ? 'text-status-high hover:text-status-high/80' : 'text-status-healthy hover:text-status-healthy/80'}`}
                        >
                          {u.active ? 'Suspend' : 'Activate'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="flex justify-between items-center px-4 py-3 bg-sns-app border-t border-sns-border">
          <span className="text-xs text-text-tertiary">
            {totalCount === 0 ? 'Showing 0 of 0 SNS accounts' : `Showing ${rangeStart}-${rangeEnd} of ${totalCount.toLocaleString()} SNS accounts`}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0 || loading}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              className="px-3.5 py-1.5 rounded-lg text-[11px] font-semibold bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary hover:bg-[var(--owner-btn-secondary-hover)] disabled:opacity-50 transition-colors"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={rangeEnd >= totalCount || loading}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              className="px-3.5 py-1.5 rounded-lg text-[11px] font-bold bg-ai text-ai-on hover:bg-ai/90 disabled:opacity-50 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
      </>
      )}

      {scope === 'AUDIT' && (
        <div className="rounded-2xl border border-sns-border bg-sns-card overflow-hidden">
          <div className="px-5 py-3 border-b border-sns-border">
            <p className="text-sm font-semibold text-text-primary">SNS Staff &amp; Access Audit History</p>
            <p className="text-xs text-text-tertiary mt-0.5">Last 30 days of staff/identity lifecycle events (invite, role change, suspend, disable, revoke, password reset). Full platform-wide activity is available on the standalone Audit Logs page.</p>
          </div>
          <div className="p-4 flex flex-col gap-2">
            {auditError && (
              <div className="px-3 py-2 rounded-lg bg-status-critical/10 border border-status-critical/20 text-status-critical text-xs">
                {auditError}
              </div>
            )}
            {auditLoading ? (
              <p className="text-sm text-text-secondary text-center py-8">Loading audit history…</p>
            ) : auditEvents.length === 0 ? (
              <p className="text-sm text-text-secondary text-center py-8">No SNS staff/identity audit events recorded in the last 30 days.</p>
            ) : (
              auditEvents.map((ev) => (
                <div key={ev.log_id} className="px-3 py-2.5 rounded-lg bg-sns-app border border-sns-border">
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] font-mono font-bold text-text-primary">{labelize(ev.action)}</span>
                    <span className="text-[11px] text-text-tertiary">{new Date(ev.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-[11px] text-text-tertiary mt-0.5">By {ev.user_display}{ev.description ? ` — ${ev.description}` : ''}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {modalMode && (
        <AddStaffModal
          mode={modalMode}
          onClose={() => setModalMode(null)}
          onCreated={(result) => { setModalMode(null); setResetResult(result); load(); }}
          availableRoles={availableRoles}
          accessLevelsByRole={accessLevelsByRole}
          availableDepartments={availableDepartments}
          availablePlatforms={availablePlatforms}
          jobTitlesByDepartment={jobTitlesByDepartment}
          availableAccountTypes={availableAccountTypes}
        />
      )}

      {drawerUserId && (
        <StaffProfileDrawer
          userId={drawerUserId}
          onClose={() => setDrawerUserId(null)}
          onChanged={load}
          availableRoles={availableRoles}
          accessLevelsByRole={accessLevelsByRole}
          availableDepartments={availableDepartments}
          availablePlatforms={availablePlatforms}
          jobTitlesByDepartment={jobTitlesByDepartment}
          canEditProfile={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.edit_profile}
          canAssignRole={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.assign_role}
          canAssignOwnerRole={actorCapabilities.includes('staff.assign_owner_role')}
          canActivate={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.activate}
          canSuspend={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.suspend}
          canDisable={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.disable}
          canRevokeAccess={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.revoke_access}
          canRemove={users.find((u) => u.user_id === drawerUserId)?.allowed_actions?.remove}
        />
      )}
    </div>
  );
}
