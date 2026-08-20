import React, { useMemo, useState } from 'react';
import { COLORS, S } from '../design';

function formatDate(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return value;
  }
}

function normalizeStatus(value) {
  const normalized = String(value ?? '').trim().toUpperCase();
  if (!normalized) return 'ACTIVE';
  return normalized;
}

export default function Admissions({ census, loading }) {
  const patients = useMemo(() => (Array.isArray(census?.patients) ? census.patients : []), [census]);
  const [expandedGroups, setExpandedGroups] = useState({});
  const maxVisiblePerGroup = 3;

  const metrics = useMemo(() => {
    const active = patients.filter((patient) => !['DISCHARGED', 'DECEASED', 'REVOKED'].includes(normalizeStatus(patient.patient_status || patient.admission_status)));
    return [
      { label: 'Active patients', value: String(active.length) },
      { label: 'In census', value: String(patients.length) },
      { label: 'Admitted this month', value: String(patients.filter((patient) => patient.admission_at).length) },
      { label: 'Current focus', value: active[0]?.full_name ? 'Live census' : 'No patients' },
    ];
  }, [patients]);

  const columns = useMemo(() => {
    const safePatients = patients.slice(0, 12);
    const groups = [
      { title: 'Active census', cards: safePatients.filter((patient) => !['DISCHARGED', 'DECEASED', 'REVOKED'].includes(normalizeStatus(patient.patient_status || patient.admission_status))) },
      { title: 'Recent admissions', cards: safePatients.filter((patient) => patient.admission_at) },
      { title: 'Pending review', cards: safePatients.filter((patient) => !patient.last_visit_at) },
    ].map((group) => ({ ...group, cards: group.cards }));

    return groups;
  }, [patients]);

  const recentActivity = useMemo(() => {
    return patients.slice(0, 6).map((patient) => ({
      date: formatDate(patient.admission_at || patient.last_visit_at),
      name: patient.full_name || 'Unknown patient',
      source: patient.payer_name || '—',
      dx: patient.primary_diagnosis || '—',
      evaluator: patient.attending_physician || 'Unassigned',
      pipeline: patient.last_visit_at ? 'Live' : 'Awaiting visit',
      status: patient.census_bucket || 'ACTIVE',
      statusColor: patient.census_bucket === 'Discharged' ? COLORS.green : COLORS.teal,
    }));
  }, [patients]);

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Assessment</h1>
          <p style={S.pageSubtitle}>RN, psychosocial, and spiritual discipline assessments for current patient census</p>
        </div>
        <button style={S.btn(COLORS.teal)} disabled={loading}>Refresh</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {metrics.map((stat, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 12, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{stat.label}</p>
            <p style={S.statValue}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
        {columns.map((col, ci) => {
          const expanded = !!expandedGroups[ci];
          const visibleCards = expanded ? col.cards : col.cards.slice(0, maxVisiblePerGroup);
          const remaining = Math.max(col.cards.length - visibleCards.length, 0);
          const isWide = col.title === 'Active census';

          const tableColumns = isWide
            ? '1.4fr 1fr 1.2fr 1fr 0.9fr'
            : '1.3fr 0.9fr 0.9fr 0.7fr';

          return (
            <div key={ci} style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 16, minHeight: 220 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.white }}>{col.title}</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted, background: 'rgba(148, 163, 184, 0.12)', borderRadius: 999, padding: '4px 8px' }}>{col.cards.length}</div>
              </div>

              {col.cards.length === 0 ? (
                <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 12, color: COLORS.muted }}>
                  No live patients in this list.
                </div>
              ) : (
                <div style={{ border: `1px solid ${COLORS.border}`, borderRadius: 10, overflow: 'hidden', background: COLORS.bg }}>
                  <div style={{ display: 'grid', gridTemplateColumns: tableColumns, fontSize: 10, fontWeight: 700, color: COLORS.muted, textTransform: 'uppercase', letterSpacing: '.08em', background: 'rgba(148, 163, 184, 0.08)' }}>
                    <div style={{ padding: '8px 10px' }}>{isWide ? 'Patient' : 'Name'}</div>
                    <div style={{ padding: '8px 10px' }}>{isWide ? 'MRN' : 'MRN'}</div>
                    <div style={{ padding: '8px 10px' }}>{isWide ? 'Diagnosis' : 'Dx'}</div>
                    {isWide ? <div style={{ padding: '8px 10px' }}>MD</div> : <div style={{ padding: '8px 10px' }}>Date</div>}
                    {isWide ? <div style={{ padding: '8px 10px', textAlign: 'right' }}>Status</div> : <div style={{ padding: '8px 10px', textAlign: 'right' }}>Status</div>}
                  </div>

                  {visibleCards.map((patient, i) => (
                    <div key={`${patient.patient_id || i}`} style={{ display: 'grid', gridTemplateColumns: tableColumns, borderTop: `1px solid ${COLORS.border}`, alignItems: 'center', fontSize: 11, color: COLORS.white }}>
                      <div style={{ padding: '10px 10px', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{patient.full_name || 'Unknown patient'}</div>
                      <div style={{ padding: '10px 10px', color: COLORS.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{patient.mrn || '—'}</div>
                      <div style={{ padding: '10px 10px', color: COLORS.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{patient.primary_diagnosis || '—'}</div>
                      {isWide ? (
                        <div style={{ padding: '10px 10px', color: COLORS.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{patient.attending_physician || 'Unassigned'}</div>
                      ) : (
                        <div style={{ padding: '10px 10px', color: COLORS.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{formatDate(patient.admission_at || patient.last_visit_at)}</div>
                      )}
                      <div style={{ padding: '10px 10px', textAlign: 'right' }}>
                        <span style={{ fontSize: 9, fontWeight: 800, color: patient.census_bucket === 'Discharged' ? COLORS.green : COLORS.teal }}>{normalizeStatus(patient.patient_status || patient.admission_status || patient.census_bucket)}</span>
                      </div>
                    </div>
                  ))}

                  {remaining > 0 && (
                    <div style={{ padding: 8 }}>
                      <button
                        type="button"
                        onClick={() => setExpandedGroups((current) => ({ ...current, [ci]: !current[ci] }))}
                        style={{
                          width: '100%',
                          border: `1px solid ${COLORS.border}`,
                          background: 'transparent',
                          color: COLORS.teal,
                          borderRadius: 8,
                          padding: '8px 10px',
                          fontSize: 11,
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        {expanded ? 'Show fewer' : `View all ${col.cards.length}`}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={S.card}>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Recent Assessment Activity</h3>
        {recentActivity.length === 0 ? (
          <div style={{ color: COLORS.muted }}>No live patient activity available.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['DATE', 'PATIENT NAME', 'SOURCE', 'DIAGNOSIS', 'PRIMARY MD', 'IN PIPELINE', 'STATUS'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recentActivity.map((row, i) => (
                <tr key={`${row.name}-${i}`}>
                  <td style={S.tableCell}>{row.date}</td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.textPrimary }}>{row.name}</td>
                  <td style={S.tableCell}>{row.source}</td>
                  <td style={S.tableCell}>{row.dx}</td>
                  <td style={S.tableCell}>{row.evaluator}</td>
                  <td style={S.tableCell}>{row.pipeline}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: row.statusColor }}>{row.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
