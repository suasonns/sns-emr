import React, { useCallback, useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import {
  listOrderTemplates,
  getOrderTemplate,
  createOrderTemplate,
  addOrderTemplateItem,
  deleteOrderTemplateItem,
  deleteOrderTemplate,
} from '../../api/ordersHub';
import { listVendors } from '../../api/vendors';
import MedicationNameInput from '../../components/MedicationNameInput';

const ORDER_TYPES = [
  { key: 'MEDICATION', label: 'Medication' },
  { key: 'DME', label: 'DME' },
  { key: 'SUPPLY', label: 'Supplies' },
  { key: 'LAB', label: 'Lab' },
  { key: 'TREATMENT', label: 'Treatment' },
  { key: 'DIET', label: 'Diet' },
  { key: 'OTHER', label: 'Other' },
];

// Same order-type → vendor-category mapping used by Orders Hub (OrdersHubCard in RNICA.jsx),
// so vendor typeahead in a pack item matches what the clinician sees on a real chart.
const ORDER_TYPE_TO_VENDOR_TYPE = {
  MEDICATION: 'Pharmacy',
  DME: 'DME',
  SUPPLY: 'DME',
  LAB: 'Laboratory',
  TREATMENT: 'Contracted Staff',
  DIET: 'Other',
  OTHER: 'Other',
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

const EMPTY_NEW_PACK = { name: '', description: '' };

const EMPTY_ITEM = {
  order_type: 'MEDICATION',
  order_text: '',
  strength: '',
  dosage: '',
  route: '',
  frequency: '',
  indication: '',
  quantity: '',
  payer: '',
  vendor: '',
  administered_by: '',
  special_instruction: '',
};

export default function OrderPackManagement() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [creating, setCreating] = useState(false);
  const [newPack, setNewPack] = useState(EMPTY_NEW_PACK);
  const [createError, setCreateError] = useState('');
  const [savingPack, setSavingPack] = useState(false);

  const [expandedId, setExpandedId] = useState(null);
  const [expandedDetail, setExpandedDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [itemForm, setItemForm] = useState(EMPTY_ITEM);
  const [savingItem, setSavingItem] = useState(false);
  const [itemError, setItemError] = useState('');
  const [vendorOptions, setVendorOptions] = useState([]);

  useEffect(() => {
    const vendorType = ORDER_TYPE_TO_VENDOR_TYPE[itemForm.order_type] || 'Other';
    listVendors({ status: 'active', vendor_type: vendorType })
      .then((list) => setVendorOptions(list || []))
      .catch((err) => console.error('Failed to load vendors:', err));
  }, [itemForm.order_type]);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    listOrderTemplates()
      .then((list) => setTemplates(list || []))
      .catch((err) => {
        console.error('Failed to load order packs:', err);
        setError(err?.response?.data?.detail || 'Unable to load order packs.');
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const loadDetail = useCallback((templateId) => {
    setDetailLoading(true);
    getOrderTemplate(templateId)
      .then((detail) => setExpandedDetail(detail))
      .catch((err) => {
        console.error('Failed to load pack detail:', err);
        setExpandedDetail(null);
      })
      .finally(() => setDetailLoading(false));
  }, []);

  const toggleExpand = (template) => {
    if (expandedId === template.id) {
      setExpandedId(null);
      setExpandedDetail(null);
      setItemForm(EMPTY_ITEM);
      setItemError('');
      return;
    }
    setExpandedId(template.id);
    setExpandedDetail(null);
    setItemForm(EMPTY_ITEM);
    setItemError('');
    loadDetail(template.id);
  };

  const handleCreatePack = async () => {
    if (!newPack.name.trim()) {
      setCreateError('Pack name is required.');
      return;
    }
    setSavingPack(true);
    setCreateError('');
    try {
      const created = await createOrderTemplate(newPack.name.trim(), newPack.description.trim() || undefined);
      setCreating(false);
      setNewPack(EMPTY_NEW_PACK);
      reload();
      setExpandedId(created.id);
      setExpandedDetail(created);
    } catch (err) {
      console.error('Create pack failed:', err);
      setCreateError(err?.response?.data?.detail || 'Unable to create order pack.');
    } finally {
      setSavingPack(false);
    }
  };

  const handleAddItem = async () => {
    if (!itemForm.order_text.trim()) {
      setItemError('Order/medication text is required.');
      return;
    }
    setSavingItem(true);
    setItemError('');
    try {
      await addOrderTemplateItem(expandedId, itemForm);
      setItemForm({ ...EMPTY_ITEM, order_type: itemForm.order_type });
      loadDetail(expandedId);
      reload();
    } catch (err) {
      console.error('Add pack item failed:', err);
      setItemError(err?.response?.data?.detail || 'Unable to add item.');
    } finally {
      setSavingItem(false);
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Remove this item from the pack?')) return;
    try {
      await deleteOrderTemplateItem(expandedId, itemId);
      loadDetail(expandedId);
      reload();
    } catch (err) {
      console.error('Delete pack item failed:', err);
      window.alert(err?.response?.data?.detail || 'Unable to remove item.');
    }
  };

  const handleDeletePack = async (template) => {
    if (!window.confirm(`Delete the "${template.name}" pack? This cannot be undone.`)) return;
    try {
      await deleteOrderTemplate(template.id);
      if (expandedId === template.id) {
        setExpandedId(null);
        setExpandedDetail(null);
      }
      reload();
    } catch (err) {
      console.error('Delete pack failed:', err);
      window.alert(err?.response?.data?.detail || 'Unable to delete pack.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Order Packs</div>
        <button
          type="button"
          onClick={() => { setCreating((v) => !v); setCreateError(''); }}
          style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: COLORS.teal, color: '#04201d', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
        >
          + New Order Pack
        </button>
      </div>
      <div style={{ fontSize: 12, color: COLORS.muted }}>
        Reusable order sets (e.g. Comfort Pack, Standard Admission Pack) that clinicians can bulk-import onto a patient
        chart from Orders Hub's "Import Pack" action. System packs (built-in, shared across all agencies) can't be
        edited or deleted here — build your own agency-specific pack instead.
      </div>

      {creating && (
        <div style={{ ...S.card, padding: 20, background: COLORS.card, border: `1px solid ${COLORS.teal}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.white }}>New Order Pack</div>
            <button type="button" onClick={() => setCreating(false)} style={{ padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.muted, fontSize: 12, cursor: 'pointer' }}>Close</button>
          </div>
          <div style={fieldGroup}>
            <label style={labelStyle}>Pack Name *</label>
            <input style={inputStyle} value={newPack.name} onChange={(e) => setNewPack((f) => ({ ...f, name: e.target.value }))} placeholder="e.g. GI Bleed Comfort Pack" />
          </div>
          <div style={fieldGroup}>
            <label style={labelStyle}>Description</label>
            <textarea style={{ ...inputStyle, minHeight: 50, resize: 'vertical' }} value={newPack.description} onChange={(e) => setNewPack((f) => ({ ...f, description: e.target.value }))} placeholder="What this pack is for and when to use it" />
          </div>
          {createError && <div style={{ color: COLORS.red, fontSize: 12.5, marginBottom: 8 }}>{createError}</div>}
          <button
            type="button"
            onClick={handleCreatePack}
            disabled={savingPack}
            style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: COLORS.teal, color: '#04201d', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
          >
            {savingPack ? 'Creating…' : 'Create Pack'}
          </button>
        </div>
      )}

      <div style={{ ...S.card, padding: 0, background: COLORS.card, overflow: 'hidden' }}>
        {loading && <div style={{ padding: 16, fontSize: 12.5, color: COLORS.muted }}>Loading…</div>}
        {error && <div style={{ padding: 16, color: COLORS.red, fontSize: 12.5 }}>{error}</div>}
        {!loading && templates.length === 0 && <div style={{ padding: 16, fontSize: 12.5, color: COLORS.muted }}>No order packs yet.</div>}
        {templates.map((t) => (
          <div key={t.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
            <div
              onClick={() => toggleExpand(t)}
              style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
            >
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: COLORS.white }}>
                  {t.name}{' '}
                  {t.is_system && (
                    <span style={{ fontSize: 10, fontWeight: 700, color: COLORS.blue, border: `1px solid ${COLORS.blue}`, borderRadius: 6, padding: '1px 6px', marginLeft: 6 }}>SYSTEM</span>
                  )}
                </div>
                {t.description && <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>{t.description}</div>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ fontSize: 12, color: COLORS.muted }}>{t.item_count} item{t.item_count === 1 ? '' : 's'}</div>
                {!t.is_system && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleDeletePack(t); }}
                    style={{ padding: '4px 10px', borderRadius: 6, border: `1px solid ${COLORS.red}`, background: 'transparent', color: COLORS.red, fontSize: 11.5, cursor: 'pointer' }}
                  >
                    Delete Pack
                  </button>
                )}
                <div style={{ color: COLORS.muted, fontSize: 13 }}>{expandedId === t.id ? '▲' : '▼'}</div>
              </div>
            </div>

            {expandedId === t.id && (
              <div style={{ padding: '0 16px 16px', background: COLORS.bg }}>
                {detailLoading && <div style={{ fontSize: 12.5, color: COLORS.muted, padding: '8px 0' }}>Loading items…</div>}
                {!detailLoading && expandedDetail && expandedDetail.items.length === 0 && (
                  <div style={{ fontSize: 12.5, color: COLORS.muted, padding: '8px 0' }}>No items in this pack yet.</div>
                )}
                {!detailLoading && expandedDetail && expandedDetail.items.length > 0 && (
                  <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                        {['Type', 'Order / Medication', 'Strength', 'Route', 'Frequency', ''].map((h) => (
                          <th key={h} style={{ padding: '8px 10px', textAlign: 'left', fontSize: 10.5, color: COLORS.muted, fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {expandedDetail.items.map((item) => (
                        <tr key={item.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                          <td style={{ padding: '8px 10px', fontSize: 12, color: COLORS.muted }}>{item.order_type}</td>
                          <td style={{ padding: '8px 10px', fontSize: 12.5, color: COLORS.white }}>{item.order_text}</td>
                          <td style={{ padding: '8px 10px', fontSize: 12, color: COLORS.muted }}>{item.strength || item.dosage || '—'}</td>
                          <td style={{ padding: '8px 10px', fontSize: 12, color: COLORS.muted }}>{item.route || '—'}</td>
                          <td style={{ padding: '8px 10px', fontSize: 12, color: COLORS.muted }}>{item.frequency || '—'}</td>
                          <td style={{ padding: '8px 10px' }}>
                            {!t.is_system && (
                              <button type="button" onClick={() => handleDeleteItem(item.id)} style={{ padding: '3px 8px', borderRadius: 6, border: `1px solid ${COLORS.red}`, background: 'transparent', color: COLORS.red, fontSize: 11, cursor: 'pointer' }}>Remove</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {!t.is_system && (
                  <div style={{ marginTop: 14, padding: 14, borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.card }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, color: COLORS.white, marginBottom: 10 }}>Add Item to Pack</div>

                    {/* Order type tabs — same as Orders Hub's Tx/Med/DME tab bar, so a pack item follows the exact
                        same protocol (Strength/Dosage/Route/Frequency/Indication) as a real chart order of that type. */}
                    <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
                      {ORDER_TYPES.map((o) => (
                        <button
                          key={o.key}
                          type="button"
                          onClick={() => setItemForm((f) => ({ ...EMPTY_ITEM, order_type: o.key }))}
                          style={{
                            padding: '6px 12px',
                            borderRadius: 8,
                            border: `1px solid ${itemForm.order_type === o.key ? COLORS.teal : COLORS.border}`,
                            background: itemForm.order_type === o.key ? 'rgba(99, 231, 211, 0.14)' : 'transparent',
                            color: itemForm.order_type === o.key ? COLORS.teal : COLORS.muted,
                            fontSize: 11.5,
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          {o.label}
                        </button>
                      ))}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                      <div style={fieldGroup}>
                        <label style={labelStyle}>{itemForm.order_type === 'MEDICATION' ? 'Medication Name *' : 'Order *'}</label>
                        {itemForm.order_type === 'MEDICATION' ? (
                          <MedicationNameInput
                            value={itemForm.order_text}
                            onChange={(val) => setItemForm((f) => ({ ...f, order_text: val }))}
                            onSelectSuggestion={(s) => setItemForm((f) => ({
                              ...f,
                              strength: s.strength || f.strength,
                              route: s.route || f.route,
                            }))}
                            inputStyle={inputStyle}
                            labelStyle={{ fontSize: 10.5, color: COLORS.muted }}
                          />
                        ) : (
                          <input style={inputStyle} value={itemForm.order_text} onChange={(e) => setItemForm((f) => ({ ...f, order_text: e.target.value }))} placeholder="e.g. Hospital Bed Full Electric" />
                        )}
                      </div>
                      {itemForm.order_type !== 'OTHER' && (
                        <>
                          <div style={fieldGroup}>
                            <label style={labelStyle}>Strength</label>
                            <input style={inputStyle} value={itemForm.strength} onChange={(e) => setItemForm((f) => ({ ...f, strength: e.target.value }))} placeholder="e.g. 20mg/mL" />
                          </div>
                          <div style={fieldGroup}>
                            <label style={labelStyle}>Dosage/Qty</label>
                            <input style={inputStyle} value={itemForm.dosage} onChange={(e) => setItemForm((f) => ({ ...f, dosage: e.target.value }))} />
                          </div>
                          <div style={fieldGroup}>
                            <label style={labelStyle}>Route</label>
                            <input style={inputStyle} value={itemForm.route} onChange={(e) => setItemForm((f) => ({ ...f, route: e.target.value }))} placeholder="e.g. Sublingual" />
                          </div>
                          <div style={fieldGroup}>
                            <label style={labelStyle}>Frequency</label>
                            <input style={inputStyle} value={itemForm.frequency} onChange={(e) => setItemForm((f) => ({ ...f, frequency: e.target.value }))} placeholder="e.g. Q2H PRN" />
                          </div>
                          <div style={fieldGroup}>
                            <label style={labelStyle}>Indication</label>
                            <input style={inputStyle} value={itemForm.indication} onChange={(e) => setItemForm((f) => ({ ...f, indication: e.target.value }))} placeholder="e.g. Pain / air hunger" />
                          </div>
                        </>
                      )}
                      <div style={fieldGroup}>
                        <label style={labelStyle}>Quantity</label>
                        <input style={inputStyle} value={itemForm.quantity} onChange={(e) => setItemForm((f) => ({ ...f, quantity: e.target.value }))} />
                      </div>
                      <div style={fieldGroup}>
                        <label style={labelStyle}>Payer</label>
                        <select style={inputStyle} value={itemForm.payer} onChange={(e) => setItemForm((f) => ({ ...f, payer: e.target.value }))}>
                          <option value="">—</option>
                          <option value="Hospice">Hospice covered</option>
                          <option value="Insurance">Insurance non-covered</option>
                          <option value="Patient">Patient non-covered</option>
                        </select>
                      </div>
                      <div style={fieldGroup}>
                        <label style={labelStyle}>Vendor</label>
                        <input
                          style={inputStyle}
                          value={itemForm.vendor}
                          onChange={(e) => setItemForm((f) => ({ ...f, vendor: e.target.value }))}
                          list="op-vendor-options"
                          placeholder={vendorOptions.length ? 'Select or type a vendor…' : 'No vendors on file — type a name'}
                        />
                        <datalist id="op-vendor-options">
                          {vendorOptions.map((v) => (
                            <option key={v.id} value={v.name} />
                          ))}
                        </datalist>
                      </div>
                      <div style={fieldGroup}>
                        <label style={labelStyle}>Administered By</label>
                        <input style={inputStyle} value={itemForm.administered_by} onChange={(e) => setItemForm((f) => ({ ...f, administered_by: e.target.value }))} placeholder="e.g. Hospice Nurse Only" />
                      </div>
                    </div>
                    <div style={fieldGroup}>
                      <label style={labelStyle}>Special Instruction</label>
                      <textarea style={{ ...inputStyle, minHeight: 50, resize: 'vertical' }} value={itemForm.special_instruction} onChange={(e) => setItemForm((f) => ({ ...f, special_instruction: e.target.value }))} />
                    </div>
                    {itemError && <div style={{ color: COLORS.red, fontSize: 12, marginBottom: 8 }}>{itemError}</div>}
                    <button
                      type="button"
                      onClick={handleAddItem}
                      disabled={savingItem}
                      style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: COLORS.teal, color: '#04201d', fontSize: 12.5, fontWeight: 700, cursor: 'pointer' }}
                    >
                      {savingItem ? 'Adding…' : '+ Add Item'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
