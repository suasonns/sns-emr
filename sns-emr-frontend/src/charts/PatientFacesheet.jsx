import React, { useEffect, useMemo, useState } from 'react';
import { createPosHistory, fetchFacesheet, fetchPosHistory, saveFacesheet, updatePosHistory } from '../api/facesheet';
import { listPhysicians } from '../api/physicians';
import PhysicianDirectoryModal from '../components/PhysicianDirectoryModal';
import { useThemeMode } from '../theme/theme';

const getColors = (mode) => mode === 'light' ? {
  bg: '#f3f8f7',
  card: '#ffffff',
  border: '#d9e6eb',
  teal: '#0d7d7a',
  white: '#18354c',
  label: '#5f7286',
  text: '#1e2d3b',
  green: '#2d7b63',
  red: '#d64d57',
  amber: '#d38a2b',
  greenBg: '#dff5ee',
  redBg: '#fbe3e7',
  amberBg: '#f9edd7',
  tealBg: '#dff8f4',
} : {
  bg: '#0f172a',
  card: '#1e293b',
  border: '#334155',
  teal: '#10b7a2',
  white: '#ffffff',
  label: '#94a3b8',
  text: '#e2e8f0',
  green: '#059669',
  red: '#ef4444',
  amber: '#f59e0b',
  greenBg: '#05966915',
  redBg: '#ef444415',
  amberBg: '#f59e0b15',
  tealBg: '#10b7a215',
};

const cardBase = (colors) => ({
  backgroundColor: colors.card,
  borderRadius: 8,
  padding: 10,
  borderLeft: `3px solid ${colors.teal}`,
  height: '100%',
  minHeight: 84,
  boxSizing: 'border-box',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
});

const baseInputStyle = (colors) => ({
  width: '100%',
  boxSizing: 'border-box',
  backgroundColor: colors.bg,
  border: `1px solid ${colors.border}`,
  borderRadius: 5,
  color: colors.white,
  fontSize: 11.5,
  lineHeight: 1.25,
  padding: '5px 7px',
  outline: 'none',
  fontFamily: 'inherit',
});

const EMPTY_DRAFT = {
  first_name: '',
  middle_name: '',
  last_name: '',
  ssn: '',
  dob: '',
  gender: '',
  race: '',
  ethnicity: '',
  language: '',
  religion: '',
  marital_status: '',
  phone: '',
  address: '',
  city: '',
  state: '',
  zip: '',
  current_pos_type: '',
  current_pos_name: '',
  current_pos_address: '',
  room_number: '',
  pos_start_date: '',
  pos_end_date: '',
  current_level_of_care: '',
  loc_effective_date: '',
  primary_payer: '',
  primary_policy_number: '',
  mbi_number: '',
  secondary_payer: '',
  secondary_policy_number: '',
  requires_prior_authorization: null,
  authorization_required_for: '',
  authorization_number: '',
  authorization_status: '',
  authorization_start_date: '',
  authorization_end_date: '',
  primary_diagnosis: '',
  secondary_diagnoses: '',
  has_allergies: null,
  allergies: '',
  ref_date: '',
  recert_date: '',
  responsible_party_name: '',
  responsible_party_relationship: '',
  responsible_party_phone: '',
  emergency_contact_name: '',
  emergency_contact_relationship: '',
  emergency_contact_phone: '',
  attending_physician_name: '',
  attending_physician_address: '',
  attending_physician_phone: '',
  attending_physician_fax: '',
  attending_physician_npi: '',
  attending_physician_following: null,
  medical_director_name: '',
  medical_director_address: '',
  medical_director_phone: '',
  medical_director_fax: '',
  medical_director_npi: '',
  medical_director_designee_name: '',
  medical_director_designee_npi: '',
  associate_medical_director_name: '',
  associate_medical_director_npi: '',
  pharmacy_name: '',
  pharmacy_phone: '',
  pharmacy_fax: '',
  dme_vendor_name: '',
  dme_vendor_phone: '',
  mortuary_name: '',
  mortuary_phone: '',
  special_instructions: '',
};

const createEmptyDraft = () => ({ ...EMPTY_DRAFT });

const EMPTY_POS_FORM = {
  pos_type: '',
  pos_name: '',
  pos_address: '',
  room_number: '',
  start_date: '',
  end_date: '',
  reason: '',
};

const createEmptyPosForm = () => ({ ...EMPTY_POS_FORM });

const POS_TYPE_OPTIONS = [
  '',
  'HOME',
  'ASSISTED_LIVING',
  'MEMORY_CARE',
  'BOARD_AND_CARE',
  'RCFE',
  'SNF',
  'LONG_TERM_CARE',
  'HOSPITAL',
  'VA_FACILITY',
  'CORRECTIONAL_FACILITY',
  'OTHER',
].map((value) => ({ value, label: value ? value.replaceAll('_', ' ') : 'Select type' }));

const LOC_OPTIONS = [
  '',
  'ROUTINE_HOME_CARE',
  'CONTINUOUS_HOME_CARE',
  'GENERAL_INPATIENT',
  'INPATIENT_RESPITE',
].map((value) => ({ value, label: value ? value.replaceAll('_', ' ') : 'Select level' }));

const AUTH_REQUIRED_FOR_OPTIONS = [
  '',
  'HOSPICE',
  'RESPITE',
  'GIP',
  'DME',
  'OTHER',
].map((value) => ({ value, label: value || 'Select type' }));

const AUTH_STATUS_OPTIONS = [
  '',
  'NOT_REQUIRED',
  'PENDING',
  'APPROVED',
  'DENIED',
  'EXPIRED',
].map((value) => ({ value, label: value ? value.replaceAll('_', ' ') : 'Select status' }));

const BOOLEAN_OPTIONS = [
  { value: '', label: 'Select' },
  { value: 'true', label: 'Yes' },
  { value: 'false', label: 'No' },
];

const normalizeDateValue = (value) => {
  if (!value) return '';
  if (typeof value === 'string') {
    const match = value.match(/^\d{4}-\d{2}-\d{2}/);
    return match ? match[0] : value;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
};

const formatDateDisplay = (value) => {
  const normalized = normalizeDateValue(value);
  if (!normalized) return '—';
  const [year, month, day] = normalized.split('-').map(Number);
  if (!year || !month || !day) return normalized;
  return new Date(year, month - 1, day).toLocaleDateString();
};

const getAge = (dob) => {
  const normalized = normalizeDateValue(dob);
  if (!normalized) return null;
  const [year, month, day] = normalized.split('-').map(Number);
  const birthDate = new Date(year, month - 1, day);
  if (Number.isNaN(birthDate.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const hasHadBirthday = today.getMonth() > birthDate.getMonth()
    || (today.getMonth() === birthDate.getMonth() && today.getDate() >= birthDate.getDate());
  if (!hasHadBirthday) age -= 1;
  return age >= 0 ? age : null;
};

const formatEnumLabel = (value) => {
  if (!value) return '—';
  return String(value)
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatDisplayValue = (value) => {
  if (value === null || value === undefined || value === '') return '—';
  return value;
};

const selectBooleanValue = (value) => {
  if (value === true) return 'true';
  if (value === false) return 'false';
  return '';
};

const parseBooleanValue = (value) => {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return null;
};

const toNullableString = (value) => {
  if (typeof value !== 'string') return value ?? null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
};

const getFullName = (parts) => parts.filter(Boolean).join(' ').trim();

const getBannerName = (draft) => {
  const firstMiddle = getFullName([draft.first_name, draft.middle_name]);
  const last = draft.last_name?.trim();
  if (!firstMiddle && !last) return 'PATIENT FACE SHEET';
  return [last, firstMiddle].filter(Boolean).join(', ').toUpperCase();
};

const getBreadcrumbName = (draft) => getFullName([draft.first_name, draft.middle_name, draft.last_name]) || 'Patient';

const getAllergySummary = (draft) => {
  if (draft.has_allergies === false) return 'None reported';
  if (draft.has_allergies === true) return draft.allergies?.trim() || 'Reported';
  return '—';
};

const getOrderingContactState = (draft) => {
  const attendingFollowing = draft.attending_physician_following === true;
  const attendingNotFollowing = draft.attending_physician_following === false;

  if (attendingFollowing) {
    return {
      responsibleRole: 'Attending Physician',
      responsibleName: draft.attending_physician_name?.trim() || 'Attending Physician',
      hasVerifiedOrderingContact: Boolean(draft.attending_physician_phone?.trim()),
    };
  }

  if (attendingNotFollowing) {
    return {
      responsibleRole: 'Medical Director',
      responsibleName: draft.medical_director_name?.trim() || 'Hospice Medical Director',
      hasVerifiedOrderingContact: Boolean(draft.medical_director_phone?.trim()),
    };
  }

  return {
    responsibleRole: 'Ordering Physician',
    responsibleName: 'Ordering Physician',
    hasVerifiedOrderingContact: true,
  };
};

const buildPayload = (draft) => {
  const primaryDiagnosis = toNullableString(draft.primary_diagnosis);

  return {
  first_name: draft.first_name.trim(),
  middle_name: toNullableString(draft.middle_name),
  last_name: draft.last_name.trim(),
  ssn: toNullableString(draft.ssn),
  dob: toNullableString(draft.dob),
  gender: toNullableString(draft.gender),
  race: toNullableString(draft.race),
  ethnicity: toNullableString(draft.ethnicity),
  language: toNullableString(draft.language),
  religion: toNullableString(draft.religion),
  marital_status: toNullableString(draft.marital_status),
  phone: toNullableString(draft.phone),
  address: toNullableString(draft.address),
  city: toNullableString(draft.city),
  state: toNullableString(draft.state),
  zip: toNullableString(draft.zip),
  current_pos_type: toNullableString(draft.current_pos_type),
  current_pos_name: toNullableString(draft.current_pos_name),
  current_pos_address: toNullableString(draft.current_pos_address),
  room_number: toNullableString(draft.room_number),
  pos_start_date: toNullableString(draft.pos_start_date),
  pos_end_date: toNullableString(draft.pos_end_date),
  current_level_of_care: toNullableString(draft.current_level_of_care),
  loc_effective_date: toNullableString(draft.loc_effective_date),
  primary_payer: toNullableString(draft.primary_payer),
  primary_policy_number: toNullableString(draft.primary_policy_number),
  mbi_number: toNullableString(draft.mbi_number),
  secondary_payer: toNullableString(draft.secondary_payer),
  secondary_policy_number: toNullableString(draft.secondary_policy_number),
  requires_prior_authorization: draft.requires_prior_authorization,
  authorization_required_for: toNullableString(draft.authorization_required_for),
  authorization_number: toNullableString(draft.authorization_number),
  authorization_status: toNullableString(draft.authorization_status),
  authorization_start_date: toNullableString(draft.authorization_start_date),
  authorization_end_date: toNullableString(draft.authorization_end_date),
  ...(primaryDiagnosis ? { primary_diagnosis: primaryDiagnosis } : {}),
  secondary_diagnoses: toNullableString(draft.secondary_diagnoses),
  has_allergies: draft.has_allergies,
  allergies: toNullableString(draft.allergies),
  ref_date: toNullableString(draft.ref_date),
  recert_date: toNullableString(draft.recert_date),
  responsible_party_name: toNullableString(draft.responsible_party_name),
  responsible_party_relationship: toNullableString(draft.responsible_party_relationship),
  responsible_party_phone: toNullableString(draft.responsible_party_phone),
  emergency_contact_name: toNullableString(draft.emergency_contact_name),
  emergency_contact_relationship: toNullableString(draft.emergency_contact_relationship),
  emergency_contact_phone: toNullableString(draft.emergency_contact_phone),
  attending_physician_name: toNullableString(draft.attending_physician_name),
  attending_physician_address: toNullableString(draft.attending_physician_address),
  attending_physician_phone: toNullableString(draft.attending_physician_phone),
  attending_physician_fax: toNullableString(draft.attending_physician_fax),
  attending_physician_npi: toNullableString(draft.attending_physician_npi),
  attending_physician_following: draft.attending_physician_following,
  medical_director_name: toNullableString(draft.medical_director_name),
  medical_director_address: toNullableString(draft.medical_director_address),
  medical_director_phone: toNullableString(draft.medical_director_phone),
  medical_director_fax: toNullableString(draft.medical_director_fax),
  medical_director_npi: toNullableString(draft.medical_director_npi),
  medical_director_designee_name: toNullableString(draft.medical_director_designee_name),
  medical_director_designee_npi: toNullableString(draft.medical_director_designee_npi),
  associate_medical_director_name: toNullableString(draft.associate_medical_director_name),
  associate_medical_director_npi: toNullableString(draft.associate_medical_director_npi),
  pharmacy_name: toNullableString(draft.pharmacy_name),
  pharmacy_phone: toNullableString(draft.pharmacy_phone),
  pharmacy_fax: toNullableString(draft.pharmacy_fax),
  dme_vendor_name: toNullableString(draft.dme_vendor_name),
  dme_vendor_phone: toNullableString(draft.dme_vendor_phone),
  mortuary_name: toNullableString(draft.mortuary_name),
  mortuary_phone: toNullableString(draft.mortuary_phone),
  special_instructions: toNullableString(draft.special_instructions),
  };
};

const buildPosHistoryPayload = (form) => ({
  pos_type: form.pos_type,
  pos_name: toNullableString(form.pos_name),
  pos_address: toNullableString(form.pos_address),
  room_number: toNullableString(form.room_number),
  start_date: form.start_date,
  end_date: toNullableString(form.end_date),
  reason: toNullableString(form.reason),
});

const buildCurrentPosUpdatePayload = (draft, currentEntry) => ({
  pos_type: draft.current_pos_type,
  pos_name: toNullableString(draft.current_pos_name),
  pos_address: toNullableString(draft.current_pos_address),
  room_number: toNullableString(draft.room_number),
  start_date: draft.pos_start_date,
  end_date: toNullableString(draft.pos_end_date),
  reason: currentEntry?.reason ?? null,
});

const mapResponseToDraft = (response) => ({
  first_name: response?.identity?.first_name || '',
  middle_name: response?.identity?.middle_name || '',
  last_name: response?.identity?.last_name || '',
  ssn: response?.identity?.ssn || '',
  dob: normalizeDateValue(response?.identity?.dob),
  gender: response?.identity?.gender || '',
  race: response?.identity?.race || '',
  ethnicity: response?.identity?.ethnicity || '',
  language: response?.identity?.language || '',
  religion: response?.identity?.religion || '',
  marital_status: response?.identity?.marital_status || '',
  phone: response?.identity?.phone || '',
  address: response?.address?.address || '',
  city: response?.address?.city || '',
  state: response?.address?.state || '',
  zip: response?.address?.zip || '',
  current_pos_type: response?.place_of_service?.current_pos_type || '',
  current_pos_name: response?.place_of_service?.current_pos_name || '',
  current_pos_address: response?.place_of_service?.current_pos_address || '',
  room_number: response?.place_of_service?.room_number || '',
  pos_start_date: normalizeDateValue(response?.place_of_service?.pos_start_date),
  pos_end_date: normalizeDateValue(response?.place_of_service?.pos_end_date),
  current_level_of_care: response?.level_of_care?.current_level_of_care || '',
  loc_effective_date: normalizeDateValue(response?.level_of_care?.loc_effective_date),
  primary_payer: response?.insurance?.primary_payer || '',
  primary_policy_number: response?.insurance?.primary_policy_number || '',
  mbi_number: response?.insurance?.mbi_number || '',
  secondary_payer: response?.insurance?.secondary_payer || '',
  secondary_policy_number: response?.insurance?.secondary_policy_number || '',
  requires_prior_authorization: response?.authorization?.requires_prior_authorization ?? null,
  authorization_required_for: response?.authorization?.authorization_required_for || '',
  authorization_number: response?.authorization?.authorization_number || '',
  authorization_status: response?.authorization?.authorization_status || '',
  authorization_start_date: normalizeDateValue(response?.authorization?.authorization_start_date),
  authorization_end_date: normalizeDateValue(response?.authorization?.authorization_end_date),
  primary_diagnosis: response?.clinical?.primary_diagnosis || '',
  secondary_diagnoses: response?.clinical?.secondary_diagnoses || '',
  has_allergies: response?.clinical?.has_allergies ?? null,
  allergies: response?.clinical?.allergies || '',
  ref_date: normalizeDateValue(response?.service_dates?.ref_date),
  recert_date: normalizeDateValue(response?.service_dates?.recert_date),
  responsible_party_name: response?.contacts?.responsible_party?.name || '',
  responsible_party_relationship: response?.contacts?.responsible_party?.relationship || '',
  responsible_party_phone: response?.contacts?.responsible_party?.phone || '',
  emergency_contact_name: response?.contacts?.emergency_contact?.name || '',
  emergency_contact_relationship: response?.contacts?.emergency_contact?.relationship || '',
  emergency_contact_phone: response?.contacts?.emergency_contact?.phone || '',
  attending_physician_name: response?.physicians?.attending?.name || '',
  attending_physician_address: response?.physicians?.attending?.address || '',
  attending_physician_phone: response?.physicians?.attending?.phone || '',
  attending_physician_fax: response?.physicians?.attending?.fax || '',
  attending_physician_npi: response?.physicians?.attending?.npi || '',
  attending_physician_following: response?.physicians?.attending?.following ?? null,
  medical_director_name: response?.physicians?.medical_director?.name || '',
  medical_director_address: response?.physicians?.medical_director?.address || '',
  medical_director_phone: response?.physicians?.medical_director?.phone || '',
  medical_director_fax: response?.physicians?.medical_director?.fax || '',
  medical_director_npi: response?.physicians?.medical_director?.npi || '',
  medical_director_designee_name: response?.physicians?.medical_director_designee?.name || '',
  medical_director_designee_npi: response?.physicians?.medical_director_designee?.npi || '',
  associate_medical_director_name: response?.physicians?.associate_medical_director?.name || '',
  associate_medical_director_npi: response?.physicians?.associate_medical_director?.npi || '',
  pharmacy_name: response?.vendors?.pharmacy?.name || '',
  pharmacy_phone: response?.vendors?.pharmacy?.phone || '',
  pharmacy_fax: response?.vendors?.pharmacy?.fax || '',
  dme_vendor_name: response?.vendors?.dme?.name || '',
  dme_vendor_phone: response?.vendors?.dme?.phone || '',
  mortuary_name: response?.vendors?.mortuary?.name || '',
  mortuary_phone: response?.vendors?.mortuary?.phone || '',
  special_instructions: response?.notes?.special_instructions || '',
});

const Field = ({
  label,
  value,
  style: extra = {},
  colors,
  editable = false,
  onChange,
  type = 'text',
  options = [],
  rows = 3,
  placeholder,
  disabled = false,
  hint,
  inputBorderColor,
  labelColor,
}) => {
  const sharedInputStyle = {
    ...baseInputStyle(colors),
    border: `1px solid ${inputBorderColor || colors.border}`,
    opacity: disabled ? 0.65 : 1,
    cursor: disabled ? 'not-allowed' : 'text',
  };

  let control = <span style={{ color: colors.white, fontSize: 11.5, lineHeight: 1.25, display: 'block', whiteSpace: 'pre-wrap' }}>{formatDisplayValue(value)}</span>;

  if (editable) {
    if (type === 'textarea') {
      control = (
        <textarea
          value={value ?? ''}
          rows={rows}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(event) => onChange && onChange(event.target.value)}
          style={{ ...sharedInputStyle, minHeight: rows * 22, resize: 'vertical' }}
        />
      );
    } else if (type === 'select') {
      control = (
        <select
          value={value ?? ''}
          disabled={disabled}
          onChange={(event) => onChange && onChange(event.target.value)}
          style={sharedInputStyle}
        >
          {options.map((option) => (
            <option key={`${label}-${option.value}`} value={option.value}>{option.label}</option>
          ))}
        </select>
      );
    } else {
      control = (
        <input
          type={type}
          value={value ?? ''}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(event) => onChange && onChange(event.target.value)}
          style={sharedInputStyle}
        />
      );
    }
  }

  return (
    <div style={{ marginBottom: 4, ...extra }}>
      <span style={{ color: labelColor || colors.label, fontSize: 8.5, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 2 }}>{label}</span>
      {control}
      {hint ? <div style={{ color: labelColor || colors.label, fontSize: 10, marginTop: 3 }}>{hint}</div> : null}
    </div>
  );
};

const Badge = ({ children, variant = 'teal', colors }) => {
  const v = {
    teal: { bg: colors.tealBg, color: colors.teal },
    green: { bg: colors.greenBg, color: colors.green },
    red: { bg: colors.redBg, color: colors.red },
    amber: { bg: colors.amberBg, color: colors.amber },
  }[variant] || { bg: colors.tealBg, color: colors.teal };
  return <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, backgroundColor: v.bg, color: v.color, letterSpacing: 0.2 }}>{children}</span>;
};

const CardHeader = ({ title, colors, onToggle, isExpanded = true }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, gap: 8 }}>
    <span style={{ color: colors.white, fontSize: 14, fontWeight: 700 }}>{title}</span>
    {onToggle ? (
      <button
        onClick={onToggle}
        style={{ background: 'none', border: `1px solid ${colors.border}`, borderRadius: 6, color: colors.label, padding: '2px 8px', cursor: 'pointer', fontSize: 10 }}
      >
        {isExpanded ? '▾ Collapse' : '▸ Expand'}
      </button>
    ) : null}
  </div>
);

const SectionNote = ({ colors, children, tone = 'muted' }) => {
  const toneColor = tone === 'warning' ? colors.amber : colors.label;
  return <div style={{ color: toneColor, fontSize: 10.5, lineHeight: 1.4, marginTop: 6 }}>{children}</div>;
};

const ToggleField = ({ colors, label, checked, onChange, hint, warning = false }) => (
  <label style={{
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    border: `1px solid ${warning ? colors.amber : colors.border}`,
    borderRadius: 8,
    padding: '8px 10px',
    backgroundColor: warning ? colors.amberBg : colors.bg,
    cursor: 'pointer',
  }}>
    <input
      type="checkbox"
      checked={checked === true}
      onChange={(event) => onChange(event.target.checked)}
      style={{ width: 16, height: 16, accentColor: colors.teal }}
    />
    <div>
      <div style={{ color: colors.white, fontSize: 12.5, fontWeight: 600 }}>{label}</div>
      {hint ? <div style={{ color: warning ? colors.amber : colors.label, fontSize: 10.5 }}>{hint}</div> : null}
    </div>
  </label>
);

const getStatusVariant = (status) => {
  const normalized = String(status || '').toUpperCase();
  if (normalized.includes('ACTIVE') || normalized.includes('ADMIT')) return 'green';
  if (normalized.includes('PENDING')) return 'amber';
  if (normalized.includes('DENIED') || normalized.includes('ERROR')) return 'red';
  return 'teal';
};

const PatientBanner = ({ colors, draft, facesheet }) => {
  const age = getAge(draft.dob);
  const status = facesheet?.service_dates?.admission_status || '—';
  const dobText = formatDateDisplay(draft.dob);
  const genderText = draft.gender || '—';

  return (
    <div style={{ backgroundColor: colors.card, borderRadius: 8, padding: '12px 16px', marginBottom: 10, boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)' }}>
      <div style={{ marginBottom: 8 }}>
        <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, lineHeight: 1.2 }}>{getBannerName(draft)}</div>
        <div style={{ color: colors.label, fontSize: 12, lineHeight: 1.4 }}>
          MRN: {facesheet?.mrn || '—'} &nbsp;|&nbsp; DOB: {dobText}{age !== null ? ` (${age}y)` : ''} &nbsp;|&nbsp; Sex: {genderText}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, max-content))', columnGap: 18, rowGap: 8, alignItems: 'end' }}>
        {[
          { label: 'SOC DATE', value: formatDateDisplay(facesheet?.service_dates?.soc_date) },
          { label: 'BENEFIT PERIOD', value: '—' },
          { label: 'ALLERGIES', value: getAllergySummary(draft), alert: draft.has_allergies === true },
        ].map((item) => (
          <div key={item.label}>
            <span style={{ color: colors.label, fontSize: 9, textTransform: 'uppercase', display: 'block', letterSpacing: 0.5 }}>{item.label}</span>
            <span style={{ color: item.alert ? colors.red : colors.white, fontSize: 13, fontWeight: 700, display: 'block' }}>{item.value}</span>
          </div>
        ))}
        <div>
          <span style={{ color: colors.label, fontSize: 9, textTransform: 'uppercase', display: 'block', letterSpacing: 0.5 }}>STATUS</span>
          <Badge variant={getStatusVariant(status)} colors={colors}>{status}</Badge>
        </div>
        {[
          { label: 'LEVEL', value: formatEnumLabel(draft.current_level_of_care) },
          { label: 'PAYER', value: draft.primary_payer || '—' },
          { label: 'TOTAL CASE DAYS', value: '—' },
        ].map((item) => (
          <div key={item.label}>
            <span style={{ color: colors.label, fontSize: 9, textTransform: 'uppercase', display: 'block', letterSpacing: 0.5 }}>{item.label}</span>
            <span style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const PatientStatusStrip = ({ colors, facesheet }) => (
  <div style={{
    ...cardBase(colors),
    padding: '10px 12px',
    minHeight: 0,
    marginBottom: 12,
    display: 'grid',
    gridTemplateColumns: 'minmax(180px, 1fr) minmax(220px, 1.4fr)',
    gap: 12,
    alignItems: 'stretch',
  }}>
    <div style={{
      backgroundColor: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      padding: '8px 10px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
    }}>
      <span style={{ color: colors.label, fontSize: 11, fontWeight: 700, letterSpacing: 0.4 }}>ADMISSION STATUS</span>
      <Badge variant={getStatusVariant(facesheet?.service_dates?.admission_status)} colors={colors}>{facesheet?.service_dates?.admission_status || '—'}</Badge>
    </div>

    <div style={{
      backgroundColor: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      padding: '8px 10px',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 8,
    }}>
      {[
        ['Effective Date', formatDateDisplay(facesheet?.service_dates?.effective_date)],
        ['Admission Date', formatDateDisplay(facesheet?.service_dates?.admission_date)],
      ].map(([label, value]) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ color: colors.label, fontSize: 11, fontWeight: 700 }}>{label}</span>
          <span style={{ color: colors.white, fontSize: 11.5, fontWeight: 600 }}>{value}</span>
        </div>
      ))}
    </div>
  </div>
);

const SafetyBanner = ({ colors, orderingContactState }) => {
  if (orderingContactState.hasVerifiedOrderingContact) {
    return null;
  }

  return (
    <div style={{
      border: `1px solid ${colors.red}`,
      backgroundColor: colors.redBg,
      color: colors.red,
      borderRadius: 8,
      padding: '10px 12px',
      marginBottom: 12,
      boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
    }}>
      <div style={{ fontSize: 12.5, fontWeight: 800, marginBottom: 4 }}>
        ⚠ PATIENT SAFETY: No verified direct phone number on file for the physician responsible for hospice orders.
      </div>
      <div style={{ fontSize: 11.5, lineHeight: 1.45 }}>
        {orderingContactState.responsibleName} ({orderingContactState.responsibleRole}) is currently responsible for hospice orders, but no direct callback number is documented. Hospice staff may be unable to obtain orders when needed. Please verify and document a callback number.
      </div>
    </div>
  );
};

const SaveBar = ({ colors, isDirty, saveState, saveMessage, onSave, disabled }) => (
  <div style={{
    position: 'sticky',
    top: 0,
    zIndex: 3,
    backgroundColor: colors.bg,
    paddingBottom: 10,
    marginBottom: 2,
  }}>
    <div style={{
      backgroundColor: colors.card,
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      padding: '10px 12px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: 12,
      boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
    }}>
      <div style={{ color: saveState === 'error' ? colors.red : colors.label, fontSize: 12, lineHeight: 1.4 }}>
        {saveMessage || (isDirty ? 'You have unsaved facesheet changes.' : 'All facesheet changes are saved.')}
      </div>
      <button
        onClick={onSave}
        disabled={disabled || (!isDirty && saveState !== 'error')}
        style={{
          padding: '8px 18px',
          backgroundColor: disabled || (!isDirty && saveState !== 'error') ? colors.border : colors.teal,
          color: '#fff',
          border: 'none',
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 600,
          cursor: disabled || (!isDirty && saveState !== 'error') ? 'not-allowed' : 'pointer',
          minWidth: 132,
        }}
      >
        {saveState === 'saving' ? 'Saving…' : 'Save Facesheet'}
      </button>
    </div>
  </div>
);

const PersonalInformation = ({ colors, draft, update }) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Personal Information" colors={colors} />
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
      <Field label="First Name" value={draft.first_name} colors={colors} editable onChange={(value) => update('first_name', value)} />
      <Field label="Middle Name" value={draft.middle_name} colors={colors} editable onChange={(value) => update('middle_name', value)} />
      <Field label="Last Name" value={draft.last_name} colors={colors} editable onChange={(value) => update('last_name', value)} />
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
      <Field label="DOB" value={draft.dob} type="date" colors={colors} editable onChange={(value) => update('dob', value)} />
      <Field label="SSN" value={draft.ssn} colors={colors} editable onChange={(value) => update('ssn', value)} />
      <Field label="Phone" value={draft.phone} colors={colors} editable onChange={(value) => update('phone', value)} />
    </div>
    <Field label="Primary Address" value={draft.address} colors={colors} editable onChange={(value) => update('address', value)} />
    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12 }}>
      <Field label="City" value={draft.city} colors={colors} editable onChange={(value) => update('city', value)} />
      <Field label="State" value={draft.state} colors={colors} editable onChange={(value) => update('state', value)} />
      <Field label="ZIP" value={draft.zip} colors={colors} editable onChange={(value) => update('zip', value)} />
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
      <Field label="Gender" value={draft.gender} colors={colors} editable onChange={(value) => update('gender', value)} />
      <Field label="Race" value={draft.race} colors={colors} editable onChange={(value) => update('race', value)} />
      <Field label="Ethnicity" value={draft.ethnicity} colors={colors} editable onChange={(value) => update('ethnicity', value)} />
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
      <Field label="Primary Language" value={draft.language} colors={colors} editable onChange={(value) => update('language', value)} />
      <Field label="Religion" value={draft.religion} colors={colors} editable onChange={(value) => update('religion', value)} />
      <Field label="Marital Status" value={draft.marital_status} colors={colors} editable onChange={(value) => update('marital_status', value)} />
    </div>
    <SectionNote colors={colors}>Email is not stored on the current facesheet backend and is not editable here.</SectionNote>
  </div>
);

const InsuranceCard = ({ colors, draft, update }) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Insurance" colors={colors} />
    <div style={{ marginBottom: 12 }}>
      <div style={{ marginBottom: 8 }}><Badge variant="teal" colors={colors}>PRIMARY</Badge></div>
      <Field label="Payer" value={draft.primary_payer} colors={colors} editable onChange={(value) => update('primary_payer', value)} />
      <Field label="Policy Number" value={draft.primary_policy_number} colors={colors} editable onChange={(value) => update('primary_policy_number', value)} />
      <Field label="MBI Number" value={draft.mbi_number} colors={colors} editable onChange={(value) => update('mbi_number', value)} />
    </div>
    <div>
      <div style={{ marginBottom: 8 }}><Badge variant="teal" colors={colors}>SECONDARY</Badge></div>
      <Field label="Payer" value={draft.secondary_payer} colors={colors} editable onChange={(value) => update('secondary_payer', value)} />
      <Field label="Policy Number" value={draft.secondary_policy_number} colors={colors} editable onChange={(value) => update('secondary_policy_number', value)} />
    </div>
    <SectionNote colors={colors}>Only primary and secondary payer details are stored on the current facesheet backend.</SectionNote>
  </div>
);

const DocumentPlaceholder = ({ colors, title, buttonLabel }) => (
  <div style={{ minWidth: 0 }}>
    <div style={{ color: colors.white, fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{title}</div>
    <div style={{ border: `1px dashed ${colors.border}`, borderRadius: 8, padding: 16, textAlign: 'center', margin: '8px 0 12px' }}>
      <span style={{ color: colors.label, fontSize: 12 }}>Document upload is not wired to this facesheet endpoint yet.</span><br />
      <button type="button" disabled style={{ marginTop: 8, padding: '6px 16px', backgroundColor: colors.border, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, cursor: 'not-allowed' }}>{buttonLabel}</button>
    </div>
    <div style={{ color: colors.label, fontSize: 11 }}>Use the save button above to persist the authorization fields on this page.</div>
  </div>
);

const AuthEligibility = ({ colors, draft, update }) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Authorization & Eligibility Documents" colors={colors} />
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1.2fr) minmax(260px, 1fr)', gap: 12, alignItems: 'stretch' }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
          <Field
            label="Requires Prior Authorization"
            value={selectBooleanValue(draft.requires_prior_authorization)}
            type="select"
            options={BOOLEAN_OPTIONS}
            colors={colors}
            editable
            onChange={(value) => update('requires_prior_authorization', parseBooleanValue(value))}
          />
          <Field
            label="Authorization Required For"
            value={draft.authorization_required_for}
            type="select"
            options={AUTH_REQUIRED_FOR_OPTIONS}
            colors={colors}
            editable
            onChange={(value) => update('authorization_required_for', value)}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
          <Field label="Authorization Number" value={draft.authorization_number} colors={colors} editable onChange={(value) => update('authorization_number', value)} />
          <Field
            label="Authorization Status"
            value={draft.authorization_status}
            type="select"
            options={AUTH_STATUS_OPTIONS}
            colors={colors}
            editable
            onChange={(value) => update('authorization_status', value)}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
          <Field label="Authorization Start Date" value={draft.authorization_start_date} type="date" colors={colors} editable onChange={(value) => update('authorization_start_date', value)} />
          <Field label="Authorization End Date" value={draft.authorization_end_date} type="date" colors={colors} editable onChange={(value) => update('authorization_end_date', value)} />
        </div>
      </div>
      <div style={{ display: 'grid', gap: 12 }}>
        <DocumentPlaceholder colors={colors} title="Authorization Documents" buttonLabel="Choose File" />
        <DocumentPlaceholder colors={colors} title="Eligibility / Submission Documents" buttonLabel="Upload" />
      </div>
    </div>
  </div>
);

const DiagnosisReferenceList = ({ title, items, colors }) => (
  <div style={{ marginBottom: 10 }}>
    <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>{title}</span>
    {items?.length ? items.map((item) => (
      <div key={item.id || `${title}-${item.display_name || item.diagnosis_description}`} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: '8px 10px', marginBottom: 6, backgroundColor: colors.bg }}>
        <div style={{ color: colors.white, fontSize: 11.5, fontWeight: 600 }}>{item.display_name || item.diagnosis_description || item.icd10_code || 'Diagnosis'}</div>
        <div style={{ color: colors.label, fontSize: 10.5, marginTop: 3 }}>
          {item.icd10_code || 'No ICD-10'} {item.is_related_to_terminal ? '• Related to terminal diagnosis' : ''}
        </div>
      </div>
    )) : <div style={{ color: colors.label, fontSize: 11 }}>No active diagnoses listed.</div>}
  </div>
);

const DiagnosesAllergies = ({ colors, draft, update, facesheet }) => {
  const activePrimary = facesheet?.clinical?.active_primary_diagnosis;
  const activeSecondary = facesheet?.clinical?.active_secondary_diagnoses || [];
  const activeComorbidities = facesheet?.clinical?.active_comorbidities || [];

  return (
    <div style={cardBase(colors)}>
      <CardHeader title="Diagnoses & Allergies" colors={colors} />
      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr 0.9fr', gap: 0, alignItems: 'stretch' }}>
        <div style={{ minWidth: 0, paddingRight: 16 }}>
          <Field label="Primary Diagnosis" value={draft.primary_diagnosis} colors={colors} editable onChange={(value) => update('primary_diagnosis', value)} />
          <Field label="Secondary Diagnoses" value={draft.secondary_diagnoses} type="textarea" rows={6} colors={colors} editable onChange={(value) => update('secondary_diagnoses', value)} />
        </div>
        <div style={{ minWidth: 0, padding: '0 16px', borderLeft: `1px solid ${colors.border}` }}>
          <span style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>Assessment-Derived Diagnosis Summary</span>
          <SectionNote colors={colors}>These diagnoses are read-only here because they are derived from other clinical assessments.</SectionNote>
          <div style={{ marginTop: 8 }}>
            <DiagnosisReferenceList title="Active Primary" items={activePrimary ? [activePrimary] : []} colors={colors} />
            <DiagnosisReferenceList title="Active Secondary" items={activeSecondary} colors={colors} />
            <DiagnosisReferenceList title="Active Comorbidities" items={activeComorbidities} colors={colors} />
          </div>
        </div>
        <div style={{ minWidth: 0, paddingLeft: 16, borderLeft: `1px solid ${colors.border}`, display: 'flex', flexDirection: 'column' }}>
          <Field
            label="Has Allergies"
            value={selectBooleanValue(draft.has_allergies)}
            type="select"
            options={BOOLEAN_OPTIONS}
            colors={colors}
            editable
            onChange={(value) => update('has_allergies', parseBooleanValue(value))}
          />
          <Field label="Allergies" value={draft.allergies} type="textarea" rows={4} colors={colors} editable onChange={(value) => update('allergies', value)} />
          <div style={{ marginTop: 'auto' }}>
            <Field label="Referral Date" value={draft.ref_date} type="date" colors={colors} editable onChange={(value) => update('ref_date', value)} />
            <Field label="Recert Date" value={draft.recert_date} type="date" colors={colors} editable onChange={(value) => update('recert_date', value)} />
            <Field label="Admission Date" value={formatDateDisplay(facesheet?.service_dates?.admission_date)} colors={colors} />
          </div>
        </div>
      </div>
    </div>
  );
};

const PlaceOfService = ({
  colors,
  draft,
  update,
  posHistory,
  posHistoryLoading,
  posHistoryError,
  addStayOpen,
  setAddStayOpen,
  posForm,
  updatePosForm,
  posHistorySaving,
  onAddStay,
}) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Place of Service" colors={colors} />
    {posHistory?.current_entry ? (
      <div style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: colors.bg, marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <Badge variant="teal" colors={colors}>Current Stay</Badge>
          <span style={{ color: colors.label, fontSize: 11 }}>
            {formatDateDisplay(posHistory.current_entry.start_date)} to {posHistory.current_entry.end_date ? formatDateDisplay(posHistory.current_entry.end_date) : 'Ongoing'}
          </span>
        </div>
        <div style={{ color: colors.white, fontSize: 12.5, fontWeight: 600 }}>
          {posHistory.current_entry.pos_name || 'Unnamed location'} — {formatEnumLabel(posHistory.current_entry.pos_type)}
        </div>
        {posHistory.current_entry.reason ? (
          <div style={{ color: colors.label, fontSize: 11, marginTop: 4 }}>{posHistory.current_entry.reason}</div>
        ) : null}
      </div>
    ) : null}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
      <Field label="Facility Type" value={draft.current_pos_type} type="select" options={POS_TYPE_OPTIONS} colors={colors} editable onChange={(value) => update('current_pos_type', value)} />
      <Field label="Facility Name" value={draft.current_pos_name} colors={colors} editable onChange={(value) => update('current_pos_name', value)} />
    </div>
    <Field label="Address" value={draft.current_pos_address} colors={colors} editable onChange={(value) => update('current_pos_address', value)} />
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
      <Field label="Room Number" value={draft.room_number} colors={colors} editable onChange={(value) => update('room_number', value)} />
      <Field label="Start Date" value={draft.pos_start_date} type="date" colors={colors} editable onChange={(value) => update('pos_start_date', value)} />
      <Field label="End Date" value={draft.pos_end_date} type="date" colors={colors} editable onChange={(value) => update('pos_end_date', value)} />
    </div>
    <div style={{ borderTop: `1px solid ${colors.border}`, marginTop: 8, paddingTop: 8 }}>
      <div style={{ marginBottom: 8 }}><Badge variant="teal" colors={colors}>LEVEL OF CARE</Badge></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
        <Field label="Current Level of Care" value={draft.current_level_of_care} type="select" options={LOC_OPTIONS} colors={colors} editable onChange={(value) => update('current_level_of_care', value)} />
        <Field label="LOC Effective Date" value={draft.loc_effective_date} type="date" colors={colors} editable onChange={(value) => update('loc_effective_date', value)} />
      </div>
    </div>
    <div style={{ borderTop: `1px solid ${colors.border}`, marginTop: 10, paddingTop: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>Stay History</div>
        <button
          type="button"
          onClick={() => setAddStayOpen((value) => !value)}
          style={{ padding: '6px 12px', backgroundColor: colors.teal, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, cursor: 'pointer' }}
        >
          {addStayOpen ? 'Cancel' : '+ Add Stay'}
        </button>
      </div>
      {addStayOpen ? (
        <div style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 10, backgroundColor: colors.bg, marginBottom: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
            <Field label="Type" value={posForm.pos_type} type="select" options={POS_TYPE_OPTIONS} colors={colors} editable onChange={(value) => updatePosForm('pos_type', value)} />
            <Field label="Facility Name" value={posForm.pos_name} colors={colors} editable onChange={(value) => updatePosForm('pos_name', value)} />
          </div>
          <Field label="Address" value={posForm.pos_address} colors={colors} editable onChange={(value) => updatePosForm('pos_address', value)} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <Field label="Room Number" value={posForm.room_number} colors={colors} editable onChange={(value) => updatePosForm('room_number', value)} />
            <Field label="Start Date" value={posForm.start_date} type="date" colors={colors} editable onChange={(value) => updatePosForm('start_date', value)} />
            <Field label="End Date" value={posForm.end_date} type="date" colors={colors} editable onChange={(value) => updatePosForm('end_date', value)} />
          </div>
          <Field label="Reason / Notes" value={posForm.reason} type="textarea" rows={3} colors={colors} editable onChange={(value) => updatePosForm('reason', value)} />
          {posHistoryError ? <div style={{ color: colors.red, fontSize: 11, marginBottom: 8 }}>{posHistoryError}</div> : null}
          <button
            type="button"
            onClick={onAddStay}
            disabled={posHistorySaving}
            style={{ padding: '8px 16px', backgroundColor: posHistorySaving ? colors.border : colors.teal, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: posHistorySaving ? 'not-allowed' : 'pointer' }}
          >
            {posHistorySaving ? 'Saving…' : 'Save Stay'}
          </button>
        </div>
      ) : null}
      {posHistoryLoading ? (
        <div style={{ color: colors.label, fontSize: 11 }}>Loading stay history...</div>
      ) : posHistory?.entries?.length ? (
        <div style={{ display: 'grid', gap: 8 }}>
          {posHistory.entries.map((entry) => (
            <div key={entry.id} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: colors.bg }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                <div style={{ color: colors.white, fontSize: 12.5, fontWeight: 600 }}>
                  {formatEnumLabel(entry.pos_type)} — {entry.pos_name || 'Unnamed location'}
                </div>
                {entry.is_current ? <Badge variant="green" colors={colors}>Current</Badge> : null}
              </div>
              <div style={{ color: colors.label, fontSize: 11, marginTop: 4 }}>
                {formatDateDisplay(entry.start_date)} to {entry.end_date ? formatDateDisplay(entry.end_date) : 'Ongoing'}
              </div>
              {entry.reason ? <div style={{ color: colors.label, fontSize: 11, marginTop: 4 }}>{entry.reason}</div> : null}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: colors.label, fontSize: 11 }}>No place-of-service history has been recorded yet.</div>
      )}
    </div>
  </div>
);

const ContactBlock = ({ colors, title, badge, nameValue, relationshipValue, phoneValue, onNameChange, onRelationshipChange, onPhoneChange }) => (
  <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: `1px solid ${colors.border}` }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 8 }}>
      <span style={{ color: colors.white, fontSize: 15, fontWeight: 600 }}>{title}</span>
      <Badge variant="teal" colors={colors}>{badge}</Badge>
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr', gap: 12 }}>
      <Field label="Name" value={nameValue} colors={colors} editable onChange={onNameChange} />
      <Field label="Relationship" value={relationshipValue} colors={colors} editable onChange={onRelationshipChange} />
      <Field label="Phone" value={phoneValue} colors={colors} editable onChange={onPhoneChange} />
    </div>
  </div>
);

const AuthorizedRep = ({ colors, draft, update }) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Authorized Rep & Emergency Contacts" colors={colors} />
    <ContactBlock
      colors={colors}
      title={draft.responsible_party_name || 'Responsible Party'}
      badge="Responsible Party"
      nameValue={draft.responsible_party_name}
      relationshipValue={draft.responsible_party_relationship}
      phoneValue={draft.responsible_party_phone}
      onNameChange={(value) => update('responsible_party_name', value)}
      onRelationshipChange={(value) => update('responsible_party_relationship', value)}
      onPhoneChange={(value) => update('responsible_party_phone', value)}
    />
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 8 }}>
        <span style={{ color: colors.white, fontSize: 15, fontWeight: 600 }}>{draft.emergency_contact_name || 'Emergency Contact'}</span>
        <Badge variant="teal" colors={colors}>Emergency Contact</Badge>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr', gap: 12 }}>
        <Field label="Name" value={draft.emergency_contact_name} colors={colors} editable onChange={(value) => update('emergency_contact_name', value)} />
        <Field label="Relationship" value={draft.emergency_contact_relationship} colors={colors} editable onChange={(value) => update('emergency_contact_relationship', value)} />
        <Field label="Phone" value={draft.emergency_contact_phone} colors={colors} editable onChange={(value) => update('emergency_contact_phone', value)} />
      </div>
    </div>
    <SectionNote colors={colors}>The backend stores one responsible party and one emergency contact on the facesheet.</SectionNote>
  </div>
);

const formatPhysicianDirectoryAddress = (physician) => {
  const lineOne = [physician?.address_street, physician?.address_suite].filter(Boolean).join(', ');
  const lineTwo = [physician?.address_city, physician?.address_state, physician?.address_zip].filter(Boolean).join(', ');
  return [lineOne, lineTwo].filter(Boolean).join(', ');
};

const getPhysicianDirectoryDisplayName = (physician) => (
  physician?.display_name
  || [physician?.first_name, physician?.last_name].filter(Boolean).join(' ').trim()
  || ''
);

const directoryActionButton = (colors) => ({
  border: `1px solid ${colors.border}`,
  backgroundColor: colors.bg,
  color: colors.white,
  borderRadius: 6,
  width: 30,
  height: 30,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 700,
});

const PhysicianPickerInput = ({
  colors,
  value,
  onChange,
  onDirectorySelect,
  onOpenDirectory,
  warning = false,
  hint = '',
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchSuggestions = async (query = value ?? '') => {
    try {
      setLoading(true);
      const trimmed = query.trim();
      const results = await listPhysicians(trimmed ? { name: trimmed, status: 'both' } : { status: 'active' });
      setSuggestions(results.slice(0, 6));
      setOpen(true);
    } catch (error) {
      console.error('Failed to fetch physician suggestions', error);
      setSuggestions([]);
      setOpen(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const trimmed = value?.trim() || '';
    if (!trimmed) {
      setSuggestions([]);
      setOpen(false);
      return undefined;
    }

    let active = true;
    const handle = window.setTimeout(async () => {
      try {
        setLoading(true);
        const results = await listPhysicians({ name: trimmed, status: 'both' });
        if (active) {
          setSuggestions(results.slice(0, 6));
          setOpen(true);
        }
      } catch (error) {
        console.error('Failed to fetch physician suggestions', error);
        if (active) {
          setSuggestions([]);
          setOpen(false);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      window.clearTimeout(handle);
    };
  }, [value]);

  return (
    <div>
      <div style={{ color: warning ? colors.amber : colors.label, fontSize: 11, textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Name</div>
      <div style={{ position: 'relative' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto auto', gap: 8, alignItems: 'center' }}>
          <input
            value={value ?? ''}
            onChange={(event) => onChange(event.target.value)}
            onFocus={() => {
              if (suggestions.length > 0) {
                setOpen(true);
              }
            }}
            onBlur={() => window.setTimeout(() => setOpen(false), 120)}
            placeholder="Type a physician name or use +"
            style={{
              ...baseInputStyle(colors),
              border: `1px solid ${warning ? colors.amber : colors.border}`,
            }}
          />
          <button type="button" aria-label="Open physician directory" title="Open physician directory" style={directoryActionButton(colors)} onMouseDown={(event) => event.preventDefault()} onClick={onOpenDirectory}>+</button>
          <button type="button" aria-label="Refresh physician suggestions" title="Refresh physician suggestions" style={directoryActionButton(colors)} onMouseDown={(event) => event.preventDefault()} onClick={() => fetchSuggestions(value)}>↻</button>
        </div>
        {loading ? <div style={{ color: colors.label, fontSize: 11, marginTop: 6 }}>Searching directory…</div> : null}
        {open && suggestions.length > 0 ? (
          <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0, backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, boxShadow: '0 10px 30px rgba(15, 23, 42, 0.18)', zIndex: 20, maxHeight: 220, overflowY: 'auto' }}>
            {suggestions.map((physician) => (
              <button
                key={physician.id}
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onDirectorySelect(physician);
                  setOpen(false);
                }}
                style={{ width: '100%', border: 'none', backgroundColor: 'transparent', color: colors.white, padding: '10px 12px', textAlign: 'left', cursor: 'pointer', borderBottom: `1px solid ${colors.border}` }}
              >
                <div style={{ fontWeight: 600 }}>{getPhysicianDirectoryDisplayName(physician)}</div>
                <div style={{ color: colors.label, fontSize: 11 }}>
                  {[physician.specialty_type, physician.phone, physician.npi].filter(Boolean).join(' • ') || 'Directory physician'}
                </div>
              </button>
            ))}
          </div>
        ) : null}
      </div>
      {hint ? <div style={{ color: warning ? colors.amber : colors.label, fontSize: 10.5, marginTop: 4 }}>{hint}</div> : null}
    </div>
  );
};

const PhysicianPanel = ({
  colors,
  title,
  name,
  address,
  npi,
  phone,
  fax,
  onNameChange,
  onAddressChange,
  onNpiChange,
  onPhoneChange,
  onFaxChange,
  onDirectorySelect,
  onOpenDirectory,
  followingValue,
  onFollowingChange,
  warning = false,
  warningHint = '',
  phoneLabel = 'Phone',
  addressLabel = 'Address',
}) => (
  <div style={{ border: `1px solid ${warning ? colors.amber : colors.border}`, borderRadius: 8, padding: 10, backgroundColor: warning ? colors.amberBg : colors.bg }}>
    <span style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 12 }}>{title}</span>
    <div style={{ display: 'grid', gridTemplateColumns: onFollowingChange ? 'minmax(0, 1.2fr) minmax(220px, 0.8fr)' : '1fr', gap: 12, alignItems: 'start' }}>
      <PhysicianPickerInput
        colors={colors}
        value={name}
        onChange={onNameChange}
        onDirectorySelect={onDirectorySelect}
        onOpenDirectory={onOpenDirectory}
        warning={warning}
        hint={warningHint}
      />
      {onFollowingChange ? (
        <ToggleField
          colors={colors}
          label="Will follow patient in hospice"
          checked={followingValue === true}
          onChange={onFollowingChange}
          warning={followingValue === false}
          hint={followingValue === false ? 'No selected — verify covering hospice physician contact below.' : 'Check when the attending physician will continue following in hospice.'}
        />
      ) : null}
    </div>
    {onAddressChange ? (
      <Field
        label={addressLabel}
        value={address}
        colors={colors}
        editable
        onChange={onAddressChange}
        inputBorderColor={warning ? colors.amber : undefined}
        labelColor={warning ? colors.amber : undefined}
        hint={warningHint}
      />
    ) : null}
    {onPhoneChange ? (
      <Field
        label={phoneLabel}
        value={phone}
        colors={colors}
        editable
        onChange={onPhoneChange}
        inputBorderColor={warning ? colors.amber : undefined}
        labelColor={warning ? colors.amber : undefined}
        hint={warningHint}
      />
    ) : null}
    {onFaxChange ? (
      <Field
        label="Fax"
        value={fax}
        colors={colors}
        editable
        onChange={onFaxChange}
      />
    ) : null}
    <Field label="NPI" value={npi} colors={colors} editable onChange={onNpiChange} />
  </div>
);

const ReferralPhysicians = ({ colors, draft, update }) => {
  const [directoryRole, setDirectoryRole] = useState(null);

  const roleConfig = {
    attending: {
      title: 'Attending Physician',
      nameField: 'attending_physician_name',
      addressField: 'attending_physician_address',
      phoneField: 'attending_physician_phone',
      faxField: 'attending_physician_fax',
      npiField: 'attending_physician_npi',
    },
    medicalDirector: {
      title: 'Medical Director',
      nameField: 'medical_director_name',
      addressField: 'medical_director_address',
      phoneField: 'medical_director_phone',
      faxField: 'medical_director_fax',
      npiField: 'medical_director_npi',
    },
    medicalDirectorDesignee: {
      title: 'Medical Director Designee',
      nameField: 'medical_director_designee_name',
      npiField: 'medical_director_designee_npi',
    },
    associateMedicalDirector: {
      title: 'Associate Medical Director',
      nameField: 'associate_medical_director_name',
      npiField: 'associate_medical_director_npi',
    },
  };

  const applyDirectorySelection = (roleKey, physician) => {
    const config = roleConfig[roleKey];
    if (!config) return;
    update(config.nameField, getPhysicianDirectoryDisplayName(physician));
    update(config.npiField, physician?.npi || '');
    if (config.addressField) {
      update(config.addressField, formatPhysicianDirectoryAddress(physician));
    }
    if (config.phoneField) {
      update(config.phoneField, physician?.phone || '');
    }
    if (config.faxField) {
      update(config.faxField, physician?.fax || '');
    }
    setDirectoryRole(null);
  };

  const attendingNotFollowing = draft.attending_physician_following === false;
  const attendingFollowing = draft.attending_physician_following === true;
  const attendingCoverageMissing = attendingFollowing
    && (!draft.attending_physician_phone.trim() || !draft.attending_physician_address.trim());
  const medicalDirectorCoverageMissing = attendingNotFollowing
    && (!draft.medical_director_name.trim() || !draft.medical_director_phone.trim() || !draft.medical_director_address.trim());

  return (
  <div style={cardBase(colors)}>
    <CardHeader title="Referral Physicians" colors={colors} />
    {attendingFollowing ? (
      <div style={{ border: `1px solid ${colors.amber}`, backgroundColor: colors.amberBg, color: colors.amber, borderRadius: 8, padding: '8px 10px', marginBottom: 12, fontSize: 11.5, fontWeight: 600 }}>
        ⚠ Attending physician will follow this patient in hospice — verify a direct, working callback number for the attending physician's office below.
      </div>
    ) : null}
    {attendingNotFollowing ? (
      <div style={{ border: `1px solid ${colors.amber}`, backgroundColor: colors.amberBg, color: colors.amber, borderRadius: 8, padding: '8px 10px', marginBottom: 12, fontSize: 11.5, fontWeight: 600 }}>
        ⚠ Attending physician will not follow this patient in hospice — verify Hospice Medical Director contact info below is complete for verbal orders.
      </div>
    ) : null}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
      <PhysicianPanel
        colors={colors}
        title="Attending Physician"
        name={draft.attending_physician_name}
        address={draft.attending_physician_address}
        phone={draft.attending_physician_phone}
        fax={draft.attending_physician_fax}
        npi={draft.attending_physician_npi}
        followingValue={draft.attending_physician_following}
        onNameChange={(value) => update('attending_physician_name', value)}
        onAddressChange={(value) => update('attending_physician_address', value)}
        onPhoneChange={(value) => update('attending_physician_phone', value)}
        onFaxChange={(value) => update('attending_physician_fax', value)}
        onNpiChange={(value) => update('attending_physician_npi', value)}
        onDirectorySelect={(physician) => applyDirectorySelection('attending', physician)}
        onOpenDirectory={() => setDirectoryRole('attending')}
        onFollowingChange={(value) => update('attending_physician_following', value)}
        warning={attendingCoverageMissing}
        warningHint={attendingFollowing ? 'Required — direct callback phone and address must be verified for the attending physician office. Do not rely only on family report.' : ''}
        phoneLabel="Direct Callback Phone"
      />
      <PhysicianPanel
        colors={colors}
        title="Medical Director"
        name={draft.medical_director_name}
        address={draft.medical_director_address}
        phone={draft.medical_director_phone}
        fax={draft.medical_director_fax}
        npi={draft.medical_director_npi}
        onNameChange={(value) => update('medical_director_name', value)}
        onAddressChange={(value) => update('medical_director_address', value)}
        onPhoneChange={(value) => update('medical_director_phone', value)}
        onFaxChange={(value) => update('medical_director_fax', value)}
        onNpiChange={(value) => update('medical_director_npi', value)}
        onDirectorySelect={(physician) => applyDirectorySelection('medicalDirector', physician)}
        onOpenDirectory={() => setDirectoryRole('medicalDirector')}
        warning={medicalDirectorCoverageMissing}
        warningHint={attendingNotFollowing ? 'Required — Hospice Medical Director will assume ordering responsibility for this patient. Verify direct phone and address.' : ''}
      />
      <PhysicianPanel
        colors={colors}
        title="Medical Director Designee"
        name={draft.medical_director_designee_name}
        npi={draft.medical_director_designee_npi}
        onNameChange={(value) => update('medical_director_designee_name', value)}
        onNpiChange={(value) => update('medical_director_designee_npi', value)}
        onDirectorySelect={(physician) => applyDirectorySelection('medicalDirectorDesignee', physician)}
        onOpenDirectory={() => setDirectoryRole('medicalDirectorDesignee')}
      />
      <PhysicianPanel
        colors={colors}
        title="Associate Medical Director"
        name={draft.associate_medical_director_name}
        npi={draft.associate_medical_director_npi}
        onNameChange={(value) => update('associate_medical_director_name', value)}
        onNpiChange={(value) => update('associate_medical_director_npi', value)}
        onDirectorySelect={(physician) => applyDirectorySelection('associateMedicalDirector', physician)}
        onOpenDirectory={() => setDirectoryRole('associateMedicalDirector')}
      />
    </div>
    <SectionNote colors={colors}>Attending and Hospice Medical Director address/phone/fax are stored here for hospice ordering workflow. Fax is optional; direct phone and address are highlighted for whichever physician is responsible for orders.</SectionNote>
    <PhysicianDirectoryModal
      key={directoryRole || 'closed'}
      open={Boolean(directoryRole)}
      onClose={() => setDirectoryRole(null)}
      onSelect={(physician) => directoryRole && applyDirectorySelection(directoryRole, physician)}
      colors={colors}
      title={directoryRole ? `${roleConfig[directoryRole].title} Directory` : 'Physician Directory'}
    />
  </div>
  );
};

const ServiceVendors = ({ colors, draft, update }) => (
  <div style={cardBase(colors)}>
    <CardHeader title="Service Vendors" colors={colors} />
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24 }}>
      <div>
        <div style={{ color: colors.white, fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Pharmacy</div>
        <Field label="Vendor" value={draft.pharmacy_name} colors={colors} editable onChange={(value) => update('pharmacy_name', value)} />
        <Field label="Phone" value={draft.pharmacy_phone} colors={colors} editable onChange={(value) => update('pharmacy_phone', value)} />
        <Field label="Fax" value={draft.pharmacy_fax} colors={colors} editable onChange={(value) => update('pharmacy_fax', value)} />
      </div>
      <div>
        <div style={{ color: colors.white, fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Durable Medical Equipment (DME)</div>
        <Field label="Vendor" value={draft.dme_vendor_name} colors={colors} editable onChange={(value) => update('dme_vendor_name', value)} />
        <Field label="Phone" value={draft.dme_vendor_phone} colors={colors} editable onChange={(value) => update('dme_vendor_phone', value)} />
      </div>
    </div>
    <SectionNote colors={colors}>Other supplies vendors are not stored on the current facesheet backend.</SectionNote>
  </div>
);

const matchingBottomCard = (colors) => ({
  ...cardBase(colors),
  minHeight: 220,
  height: '100%',
  width: '100%',
  padding: 8,
  boxSizing: 'border-box',
  overflow: 'hidden',
});

const MortuaryInfo = ({ colors, draft, update }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div style={matchingBottomCard(colors)}>
      <CardHeader title="Mortuary Information" colors={colors} onToggle={() => setExpanded((value) => !value)} isExpanded={expanded} />
      {expanded ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, alignItems: 'start' }}>
            <Field label="Name" value={draft.mortuary_name} colors={colors} editable onChange={(value) => update('mortuary_name', value)} />
            <Field label="Phone" value={draft.mortuary_phone} colors={colors} editable onChange={(value) => update('mortuary_phone', value)} />
          </div>
          <SectionNote colors={colors}>Address, fax, email, contact person, and pre-arrangement are not stored on the current facesheet backend.</SectionNote>
        </>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, alignItems: 'center' }}>
          <Field label="Name" value={draft.mortuary_name} style={{ marginBottom: 0 }} colors={colors} />
          <Field label="Phone" value={draft.mortuary_phone} style={{ marginBottom: 0 }} colors={colors} />
        </div>
      )}
    </div>
  );
};

const SpecialInstructions = ({ colors, draft, update }) => (
  <div style={matchingBottomCard(colors)}>
    <CardHeader title="Special Instructions" colors={colors} />
    <Field
      label="Special Instructions"
      value={draft.special_instructions}
      type="textarea"
      rows={8}
      colors={colors}
      editable
      onChange={(value) => update('special_instructions', value)}
      placeholder="Enter special instructions for the care team"
    />
  </div>
);

const PatientFacesheet = ({ patientId }) => {
  const { mode } = useThemeMode();
  const colors = getColors(mode);
  const [facesheet, setFacesheet] = useState(null);
  const [posHistory, setPosHistory] = useState({ current_entry: null, entries: [] });
  const [draft, setDraft] = useState(createEmptyDraft());
  const [savedDraft, setSavedDraft] = useState(createEmptyDraft());
  const [posForm, setPosForm] = useState(createEmptyPosForm());
  const [addStayOpen, setAddStayOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [posHistoryLoading, setPosHistoryLoading] = useState(false);
  const [posHistorySaving, setPosHistorySaving] = useState(false);
  const [posHistoryError, setPosHistoryError] = useState('');
  const [saveState, setSaveState] = useState('idle');
  const [saveMessage, setSaveMessage] = useState('');

  const loadFacesheetData = async (activePatientId) => {
    const result = await fetchFacesheet(activePatientId);
    const nextDraft = mapResponseToDraft(result);
    setFacesheet(result);
    setDraft(nextDraft);
    setSavedDraft(nextDraft);
  };

  const loadPosHistoryData = async (activePatientId) => {
    setPosHistoryLoading(true);
    try {
      const result = await fetchPosHistory(activePatientId);
      setPosHistory(result);
      setPosHistoryError('');
    } catch {
      setPosHistory({ current_entry: null, entries: [] });
      setPosHistoryError('Unable to load place-of-service history.');
    } finally {
      setPosHistoryLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    if (!patientId) {
      setFacesheet(null);
      setPosHistory({ current_entry: null, entries: [] });
      setDraft(createEmptyDraft());
      setSavedDraft(createEmptyDraft());
      setPosForm(createEmptyPosForm());
      setAddStayOpen(false);
      setLoadError('No patient selected.');
      setLoading(false);
      return () => {
        mounted = false;
      };
    }

    setLoading(true);
    setLoadError('');
    setPosHistoryError('');
    setSaveState('idle');
    setSaveMessage('');

    Promise.all([
      fetchFacesheet(patientId),
      fetchPosHistory(patientId).catch(() => null),
    ])
      .then(([facesheetResult, posHistoryResult]) => {
        if (!mounted) return;
        const nextDraft = mapResponseToDraft(facesheetResult);
        setFacesheet(facesheetResult);
        setDraft(nextDraft);
        setSavedDraft(nextDraft);
        setPosHistory(posHistoryResult || { current_entry: null, entries: [] });
        setPosHistoryError(posHistoryResult ? '' : 'Unable to load place-of-service history.');
      })
      .catch(() => {
        if (!mounted) return;
        setFacesheet(null);
        setPosHistory({ current_entry: null, entries: [] });
        setDraft(createEmptyDraft());
        setSavedDraft(createEmptyDraft());
        setLoadError('Unable to load patient facesheet.');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    if (saveState !== 'saved') return undefined;
    const timer = window.setTimeout(() => {
      setSaveState('idle');
      setSaveMessage('');
    }, 3000);
    return () => window.clearTimeout(timer);
  }, [saveState]);

  const isDirty = useMemo(() => JSON.stringify(draft) !== JSON.stringify(savedDraft), [draft, savedDraft]);
  const orderingContactState = useMemo(() => getOrderingContactState(draft), [draft]);

  const update = (field, value) => {
    setDraft((previous) => ({ ...previous, [field]: value }));
    if (saveState === 'error') {
      setSaveState('idle');
      setSaveMessage('');
    }
  };

  const handleSave = async () => {
    if (!patientId || saveState === 'saving') return;
    if (!draft.first_name.trim() || !draft.last_name.trim()) {
      setSaveState('error');
      setSaveMessage('First name and last name are required before saving.');
      return;
    }

    const payload = buildPayload(draft);
    setSaveState('saving');
    setSaveMessage('Saving facesheet…');

    try {
      if (posHistory?.current_entry?.id && draft.current_pos_type && draft.pos_start_date) {
        await updatePosHistory(
          patientId,
          posHistory.current_entry.id,
          buildCurrentPosUpdatePayload(draft, posHistory.current_entry),
        );
      } else if (!posHistory?.entries?.length && draft.current_pos_type && draft.pos_start_date) {
        await createPosHistory(
          patientId,
          buildPosHistoryPayload({
            pos_type: draft.current_pos_type,
            pos_name: draft.current_pos_name,
            pos_address: draft.current_pos_address,
            room_number: draft.room_number,
            start_date: draft.pos_start_date,
            end_date: draft.pos_end_date,
            reason: '',
          }),
        );
      }
      await saveFacesheet(patientId, payload);
      setSavedDraft(draft);
      setSaveState('saved');
      setSaveMessage('Saved ✓');

      try {
        await Promise.all([
          loadFacesheetData(patientId),
          loadPosHistoryData(patientId),
        ]);
      } catch {
        setFacesheet((previous) => previous);
      }
    } catch (error) {
      const detail = error?.response?.data?.detail;
      setSaveState('error');
      setSaveMessage(detail || 'Unable to save facesheet changes.');
    }
  };

  const updatePosForm = (field, value) => {
    setPosForm((previous) => ({ ...previous, [field]: value }));
    if (posHistoryError) {
      setPosHistoryError('');
    }
  };

  const handleAddStay = async () => {
    if (!patientId || posHistorySaving) return;
    if (!posForm.pos_type || !posForm.start_date) {
      setPosHistoryError('Type and start date are required to add a stay.');
      return;
    }

    setPosHistorySaving(true);
    setPosHistoryError('');
    try {
      await createPosHistory(patientId, buildPosHistoryPayload(posForm));
      setPosForm(createEmptyPosForm());
      setAddStayOpen(false);
      await Promise.all([
        loadFacesheetData(patientId),
        loadPosHistoryData(patientId),
      ]);
    } catch (error) {
      const detail = error?.response?.data?.detail;
      setPosHistoryError(detail || 'Unable to save stay history.');
    } finally {
      setPosHistorySaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg, fontFamily: "'Inter', sans-serif", color: colors.text }}>
        Loading patient chart...
      </div>
    );
  }

  if (!patientId || loadError) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg, fontFamily: "'Inter', sans-serif", color: colors.text, padding: 24, textAlign: 'center' }}>
        {loadError || 'No patient selected.'}
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minWidth: 0, minHeight: 0, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', overflowX: 'hidden', fontFamily: "'Inter', sans-serif" }}>
      <SaveBar
        colors={colors}
        isDirty={isDirty}
        saveState={saveState}
        saveMessage={saveMessage}
        onSave={handleSave}
        disabled={saveState === 'saving'}
      />
      <div style={{ color: colors.label, fontSize: 12, marginBottom: 10 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{getBreadcrumbName(draft)}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: colors.white }}>Facesheet</span>
      </div>
      <PatientBanner colors={colors} draft={draft} facesheet={facesheet} />
      <PatientStatusStrip colors={colors} facesheet={facesheet} />
      <SafetyBanner colors={colors} orderingContactState={orderingContactState} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12, marginBottom: 12, alignItems: 'stretch' }}>
        <div style={{ minWidth: 0 }}><PersonalInformation colors={colors} draft={draft} update={update} /></div>
        <div style={{ minWidth: 0 }}><InsuranceCard colors={colors} draft={draft} update={update} /></div>
      </div>
      <div style={{ marginBottom: 12 }}><AuthEligibility colors={colors} draft={draft} update={update} /></div>
      <div style={{ marginBottom: 12 }}><DiagnosesAllergies colors={colors} draft={draft} update={update} facesheet={facesheet} /></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12, marginBottom: 12, alignItems: 'stretch' }}>
        <div style={{ minWidth: 0 }}><PlaceOfService colors={colors} draft={draft} update={update} posHistory={posHistory} posHistoryLoading={posHistoryLoading} posHistoryError={posHistoryError} addStayOpen={addStayOpen} setAddStayOpen={setAddStayOpen} posForm={posForm} updatePosForm={updatePosForm} posHistorySaving={posHistorySaving} onAddStay={handleAddStay} /></div>
        <div style={{ minWidth: 0 }}><AuthorizedRep colors={colors} draft={draft} update={update} /></div>
      </div>
      <div style={{ marginBottom: 12 }}><ReferralPhysicians colors={colors} draft={draft} update={update} /></div>
      <div style={{ marginBottom: 12 }}><ServiceVendors colors={colors} draft={draft} update={update} /></div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12, alignItems: 'stretch' }}>
        <div style={{ minWidth: 0, display: 'flex', minHeight: 0 }}><div style={{ flex: 1, minWidth: 0, display: 'flex' }}><MortuaryInfo colors={colors} draft={draft} update={update} /></div></div>
        <div style={{ minWidth: 0, display: 'flex', minHeight: 0 }}><div style={{ flex: 1, minWidth: 0, display: 'flex' }}><SpecialInstructions colors={colors} draft={draft} update={update} /></div></div>
      </div>
    </div>
  );
};

export { mapResponseToDraft };
export default PatientFacesheet;
