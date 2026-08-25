import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { COLORS, S } from '../design';
import { setActivePatientId } from '../../utils/activePatient';
import ReferralIntakeModal from './ReferralIntakeModal';

function formatCareLevel(value) {
  if (!value) return 'Routine';
  const normalized = String(value).toUpperCase().replace(/[_-]/g, ' ');
  if (normalized.includes('ROUTINE')) return 'Routine';
  if (normalized.includes('CONTINUOUS')) return 'Continuous';
  if (normalized.includes('RESPITE')) return 'Respite';
  if (normalized.includes('GIP')) return 'GIP';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
}

function formatStatus(value) {
  const status = String(value ?? '').trim();
  if (!status) return 'Active';
  const normalized = status.toUpperCase();
  if (normalized.includes('DISCH')) return 'Pending DC';
  if (normalized.includes('HOLD')) return 'On Hold';
  if (normalized.includes('PENDING')) return 'Pending';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
}

const QUICK_LINKS = ['View Full Chart', 'Visit History', 'Medications & Orders', 'Care Plan & Goals', 'Billing Ledger'];

const ACTIVITY = [
  { title: 'RN Visit Completed', sub: 'John Higgins RN • 10:15 AM' },
  { title: 'Medication Renewal Signed', sub: 'Dr Albert Chen • Yesterday' },
  { title: 'MSW Evaluation Updated', sub: 'Sarah Cole MSW • 2 days ago' },
];

export default function PatientCensus({ census, loading }) {
  const navigate = useNavigate();
  const patientRows = Array.isArray(census?.patients) ? census.patients : [];
  const [selectedPatientId, setSelectedPatientId] = useState(patientRows[0]?.patient_id || null);
  const [showIntakeModal, setShowIntakeModal] = useState(false);
  const [referralSubmittedMessage, setReferralSubmittedMessage] = useState('');

  useEffect(() => {
    if (!patientRows.length) {
      setSelectedPatientId(null);
      return;
    }

    if (!selectedPatientId || !patientRows.some((patient) => patient.patient_id === selectedPatientId)) {
      setSelectedPatientId(patientRows[0].patient_id);
    }
  }, [patientRows, selectedPatientId]);

  const selectedPatient = patientRows.find((patient) => patient.patient_id === selectedPatientId) || patientRows[0] || null;
  const totalPatients = census?.patient_count ?? patientRows.length;

  const handleOpenChart = (patient) => {
    const patientId = patient?.patient_id || patient?.id;
    if (!patientId) return;

    setActivePatientId(patientId);
    setSelectedPatientId(patientId);
    navigate(`/chart/${encodeURIComponent(patientId)}`);
  };

  const handleReferralCreated = () => {
    setShowIntakeModal(false);
    setReferralSubmittedMessage('Referral submitted for review. It will appear on the Referrals queue until accepted or declined.');
  };

  return (
    <div>
      {showIntakeModal ? (
        <ReferralIntakeModal onClose={() => setShowIntakeModal(false)} onCreated={handleReferralCreated} />
      ) : null}
      {referralSubmittedMessage ? (
        <div style={{ marginBottom: 16, padding: '10px 14px', borderRadius: 8, background: 'rgba(20,184,166,0.12)', color: COLORS.teal, fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{referralSubmittedMessage}</span>
          <button type="button" style={{ ...S.btnOutline, padding: '4px 10px' }} onClick={() => setReferralSubmittedMessage('')}>Dismiss</button>
        </div>
      ) : null}
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Patient Census</h1>
          <p style={S.pageSubtitle}>Complete active patient registry with care plans and clinical status</p>
        </div>
        <button style={S.btn(COLORS.teal)} onClick={() => setShowIntakeModal(true)}>Add New Patient</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Census', value: String(totalPatients) },
          { label: 'Routine Care', value: String(patientRows.filter((patient) => String(patient.census_bucket || patient.level || '').toUpperCase().includes('ROUTINE')).length || 0) },
          { label: 'Continuous Care', value: String(patientRows.filter((patient) => String(patient.census_bucket || patient.level || '').toUpperCase().includes('CONTINUOUS')).length || 0) },
          { label: 'Respite Care', value: String(patientRows.filter((patient) => String(patient.census_bucket || patient.level || '').toUpperCase().includes('RESPITE')).length || 0) },
          { label: 'GIP', value: String(patientRows.filter((patient) => String(patient.census_bucket || patient.level || '').toUpperCase().includes('GIP')).length || 0) },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input style={S.searchBar} placeholder="Search by name, MRN, clinician..." readOnly />
        </div>
        {['Dx Group', 'Care Level', 'Assigned RN', 'Status'].map((f) => (
          <select key={f} style={S.select}><option>{f}</option></select>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, margin: 0 }}>Active Registry</h3>
            <span style={{ fontSize: 12, fontWeight: 400, color: COLORS.dim }}>
              {patientRows.length ? `Showing ${Math.min(patientRows.length, 12)} of ${totalPatients} Patients` : 'No active patients'}
            </span>
          </div>

          {!patientRows.length ? (
            <div style={{ padding: '24px 16px', color: COLORS.dim, textAlign: 'center' }}>
              <p style={{ margin: 0, fontSize: 15, color: COLORS.textPrimary }}>No patients found in this census.</p>
              <p style={{ margin: '8px 0 0', fontSize: 12 }}>New referrals and admissions will appear here once they are created.</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['PATIENT NAME', 'MRN', 'PRIMARY DX', 'CARE LEVEL', 'ASSIGNED RN', 'POC EXPIRY', 'STATUS'].map((h) => (
                    <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {patientRows.slice(0, 12).map((p, i) => {
                  const name = p.full_name || p.name;
                  const mrn = p.mrn || p.patient_id;
                  const dx = p.primary_diagnosis || p.dx || '—';
                  const careLevel = formatCareLevel(p.census_bucket || p.level);
                  const status = formatStatus(p.patient_status || p.status);
                  const poc = p.last_visit_at ? new Date(p.last_visit_at).toLocaleDateString() : (p.poc || '—');
                  const statusColor = status === 'On Hold' ? COLORS.orange : status === 'Pending DC' ? COLORS.red : COLORS.green;
                  const pocColor = poc === '—' ? COLORS.muted : status === 'On Hold' ? COLORS.orange : status === 'Pending DC' ? COLORS.red : COLORS.muted;

                  return (
                    <tr
                      key={`${name}-${mrn}-${i}`}
                      onClick={() => handleOpenChart(p)}
                      style={{ cursor: 'pointer', transition: 'background 0.2s ease' }}
                      onMouseEnter={(event) => {
                        event.currentTarget.style.background = 'rgba(94, 234, 212, 0.08)';
                      }}
                      onMouseLeave={(event) => {
                        event.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <td style={{ ...S.tableCell, fontWeight: 600, color: selectedPatient?.patient_id === p.patient_id ? COLORS.teal : COLORS.textPrimary }}>{name}</td>
                      <td style={S.tableCell}>{mrn}</td>
                      <td style={S.tableCell}>{dx}</td>
                      <td style={S.tableCell}>{careLevel}</td>
                      <td style={S.tableCell}>{p.assigned_rn || p.rn || '—'}</td>
                      <td style={{ ...S.tableCell, fontWeight: 500, color: pocColor }}>{poc}</td>
                      <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: statusColor }}>{status}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div style={S.card}>
          {selectedPatient ? (
            <>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{ width: 56, height: 56, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', fontSize: 18, fontWeight: 700, color: COLORS.white }}>
                  <span>{(selectedPatient.full_name || selectedPatient.name || 'P').split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}</span>
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>{selectedPatient.full_name || selectedPatient.name}</h3>
                <p style={{ fontSize: 12, fontWeight: 400, color: COLORS.muted, margin: '6px 0 0' }}>MRN {(selectedPatient.mrn || selectedPatient.patient_id || '—')} • DOB: {(selectedPatient.date_of_birth ? new Date(selectedPatient.date_of_birth).toLocaleDateString() : '—')}</p>
              </div>

              {[
                { label: 'Primary Diagnosis', value: selectedPatient.primary_diagnosis || selectedPatient.dx || '—' },
                { label: 'Attending Physician', value: selectedPatient.attending_physician || '—' },
                { label: 'Admission Date', value: selectedPatient.admission_at ? new Date(selectedPatient.admission_at).toLocaleDateString() : '—' },
                { label: 'Current Care Level', value: formatCareLevel(selectedPatient.census_bucket || selectedPatient.level) },
                { label: 'POC Period', value: selectedPatient.last_visit_at ? new Date(selectedPatient.last_visit_at).toLocaleDateString() : '—' },
              ].map((f, i) => (
                <div key={i} style={{ marginBottom: 12 }}>
                  <p style={{ fontSize: 11, fontWeight: 400, color: COLORS.dim, margin: '0 0 2px' }}>{f.label}</p>
                  <p style={{ fontSize: 13, fontWeight: 400, color: COLORS.textPrimary, margin: 0 }}>{f.value}</p>
                </div>
              ))}
            </>
          ) : null}

          <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.dim, margin: '20px 0 10px' }}>QUICK CHART ACTIONS</p>
          {QUICK_LINKS.map((label, i) => (
            <div
              key={label}
              onClick={() => {
                if (selectedPatient && label === 'View Full Chart') {
                  handleOpenChart(selectedPatient);
                }
              }}
              style={{ padding: '8px 12px', background: COLORS.bg, borderRadius: 6, marginBottom: 6, fontSize: 13, fontWeight: 600, color: COLORS.white, cursor: selectedPatient ? 'pointer' : 'default', border: `1px solid ${COLORS.border}` }}
            >
              {label}
            </div>
          ))}

          <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.dim, margin: '20px 0 10px' }}>RECENT ACTIVITY</p>
          {ACTIVITY.map((a, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary, margin: 0 }}>{a.title}</p>
              <p style={{ fontSize: 11, fontWeight: 400, color: COLORS.dim, margin: '2px 0 0' }}>{a.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
