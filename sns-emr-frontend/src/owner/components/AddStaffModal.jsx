import React, { useEffect, useState } from 'react';
import { createOwnerPlatformStaff, fetchOwnerPlatformUsers } from '../../api/ownerAdmin';
import { IconChevronDown, IconClose } from '../shell/icons';
import { accessLevelLabel } from '../accessLevels';

// Shared field/select classes, matching the pattern established in
// TenantManagement.jsx's OnboardModal so every owner-portal modal reads
// consistently against the sns.card/sns.border design tokens.
const FIELD_CLASS =
  'w-full px-3 py-2.5 rounded-lg border border-sns-border bg-sns-app text-[13px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-ai/50 transition-colors';
const SELECT_CLASS = `${FIELD_CLASS} appearance-none pr-9`;

function labelize(value) {
  if (!value) return '';
  return value
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

const EMPTY_FORM = {
  first_name: '',
  middle_name: '',
  last_name: '',
  email: '',
  phone: '',
  platform: 'SNS Hospice Solutions',
  department: '',
  role: '',
  account_type: 'HUMAN_STAFF',
  start_date: '',
  job_title: '',
  responsible_owner_id: '',
  purpose: '',
  scope: '',
};

/**
 * SNS Staff & Access -- "+ Add Staff" / "+ Invite Staff" modal.
 *
 * Both primary actions on the SNS Staff & Access page open this same
 * modal (`mode` only changes the header/submit copy). There is currently
 * no separate invite-only (no-password-yet, pending, resend/cancel)
 * lifecycle on the backend -- POST /api/owner/users already creates the
 * account AND issues a temporary password + reset link in one step,
 * which functions as an implicit invitation. A distinct pending-invite
 * lifecycle is deferred to Phase UM-3 per the approved roadmap.
 */
export default function AddStaffModal({ mode = 'add', onClose, onCreated, availableRoles, accessLevelsByRole, availableDepartments, availableAccountTypes, availablePlatforms, jobTitlesByDepartment }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [humanStaffOptions, setHumanStaffOptions] = useState([]);

  const isPlatformIdentity = form.account_type !== 'HUMAN_STAFF';

  // Responsible Owner must reference a real SNS human staff account --
  // fetched once so Service Account / API Client creation can select a
  // real accountable person rather than free-text.
  useEffect(() => {
    fetchOwnerPlatformUsers({ accountType: 'HUMAN_STAFF', limit: 200 })
      .then((res) => setHumanStaffOptions(res.users))
      .catch(() => setHumanStaffOptions([]));
  }, []);

  // Job Title is department-scoped (Platform > Department > Job Title >
  // Platform Role > Access Level). Departments with a defined catalog
  // (see app/core/job_titles.py) get a validated dropdown; departments
  // without one yet fall back to free text.
  const catalogJobTitles = (jobTitlesByDepartment && jobTitlesByDepartment[form.department]) || [];

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  // Changing Department resets Job Title -- a title picked for a prior
  // department's catalog is not guaranteed valid for the new one.
  const updateDepartment = (e) => setForm((f) => ({ ...f, department: e.target.value, job_title: '' }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.role) {
      setError('Platform role is required.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        middle_name: form.middle_name.trim() || undefined,
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        department: form.department || undefined,
        platform: form.platform || undefined,
        role: form.role,
        account_type: form.account_type,
        start_date: form.start_date || undefined,
        job_title: !isPlatformIdentity ? (form.job_title.trim() || undefined) : undefined,
        responsible_owner_id: isPlatformIdentity ? (form.responsible_owner_id || undefined) : undefined,
        purpose: isPlatformIdentity ? (form.purpose.trim() || undefined) : undefined,
        scope: (isPlatformIdentity && form.account_type === 'API_CLIENT') ? (form.scope.trim() || undefined) : undefined,
      };
      const result = await createOwnerPlatformStaff(payload);
      onCreated(result);
    } catch (err) {
      setError(err?.message || 'Failed to create SNS staff account');
    } finally {
      setSubmitting(false);
    }
  };

  const title = mode === 'invite' ? 'Invite SNS Staff' : 'Add SNS Staff';
  const submitLabel = mode === 'invite' ? 'Send Invitation' : 'Add Staff';

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[1000] p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-[520px] max-h-[85vh] overflow-y-auto rounded-2xl bg-sns-card border border-sns-border shadow-panel p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-text-primary">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-md bg-transparent flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-sns-border-subtle transition-colors"
            aria-label="Close"
          >
            <IconClose />
          </button>
        </div>

        {mode === 'invite' && (
          <p className="mb-3 text-xs text-text-tertiary">
            The account is created immediately with a temporary password and reset link -- there is no separate pending-invitation state yet (planned for a future phase).
          </p>
        )}

        {error && (
          <div className="mb-3 px-3 py-2 rounded-lg bg-status-critical/10 border border-status-critical/20 text-status-critical text-xs">
            {error}
          </div>
        )}

        <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-3 mb-1.5">Identity</p>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <input className={FIELD_CLASS} placeholder="First name (required)" required value={form.first_name} onChange={update('first_name')} />
            <input className={FIELD_CLASS} placeholder="Middle name" value={form.middle_name} onChange={update('middle_name')} />
            <input className={FIELD_CLASS} placeholder="Last name (required)" required value={form.last_name} onChange={update('last_name')} />
          </div>
          <input className={FIELD_CLASS} type="email" placeholder="Work email (required)" required value={form.email} onChange={update('email')} />
          <input className={FIELD_CLASS} placeholder="Phone (optional)" value={form.phone} onChange={update('phone')} />
        </div>

        <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-4 mb-1.5">Platform Assignment</p>
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-text-tertiary">Platform</span>
            <div className="relative">
              <select className={SELECT_CLASS} value={form.platform} onChange={update('platform')}>
                {(availablePlatforms || ['SNS Hospice Solutions']).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
            </div>
          </label>
          <div className="relative">
            <select className={SELECT_CLASS} value={form.department} onChange={updateDepartment}>
              <option value="">No department selected</option>
              {(availableDepartments || []).map((d) => (
                <option key={d} value={d}>{labelize(d)}</option>
              ))}
            </select>
            <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
          {!isPlatformIdentity && (
            catalogJobTitles.length > 0 ? (
              <div className="relative">
                <select className={SELECT_CLASS} value={form.job_title} onChange={update('job_title')}>
                  <option value="">Select a job title (optional)</option>
                  {catalogJobTitles.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
              </div>
            ) : (
              <input className={FIELD_CLASS} placeholder="Job title (optional)" value={form.job_title} onChange={update('job_title')} />
            )
          )}
          <div className="relative">
            <select className={SELECT_CLASS} required value={form.role} onChange={update('role')}>
              <option value="">Select a platform role (required)</option>
              {(availableRoles || []).map((r) => (
                <option key={r} value={r}>{labelize(r)}</option>
              ))}
            </select>
            <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
          {form.role && (
            <p className="text-[11px] text-text-tertiary px-1">
              Access Level (derived): <span className="font-semibold text-text-secondary">{accessLevelLabel((accessLevelsByRole || {})[form.role])}</span>
            </p>
          )}
        </div>

        <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-4 mb-1.5">Employment</p>
        <div className="flex flex-col gap-2">
          <div className="px-3 py-2.5 rounded-lg border border-sns-border bg-sns-app text-[13px] text-text-tertiary">
            Status: Active (new accounts start active; use Suspend/Activate after creation)
          </div>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-text-tertiary">Start date (optional)</span>
            <input className={FIELD_CLASS} type="date" value={form.start_date} onChange={update('start_date')} />
          </label>
        </div>

        <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-4 mb-1.5">Security</p>
        <div className="flex flex-col gap-2">
          <div className="relative">
            <select className={SELECT_CLASS} value={form.account_type} onChange={update('account_type')}>
              {(availableAccountTypes || ['HUMAN_STAFF']).map((t) => (
                <option key={t} value={t}>{labelize(t)}</option>
              ))}
            </select>
            <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
        </div>


        {isPlatformIdentity && (
          <>
            <p className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider mt-4 mb-1.5">Identity Accountability</p>
            <p className="text-xs text-text-tertiary mb-2">
              {form.account_type === 'API_CLIENT' ? 'API Clients' : 'Service Accounts and Automation Accounts'} are platform identities, not employees -- every one must be accountable to a real SNS staff member.
            </p>
            <div className="flex flex-col gap-2">
              <div className="relative">
                <select className={SELECT_CLASS} value={form.responsible_owner_id} onChange={update('responsible_owner_id')}>
                  <option value="">Select a responsible owner (optional)</option>
                  {humanStaffOptions.map((u) => (
                    <option key={u.user_id} value={u.user_id}>{u.full_name} ({u.email})</option>
                  ))}
                </select>
                <IconChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
              </div>
              <textarea className={FIELD_CLASS} placeholder="Purpose -- why this identity exists (optional)" rows={2} value={form.purpose} onChange={update('purpose')} />
              {form.account_type === 'API_CLIENT' && (
                <input className={FIELD_CLASS} placeholder="Scope -- what it is authorized to touch (optional)" value={form.scope} onChange={update('scope')} />
              )}
            </div>
          </>
        )}

        <div className="flex gap-2.5 mt-5 justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] text-text-primary text-[13px] font-semibold hover:bg-[var(--owner-btn-secondary-hover)] transition-colors disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-ai text-ai-on text-[13px] font-bold hover:bg-ai/90 transition-colors disabled:opacity-60"
          >
            {submitting ? 'Saving…' : submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
}
