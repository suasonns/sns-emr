import React, { useEffect, useState } from 'react';
import {
  fetchOwnerPlatformStaffDetail,
  fetchOwnerPlatformStaffAuditHistory,
  updateOwnerPlatformStaffProfile,
  updateOwnerPlatformStaffRole,
  resetOwnerPlatformUserPassword,
  setOwnerPlatformStaffStatus,
  revokeOwnerPlatformStaffAccess,
  removeOwnerPlatformStaff,
  fetchOwnerPlatformUsers,
} from '../../api/ownerAdmin';
import { IconChevronDown, IconClose } from '../shell/icons';
import { accessLevelLabel } from '../accessLevels';

const FIELD_CLASS =
  'w-full px-3 py-2.5 rounded-lg border border-sns-border bg-sns-app text-[13px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-ai/50 transition-colors';
const SELECT_CLASS = `${FIELD_CLASS} appearance-none pr-9`;

function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString();
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString();
}

function Field({ label, value }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">{label}</span>
      <span className="text-sm text-text-primary">{value ?? '—'}</span>
    </div>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3.5 py-2 text-[13px] font-semibold rounded-lg transition-colors ${
        active ? 'bg-ai text-ai-on' : 'text-text-secondary hover:text-text-primary hover:bg-sns-border-subtle'
      }`}
    >
      {children}
    </button>
  );
}

function ComingSoon({ text }) {
  return (
    <div className="px-3 py-2.5 rounded-lg bg-sns-app border border-dashed border-sns-border text-xs text-text-tertiary italic">
      {text || 'Coming in a future phase'}
    </div>
  );
}

/**
 * SNS Staff & Access -- Staff Profile Drawer. Slide-out panel (never a
 * separate route) with 4 tabs: Profile, Access, Security, Audit. Every
 * field is either real data from the backend or an explicit "Coming in a
 * future phase" placeholder -- nothing here is fabricated.
 */
export default function StaffProfileDrawer({ userId, onClose, onChanged, availableRoles, accessLevelsByRole, availableDepartments, availablePlatforms, jobTitlesByDepartment, canEditProfile, canAssignRole, canAssignOwnerRole, canActivate, canSuspend, canDisable, canRevokeAccess, canRemove }) {
  const [tab, setTab] = useState('profile');
  const [detail, setDetail] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);

  const [roleDraft, setRoleDraft] = useState('');
  const [changingRole, setChangingRole] = useState(false);
  const [resetResult, setResetResult] = useState(null);
  const [humanStaffOptions, setHumanStaffOptions] = useState([]);
  const [transferTargetId, setTransferTargetId] = useState('');
  const [transferring, setTransferring] = useState(false);
  const [lifecycleBusy, setLifecycleBusy] = useState(false);

  const load = () => {
    setLoading(true);
    setError('');
    Promise.all([
      fetchOwnerPlatformStaffDetail(userId),
      fetchOwnerPlatformStaffAuditHistory(userId).catch(() => ({ events: [] })),
    ])
      .then(([d, audit]) => {
        setDetail(d);
        setAuditEvents(audit.events || []);
        setRoleDraft(d.role);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load staff profile'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    fetchOwnerPlatformUsers({ accountType: 'HUMAN_STAFF', limit: 200 })
      .then((res) => setHumanStaffOptions(res.users))
      .catch(() => setHumanStaffOptions([]));
  }, []);

  const startEdit = () => {
    setForm({
      first_name: detail.first_name || '',
      middle_name: detail.middle_name || '',
      last_name: detail.last_name || '',
      platform: detail.platform || 'SNS Hospice Solutions',
      department: detail.department || '',
      phone: detail.phone || '',
      address_street: detail.address_street || '',
      address_city: detail.address_city || '',
      address_state: detail.address_state || '',
      address_zip: detail.address_zip || '',
      start_date: detail.start_date ? detail.start_date.slice(0, 10) : '',
      notes: detail.notes || '',
      job_title: detail.job_title || '',
      responsible_owner_id: detail.responsible_owner_id || '',
      purpose: detail.purpose || '',
      scope: detail.scope || '',
    });
    setEditing(true);
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        middle_name: form.middle_name.trim() || undefined,
        department: form.department || undefined,
        phone: form.phone.trim() || undefined,
        address_street: form.address_street.trim() || undefined,
        address_city: form.address_city.trim() || undefined,
        address_state: form.address_state.trim() || undefined,
        address_zip: form.address_zip.trim() || undefined,
        start_date: form.start_date || undefined,
        notes: form.notes.trim() || undefined,
        job_title: form.job_title.trim() || undefined,
        responsible_owner_id: form.responsible_owner_id || undefined,
        purpose: form.purpose.trim() || undefined,
        scope: form.scope.trim() || undefined,
      };
      const updated = await updateOwnerPlatformStaffProfile(userId, payload);
      setDetail(updated);
      setEditing(false);
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const saveRole = async () => {
    if (!roleDraft || roleDraft === detail.role) return;
    setChangingRole(true);
    setError('');
    try {
      const updated = await updateOwnerPlatformStaffRole(userId, roleDraft);
      setDetail(updated);
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change role');
      setRoleDraft(detail.role);
    } finally {
      setChangingRole(false);
    }
  };

  const promoteToOwner = async () => {
    if (!window.confirm(`Assign ${detail.full_name} as an additional Platform Owner? This grants full platform authority, including the ability to manage other Platform Owners.`)) return;
    setChangingRole(true);
    setError('');
    try {
      const updated = await updateOwnerPlatformStaffRole(userId, 'OWNER');
      setDetail(updated);
      setRoleDraft('OWNER');
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign as Platform Owner');
    } finally {
      setChangingRole(false);
    }
  };

  // Transfer Ownership Authority: hand this account's Platform Owner
  // authority to another SNS staff member in one guided step (promote
  // the chosen successor, then step this account down to Platform
  // Administrator). Only offered when at least one other active Owner
  // will remain, or the successor becomes one -- the backend's
  // Final-Active-Owner safeguard still enforces this server-side
  // regardless.
  const transferOwnershipAuthority = async () => {
    if (!transferTargetId) return;
    const successor = humanStaffOptions.find((u) => u.user_id === transferTargetId);
    if (!window.confirm(`Transfer Platform Owner authority from ${detail.full_name} to ${successor?.full_name || 'the selected account'}? ${detail.full_name} will be stepped down to Platform Administrator.`)) return;
    setTransferring(true);
    setError('');
    try {
      if (successor?.role !== 'OWNER') {
        await updateOwnerPlatformStaffRole(transferTargetId, 'OWNER');
      }
      const updated = await updateOwnerPlatformStaffRole(userId, 'PLATFORM_ADMIN');
      setDetail(updated);
      setRoleDraft('PLATFORM_ADMIN');
      setTransferTargetId('');
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to transfer ownership authority');
    } finally {
      setTransferring(false);
    }
  };

  const doResetPassword = async () => {
    if (!window.confirm(`Reset password for ${detail.full_name}? They will be required to set a new password on next login.`)) return;
    setError('');
    try {
      const res = await resetOwnerPlatformUserPassword(userId);
      setResetResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    }
  };

  // Account Lifecycle actions -- Suspend/Disable/Activate (distinct
  // ACTIVE/SUSPENDED/DISABLED status transitions), Revoke Access (its own
  // audited action, distinct from Suspend/Disable), and Remove Staff
  // (one-way soft-removal). Each requires a reason and is gated by the
  // real backend-derived allowed_actions for this row -- never assumed
  // client-side. The Final-Active-Owner safeguard is enforced
  // server-side regardless of what the UI shows.
  const doSetStatus = async (status, verb) => {
    const reason = window.prompt(`Reason for marking ${detail.full_name} as ${verb}:`, '');
    if (reason === null) return;
    setLifecycleBusy(true);
    setError('');
    try {
      const updated = await setOwnerPlatformStaffStatus(userId, status, reason || undefined);
      setDetail(updated);
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to set status to ${status}`);
    } finally {
      setLifecycleBusy(false);
    }
  };

  const doRevokeAccess = async () => {
    const reason = window.prompt(`Reason for revoking ${detail.full_name}'s access:`, '');
    if (reason === null) return;
    setLifecycleBusy(true);
    setError('');
    try {
      const updated = await revokeOwnerPlatformStaffAccess(userId, reason || undefined);
      setDetail(updated);
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke access');
    } finally {
      setLifecycleBusy(false);
    }
  };

  const doRemoveStaff = async () => {
    const reason = window.prompt(`Reason for removing ${detail.full_name} from SNS Staff & Access (required):`, '');
    if (reason === null) return;
    if (!reason.trim()) {
      setError('A reason is required to remove an SNS staff account.');
      return;
    }
    if (!window.confirm(`Remove ${detail.full_name}? This blocks their authentication immediately. The account and its audit history are preserved (never hard-deleted) and can only be viewed via the Removed status filter.`)) return;
    setLifecycleBusy(true);
    setError('');
    try {
      const updated = await removeOwnerPlatformStaff(userId, reason.trim());
      setDetail(updated);
      onChanged?.();
      onClose?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove SNS staff account');
    } finally {
      setLifecycleBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[1000] flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-[560px] h-full bg-sns-card border-l border-sns-border shadow-panel flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-sns-border shrink-0">
          <div>
            <h3 className="text-base font-bold text-text-primary">{detail?.full_name || 'SNS Staff Profile'}</h3>
            {detail && <p className="text-xs text-text-tertiary mt-0.5">{detail.email}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-md flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-sns-border-subtle transition-colors"
            aria-label="Close"
          >
            <IconClose />
          </button>
        </div>

        <div className="flex gap-1 px-5 py-3 border-b border-sns-border shrink-0">
          <TabButton active={tab === 'profile'} onClick={() => setTab('profile')}>Profile</TabButton>
          <TabButton active={tab === 'access'} onClick={() => setTab('access')}>Access</TabButton>
          <TabButton active={tab === 'security'} onClick={() => setTab('security')}>Security</TabButton>
          <TabButton active={tab === 'audit'} onClick={() => setTab('audit')}>Audit</TabButton>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {error && (
            <div className="mb-3 px-3 py-2 rounded-lg bg-status-critical/10 border border-status-critical/20 text-status-critical text-xs">
              {error}
            </div>
          )}
          {resetResult && (
            <div className="mb-3 px-3 py-2.5 rounded-lg bg-ai/10 border border-ai/20 text-xs text-text-primary">
              Set-password link (expires in 72h, single use): <code className="text-ai break-all">{resetResult.reset_link}</code>
            </div>
          )}

          {loading || !detail ? (
            <p className="text-sm text-text-secondary text-center py-8">Loading…</p>
          ) : tab === 'profile' ? (
            editing ? (
              <form onSubmit={saveProfile} className="flex flex-col gap-2.5">
                <div className="flex gap-2">
                  <input className={FIELD_CLASS} placeholder="First name" required value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} />
                  <input className={FIELD_CLASS} placeholder="Middle name" value={form.middle_name} onChange={(e) => setForm((f) => ({ ...f, middle_name: e.target.value }))} />
                  <input className={FIELD_CLASS} placeholder="Last name" required value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} />
                </div>
                <div className="relative">
                  <select className={SELECT_CLASS} value={form.platform} onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}>
                    {(availablePlatforms || ['SNS Hospice Solutions']).map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                  <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                </div>
                <div className="relative">
                  <select
                    className={SELECT_CLASS}
                    value={form.department}
                    onChange={(e) => setForm((f) => ({ ...f, department: e.target.value, job_title: '' }))}
                  >
                    <option value="">No department selected</option>
                    {(availableDepartments || []).map((d) => (
                      <option key={d} value={d}>{labelize(d)}</option>
                    ))}
                  </select>
                  <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                </div>
                {detail.account_type === 'HUMAN_STAFF' && (
                  (jobTitlesByDepartment && jobTitlesByDepartment[form.department] || []).length > 0 ? (
                    <div className="relative">
                      <select className={SELECT_CLASS} value={form.job_title} onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))}>
                        <option value="">Select a job title (optional)</option>
                        {jobTitlesByDepartment[form.department].map((t) => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                      <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                    </div>
                  ) : (
                    <input className={FIELD_CLASS} placeholder="Job title" value={form.job_title} onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))} />
                  )
                )}
                <input className={FIELD_CLASS} placeholder="Phone" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
                <input className={FIELD_CLASS} placeholder="Street address" value={form.address_street} onChange={(e) => setForm((f) => ({ ...f, address_street: e.target.value }))} />
                <div className="flex gap-2">
                  <input className={FIELD_CLASS} placeholder="City" value={form.address_city} onChange={(e) => setForm((f) => ({ ...f, address_city: e.target.value }))} />
                  <input className={FIELD_CLASS} placeholder="State" maxLength={2} value={form.address_state} onChange={(e) => setForm((f) => ({ ...f, address_state: e.target.value }))} />
                  <input className={FIELD_CLASS} placeholder="ZIP" value={form.address_zip} onChange={(e) => setForm((f) => ({ ...f, address_zip: e.target.value }))} />
                </div>
                <label className="flex flex-col gap-1">
                  <span className="text-[11px] text-text-tertiary">Start date</span>
                  <input className={FIELD_CLASS} type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
                </label>
                <textarea className={FIELD_CLASS} placeholder="Notes" rows={3} value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
                {detail.account_type !== 'HUMAN_STAFF' && (
                  <>
                    <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-1">Identity Accountability</p>
                    <div className="relative">
                      <select className={SELECT_CLASS} value={form.responsible_owner_id} onChange={(e) => setForm((f) => ({ ...f, responsible_owner_id: e.target.value }))}>
                        <option value="">Select a responsible owner</option>
                        {humanStaffOptions.map((u) => (
                          <option key={u.user_id} value={u.user_id}>{u.full_name} ({u.email})</option>
                        ))}
                      </select>
                      <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                    </div>
                    <textarea className={FIELD_CLASS} placeholder="Purpose" rows={2} value={form.purpose} onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))} />
                    {detail.account_type === 'API_CLIENT' && (
                      <input className={FIELD_CLASS} placeholder="Scope" value={form.scope} onChange={(e) => setForm((f) => ({ ...f, scope: e.target.value }))} />
                    )}
                  </>
                )}
                <div className="flex gap-2 justify-end mt-1">
                  <button type="button" disabled={saving} onClick={() => setEditing(false)} className="px-3.5 py-2 rounded-lg bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary text-[13px] font-semibold hover:bg-[var(--owner-btn-secondary-hover)] transition-colors disabled:opacity-60">Cancel</button>
                  <button type="submit" disabled={saving} className="px-3.5 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 transition-colors disabled:opacity-60">{saving ? 'Saving…' : 'Save'}</button>
                </div>
              </form>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Full Name" value={detail.full_name} />
                  <Field label="Email" value={detail.email} />
                  <Field label="Phone" value={detail.phone} />
                  <Field label="Platform" value={detail.platform} />
                  <Field label="Department" value={labelize(detail.department)} />
                  {detail.account_type === 'HUMAN_STAFF' && <Field label="Job Title" value={detail.job_title} />}
                  <Field label="Status" value={detail.active ? 'Active' : 'Disabled'} />
                  <Field label="Start Date" value={formatDate(detail.start_date)} />
                </div>
                {detail.notes && <Field label="Notes" value={detail.notes} />}
                {detail.account_type !== 'HUMAN_STAFF' && (
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">Platform Identity — Not an Employee</span>
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Responsible Owner" value={detail.responsible_owner_name} />
                      {detail.account_type === 'API_CLIENT' && <Field label="Scope" value={detail.scope} />}
                    </div>
                    {detail.purpose && <Field label="Purpose" value={detail.purpose} />}
                  </div>
                )}
                {canEditProfile && (
                  <button type="button" onClick={startEdit} className="self-start px-3.5 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 transition-colors">
                    Edit Profile
                  </button>
                )}
              </div>
            )
          ) : tab === 'access' ? (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Platform Role" value={labelize(detail.role)} />
                <Field label="Access Level" value={accessLevelLabel(detail.access_level)} />
                <Field label="Account Type" value={labelize(detail.account_type)} />
              </div>

              {/* Ownership Continuity -- always visible (not buried in the
                  generic role selector) per the approved SNS Staff &
                  Access final IAM direction: business continuity, not
                  succession/death planning. Two explicit actions:
                  "Assign Additional Platform Owner" (grant a non-owner
                  account full Owner authority) and "Transfer Ownership
                  Authority" (hand this Owner's authority to a chosen
                  successor in one guided step). The hard Final-Active-
                  Owner safeguard is enforced server-side regardless. */}
              {detail.role === 'OWNER' ? (
                <div className="flex flex-col gap-3">
                  <div className={`px-3 py-2.5 rounded-lg border text-xs ${detail.is_final_active_owner ? 'bg-status-high/10 border-status-high/30 text-status-high' : 'bg-ai/10 border-ai/20 text-text-primary'}`}>
                    <p className="font-bold uppercase tracking-wider text-[11px] mb-1">
                      {detail.is_final_active_owner ? 'Final Active Platform Owner — Protected' : 'Ownership Continuity'}
                    </p>
                    <p>
                      {detail.is_final_active_owner
                        ? 'This is the only active Platform Owner. To preserve business continuity, this account cannot be demoted, disabled, or have access revoked until at least one other active Platform Owner exists. Use Transfer Ownership Authority below to safely hand off before stepping down.'
                        : 'This account holds full Platform Owner authority, including the ability to create or assign other Platform Owners.'}
                    </p>
                  </div>

                  {canAssignOwnerRole && (
                    <div className="px-3 py-2.5 rounded-lg bg-sns-app border border-sns-border">
                      <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mb-1.5">Transfer Ownership Authority</p>
                      <p className="text-xs text-text-tertiary mb-2">Hand this account's Platform Owner authority to another SNS staff member. The successor is promoted to Platform Owner and this account is stepped down to Platform Administrator, in one action.</p>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <select className={SELECT_CLASS} value={transferTargetId} onChange={(e) => setTransferTargetId(e.target.value)}>
                            <option value="">Select a successor</option>
                            {humanStaffOptions.filter((u) => u.user_id !== detail.user_id && u.role !== 'OWNER').map((u) => (
                              <option key={u.user_id} value={u.user_id}>{u.full_name} ({u.email})</option>
                            ))}
                          </select>
                          <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                        </div>
                        <button
                          type="button"
                          disabled={transferring || !transferTargetId}
                          onClick={transferOwnershipAuthority}
                          className="px-3.5 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 disabled:opacity-50 transition-colors whitespace-nowrap"
                        >
                          {transferring ? 'Transferring…' : 'Transfer Ownership Authority'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                canAssignOwnerRole && (
                  <div className="px-3 py-2.5 rounded-lg bg-sns-app border border-sns-border">
                    <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mb-1.5">Ownership Continuity</p>
                    <p className="text-xs text-text-tertiary mb-2">Assign this account as an additional Platform Owner for business continuity. Multiple active Platform Owners are supported so the platform is never left without an active Owner.</p>
                    <button
                      type="button"
                      disabled={changingRole}
                      onClick={promoteToOwner}
                      className="px-3.5 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 disabled:opacity-50 transition-colors"
                    >
                      {changingRole ? 'Assigning…' : 'Assign Additional Platform Owner'}
                    </button>
                  </div>
                )
              )}

              {canAssignRole && (
                <div className="flex flex-col gap-1.5">
                  <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">Change Platform Role</span>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <select className={SELECT_CLASS} value={roleDraft} onChange={(e) => setRoleDraft(e.target.value)}>
                        {(availableRoles || []).map((r) => (
                          <option key={r} value={r}>{labelize(r)}</option>
                        ))}
                      </select>
                      <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                    </div>
                    <button
                      type="button"
                      disabled={changingRole || roleDraft === detail.role}
                      onClick={saveRole}
                      className="px-3.5 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 disabled:opacity-50 transition-colors"
                    >
                      {changingRole ? 'Saving…' : 'Apply'}
                    </button>
                  </div>
                  <p className="text-[11px] text-text-tertiary">
                    Access Level (derived): <span className="font-semibold text-text-secondary">{accessLevelLabel((accessLevelsByRole || {})[roleDraft])}</span>
                  </p>
                  <p className="text-[11px] text-text-tertiary">Final Platform Owner protections are enforced by the backend.</p>
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">Effective Permission Summary</span>
                {detail.capabilities?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {detail.capabilities.map((cap) => (
                      <span key={cap} className="px-2 py-0.5 rounded font-mono text-[11px] bg-ai/10 text-ai border border-ai/20">{cap}</span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-text-tertiary">No platform capabilities granted.</span>
                )}
              </div>
            </div>
          ) : tab === 'security' ? (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Account Status" value={labelize(detail.platform_staff_status || (detail.active ? 'ACTIVE' : 'DISABLED'))} />
                <Field label="Last Login" value={formatDateTime(detail.last_login)} />
                <Field label="Must Change Password" value={detail.must_change_password ? 'Yes' : 'No'} />
              </div>
              <div>
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider block mb-1.5">MFA Status</span>
                <ComingSoon />
              </div>
              <div>
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider block mb-1.5">Password Reset History</span>
                {(() => {
                  const resets = auditEvents.filter((ev) => ev.action === 'OWNER_RESET_USER_PASSWORD');
                  return resets.length === 0 ? (
                    <p className="text-xs text-text-tertiary italic">No password resets recorded.</p>
                  ) : (
                    <div className="flex flex-col gap-1">
                      {resets.slice(0, 5).map((ev) => (
                        <p key={ev.log_id} className="text-xs text-text-secondary">{formatDateTime(ev.created_at)} — by {ev.actor_full_name || 'Unknown'}</p>
                      ))}
                    </div>
                  );
                })()}
              </div>
              <div>
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider block mb-1.5">Access Revocation History</span>
                {(() => {
                  const revocations = auditEvents.filter((ev) => ev.action === 'OWNER_REVOKED_STAFF_ACCESS');
                  return revocations.length === 0 ? (
                    <p className="text-xs text-text-tertiary italic">No access revocations recorded.</p>
                  ) : (
                    <div className="flex flex-col gap-1">
                      {revocations.slice(0, 5).map((ev) => (
                        <p key={ev.log_id} className="text-xs text-text-secondary">{formatDateTime(ev.created_at)} — by {ev.actor_full_name || 'Unknown'}</p>
                      ))}
                    </div>
                  );
                })()}
              </div>
              <div>
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider block mb-1.5">Security Alerts</span>
                <ComingSoon />
              </div>

              {/* Account Lifecycle -- Staff Lifecycle Actions, distinct
                  from Ownership Continuity (Access tab). Each transition
                  is gated by its own real, backend-derived
                  allowed_actions flag for this row and requires a
                  reason, which is captured in the audit trail. The
                  Final-Active-Owner safeguard is enforced server-side
                  regardless of what buttons are shown here. */}
              <div className="flex flex-col gap-2 pt-2 border-t border-sns-border">
                <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">Account Lifecycle</span>
                {detail.is_final_active_owner && (
                  <p className="text-[11px] text-status-high">Final Active Platform Owner — suspend, disable, revoke, and remove are blocked until another active Platform Owner exists.</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={doResetPassword}
                    disabled={lifecycleBusy}
                    className="px-3.5 py-2 rounded-lg bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary text-[13px] font-semibold hover:bg-[var(--owner-btn-secondary-hover)] disabled:opacity-50 transition-colors"
                  >
                    Reset Password
                  </button>
                  {canActivate && detail.platform_staff_status !== 'ACTIVE' && (
                    <button
                      type="button"
                      disabled={lifecycleBusy}
                      onClick={() => doSetStatus('ACTIVE', 'Active')}
                      className="px-3.5 py-2 rounded-lg bg-status-healthy/15 border border-status-healthy/30 text-status-healthy text-[13px] font-semibold hover:bg-status-healthy/25 disabled:opacity-50 transition-colors"
                    >
                      Activate
                    </button>
                  )}
                  {canSuspend && detail.platform_staff_status === 'ACTIVE' && (
                    <button
                      type="button"
                      disabled={lifecycleBusy}
                      onClick={() => doSetStatus('SUSPENDED', 'Suspended')}
                      className="px-3.5 py-2 rounded-lg bg-status-high/15 border border-status-high/30 text-status-high text-[13px] font-semibold hover:bg-status-high/25 disabled:opacity-50 transition-colors"
                    >
                      Suspend
                    </button>
                  )}
                  {canDisable && detail.platform_staff_status !== 'DISABLED' && (
                    <button
                      type="button"
                      disabled={lifecycleBusy}
                      onClick={() => doSetStatus('DISABLED', 'Disabled')}
                      className="px-3.5 py-2 rounded-lg bg-status-critical/15 border border-status-critical/30 text-status-critical text-[13px] font-semibold hover:bg-status-critical/25 disabled:opacity-50 transition-colors"
                    >
                      Disable Account
                    </button>
                  )}
                  {canRevokeAccess && (
                    <button
                      type="button"
                      disabled={lifecycleBusy}
                      onClick={doRevokeAccess}
                      className="px-3.5 py-2 rounded-lg bg-status-critical/15 border border-status-critical/30 text-status-critical text-[13px] font-semibold hover:bg-status-critical/25 disabled:opacity-50 transition-colors"
                    >
                      Revoke Access
                    </button>
                  )}
                  {canRemove && (
                    <button
                      type="button"
                      disabled={lifecycleBusy}
                      onClick={doRemoveStaff}
                      className="px-3.5 py-2 rounded-lg bg-status-critical text-white text-[13px] font-bold hover:bg-status-critical/90 disabled:opacity-50 transition-colors"
                    >
                      Remove Staff
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {auditEvents.length === 0 ? (
                <p className="text-sm text-text-secondary text-center py-8">No audit events recorded for this account yet.</p>
              ) : (
                auditEvents.map((ev) => (
                  <div key={ev.log_id} className="px-3 py-2.5 rounded-lg bg-sns-app border border-sns-border">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-mono font-bold text-text-primary">{labelize(ev.action)}</span>
                      <span className="text-[11px] text-text-tertiary">{formatDateTime(ev.created_at)}</span>
                    </div>
                    <p className="text-[11px] text-text-tertiary mt-0.5">
                      By {ev.actor_full_name || ev.actor_email || 'System'}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
