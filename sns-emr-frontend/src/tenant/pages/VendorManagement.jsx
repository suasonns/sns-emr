import React, { useCallback, useEffect, useRef, useState } from 'react';
import { COLORS, S } from '../design';
import { listVendors, createVendor, updateVendor, deleteVendor, lookupVendorAddress } from '../../api/vendors';

const VENDOR_TYPES = ['Pharmacy', 'DME', 'Laboratory', 'AL', 'Contracted Staff', 'Other'];

const EMPTY_FORM = {
  vendor_type: 'Pharmacy',
  name: '',
  ncpdp_id: '',
  address_street: '',
  address_city: '',
  address_state: '',
  address_zip: '',
  phone: '',
  fax: '',
  email: '',
  contact_person: '',
  npi: '',
  rx_state_lic: '',
  bus_lic: '',
  insurance: '',
  note: '',
};

const inputStyle = {
  width: '100%',
  padding: '8px 10px',
  borderRadius: 6,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.white,
  fontSize: 13,
  boxSizing: 'border-box',
};
const labelStyle = { fontSize: 11, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', marginBottom: 4, display: 'block' };
const fieldGroup = { marginBottom: 10 };

export default function VendorManagement() {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [nameFilter, setNameFilter] = useState('');

  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [addressLookupStatus, setAddressLookupStatus] = useState('idle'); // idle | searching | found | notfound
  const addressLookupTimer = useRef(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    listVendors({ status: 'both', vendor_type: typeFilter || undefined, name: nameFilter || undefined })
      .then((list) => setVendors(list || []))
      .catch((err) => {
        console.error('Failed to load vendors:', err);
        setError(err?.response?.data?.detail || 'Unable to load vendors.');
      })
      .finally(() => setLoading(false));
  }, [typeFilter, nameFilter]);

  useEffect(() => { reload(); }, [reload]);

  // Auto-populate city/state/zip once the user types enough of a street address.
  useEffect(() => {
    if (addressLookupTimer.current) clearTimeout(addressLookupTimer.current);
    const street = (form.address_street || '').trim();
    if (street.length < 8) {
      setAddressLookupStatus('idle');
      return;
    }
    addressLookupTimer.current = setTimeout(() => {
      const combined = [street, form.address_city, form.address_state, form.address_zip].filter(Boolean).join(' ');
      setAddressLookupStatus('searching');
      lookupVendorAddress(combined)
        .then((result) => {
          if (!result.found) {
            setAddressLookupStatus('notfound');
            return;
          }
          setAddressLookupStatus('found');
          setForm((f) => ({
            ...f,
            address_city: f.address_city || result.address_city || f.address_city,
            address_state: f.address_state || result.address_state || f.address_state,
            address_zip: f.address_zip || result.address_zip || f.address_zip,
          }));
        })
        .catch(() => setAddressLookupStatus('notfound'));
    }, 700);
    return () => { if (addressLookupTimer.current) clearTimeout(addressLookupTimer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.address_street]);

  const openNew = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setSaveError('');
    setAddressLookupStatus('idle');
    setFormOpen(true);
  };

  const openEdit = (vendor) => {
    setEditingId(vendor.id);
    setForm({
      vendor_type: vendor.vendor_type || 'Pharmacy',
      name: vendor.name || '',
      ncpdp_id: vendor.ncpdp_id || '',
      address_street: vendor.address_street || '',
      address_city: vendor.address_city || '',
      address_state: vendor.address_state || '',
      address_zip: vendor.address_zip || '',
      phone: vendor.phone || '',
      fax: vendor.fax || '',
      email: vendor.email || '',
      contact_person: vendor.contact_person || '',
      npi: vendor.npi || '',
      rx_state_lic: vendor.rx_state_lic || '',
      bus_lic: vendor.bus_lic || '',
      insurance: vendor.insurance || '',
      note: vendor.note || '',
    });
    setSaveError('');
    setAddressLookupStatus('idle');
    setFormOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      setSaveError('Vendor name is required.');
      return;
    }
    setSaving(true);
    setSaveError('');
    try {
      if (editingId) {
        await updateVendor(editingId, form);
      } else {
        await createVendor(form);
      }
      setFormOpen(false);
      reload();
    } catch (err) {
      console.error('Save vendor failed:', err);
      setSaveError(err?.response?.data?.detail || 'Unable to save vendor.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (vendor) => {
    if (!window.confirm(`Deactivate "${vendor.name}"? It will no longer appear in order dropdowns.`)) return;
    try {
      await deleteVendor(vendor.id);
      reload();
    } catch (err) {
      console.error('Deactivate vendor failed:', err);
      window.alert(err?.response?.data?.detail || 'Unable to deactivate vendor.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Vendor Directory</div>
        <button
          type="button"
          onClick={openNew}
          style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: COLORS.teal, color: '#04201d', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
        >
          + Add New Vendor
        </button>
      </div>
      <div style={{ fontSize: 12, color: COLORS.muted }}>
        Pharmacies, DME suppliers, labs, assisted-living facilities, and contracted staff. Once added, vendors appear as selectable options when placing DME/Supply/Lab/Treatment orders.
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <select style={{ ...inputStyle, width: 200 }} value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          {VENDOR_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <input style={{ ...inputStyle, width: 240 }} placeholder="Search by name…" value={nameFilter} onChange={(e) => setNameFilter(e.target.value)} />
      </div>

      {formOpen && (
        <div style={{ ...S.card, padding: 20, background: COLORS.card, border: `1px solid ${COLORS.teal}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white }}>{editingId ? 'Edit Vendor' : 'Add New Vendor'}</div>
            <button type="button" onClick={() => setFormOpen(false)} style={{ padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.muted, fontSize: 12, cursor: 'pointer' }}>Close</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
            <div style={fieldGroup}>
              <label style={labelStyle}>Vendor Type *</label>
              <select style={inputStyle} value={form.vendor_type} onChange={(e) => setForm((f) => ({ ...f, vendor_type: e.target.value }))}>
                {VENDOR_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Name *</label>
              <input style={inputStyle} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="e.g. Alma Cre Pharmacy" />
            </div>
            {form.vendor_type === 'Pharmacy' && (
              <div style={fieldGroup}>
                <label style={labelStyle}>NCPDP ID#</label>
                <input style={inputStyle} value={form.ncpdp_id} onChange={(e) => setForm((f) => ({ ...f, ncpdp_id: e.target.value }))} />
              </div>
            )}
            <div style={fieldGroup}>
              <label style={labelStyle}>Street</label>
              <input style={inputStyle} value={form.address_street} onChange={(e) => setForm((f) => ({ ...f, address_street: e.target.value }))} placeholder="e.g. 15475 Seneca Rd Suite C" />
              {addressLookupStatus === 'searching' && <div style={{ fontSize: 10.5, color: COLORS.muted, marginTop: 3 }}>Looking up address…</div>}
              {addressLookupStatus === 'found' && <div style={{ fontSize: 10.5, color: COLORS.teal, marginTop: 3 }}>✓ City/state/zip auto-filled</div>}
              {addressLookupStatus === 'notfound' && <div style={{ fontSize: 10.5, color: COLORS.muted, marginTop: 3 }}>Address not recognized — enter city/state/zip manually.</div>}
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>City</label>
              <input style={inputStyle} value={form.address_city} onChange={(e) => setForm((f) => ({ ...f, address_city: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>State</label>
              <input style={inputStyle} value={form.address_state} onChange={(e) => setForm((f) => ({ ...f, address_state: e.target.value }))} maxLength={2} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Zip</label>
              <input style={inputStyle} value={form.address_zip} onChange={(e) => setForm((f) => ({ ...f, address_zip: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Phone</label>
              <input style={inputStyle} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Fax</label>
              <input style={inputStyle} value={form.fax} onChange={(e) => setForm((f) => ({ ...f, fax: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Email</label>
              <input style={inputStyle} value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Contact Person</label>
              <input style={inputStyle} value={form.contact_person} onChange={(e) => setForm((f) => ({ ...f, contact_person: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>NPI#</label>
              <input style={inputStyle} value={form.npi} onChange={(e) => setForm((f) => ({ ...f, npi: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Rx State Lic#</label>
              <input style={inputStyle} value={form.rx_state_lic} onChange={(e) => setForm((f) => ({ ...f, rx_state_lic: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Bus Lic#</label>
              <input style={inputStyle} value={form.bus_lic} onChange={(e) => setForm((f) => ({ ...f, bus_lic: e.target.value }))} />
            </div>
            <div style={fieldGroup}>
              <label style={labelStyle}>Insurance</label>
              <input style={inputStyle} value={form.insurance} onChange={(e) => setForm((f) => ({ ...f, insurance: e.target.value }))} />
            </div>
          </div>
          <div style={fieldGroup}>
            <label style={labelStyle}>Note/Comment</label>
            <textarea style={{ ...inputStyle, minHeight: 50, resize: 'vertical' }} value={form.note} onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} />
          </div>
          {saveError && <div style={{ color: COLORS.red, fontSize: 12.5, marginBottom: 8 }}>{saveError}</div>}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: COLORS.teal, color: '#04201d', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
          >
            {saving ? 'Saving…' : 'Save Vendor'}
          </button>
        </div>
      )}

      <div style={{ ...S.card, padding: 0, background: COLORS.card, overflow: 'hidden' }}>
        {loading && <div style={{ padding: 16, fontSize: 12.5, color: COLORS.muted }}>Loading…</div>}
        {error && <div style={{ padding: 16, color: COLORS.red, fontSize: 12.5 }}>{error}</div>}
        {!loading && vendors.length === 0 && <div style={{ padding: 16, fontSize: 12.5, color: COLORS.muted }}>No vendors on file yet.</div>}
        {vendors.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {['Name', 'Type', 'Address', 'Phone', 'Fax', 'Contact', 'Status', ''].map((h) => (
                  <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, color: COLORS.muted, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {vendors.map((v) => (
                <tr key={v.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: '10px 14px', fontSize: 13, color: COLORS.white, fontWeight: 600 }}>{v.name}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12.5, color: COLORS.muted }}>{v.vendor_type}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12.5, color: COLORS.muted }}>
                    {[v.address_street, v.address_city, v.address_state, v.address_zip].filter(Boolean).join(', ') || '—'}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: 12.5, color: COLORS.muted }}>{v.phone || '—'}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12.5, color: COLORS.muted }}>{v.fax || '—'}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12.5, color: COLORS.muted }}>{v.contact_person || '—'}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12, fontWeight: 700, color: v.status === 'active' ? COLORS.teal : COLORS.red }}>{v.status}</td>
                  <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                    <button type="button" onClick={() => openEdit(v)} style={{ padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 11.5, cursor: 'pointer', marginRight: 6 }}>Edit</button>
                    {v.status === 'active' && (
                      <button type="button" onClick={() => handleDeactivate(v)} style={{ padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.red}`, background: 'transparent', color: COLORS.red, fontSize: 11.5, cursor: 'pointer' }}>Deactivate</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
