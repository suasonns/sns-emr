import React, { useState } from 'react';
import { useThemeMode } from '../theme/theme';
import { getChartColors } from '../theme/chartColors';
import { defaultPatient } from './ConsentNotifications';

const cardStyle = (colors) => ({
  backgroundColor: colors.card,
  borderRadius: 8,
  padding: 24,
  borderLeft: `4px solid ${colors.teal}`,
  marginBottom: 24,
});

const Badge = ({ children, variant = 'green', colors }) => {
  const map = {
    green: { bg: colors.greenBg, color: colors.green },
    red: { bg: colors.redBg, color: colors.red },
    amber: { bg: colors.amberBg, color: colors.amber },
    teal: { bg: colors.tealBg, color: colors.teal },
  };
  const v = map[variant] || map.teal;
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 4,
      fontSize: 11, fontWeight: 600, backgroundColor: v.bg, color: v.color,
    }}>{children}</span>
  );
};

const PatientBanner = ({ patient, colors }) => (
  <div style={{ backgroundColor: colors.card, borderRadius: 8, padding: '16px 24px', marginBottom: 24 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ color: colors.white, fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
          {patient.lastName}, {patient.firstName}
        </div>
        <div style={{ color: colors.label, fontSize: 13 }}>
          MRN: {patient.mrn} &nbsp;|&nbsp; DOB: {patient.dob} ({patient.age}y) &nbsp;|&nbsp; Sex: {patient.sex} &nbsp;|&nbsp; Payer: {patient.payer}
        </div>
      </div>
      <Badge variant="green" colors={colors}>{patient.status}</Badge>
    </div>
  </div>
);

const disciplines = [
  {
    key: 'md', label: 'MD / NP / DO', staff: [
      { name: 'Dr. Angela Reyes', role: 'Attending Physician', primary: true, assigned: true, caseload: 18, phone: '(555) 201-3344', email: 'a.reyes@snshospice.org' },
    ]
  },
  {
    key: 'cm', label: 'Case Manager (CM)', staff: [
      { name: 'Marcus Whitfield, RN', role: 'RN Case Manager', primary: true, assigned: true, caseload: 12, phone: '(555) 201-3401', email: 'm.whitfield@snshospice.org' },
    ]
  },
  {
    key: 'rn', label: 'RN', staff: [
      { name: 'Marcus Whitfield, RN', role: 'Primary RN', primary: true, assigned: true, caseload: 12, phone: '(555) 201-3401', email: 'm.whitfield@snshospice.org' },
      { name: 'Diane Coleman, RN', role: 'Backup RN', primary: false, assigned: true, caseload: 15, phone: '(555) 201-3410', email: 'd.coleman@snshospice.org' },
    ]
  },
  {
    key: 'lvn', label: 'LVN', staff: [
      { name: 'Priya Nandakumar, LVN', role: 'LVN', primary: true, assigned: true, caseload: 20, phone: '(555) 201-3422', email: 'p.nandakumar@snshospice.org' },
    ]
  },
  {
    key: 'ha', label: 'Home Health Aide (HA)', staff: [
      { name: 'Renee Ortiz, HHA', role: 'Home Health Aide', primary: true, assigned: true, caseload: 9, phone: '(555) 201-3455', email: 'r.ortiz@snshospice.org' },
    ]
  },
  {
    key: 'msw', label: 'MSW / BSW / LCSW', staff: [
      { name: 'Jonathan Blake, LCSW', role: 'Medical Social Worker', primary: true, assigned: true, caseload: 24, phone: '(555) 201-3480', email: 'j.blake@snshospice.org' },
    ]
  },
  {
    key: 'sc', label: 'Spiritual Care (SC)', staff: [
      { name: 'Rev. Thomas Grady', role: 'Chaplain', primary: true, assigned: true, caseload: 30, phone: '(555) 201-3502', email: 't.grady@snshospice.org' },
    ]
  },
  {
    key: 'bc', label: 'Bereavement Counselor (BC)', staff: [
      { name: 'Unassigned', role: 'Bereavement Counselor', primary: false, assigned: false, caseload: null, phone: null, email: null },
    ]
  },
  {
    key: 'vol', label: 'Volunteer (VOL)', staff: [
      { name: 'Unassigned', role: 'Volunteer', primary: false, assigned: false, caseload: null, phone: null, email: null },
    ]
  },
  {
    key: 'pt', label: 'PT / ST / OT / MT / NU / MFT', staff: [
      { name: 'Unassigned', role: 'Therapy Services', primary: false, assigned: false, caseload: null, phone: null, email: null },
    ]
  },
];

// Candidate roster available for reassignment, grouped by discipline.
const staffRoster = {
  md: [
    { name: 'Dr. Angela Reyes', role: 'Attending Physician', caseload: 18, phone: '(555) 201-3344', email: 'a.reyes@snshospice.org' },
    { name: 'Dr. Samuel Okafor', role: 'Attending Physician', caseload: 14, phone: '(555) 201-3350', email: 's.okafor@snshospice.org' },
  ],
  cm: [
    { name: 'Marcus Whitfield, RN', role: 'RN Case Manager', caseload: 12, phone: '(555) 201-3401', email: 'm.whitfield@snshospice.org' },
    { name: 'Diane Coleman, RN', role: 'RN Case Manager', caseload: 15, phone: '(555) 201-3410', email: 'd.coleman@snshospice.org' },
  ],
  rn: [
    { name: 'Marcus Whitfield, RN', role: 'RN', caseload: 12, phone: '(555) 201-3401', email: 'm.whitfield@snshospice.org' },
    { name: 'Diane Coleman, RN', role: 'RN', caseload: 15, phone: '(555) 201-3410', email: 'd.coleman@snshospice.org' },
    { name: 'Felicia Ann Marsh, RN', role: 'RN', caseload: 11, phone: '(555) 201-3417', email: 'f.marsh@snshospice.org' },
  ],
  lvn: [
    { name: 'Priya Nandakumar, LVN', role: 'LVN', caseload: 20, phone: '(555) 201-3422', email: 'p.nandakumar@snshospice.org' },
    { name: 'Carlos Medina, LVN', role: 'LVN', caseload: 17, phone: '(555) 201-3428', email: 'c.medina@snshospice.org' },
  ],
  ha: [
    { name: 'Renee Ortiz, HHA', role: 'Home Health Aide', caseload: 9, phone: '(555) 201-3455', email: 'r.ortiz@snshospice.org' },
    { name: 'Wanda Price, HHA', role: 'Home Health Aide', caseload: 13, phone: '(555) 201-3461', email: 'w.price@snshospice.org' },
  ],
  msw: [
    { name: 'Jonathan Blake, LCSW', role: 'Medical Social Worker', caseload: 24, phone: '(555) 201-3480', email: 'j.blake@snshospice.org' },
    { name: 'Nina Alvarez, MSW', role: 'Medical Social Worker', caseload: 19, phone: '(555) 201-3487', email: 'n.alvarez@snshospice.org' },
  ],
  sc: [
    { name: 'Rev. Thomas Grady', role: 'Chaplain', caseload: 30, phone: '(555) 201-3502', email: 't.grady@snshospice.org' },
    { name: 'Rev. Linda Osei', role: 'Chaplain', caseload: 22, phone: '(555) 201-3509', email: 'l.osei@snshospice.org' },
  ],
  bc: [
    { name: 'Karen Byrd, LCSW', role: 'Bereavement Counselor', caseload: 27, phone: '(555) 201-3520', email: 'k.byrd@snshospice.org' },
  ],
  vol: [
    { name: 'Michael Turner', role: 'Volunteer', caseload: 8, phone: '(555) 201-3540', email: 'm.turner@volunteers.org' },
  ],
  pt: [
    { name: 'Alicia Fenwick, PT', role: 'Physical Therapist', caseload: 10, phone: '(555) 201-3560', email: 'a.fenwick@snshospice.org' },
  ],
};

const StaffCard = ({ member, colors, onReplace, roster }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  const alternates = (roster || []).filter((r) => r.name !== member.name);

  return (
    <div style={{
      backgroundColor: colors.bg, borderRadius: 8,
      border: `1px solid ${colors.border}`, marginBottom: 8, overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 18,
            backgroundColor: member.assigned ? colors.tealBg : colors.border,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: member.assigned ? colors.teal : colors.label, fontWeight: 700, fontSize: 13,
          }}>
            {member.assigned ? member.name.split(' ').map((p) => p[0]).slice(0, 2).join('') : '—'}
          </div>
          <div>
            <div style={{ color: colors.white, fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              {member.name}
              {member.primary && <Badge variant="teal" colors={colors}>Primary</Badge>}
            </div>
            <div style={{ color: colors.label, fontSize: 12 }}>{member.role}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          {member.assigned ? (
            <>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase' }}>Caseload</div>
                <div style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>{member.caseload}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase' }}>Phone</div>
                <div style={{ color: colors.white, fontSize: 13 }}>{member.phone}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: colors.label, fontSize: 10, textTransform: 'uppercase' }}>Email</div>
                <div style={{ color: colors.teal, fontSize: 12 }}>{member.email}</div>
              </div>
              <Badge variant="green" colors={colors}>Assigned</Badge>
            </>
          ) : (
            <Badge variant="amber" colors={colors}>Not Assigned</Badge>
          )}
          {onReplace && (
            <button
              onClick={() => setPickerOpen((v) => !v)}
              style={{
                padding: '6px 14px', backgroundColor: 'transparent', color: colors.teal,
                border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 12,
                fontWeight: 600, cursor: 'pointer', fontFamily: "'Inter', sans-serif", whiteSpace: 'nowrap',
              }}
            >
              {member.assigned ? 'Replace' : 'Assign'}
            </button>
          )}
        </div>
      </div>

      {pickerOpen && (
        <div style={{ padding: '10px 16px 14px', borderTop: `1px solid ${colors.border}` }}>
          <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase', marginBottom: 8 }}>
            Select replacement staff
          </div>
          {alternates.length === 0 && (
            <div style={{ color: colors.label, fontSize: 12 }}>No other staff available for this discipline.</div>
          )}
          {alternates.map((candidate) => (
            <div
              key={candidate.name}
              onClick={() => { onReplace(candidate); setPickerOpen(false); }}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', borderRadius: 6, cursor: 'pointer', marginBottom: 4,
                backgroundColor: colors.card,
              }}
            >
              <div>
                <span style={{ color: colors.white, fontSize: 13, fontWeight: 600 }}>{candidate.name}</span>
                <span style={{ color: colors.label, fontSize: 12, marginLeft: 8 }}>Caseload: {candidate.caseload}</span>
              </div>
              <span style={{ color: colors.teal, fontSize: 12, fontWeight: 600 }}>Select</span>
            </div>
          ))}
          {member.assigned && (
            <div
              onClick={() => { onReplace(null); setPickerOpen(false); }}
              style={{ color: colors.red, fontSize: 12, fontWeight: 600, cursor: 'pointer', marginTop: 4 }}
            >
              Unassign this staff member
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const DisciplineSection = ({ discipline, colors, expanded, onToggle, onReplaceStaff }) => (
  <div style={{ marginBottom: 16, border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
    <div
      onClick={onToggle}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 20px', backgroundColor: colors.card, cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: colors.white, fontSize: 14, fontWeight: 700 }}>{discipline.label}</span>
        <Badge variant={discipline.staff.some((s) => s.assigned) ? 'green' : 'amber'} colors={colors}>
          {discipline.staff.filter((s) => s.assigned).length}/{discipline.staff.length} Assigned
        </Badge>
      </div>
      <span style={{ color: colors.label, fontSize: 14 }}>{expanded ? '▾' : '▸'}</span>
    </div>
    {expanded && (
      <div style={{ padding: '12px 20px 16px', backgroundColor: colors.bg }}>
        {discipline.staff.map((member, i) => (
          <StaffCard
            key={i}
            member={member}
            colors={colors}
            roster={staffRoster[discipline.key]}
            onReplace={(candidate) => onReplaceStaff(discipline.key, i, candidate)}
          />
        ))}
      </div>
    )}
  </div>
);

const StaffAssignment = ({ patient = defaultPatient }) => {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const [filter, setFilter] = useState('all');
  const [expandedKeys, setExpandedKeys] = useState(() => new Set(['md', 'cm', 'rn']));
  const [disciplineState, setDisciplineState] = useState(disciplines);

  const toggleExpanded = (key) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const handleReplaceStaff = (disciplineKey, staffIndex, candidate) => {
    setDisciplineState((prev) => prev.map((d) => {
      if (d.key !== disciplineKey) return d;
      const staff = [...d.staff];
      const current = staff[staffIndex];
      staff[staffIndex] = candidate
        ? { ...candidate, primary: current.primary, assigned: true }
        : { name: 'Unassigned', role: current.role, primary: false, assigned: false, caseload: null, phone: null, email: null };
      return { ...d, staff };
    }));
  };

  const filteredDisciplines = filter === 'all'
    ? disciplineState
    : filter === 'assigned'
      ? disciplineState.filter((d) => d.staff.some((s) => s.assigned))
      : disciplineState.filter((d) => d.staff.some((s) => !s.assigned));

  const selectStyle = {
    backgroundColor: colors.card, border: `1px solid ${colors.border}`,
    borderRadius: 6, padding: '8px 12px', color: colors.white,
    fontSize: 13, fontFamily: "'Inter', sans-serif", outline: 'none',
  };

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ color: colors.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{patient.firstName} {patient.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>Intake & Admission</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: colors.white }}>Staff Assignment</span>
      </div>

      <PatientBanner patient={patient} colors={colors} />

      <div style={cardStyle(colors)}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Staff Assignment</div>
            <div style={{ color: colors.label, fontSize: 13 }}>
              Interdisciplinary team assignment by discipline for this patient's care.
            </div>
          </div>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={selectStyle}>
            <option value="all">All Disciplines</option>
            <option value="assigned">Assigned Only</option>
            <option value="unassigned">Unassigned Only</option>
          </select>
        </div>

        {filteredDisciplines.map((d) => (
          <DisciplineSection
            key={d.key}
            discipline={d}
            colors={colors}
            expanded={expandedKeys.has(d.key)}
            onToggle={() => toggleExpanded(d.key)}
            onReplaceStaff={handleReplaceStaff}
          />
        ))}
      </div>
    </div>
  );
};

export default StaffAssignment;
