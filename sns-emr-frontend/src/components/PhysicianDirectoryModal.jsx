import React, { useEffect, useMemo, useState } from 'react';
import {
  createPhysician,
  getPhysician,
  listPhysicians,
  npiLookup,
  pecosCheck,
  updatePhysician,
} from '../api/physicians';

const TITLE_OPTIONS = ['', 'MD', 'DO', 'NP', 'PA', 'Other'];
const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'both', label: 'Both' },
];

const createDefaultFilters = () => ({
  status: 'active',
  specialty: '',
  name: '',
  license_number: '',
  npi: '',
});

const createEmptyForm = () => ({
  id: '',
  npi: '',
  display_name: '',
  last_name: '',
  first_name: '',
  title: '',
  specialty_type: '',
  license_number: '',
  taxonomy_code: '',
  address_street: '',
  address_suite: '',
  address_city: '',
  address_state: '',
  address_zip: '',
  phone: '',
  fax: '',
  email: '',
  contact_name: '',
  protocol_notes: '',
  status: 'active',
  register_for_eprescription: false,
  pecos_status: '',
  pecos_checked_at: null,
});

const overlayStyle = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(15, 23, 42, 0.55)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 20,
  zIndex: 1100,
};

const modalStyle = (colors) => ({
  width: 'min(1180px, 100%)',
  maxHeight: '90vh',
  overflow: 'hidden',
  backgroundColor: colors.card,
  color: colors.white,
  border: `1px solid ${colors.border}`,
  borderRadius: 14,
  boxShadow: '0 24px 80px rgba(15, 23, 42, 0.35)',
  display: 'flex',
  flexDirection: 'column',
});

const inputStyle = (colors) => ({
  width: '100%',
  boxSizing: 'border-box',
  backgroundColor: colors.bg,
  border: `1px solid ${colors.border}`,
  borderRadius: 8,
  color: colors.white,
  fontSize: 12,
  lineHeight: 1.3,
  padding: '8px 10px',
  outline: 'none',
  fontFamily: 'inherit',
});

const buttonStyle = (colors, variant = 'primary') => {
  const isPrimary = variant === 'primary';
  return {
    border: `1px solid ${isPrimary ? colors.teal : colors.border}`,
    backgroundColor: isPrimary ? colors.teal : colors.bg,
    color: isPrimary ? '#ffffff' : colors.white,
    borderRadius: 8,
    padding: '8px 12px',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
  };
};

const badgeStyle = (colors, status) => {
  if (status === 'enrolled') {
    return { color: colors.green, backgroundColor: colors.greenBg, borderColor: colors.green, label: '✓ Enrolled' };
  }
  if (status === 'opted_out') {
    return { color: colors.amber, backgroundColor: colors.amberBg, borderColor: colors.amber, label: '⚠ Opted out' };
  }
  return { color: colors.label, backgroundColor: colors.bg, borderColor: colors.border, label: '? Unknown' };
};

const normalizeText = (value) => (typeof value === 'string' ? value : value ?? '');
const buildDisplayName = (form) => form.display_name.trim() || [form.first_name.trim(), form.last_name.trim()].filter(Boolean).join(' ');

const createFormFromPhysician = (physician) => ({
  ...createEmptyForm(),
  id: physician?.id || '',
  npi: normalizeText(physician?.npi),
  display_name: normalizeText(physician?.display_name),
  last_name: normalizeText(physician?.last_name),
  first_name: normalizeText(physician?.first_name),
  title: normalizeText(physician?.title),
  specialty_type: normalizeText(physician?.specialty_type),
  license_number: normalizeText(physician?.license_number),
  taxonomy_code: normalizeText(physician?.taxonomy_code),
  address_street: normalizeText(physician?.address_street),
  address_suite: normalizeText(physician?.address_suite),
  address_city: normalizeText(physician?.address_city),
  address_state: normalizeText(physician?.address_state),
  address_zip: normalizeText(physician?.address_zip),
  phone: normalizeText(physician?.phone),
  fax: normalizeText(physician?.fax),
  email: normalizeText(physician?.email),
  contact_name: normalizeText(physician?.contact_name),
  protocol_notes: normalizeText(physician?.protocol_notes),
  status: physician?.status || 'active',
  register_for_eprescription: Boolean(physician?.register_for_eprescription),
  pecos_status: normalizeText(physician?.pecos_status),
  pecos_checked_at: physician?.pecos_checked_at || null,
});

const Field = ({ colors, label, value, onChange, textarea = false, selectOptions = null, type = 'text' }) => (
  <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
    <span style={{ fontSize: 11, color: colors.label, fontWeight: 600, textTransform: 'uppercase' }}>{label}</span>
    {selectOptions ? (
      <select value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle(colors)}>
        {selectOptions.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    ) : textarea ? (
      <textarea value={value} rows={3} onChange={(event) => onChange(event.target.value)} style={{ ...inputStyle(colors), resize: 'vertical', minHeight: 84 }} />
    ) : (
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle(colors)} />
    )}
  </label>
);

const PecosBadge = ({ colors, status }) => {
  const tone = badgeStyle(colors, status);
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      borderRadius: 999,
      border: `1px solid ${tone.borderColor}`,
      backgroundColor: tone.backgroundColor,
      color: tone.color,
      fontSize: 11,
      fontWeight: 700,
      padding: '4px 8px',
      whiteSpace: 'nowrap',
    }}>
      {tone.label}
    </span>
  );
};

const PhysicianDirectoryModal = ({ open, onClose, onSelect, colors, title = 'Physician Directory' }) => {
  const [filters, setFilters] = useState(createDefaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(createDefaultFilters);
  const [physicians, setPhysicians] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editorMode, setEditorMode] = useState('hidden');
  const [form, setForm] = useState(createEmptyForm());
  const [saving, setSaving] = useState(false);
  const [editorError, setEditorError] = useState('');
  const [lookupState, setLookupState] = useState({ loading: false, error: '', message: '' });
  const [pecosState, setPecosState] = useState({ loading: false, error: '', result: null });

  const activePecosStatus = pecosState.result?.status || form.pecos_status || 'unknown';
  const editorHeading = editorMode === 'edit' ? 'Edit Physician' : 'Add New Physician';

  const loadPhysicians = async (nextFilters = appliedFilters) => {
    try {
      setLoading(true);
      const data = await listPhysicians(nextFilters);
      setPhysicians(data);
    } catch (error) {
      console.error('Failed to load physicians', error);
      setPhysicians([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!open) return;

    const defaults = createDefaultFilters();
    setFilters(defaults);
    setAppliedFilters(defaults);
    setEditorMode('hidden');
    setForm(createEmptyForm());
    setEditorError('');
    setLookupState({ loading: false, error: '', message: '' });
    setPecosState({ loading: false, error: '', result: null });
    loadPhysicians(defaults);
  }, [open]);

  const handleApplyFilters = async () => {
    setAppliedFilters(filters);
    await loadPhysicians(filters);
  };

  const handleResetFilters = async () => {
    const defaults = createDefaultFilters();
    setFilters(defaults);
    setAppliedFilters(defaults);
    await loadPhysicians(defaults);
  };

  const handleEdit = async (physician) => {
    try {
      setEditorError('');
      setLookupState({ loading: false, error: '', message: '' });
      setPecosState({ loading: false, error: '', result: physician?.pecos_status ? { status: physician.pecos_status } : null });
      setEditorMode('edit');
      const latest = physician?.id ? await getPhysician(physician.id) : physician;
      setForm(createFormFromPhysician(latest));
    } catch (error) {
      console.error('Failed to load physician', error);
      setEditorError('Unable to load physician details.');
    }
  };

  const startAdd = () => {
    setEditorMode('add');
    setForm(createEmptyForm());
    setEditorError('');
    setLookupState({ loading: false, error: '', message: '' });
    setPecosState({ loading: false, error: '', result: null });
  };

  const persistPhysician = async (selectAfterSave = false) => {
    const displayName = buildDisplayName(form);
    if (!displayName) {
      setEditorError('Name, first name, or last name is required.');
      return;
    }

    const payload = {
      npi: form.npi || null,
      display_name: displayName,
      last_name: form.last_name || null,
      first_name: form.first_name || null,
      title: form.title || null,
      specialty_type: form.specialty_type || null,
      license_number: form.license_number || null,
      taxonomy_code: form.taxonomy_code || null,
      address_street: form.address_street || null,
      address_suite: form.address_suite || null,
      address_city: form.address_city || null,
      address_state: form.address_state || null,
      address_zip: form.address_zip || null,
      phone: form.phone || null,
      fax: form.fax || null,
      email: form.email || null,
      contact_name: form.contact_name || null,
      protocol_notes: form.protocol_notes || null,
      status: form.status || 'active',
      register_for_eprescription: Boolean(form.register_for_eprescription),
      pecos_status: form.pecos_status || null,
      pecos_checked_at: form.pecos_status ? (form.pecos_checked_at || new Date().toISOString()) : null,
    };

    try {
      setSaving(true);
      setEditorError('');
      const saved = form.id
        ? await updatePhysician(form.id, payload)
        : await createPhysician(payload);
      await loadPhysicians(appliedFilters);
      setEditorMode('edit');
      setForm(createFormFromPhysician(saved));
      if (selectAfterSave) {
        onSelect(saved);
        onClose();
      }
    } catch (error) {
      console.error('Failed to save physician', error);
      setEditorError('Unable to save physician. Please review the entry and try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleNpiLookup = async () => {
    if (!form.npi.trim()) {
      setLookupState({ loading: false, error: 'Enter an NPI before lookup.', message: '' });
      return;
    }

    try {
      setLookupState({ loading: true, error: '', message: '' });
      const result = await npiLookup(form.npi.trim());
      if (!result.found) {
        setLookupState({ loading: false, error: result.error || 'No NPI registry match found.', message: '' });
        return;
      }

      setForm((current) => {
        const firstName = result.first_name || current.first_name;
        const lastName = result.last_name || current.last_name;
        const lookedUpDisplayName = [result.first_name, result.last_name].filter(Boolean).join(' ');
        const nextDisplayName = lookedUpDisplayName || current.display_name;
        return {
          ...current,
          first_name: firstName,
          last_name: lastName,
          display_name: nextDisplayName,
          title: result.credential || current.title,
          specialty_type: result.taxonomy_description || current.specialty_type,
          taxonomy_code: result.taxonomy_code || current.taxonomy_code,
          address_street: result.address_street || current.address_street,
          address_city: result.address_city || current.address_city,
          address_state: result.address_state || current.address_state,
          address_zip: result.address_zip || current.address_zip,
          phone: result.phone || current.phone,
        };
      });
      setLookupState({ loading: false, error: '', message: 'NPI registry data applied.' });
    } catch (error) {
      console.error('NPI lookup failed', error);
      setLookupState({ loading: false, error: 'NPI lookup is unavailable right now.', message: '' });
    }
  };

  const handlePecosCheck = async () => {
    if (!form.npi.trim()) {
      setPecosState({ loading: false, error: 'Enter an NPI before checking PECOS.', result: null });
      return;
    }

    try {
      setPecosState({ loading: true, error: '', result: null });
      const result = await pecosCheck(form.npi.trim());
      setPecosState({ loading: false, error: '', result });
      setForm((current) => ({
        ...current,
        pecos_status: result.status || 'unknown',
        pecos_checked_at: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('PECOS check failed', error);
      setPecosState({ loading: false, error: 'PECOS check is unavailable right now.', result: null });
    }
  };

  const rows = useMemo(() => physicians, [physicians]);
  if (!open) return null;

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle(colors)} onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 18px', borderBottom: `1px solid ${colors.border}` }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{title}</div>
            <div style={{ color: colors.label, fontSize: 12, marginTop: 4 }}>Confidential physician directory — accessible only from the Facesheet physician picker.</div>
          </div>
          <button type="button" onClick={onClose} style={{ ...buttonStyle(colors, 'secondary'), paddingInline: 10 }}>✕</button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: editorMode === 'hidden' ? '1fr' : 'minmax(0, 1.25fr) minmax(320px, 0.9fr)', gap: 0, minHeight: 0, flex: 1 }}>
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, borderRight: editorMode === 'hidden' ? 'none' : `1px solid ${colors.border}` }}>
            <div style={{ padding: 16, borderBottom: `1px solid ${colors.border}`, display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 10 }}>
              <Field colors={colors} label="Status" value={filters.status} onChange={(value) => setFilters((current) => ({ ...current, status: value }))} selectOptions={STATUS_OPTIONS} />
              <Field colors={colors} label="Type / Specialty" value={filters.specialty} onChange={(value) => setFilters((current) => ({ ...current, specialty: value }))} />
              <Field colors={colors} label="Name" value={filters.name} onChange={(value) => setFilters((current) => ({ ...current, name: value }))} />
              <Field colors={colors} label="License #" value={filters.license_number} onChange={(value) => setFilters((current) => ({ ...current, license_number: value }))} />
              <Field colors={colors} label="NPI #" value={filters.npi} onChange={(value) => setFilters((current) => ({ ...current, npi: value }))} />
              <div style={{ display: 'flex', gap: 8, alignItems: 'end', gridColumn: '1 / -1' }}>
                <button type="button" style={buttonStyle(colors)} onClick={handleApplyFilters}>Search</button>
                <button type="button" style={buttonStyle(colors, 'secondary')} onClick={handleResetFilters}>Reset</button>
                <button type="button" style={buttonStyle(colors)} onClick={startAdd}>+ Add New Physician</button>
              </div>
            </div>

            <div style={{ overflow: 'auto', padding: 16 }}>
              {loading ? (
                <div style={{ color: colors.label, fontSize: 12 }}>Loading directory…</div>
              ) : rows.length === 0 ? (
                <div style={{ color: colors.label, fontSize: 12 }}>No physicians matched the current filters.</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr>
                      {['Type', 'Name', 'Title', 'Specialty', 'License#', 'NPI#', 'Address', 'Phone', 'Fax', 'Status', 'Actions'].map((heading) => (
                        <th key={heading} style={{ textAlign: 'left', padding: '8px 10px', position: 'sticky', top: 0, backgroundColor: colors.card, color: colors.label, borderBottom: `1px solid ${colors.border}`, whiteSpace: 'nowrap' }}>{heading}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((physician) => {
                      const address = [physician.address_street, physician.address_suite, physician.address_city, physician.address_state, physician.address_zip].filter(Boolean).join(', ');
                      return (
                        <tr key={physician.id} style={{ borderBottom: `1px solid ${colors.border}` }}>
                          <td style={{ padding: '10px' }}>{physician.specialty_type || '—'}</td>
                          <td style={{ padding: '10px', fontWeight: 600 }}>{physician.display_name}</td>
                          <td style={{ padding: '10px' }}>{physician.title || '—'}</td>
                          <td style={{ padding: '10px' }}>{physician.specialty_type || physician.taxonomy_code || '—'}</td>
                          <td style={{ padding: '10px' }}>{physician.license_number || '—'}</td>
                          <td style={{ padding: '10px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                              <span>{physician.npi || '—'}</span>
                              <PecosBadge colors={colors} status={physician.pecos_status || 'unknown'} />
                            </div>
                          </td>
                          <td style={{ padding: '10px', minWidth: 180 }}>{address || '—'}</td>
                          <td style={{ padding: '10px' }}>{physician.phone || '—'}</td>
                          <td style={{ padding: '10px' }}>{physician.fax || '—'}</td>
                          <td style={{ padding: '10px' }}>{physician.status === 'inactive' ? 'Inactive' : 'Active'}</td>
                          <td style={{ padding: '10px' }}>
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                              <button type="button" style={buttonStyle(colors)} onClick={() => { onSelect(physician); onClose(); }}>Select</button>
                              <button type="button" style={buttonStyle(colors, 'secondary')} onClick={() => handleEdit(physician)}>Edit</button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {editorMode !== 'hidden' ? (
            <div style={{ padding: 16, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700 }}>{editorHeading}</div>
                  <div style={{ fontSize: 12, color: colors.label, marginTop: 4 }}>Save a reusable physician profile, or save and select it immediately for this patient.</div>
                </div>
                <button type="button" style={buttonStyle(colors, 'secondary')} onClick={() => setEditorMode('hidden')}>Hide</button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 8, alignItems: 'end' }}>
                <Field colors={colors} label="NPI#" value={form.npi} onChange={(value) => setForm((current) => ({ ...current, npi: value }))} />
                <button type="button" style={buttonStyle(colors, 'secondary')} onClick={handleNpiLookup} disabled={lookupState.loading}>{lookupState.loading ? 'Looking up…' : 'NPI Lookup'}</button>
                <button type="button" style={buttonStyle(colors, 'secondary')} onClick={handlePecosCheck} disabled={pecosState.loading}>{pecosState.loading ? 'Checking…' : 'Check PECOS'}</button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                <PecosBadge colors={colors} status={activePecosStatus} />
                {lookupState.message ? <span style={{ color: colors.green, fontSize: 12 }}>{lookupState.message}</span> : null}
                {lookupState.error ? <span style={{ color: colors.red, fontSize: 12 }}>{lookupState.error}</span> : null}
                {pecosState.error ? <span style={{ color: colors.red, fontSize: 12 }}>{pecosState.error}</span> : null}
                {pecosState.result?.reason ? <span style={{ color: colors.label, fontSize: 12 }}>{pecosState.result.reason}</span> : null}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
                <Field colors={colors} label="Name" value={form.display_name} onChange={(value) => setForm((current) => ({ ...current, display_name: value }))} />
                <Field colors={colors} label="Title" value={form.title} onChange={(value) => setForm((current) => ({ ...current, title: value }))} selectOptions={TITLE_OPTIONS.map((option) => ({ value: option, label: option || 'Select title' }))} />
                <Field colors={colors} label="Last Name" value={form.last_name} onChange={(value) => setForm((current) => ({ ...current, last_name: value }))} />
                <Field colors={colors} label="First Name" value={form.first_name} onChange={(value) => setForm((current) => ({ ...current, first_name: value }))} />
                <Field colors={colors} label="Specialty / Type" value={form.specialty_type} onChange={(value) => setForm((current) => ({ ...current, specialty_type: value }))} />
                <Field colors={colors} label="License#" value={form.license_number} onChange={(value) => setForm((current) => ({ ...current, license_number: value }))} />
                <Field colors={colors} label="Taxonomy" value={form.taxonomy_code} onChange={(value) => setForm((current) => ({ ...current, taxonomy_code: value }))} />
                <Field colors={colors} label="Status" value={form.status} onChange={(value) => setForm((current) => ({ ...current, status: value }))} selectOptions={STATUS_OPTIONS.filter((option) => option.value !== 'both')} />
                <Field colors={colors} label="Street" value={form.address_street} onChange={(value) => setForm((current) => ({ ...current, address_street: value }))} />
                <Field colors={colors} label="Suite / Apt" value={form.address_suite} onChange={(value) => setForm((current) => ({ ...current, address_suite: value }))} />
                <Field colors={colors} label="City" value={form.address_city} onChange={(value) => setForm((current) => ({ ...current, address_city: value }))} />
                <Field colors={colors} label="State" value={form.address_state} onChange={(value) => setForm((current) => ({ ...current, address_state: value }))} />
                <Field colors={colors} label="Zip" value={form.address_zip} onChange={(value) => setForm((current) => ({ ...current, address_zip: value }))} />
                <Field colors={colors} label="Phone" value={form.phone} onChange={(value) => setForm((current) => ({ ...current, phone: value }))} />
                <Field colors={colors} label="Fax" value={form.fax} onChange={(value) => setForm((current) => ({ ...current, fax: value }))} />
                <Field colors={colors} label="Email" value={form.email} onChange={(value) => setForm((current) => ({ ...current, email: value }))} type="email" />
                <Field colors={colors} label="Contact Name" value={form.contact_name} onChange={(value) => setForm((current) => ({ ...current, contact_name: value }))} />
              </div>

              <Field colors={colors} label="Protocol / Notes" value={form.protocol_notes} onChange={(value) => setForm((current) => ({ ...current, protocol_notes: value }))} textarea />

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: colors.white }}>
                <input
                  type="checkbox"
                  checked={Boolean(form.register_for_eprescription)}
                  onChange={(event) => setForm((current) => ({ ...current, register_for_eprescription: event.target.checked }))}
                />
                Register for e-Prescription
              </label>

              {editorError ? <div style={{ color: colors.red, fontSize: 12 }}>{editorError}</div> : null}

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" style={buttonStyle(colors)} onClick={() => persistPhysician(false)} disabled={saving}>{saving ? 'Saving…' : 'Save Physician'}</button>
                <button type="button" style={buttonStyle(colors)} onClick={() => persistPhysician(true)} disabled={saving}>{saving ? 'Saving…' : 'Save & Select'}</button>
                <button type="button" style={buttonStyle(colors, 'secondary')} onClick={() => setForm(createEmptyForm())}>Clear</button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default PhysicianDirectoryModal;
