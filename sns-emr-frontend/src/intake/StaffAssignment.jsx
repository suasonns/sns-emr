import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useThemeMode } from '../theme/theme';
import { getChartColors } from '../theme/chartColors';
import { defaultPatient } from './ConsentNotifications';
import { getActivePatientId } from '../utils/activePatient';
import { getCurrentUser } from '../api/session';
import { listStaff } from '../api/staff';
import {
  assignPatientStaff,
  deactivatePatientAssignment,
  listPatientAssignments,
} from '../api/patientAssignments';
import { formatRoleLabel } from '../utils/roleLabel';

const CLINICAL_ADMIN_ROLES = new Set(['ADMINISTRATOR', 'DPCS', 'DPCS_ADMINISTRATOR']);

const DISCIPLINE_GROUPS = [
  { key: 'providers', label: 'MD / NP / DO', disciplines: ['MEDICAL_DIRECTOR', 'ATTENDING_PHYSICIAN', 'MD', 'DO', 'NP', 'PA'] },
  { key: 'case-manager', label: 'Case Manager (RN or LVN)', disciplines: ['CASE_MANAGER'] },
  { key: 'rn', label: 'RN', disciplines: ['RN'] },
  { key: 'msw', label: 'MSW', disciplines: ['MSW', 'SW', 'BSW', 'LCSW'] },
  { key: 'sc', label: 'Spiritual Care (SC)', disciplines: ['SC', 'CHAPLAIN'] },
  { key: 'ha', label: 'HHA / CHHA', disciplines: ['CHHA', 'AIDE'] },
  { key: 'lvn', label: 'LVN / LPN', disciplines: ['LVN', 'LPN'] },
];

const DISCIPLINE_LABELS = {
  MEDICAL_DIRECTOR: 'Medical Director',
  ATTENDING_PHYSICIAN: 'Attending Physician',
  MD: 'MD',
  DO: 'DO',
  NP: 'NP',
  PA: 'PA',
  CASE_MANAGER: 'Case Manager',
  RN: 'RN',
  MSW: 'MSW',
  SW: 'Social Worker',
  BSW: 'BSW',
  LCSW: 'LCSW',
  SC: 'Spiritual Counselor',
  CHAPLAIN: 'Chaplain',
  CHHA: 'CHHA / HHA',
  AIDE: 'Aide',
  LVN: 'LVN',
  LPN: 'LPN',
};

const ROLE_ALIASES = {
  ADMIN: 'ADMINISTRATOR',
  CLINICAL_ADMIN: 'ADMINISTRATOR',
  DPCS_ADMIN: 'DPCS',
  DPCS_DESIGNEE: 'DPCS',
  SUPER_ADMIN: 'ADMINISTRATOR',
  SUPERVISOR: 'CLINICAL_SUPERVISOR',
  MSW: 'SW',
  LCSW: 'SW',
  LPN: 'LVN',
  MD: 'ATTENDING_PHYSICIAN',
};

const PROFILE_DISCIPLINE_ALIASES = {
  ADMN: null,
  HA: 'CHHA',
  HHA: 'CHHA',
  VOL: null,
};

const ASSIGNABLE_DISCIPLINES = new Set(
  DISCIPLINE_GROUPS.flatMap((group) => group.disciplines),
);

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
    muted: { bg: colors.border, color: colors.label },
  };
  const tone = map[variant] || map.teal;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 600,
      backgroundColor: tone.bg,
      color: tone.color,
    }}
    >
      {children}
    </span>
  );
};

const PatientBanner = ({ patient, colors }) => (
  <div style={{ backgroundColor: colors.card, borderRadius: 8, padding: '16px 24px', marginBottom: 24 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
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

function cleanToken(value) {
  return String(value || '').trim().toUpperCase().replace(/-/g, '_');
}

function normalizeRoleToken(value) {
  const token = cleanToken(value);
  return ROLE_ALIASES[token] || token;
}

function getAssignableDisciplinesForStaff(staff) {
  const tokens = new Set([cleanToken(staff?.role), normalizeRoleToken(staff?.role)]);
  const profileToken = PROFILE_DISCIPLINE_ALIASES[cleanToken(staff?.discipline)] ?? cleanToken(staff?.discipline);
  if (profileToken) tokens.add(profileToken);

  const assignable = new Set();
  tokens.forEach((token) => {
    if (token && ASSIGNABLE_DISCIPLINES.has(token)) {
      assignable.add(token);
    }
  });

  switch (cleanToken(staff?.role)) {
    case 'CHHA':
      assignable.add('CHHA');
      break;
    case 'SW':
      assignable.add('SW');
      break;
    case 'SC':
      assignable.add('SC');
      break;
    case 'RN':
      assignable.add('RN');
      break;
    case 'LVN':
      assignable.add('LVN');
      break;
    case 'LPN':
      assignable.add('LPN');
      break;
    default:
      break;
  }

  // Case Manager is not its own clinical credential — it's an assignable
  // administrative role the agency designates to one of its RN or LVN/LPN
  // staff. Anyone whose real discipline is RN or LVN/LPN is eligible to be
  // picked as Case Manager; the agency decides who for a given patient.
  if (assignable.has('RN') || assignable.has('LVN') || assignable.has('LPN')) {
    assignable.add('CASE_MANAGER');
  }

  return assignable;
}

// Prefer the staff member's real job title / clinical discipline for display
// (e.g. "CEO" / "LVN") over their internal system access role (e.g.
// "DPCS_ADMINISTRATOR"), which controls login permissions but is not a job
// title or clinical credential and should never be shown to represent one.
function staffDisplayLabel(staff) {
  const jobTitle = staff?.job_title && String(staff.job_title).trim();
  const discipline = staff?.discipline && String(staff.discipline).trim();
  if (jobTitle && discipline) return `${discipline} • ${jobTitle}`;
  if (discipline) return discipline;
  if (jobTitle) return jobTitle;
  return formatRoleLabel(staff?.role);
}

function assignmentStaffDisplayLabel(assignment) {
  const jobTitle = assignment?.staff_job_title && String(assignment.staff_job_title).trim();
  const discipline = assignment?.staff_discipline && String(assignment.staff_discipline).trim();
  if (jobTitle && discipline) return `${discipline} • ${jobTitle}`;
  if (discipline) return discipline;
  if (jobTitle) return jobTitle;
  return assignment?.staff_role ? formatRoleLabel(assignment.staff_role) : '';
}

function formatDateTime(value) {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function emptyDraft(group) {
  return {
    discipline: group.disciplines[0],
    userId: '',
    serviceArea: '',
    note: '',
  };
}

const AssignmentRow = ({
  assignment,
  colors,
  canManageAssignments,
  onDeactivate,
  onPrepareReassign,
  deactivatingAssignmentId,
}) => {
  const isHistorical = !assignment.active;
  const staffLabel = assignment.staff_name || assignment.staff_full_name || 'Unknown staff';
  return (
    <div style={{
      backgroundColor: colors.bg,
      borderRadius: 8,
      border: `1px solid ${colors.border}`,
      marginBottom: 8,
      overflow: 'hidden',
      opacity: isHistorical ? 0.78 : 1,
    }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', padding: '12px 16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'grid', gap: 6, minWidth: 260 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ color: colors.white, fontSize: 14, fontWeight: 700 }}>{staffLabel}</span>
            <Badge variant={assignment.active ? 'green' : 'amber'} colors={colors}>{assignment.status}</Badge>
            {assignment.is_primary ? <Badge variant="teal" colors={colors}>Primary</Badge> : null}
          </div>
          <div style={{ color: colors.label, fontSize: 12 }}>
            {DISCIPLINE_LABELS[assignment.discipline] || assignment.discipline}
            {assignmentStaffDisplayLabel(assignment) ? ` • ${assignmentStaffDisplayLabel(assignment)}` : ''}
          </div>
          <div style={{ color: colors.label, fontSize: 12 }}>
            Assigned {formatDateTime(assignment.assigned_at)}
            {assignment.assigned_by_name ? ` by ${assignment.assigned_by_name}` : ''}
          </div>
          {assignment.service_area ? (
            <div style={{ color: colors.label, fontSize: 12 }}>Service area: {assignment.service_area}</div>
          ) : null}
          {assignment.note ? (
            <div style={{ color: colors.label, fontSize: 12, lineHeight: 1.5 }}>Note: {assignment.note}</div>
          ) : null}
        </div>
        <div style={{ display: 'grid', gap: 8, justifyItems: 'end', minWidth: 200 }}>
          <div style={{ color: colors.teal, fontSize: 12 }}>{assignment.staff_full_name || assignment.staff_name || ''}</div>
          {canManageAssignments && assignment.active ? (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => onPrepareReassign(assignment.discipline)}
                style={{
                  padding: '6px 14px',
                  backgroundColor: 'transparent',
                  color: colors.teal,
                  border: `1px solid ${colors.teal}`,
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: "'Inter', sans-serif",
                }}
              >
                Reassign
              </button>
              <button
                type="button"
                disabled={deactivatingAssignmentId === assignment.id}
                onClick={() => onDeactivate(assignment)}
                style={{
                  padding: '6px 14px',
                  backgroundColor: 'transparent',
                  color: colors.red,
                  border: `1px solid ${colors.red}`,
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: deactivatingAssignmentId === assignment.id ? 'not-allowed' : 'pointer',
                  opacity: deactivatingAssignmentId === assignment.id ? 0.6 : 1,
                  fontFamily: "'Inter', sans-serif",
                }}
              >
                {deactivatingAssignmentId === assignment.id ? 'Deactivating…' : 'Deactivate'}
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

const DisciplineSection = ({
  group,
  rows,
  colors,
  expanded,
  onToggle,
  canManageAssignments,
  draft,
  onDraftChange,
  onAssign,
  onDeactivate,
  onPrepareReassign,
  deactivatingAssignmentId,
  savingGroupKey,
  roster,
}) => {
  const activeRows = rows.filter((row) => row.active);
  const historicalRows = rows.filter((row) => !row.active);
  const selectedDiscipline = draft.discipline || group.disciplines[0];
  const matchingStaff = roster
    .filter((staff) => getAssignableDisciplinesForStaff(staff).has(selectedDiscipline))
    .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));
  const existingAssignment = activeRows.find((row) => row.discipline === selectedDiscipline);
  const saveBusy = savingGroupKey === group.key;

  const inputStyle = {
    backgroundColor: colors.card,
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    padding: '8px 12px',
    color: colors.white,
    fontSize: 13,
    fontFamily: "'Inter', sans-serif",
    outline: 'none',
    width: '100%',
  };

  return (
    <div style={{ marginBottom: 16, border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
      <div
        onClick={onToggle}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', backgroundColor: colors.card, cursor: 'pointer' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ color: colors.white, fontSize: 14, fontWeight: 700 }}>{group.label}</span>
          <Badge variant={activeRows.length ? 'green' : 'amber'} colors={colors}>
            {activeRows.length ? `${activeRows.length} Active` : 'Unassigned'}
          </Badge>
          {historicalRows.length ? <Badge variant="muted" colors={colors}>{historicalRows.length} Historical</Badge> : null}
        </div>
        <span style={{ color: colors.label, fontSize: 14 }}>{expanded ? '▾' : '▸'}</span>
      </div>

      {expanded ? (
        <div style={{ padding: '12px 20px 16px', backgroundColor: colors.bg }}>
          {activeRows.length ? activeRows.map((assignment) => (
            <AssignmentRow
              key={assignment.id}
              assignment={assignment}
              colors={colors}
              canManageAssignments={canManageAssignments}
              onDeactivate={onDeactivate}
              onPrepareReassign={onPrepareReassign}
              deactivatingAssignmentId={deactivatingAssignmentId}
            />
          )) : (
            <div style={{ color: colors.label, fontSize: 12, marginBottom: canManageAssignments ? 12 : 0 }}>
              No active assignment documented for this discipline group.
            </div>
          )}

          {historicalRows.length ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ color: colors.label, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
                Historical assignments
              </div>
              {historicalRows.map((assignment) => (
                <AssignmentRow
                  key={assignment.id}
                  assignment={assignment}
                  colors={colors}
                  canManageAssignments={false}
                  onDeactivate={onDeactivate}
                  onPrepareReassign={onPrepareReassign}
                  deactivatingAssignmentId={deactivatingAssignmentId}
                />
              ))}
            </div>
          ) : null}

          {canManageAssignments ? (
            <div style={{ marginTop: 12, backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, padding: 16 }}>
              <div style={{ color: colors.white, fontSize: 13, fontWeight: 700, marginBottom: 12 }}>
                {existingAssignment ? 'Reassign staff' : 'Assign staff'}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                <label style={{ color: colors.label, fontSize: 12 }}>
                  Discipline
                  <select
                    value={selectedDiscipline}
                    onChange={(event) => {
                      const nextDiscipline = event.target.value;
                      const nextStaffStillMatches = roster.some(
                        (staff) => staff.id === draft.userId && getAssignableDisciplinesForStaff(staff).has(nextDiscipline),
                      );
                      onDraftChange(group.key, {
                        discipline: nextDiscipline,
                        userId: nextStaffStillMatches ? draft.userId : '',
                      });
                    }}
                    style={{ ...inputStyle, marginTop: 6 }}
                  >
                    {group.disciplines.map((discipline) => (
                      <option key={discipline} value={discipline}>
                        {DISCIPLINE_LABELS[discipline] || discipline}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={{ color: colors.label, fontSize: 12 }}>
                  Staff member
                  <select
                    value={draft.userId}
                    onChange={(event) => onDraftChange(group.key, { userId: event.target.value })}
                    style={{ ...inputStyle, marginTop: 6 }}
                  >
                    <option value="">— Select staff —</option>
                    {matchingStaff.map((staff) => (
                      <option key={staff.id} value={staff.id}>
                        {staff.full_name} • {staffDisplayLabel(staff)}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={{ color: colors.label, fontSize: 12 }}>
                  Service area
                  <input
                    value={draft.serviceArea}
                    onChange={(event) => onDraftChange(group.key, { serviceArea: event.target.value })}
                    style={{ ...inputStyle, marginTop: 6 }}
                    placeholder="Optional"
                  />
                </label>
                <label style={{ color: colors.label, fontSize: 12 }}>
                  Note
                  <input
                    value={draft.note}
                    onChange={(event) => onDraftChange(group.key, { note: event.target.value })}
                    style={{ ...inputStyle, marginTop: 6 }}
                    placeholder="Optional"
                  />
                </label>
              </div>
              {matchingStaff.length === 0 ? (
                <div style={{ color: colors.label, fontSize: 12, marginTop: 10 }}>
                  No active staff roster entries match {DISCIPLINE_LABELS[selectedDiscipline] || selectedDiscipline}.
                </div>
              ) : null}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
                <button
                  type="button"
                  disabled={!draft.userId || saveBusy}
                  onClick={() => onAssign(group.key)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: colors.teal,
                    color: colors.bg,
                    border: 'none',
                    borderRadius: 6,
                    fontSize: 12.5,
                    fontWeight: 700,
                    cursor: !draft.userId || saveBusy ? 'not-allowed' : 'pointer',
                    opacity: !draft.userId || saveBusy ? 0.6 : 1,
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  {saveBusy ? 'Saving…' : existingAssignment ? 'Reassign staff' : 'Assign staff'}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
};

const StaffAssignment = ({ patient = defaultPatient }) => {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const patientId = getActivePatientId() || '';
  const currentUser = getCurrentUser();
  const canManageAssignments = CLINICAL_ADMIN_ROLES.has(normalizeRoleToken(currentUser?.role));

  const [filter, setFilter] = useState('all');
  const [showHistory, setShowHistory] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState(() => new Set(['providers', 'case-manager', 'rn', 'ha', 'lvn']));
  const [assignments, setAssignments] = useState([]);
  const [roster, setRoster] = useState([]);
  const [drafts, setDrafts] = useState(() => (
    DISCIPLINE_GROUPS.reduce((acc, group) => ({ ...acc, [group.key]: emptyDraft(group) }), {})
  ));
  const [loading, setLoading] = useState(true);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [savingGroupKey, setSavingGroupKey] = useState('');
  const [deactivatingAssignmentId, setDeactivatingAssignmentId] = useState('');

  const loadAssignments = useCallback(() => {
    if (!patientId) {
      setAssignments([]);
      setLoading(false);
      return Promise.resolve();
    }

    setLoading(true);
    setError('');
    return listPatientAssignments(patientId, { include_inactive: showHistory })
      .then((result) => {
        setAssignments(result?.assignments || []);
      })
      .catch((err) => {
        setAssignments([]);
        setError(err instanceof Error ? err.message : 'Failed to load staff assignments');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [patientId, showHistory]);

  useEffect(() => {
    loadAssignments();
  }, [loadAssignments]);

  useEffect(() => {
    setRosterLoading(true);
    listStaff({ status: 'active' })
      .then((result) => {
        setRoster(result || []);
      })
      .catch((err) => {
        setRoster([]);
        setError((previous) => previous || (err instanceof Error ? err.message : 'Failed to load staff roster'));
      })
      .finally(() => {
        setRosterLoading(false);
      });
  }, []);

  const groupedAssignments = useMemo(() => (
    DISCIPLINE_GROUPS.map((group) => ({
      ...group,
      rows: assignments.filter((assignment) => group.disciplines.includes(assignment.discipline)),
    }))
  ), [assignments]);

  const filteredGroups = useMemo(() => {
    if (filter === 'assigned') {
      return groupedAssignments.filter((group) => group.rows.some((row) => row.active));
    }
    if (filter === 'unassigned') {
      return groupedAssignments.filter((group) => !group.rows.some((row) => row.active));
    }
    return groupedAssignments;
  }, [filter, groupedAssignments]);

  const toggleExpanded = (key) => {
    setExpandedKeys((previous) => {
      const next = new Set(previous);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const updateDraft = (groupKey, patch) => {
    setDrafts((previous) => ({
      ...previous,
      [groupKey]: {
        ...(previous[groupKey] || emptyDraft(DISCIPLINE_GROUPS.find((group) => group.key === groupKey) || DISCIPLINE_GROUPS[0])),
        ...patch,
      },
    }));
  };

  const resetDraft = (groupKey) => {
    const group = DISCIPLINE_GROUPS.find((item) => item.key === groupKey);
    if (!group) return;
    setDrafts((previous) => ({ ...previous, [groupKey]: emptyDraft(group) }));
  };

  const handleAssign = async (groupKey) => {
    const group = DISCIPLINE_GROUPS.find((item) => item.key === groupKey);
    const draft = drafts[groupKey];
    if (!group || !draft?.userId || !patientId) return;

    setSavingGroupKey(groupKey);
    setError('');
    setSuccessMessage('');
    try {
      await assignPatientStaff({
        patient_id: patientId,
        discipline: draft.discipline,
        user_id: draft.userId,
        service_area: draft.serviceArea || null,
        note: draft.note || null,
      });
      resetDraft(groupKey);
      await loadAssignments();
      setSuccessMessage(`${DISCIPLINE_LABELS[draft.discipline] || draft.discipline} assignment saved.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save assignment');
    } finally {
      setSavingGroupKey('');
    }
  };

  const handleDeactivate = async (assignment) => {
    setDeactivatingAssignmentId(assignment.id);
    setError('');
    setSuccessMessage('');
    try {
      await deactivatePatientAssignment(assignment.id);
      await loadAssignments();
      setSuccessMessage(`${assignment.staff_name || assignment.staff_full_name || 'Staff member'} deactivated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate assignment');
    } finally {
      setDeactivatingAssignmentId('');
    }
  };

  const handlePrepareReassign = (discipline) => {
    const group = DISCIPLINE_GROUPS.find((item) => item.disciplines.includes(discipline));
    if (!group) return;
    setExpandedKeys((previous) => new Set(previous).add(group.key));
    updateDraft(group.key, { discipline, userId: '' });
  };

  const selectStyle = {
    backgroundColor: colors.card,
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    padding: '8px 12px',
    color: colors.white,
    fontSize: 13,
    fontFamily: "'Inter', sans-serif",
    outline: 'none',
  };

  if (!patientId) {
    return (
      <div style={{ flex: 1, backgroundColor: colors.bg, padding: 24, fontFamily: "'Inter', sans-serif" }}>
        <PatientBanner patient={patient} colors={colors} />
        <div style={cardStyle(colors)}>
          <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Staff Assignment</div>
          <div style={{ color: colors.label, fontSize: 13 }}>No patient is currently selected.</div>
        </div>
      </div>
    );
  }

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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, gap: 12, flexWrap: 'wrap' }}>
          <div>
            <div style={{ color: colors.white, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Staff Assignment</div>
            <div style={{ color: colors.label, fontSize: 13 }}>
              Real patient assignments sourced from the backend care-team records.
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <label style={{ color: colors.label, fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={showHistory}
                onChange={(event) => setShowHistory(event.target.checked)}
              />
              Show history
            </label>
            <select value={filter} onChange={(event) => setFilter(event.target.value)} style={selectStyle}>
              <option value="all">All Disciplines</option>
              <option value="assigned">Assigned Only</option>
              <option value="unassigned">Unassigned Only</option>
            </select>
          </div>
        </div>

        {error ? (
          <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, backgroundColor: colors.redBg, color: colors.red, fontSize: 12.5 }}>
            {error}
          </div>
        ) : null}
        {successMessage ? (
          <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, backgroundColor: colors.greenBg, color: colors.green, fontSize: 12.5 }}>
            {successMessage}
          </div>
        ) : null}
        {!canManageAssignments ? (
          <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, backgroundColor: colors.tealBg, color: colors.teal, fontSize: 12.5 }}>
            You can view the live care team here. Assignment changes require an Administrator or DPCS account.
          </div>
        ) : null}
        {(loading || rosterLoading) ? (
          <div style={{ color: colors.label, fontSize: 13 }}>
            Loading staff assignments…
          </div>
        ) : filteredGroups.length ? (
          filteredGroups.map((group) => (
            <DisciplineSection
              key={group.key}
              group={group}
              rows={group.rows}
              colors={colors}
              expanded={expandedKeys.has(group.key)}
              onToggle={() => toggleExpanded(group.key)}
              canManageAssignments={canManageAssignments}
              draft={drafts[group.key] || emptyDraft(group)}
              onDraftChange={updateDraft}
              onAssign={handleAssign}
              onDeactivate={handleDeactivate}
              onPrepareReassign={handlePrepareReassign}
              deactivatingAssignmentId={deactivatingAssignmentId}
              savingGroupKey={savingGroupKey}
              roster={roster}
            />
          ))
        ) : (
          <div style={{ color: colors.label, fontSize: 13 }}>
            No discipline groups match the selected filter.
          </div>
        )}
      </div>
    </div>
  );
};

export default StaffAssignment;
