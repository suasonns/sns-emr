import React, { useCallback, useEffect, useState } from 'react';
import { COLORS } from '../../design';
import { listStaff, createStaff, updateStaff, revealStaffSsn } from '../../../api/staff';
import { formatRoleLabel } from '../../../utils/roleLabel';

const ROLE_OPTIONS = [
  { value: 'ADMINISTRATOR', label: 'Administrator' },
  { value: 'DPCS', label: 'DPCS' },
  { value: 'DPCS_ADMINISTRATOR', label: 'DPCS / Administrator' },
  { value: 'MEDICAL_DIRECTOR', label: 'Medical Director' },
  { value: 'ATTENDING_PHYSICIAN', label: 'Attending Physician' },
  { value: 'RN', label: 'RN' },
  { value: 'LVN', label: 'LVN' },
  { value: 'CHHA', label: 'CHHA' },
  { value: 'SW', label: 'Social Worker' },
  { value: 'CHAPLAIN', label: 'Chaplain' },
  { value: 'VOLUNTEER_COORDINATOR', label: 'Volunteer Coordinator' },
  { value: 'CLINICAL_SUPERVISOR', label: 'Clinical Supervisor' },
  { value: 'CASE_MANAGER', label: 'Case Manager' },
  { value: 'BILLING', label: 'Billing' },
  { value: 'BILLING_MANAGER', label: 'Billing Manager' },
  { value: 'BILLING_SPECIALIST', label: 'Billing Specialist' },
  { value: 'COLLECTIONS', label: 'Collections' },
  { value: 'REVENUE_CYCLE', label: 'Revenue Cycle' },
  { value: 'QA_MANAGER', label: 'QA Manager' },
  { value: 'QA_REVIEWER', label: 'QA Reviewer' },
  { value: 'COMPLIANCE_OFFICER', label: 'Compliance Officer' },
  { value: 'INTAKE_MANAGER', label: 'Intake Manager' },
  { value: 'INTAKE_COORDINATOR', label: 'Intake Coordinator' },
  { value: 'SCHEDULER', label: 'Scheduler' },
  { value: 'STAFFING_COORDINATOR', label: 'Staffing Coordinator' },
];

const STAFF_TYPE_OPTIONS = [
  { value: 'C', label: 'C - Clinical' },
  { value: 'A', label: 'A - Administrative' },
  { value: 'X', label: 'X - Contracted Staff' },
  { value: 'Y', label: 'Y - Referral Source' },
];

const EMPTY_FORM = {
  email: '',
  first_name: '',
  middle_name: '',
  last_name: '',
  role: 'RN',
  active: true,
  date_of_birth: '',
  address_street: '',
  address_city: '',
  address_state: '',
  address_zip: '',
  phone: '',
  home_phone: '',
  job_title: '',
  discipline: '',
  license_number: '',
  npi: '',
  employment_date: '',
  staff_type: 'C',
  ssn: '',
};

const inputStyle = {
  width: '100%',
  padding: '8px 10px',
  borderRadius: 6,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.text,
  fontSize: 13,
  boxSizing: 'border-box',
  fontFamily: 'Inter, sans-serif',
};
const labelStyle = { fontSize: 11, fontWeight: 600, color: COLORS.textDim, textTransform: 'uppercase', marginBottom: 4, display: 'block', fontFamily: 'Inter, sans-serif' };
const fieldGroup = { marginBottom: 10 };

function Field({ label, children }) {
  return (
    <div style={fieldGroup}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

export default function AnalyticsHR() {
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('active');

  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [ssnMasked, setSsnMasked] = useState('');
  const [ssnRevealed, setSsnRevealed] = useState('');
  const [ssnRevealing, setSsnRevealing] = useState(false);
  const [ssnRevealError, setSsnRevealError] = useState('');

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    listStaff({ status: statusFilter })
      .then((list) => setStaffList(list || []))
      .catch((err) => {
        console.error('Failed to load staff:', err);
        setError(err?.response?.data?.detail || 'Unable to load staff.');
      })
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => { reload(); }, [reload]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setSaveError('');
    setSsnMasked('');
    setSsnRevealed('');
    setSsnRevealError('');
    setFormOpen(true);
  };

  const openEdit = (member) => {
    setEditingId(member.id);
    setForm({
      email: member.email || '',
      first_name: member.first_name || '',
      middle_name: member.middle_name || '',
      last_name: member.last_name || '',
      role: member.role || 'RN',
      active: !!member.active,
      date_of_birth: member.date_of_birth || '',
      address_street: member.address_street || '',
      address_city: member.address_city || '',
      address_state: member.address_state || '',
      address_zip: member.address_zip || '',
      phone: member.phone || '',
      home_phone: member.home_phone || '',
      job_title: member.job_title || '',
      discipline: member.discipline || '',
      license_number: member.license_number || '',
      npi: member.npi || '',
      employment_date: member.employment_date || '',
      staff_type: member.staff_type || 'C',
      ssn: '',
    });
    setSaveError('');
    setSsnMasked(member.ssn_masked || '');
    setSsnRevealed('');
    setSsnRevealError('');
    setFormOpen(true);
  };

  const handleRevealSsn = () => {
    if (!editingId) return;
    setSsnRevealing(true);
    setSsnRevealError('');
    revealStaffSsn(editingId)
      .then((res) => setSsnRevealed(res.ssn))
      .catch((err) => setSsnRevealError(err?.response?.data?.detail || 'Unable to reveal SSN.'))
      .finally(() => setSsnRevealing(false));
  };

  const update = (key) => (e) => {
    const value = e && e.target ? (e.target.type === 'checkbox' ? e.target.checked : e.target.value) : e;
    setForm((f) => ({ ...f, [key]: value }));
  };

  const submit = (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError('');
    const payload = {
      ...form,
      date_of_birth: form.date_of_birth || null,
      employment_date: form.employment_date || null,
    };
    if (!payload.ssn) {
      delete payload.ssn;
    }
    const action = editingId ? updateStaff(editingId, payload) : createStaff(payload);
    action
      .then(() => {
        setFormOpen(false);
        reload();
      })
      .catch((err) => {
        console.error('Failed to save staff member:', err);
        setSaveError(err?.response?.data?.detail || 'Unable to save staff member.');
      })
      .finally(() => setSaving(false));
  };

  const totalActive = staffList.filter((s) => s.active).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: '18px 20px' }}>
          <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>Total Staff</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{staffList.length}</div>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: '18px 20px' }}>
          <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>Active</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{totalActive}</div>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: '18px 20px' }}>
          <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>Inactive</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{staffList.length - totalActive}</div>
        </div>
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Staff Roster</div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ ...inputStyle, width: 'auto' }}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="both">All</option>
            </select>
            <button
              onClick={openCreate}
              style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}
            >
              + Add Staff Member
            </button>
          </div>
        </div>

        {error && <div style={{ padding: '12px 20px', color: COLORS.danger || '#e53935', fontSize: 13, fontFamily: 'Inter, sans-serif' }}>{error}</div>}
        {loading && <div style={{ padding: '12px 20px', color: COLORS.textDim, fontSize: 13, fontFamily: 'Inter, sans-serif' }}>Loading...</div>}

        {!loading && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {['Name', 'Role', 'Job Title', 'Phone', 'Email', 'License #', 'Status', ''].map((header) => (
                  <th key={header} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 11, color: COLORS.textDim, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {staffList.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: '20px', textAlign: 'center', color: COLORS.textDim, fontSize: 13, fontFamily: 'Inter, sans-serif' }}>No staff members found.</td>
                </tr>
              )}
              {staffList.map((person, index) => (
                <tr key={person.id} style={{ borderBottom: index < staffList.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }} onClick={() => openEdit(person)}>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{person.full_name}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{formatRoleLabel(person.role)}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{person.job_title || '—'}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{person.phone || '—'}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{person.email}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{person.license_number || '—'}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: person.active ? COLORS.success : COLORS.textDim, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{person.active ? 'Active' : 'Inactive'}</td>
                  <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.primary, fontFamily: 'Inter, sans-serif' }}>Edit</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {formOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', zIndex: 1000, overflowY: 'auto', padding: '40px 20px' }} onClick={() => setFormOpen(false)}>
          <form
            onSubmit={submit}
            onClick={(e) => e.stopPropagation()}
            style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, width: 640, maxWidth: '100%' }}
          >
            <h2 style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, marginTop: 0, fontFamily: 'Inter, sans-serif' }}>
              {editingId ? 'Edit Staff Member' : 'Add Staff Member'}
            </h2>

            <h3 style={{ fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Personal Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <Field label="First Name"><input style={inputStyle} required value={form.first_name} onChange={update('first_name')} /></Field>
              <Field label="Middle Name"><input style={inputStyle} value={form.middle_name} onChange={update('middle_name')} /></Field>
              <Field label="Last Name"><input style={inputStyle} required value={form.last_name} onChange={update('last_name')} /></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <Field label="Date of Birth"><input type="date" style={inputStyle} value={form.date_of_birth || ''} onChange={update('date_of_birth')} /></Field>
              <Field label="Cell Phone"><input style={inputStyle} value={form.phone} onChange={update('phone')} /></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <Field label="Social Security Number">
                <input
                  style={inputStyle}
                  placeholder={ssnMasked ? `On file: ${ssnMasked}` : 'e.g. 123-45-6789'}
                  value={form.ssn}
                  onChange={update('ssn')}
                  autoComplete="off"
                />
                <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 4, fontFamily: 'Inter, sans-serif' }}>
                  {ssnMasked ? 'Leave blank to keep the SSN on file unchanged.' : 'Encrypted at rest. Optional.'}
                </div>
              </Field>
              {editingId && ssnMasked && (
                <Field label=" ">
                  {ssnRevealed ? (
                    <div style={{ ...inputStyle, background: 'transparent', border: 'none', padding: '8px 0', fontWeight: 700, color: COLORS.text }}>{ssnRevealed}</div>
                  ) : (
                    <button
                      type="button"
                      onClick={handleRevealSsn}
                      disabled={ssnRevealing}
                      style={{ padding: '9px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}
                    >
                      {ssnRevealing ? 'Revealing...' : 'Reveal SSN on file'}
                    </button>
                  )}
                  {ssnRevealError && <div style={{ color: COLORS.danger || '#e53935', fontSize: 12, marginTop: 4, fontFamily: 'Inter, sans-serif' }}>{ssnRevealError}</div>}
                </Field>
              )}
            </div>
            <Field label="Street Address"><input style={inputStyle} value={form.address_street} onChange={update('address_street')} /></Field>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <Field label="City"><input style={inputStyle} value={form.address_city} onChange={update('address_city')} /></Field>
              <Field label="State"><input style={inputStyle} maxLength={2} value={form.address_state} onChange={update('address_state')} /></Field>
              <Field label="Zip"><input style={inputStyle} value={form.address_zip} onChange={update('address_zip')} /></Field>
            </div>

            <h3 style={{ fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Professional Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <Field label="Job Title"><input style={inputStyle} value={form.job_title} onChange={update('job_title')} /></Field>
              <Field label="Discipline"><input style={inputStyle} value={form.discipline} onChange={update('discipline')} /></Field>
              <Field label="Professional License #"><input style={inputStyle} value={form.license_number} onChange={update('license_number')} /></Field>
              <Field label="NPI (MD/NP/PA)"><input style={inputStyle} value={form.npi} onChange={update('npi')} /></Field>
              <Field label="Employment Date"><input type="date" style={inputStyle} value={form.employment_date || ''} onChange={update('employment_date')} /></Field>
            </div>

            <h3 style={{ fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Access / Account Setting</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <Field label="Email">
                <input type="email" style={inputStyle} required value={form.email} onChange={update('email')} disabled={!!editingId} />
              </Field>
              <Field label="Access Level (Role)">
                <select style={inputStyle} value={form.role} onChange={update('role')}>
                  {ROLE_OPTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </Field>
              <Field label="Staff Type">
                <select style={inputStyle} value={form.staff_type} onChange={update('staff_type')}>
                  {STAFF_TYPE_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <Field label="Status">
                <select style={inputStyle} value={form.active ? 'active' : 'inactive'} onChange={(e) => setForm((f) => ({ ...f, active: e.target.value === 'active' }))}>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </Field>
            </div>

            {saveError && <div style={{ color: COLORS.danger || '#e53935', fontSize: 13, marginTop: 8, fontFamily: 'Inter, sans-serif' }}>{saveError}</div>}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
              <button type="button" onClick={() => setFormOpen(false)} style={{ padding: '9px 18px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Cancel</button>
              <button type="submit" disabled={saving} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
