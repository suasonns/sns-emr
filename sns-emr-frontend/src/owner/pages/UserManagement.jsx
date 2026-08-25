import React, { useCallback, useEffect, useRef, useState } from 'react';
import { COLORS, S } from '../design';
import {
  fetchOwnerPlatformUsers,
  fetchOwnerTenants,
  resetOwnerPlatformUserPassword,
  setOwnerPlatformUserActive,
} from '../../api/ownerAdmin';

const PAGE_SIZE = 25;

const ROLE_COLOR_RULES = [
  { test: (r) => r.includes('OWNER') || r.includes('PLATFORM'), color: COLORS.green },
  { test: (r) => r.includes('ADMIN') || r.includes('DPCS'), color: COLORS.purple },
  { test: (r) => r.includes('BILLING'), color: COLORS.orange },
  { test: (r) => ['RN', 'LVN', 'NP', 'PA'].some((x) => r === x) || r.includes('PHYSICIAN') || r.includes('MEDICAL_DIRECTOR'), color: COLORS.blue },
];

function roleColor(role) {
  const r = (role || '').toUpperCase();
  const hit = ROLE_COLOR_RULES.find((rule) => rule.test(r));
  return hit ? hit.color : COLORS.teal;
}

function roleLabel(role) {
  if (!role) return 'Unknown';
  return role
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

export default function UserManagement() {
  const [tenants, setTenants] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({ total_users: 0, active_users: 0, active_now: 0, agency_admins: 0, disabled_users: 0 });
  const [availableRoles, setAvailableRoles] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const [actioningId, setActioningId] = useState(null);
  const [resetResult, setResetResult] = useState(null);

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

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    fetchOwnerPlatformUsers({
      search: search || undefined,
      role: role || undefined,
      tenantId: tenantId || undefined,
      status: status || undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => {
        setUsers(res.users);
        setTotalCount(res.total_count);
        setStats(res.stats);
        setAvailableRoles(res.available_roles);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load users'))
      .finally(() => setLoading(false));
  }, [search, role, tenantId, status, offset]);

  useEffect(() => {
    load();
  }, [load]);

  const handleToggleActive = async (targetUser) => {
    setActioningId(targetUser.user_id);
    setError('');
    try {
      await setOwnerPlatformUserActive(targetUser.user_id, !targetUser.active);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status');
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
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>User Management</h1>
          <p style={S.pageSubtitle}>Orchestrate personnel access, security permissions, and roles across active agencies</p>
        </div>
        <button style={{ ...S.btn(COLORS.teal), display: 'flex', alignItems: 'center', gap: 6 }} onClick={load} disabled={loading}>
          {loading ? 'REFRESHING…' : '⟳ REFRESH'}
        </button>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13 }}>{error}</div>
      ) : null}

      {resetResult ? (
        <div style={{ ...S.card, borderColor: COLORS.teal, fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            Temporary password for <strong>{resetResult.email}</strong>: <code style={{ color: COLORS.teal }}>{resetResult.temporary_password}</code>
            {' '}— user must change it on next login.
          </span>
          <span style={{ cursor: 'pointer', color: COLORS.muted }} onClick={() => setResetResult(null)}>✕</span>
        </div>
      ) : null}

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'TOTAL USERS', value: stats.total_users, desc: 'Registered active directories', dot: COLORS.green },
          { label: 'ACTIVE NOW', value: stats.active_now, desc: 'Logged in within the last 24h', dot: COLORS.green },
          { label: 'AGENCY ADMINS', value: stats.agency_admins, desc: 'DPCS / Administrator role holders', dot: COLORS.green },
          { label: 'DISABLED USERS', value: stats.disabled_users, desc: 'Revoked credentials', dot: COLORS.red },
        ].map((s) => (
          <div key={s.label} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <p style={S.statValue}>{s.value}</p>
            </div>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input
            style={S.searchBar}
            placeholder="Search users by name, email, or agency..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Role:</span>
          <select
            style={S.select}
            value={role}
            onChange={(e) => {
              setRole(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All Roles</option>
            {availableRoles.map((r) => (
              <option key={r} value={r}>{roleLabel(r)}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Agency:</span>
          <select
            style={S.select}
            value={tenantId}
            onChange={(e) => {
              setTenantId(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All Agencies</option>
            {tenants.map((t) => (
              <option key={t.tenant_id} value={t.tenant_id}>{t.display_name}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Status:</span>
          <select
            style={S.select}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active Only</option>
            <option value="DISABLED">Disabled Only</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={S.card}>
        {loading && users.length === 0 ? (
          <p style={{ fontSize: 13, color: COLORS.muted, padding: '20px 0', textAlign: 'center' }}>Loading user roster…</p>
        ) : users.length === 0 ? (
          <p style={{ fontSize: 13, color: COLORS.muted, padding: '20px 0', textAlign: 'center' }}>
            No users match these filters.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Name', 'Email', 'Role', 'Tenant/Agency', 'Status', 'Last Login', 'Actions'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const rColor = roleColor(u.role);
                const statusColor = u.active ? COLORS.green : COLORS.red;
                return (
                  <tr key={u.user_id}>
                    <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.white }}>{u.full_name}</td>
                    <td style={S.tableCell}>{u.email}</td>
                    <td style={{ ...S.tableCell }}>
                      <span style={S.badge(rColor + '22', rColor)}>{roleLabel(u.role)}</span>
                    </td>
                    <td style={S.tableCell}>{u.tenant_name}</td>
                    <td style={{ ...S.tableCell }}>
                      <span style={S.badge(statusColor + '22', statusColor)}>{u.active ? 'Active' : 'Disabled'}</span>
                    </td>
                    <td style={S.tableCell}>{formatLastLogin(u.last_login)}</td>
                    <td style={{ ...S.tableCell }}>
                      <div style={{ display: 'flex', gap: 12 }}>
                        <span
                          style={{ fontSize: 11, fontWeight: 500, color: actioningId === u.user_id ? COLORS.dim : COLORS.muted, cursor: actioningId === u.user_id ? 'default' : 'pointer' }}
                          onClick={() => actioningId === u.user_id ? null : handleResetPassword(u)}
                        >
                          Reset
                        </span>
                        <span
                          style={{ fontSize: 11, fontWeight: 600, color: actioningId === u.user_id ? COLORS.dim : (u.active ? COLORS.orange : COLORS.green), cursor: actioningId === u.user_id ? 'default' : 'pointer' }}
                          onClick={() => actioningId === u.user_id ? null : handleToggleActive(u)}
                        >
                          {u.active ? 'Disable' : 'Enable'}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ fontSize: 12, color: COLORS.muted }}>
            {totalCount === 0
              ? 'Showing 0 of 0 users'
              : `Showing ${rangeStart}-${rangeEnd} of ${totalCount.toLocaleString()} users`}
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
