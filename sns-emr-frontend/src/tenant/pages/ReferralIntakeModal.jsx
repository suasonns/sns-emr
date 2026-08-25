import React, { useState } from 'react';
import { COLORS, S } from '../design';
import { createReferral } from '../../api/referrals';

const FIELD_GROUPS = [
  {
    title: 'Patient Information',
    fields: [
      { name: 'first_name', label: 'First Name *', required: true },
      { name: 'middle_name', label: 'Middle Name' },
      { name: 'last_name', label: 'Last Name *', required: true },
      { name: 'date_of_birth', label: 'Date of Birth *', type: 'date', required: true },
      { name: 'gender', label: 'Gender' },
      { name: 'phone', label: 'Phone' },
      { name: 'address', label: 'Address' },
      { name: 'city', label: 'City' },
      { name: 'state', label: 'State' },
      { name: 'zip', label: 'Zip' },
      { name: 'language', label: 'Language' },
      { name: 'religion', label: 'Religion' },
      { name: 'marital_status', label: 'Marital Status' },
    ],
  },
  {
    title: 'Referral & Clinical',
    fields: [
      { name: 'referral_source', label: 'Referral Source (hospital/SNF/physician/etc.)' },
      { name: 'referral_date', label: 'Referral Date', type: 'date' },
      { name: 'primary_diagnosis', label: 'Primary Diagnosis' },
      { name: 'secondary_diagnoses', label: 'Secondary Diagnoses', textarea: true },
      { name: 'current_level_of_care', label: 'Current Level of Care' },
      { name: 'attending_physician_name', label: 'Attending Physician Name' },
      { name: 'attending_physician_npi', label: 'Attending Physician NPI' },
      { name: 'special_instructions', label: 'Special Instructions', textarea: true },
    ],
  },
  {
    title: 'Payer',
    fields: [
      { name: 'primary_payer', label: 'Primary Payer' },
      { name: 'primary_policy_number', label: 'Primary Policy Number' },
      { name: 'authorization_status', label: 'Authorization Status' },
    ],
  },
  {
    title: 'Responsible Party / Emergency Contact',
    fields: [
      { name: 'responsible_party_name', label: 'Responsible Party Name' },
      { name: 'responsible_party_relationship', label: 'Responsible Party Relationship' },
      { name: 'responsible_party_phone', label: 'Responsible Party Phone' },
      { name: 'emergency_contact_name', label: 'Emergency Contact Name' },
      { name: 'emergency_contact_relationship', label: 'Emergency Contact Relationship' },
      { name: 'emergency_contact_phone', label: 'Emergency Contact Phone' },
    ],
  },
];

const inputStyle = {
  width: '100%',
  padding: '9px 10px',
  borderRadius: 8,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.textPrimary,
  fontSize: 13,
  outline: 'none',
  boxSizing: 'border-box',
};

export default function ReferralIntakeModal({ onClose, onCreated }) {
  const [form, setForm] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const update = (name, value) => setForm((prev) => ({ ...prev, [name]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!form.first_name?.trim() || !form.last_name?.trim() || !form.date_of_birth) {
      setError('First name, last name, and date of birth are required.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = Object.fromEntries(
        Object.entries(form).filter(([, value]) => value !== undefined && value !== ''),
      );
      const result = await createReferral(payload);
      onCreated?.(result);
    } catch (err) {
      setError(err?.response?.data?.detail ? String(err.response.data.detail) : 'Failed to submit referral. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.55)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        padding: '40px 16px',
        zIndex: 1000,
        overflowY: 'auto',
      }}
      onClick={onClose}
    >
      <div
        style={{ ...S.card, width: '100%', maxWidth: 720, marginBottom: 40 }}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ ...S.pageTitle, fontSize: 18 }}>New Referral Intake</h2>
            <p style={S.pageSubtitle}>Submits the referral for staff review. No patient record is created until it is accepted.</p>
          </div>
          <button type="button" style={S.btnOutline} onClick={onClose}>Close</button>
        </div>

        {error ? (
          <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, background: 'rgba(220,53,69,0.12)', color: COLORS.red, fontSize: 13 }}>
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit}>
          {FIELD_GROUPS.map((group) => (
            <div key={group.title} style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, color: COLORS.dim, textTransform: 'uppercase', marginBottom: 10 }}>
                {group.title}
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                {group.fields.map((field) => (
                  <div key={field.name} style={field.textarea ? { gridColumn: '1 / -1' } : undefined}>
                    <label style={{ display: 'block', fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                      {field.label}
                    </label>
                    {field.textarea ? (
                      <textarea
                        style={{ ...inputStyle, minHeight: 60, resize: 'vertical', fontFamily: 'inherit' }}
                        value={form[field.name] || ''}
                        onChange={(event) => update(field.name, event.target.value)}
                      />
                    ) : (
                      <input
                        type={field.type || 'text'}
                        style={inputStyle}
                        value={form[field.name] || ''}
                        onChange={(event) => update(field.name, event.target.value)}
                        required={field.required}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
            <button type="button" style={S.btnOutline} onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" style={S.btn(COLORS.teal)} disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit Referral'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
