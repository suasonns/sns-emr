import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PatientChartSidebar from './PatientChartSidebar';
import PatientFacesheet from './PatientFacesheet';
import ConsentNotifications from '../intake/ConsentNotifications';
import StaffAssignment from '../intake/StaffAssignment';
import ChartCompletionChecklist from '../intake/ChartCompletionChecklist';
import NursingAssessmentBoard from '../intake/NursingAssessmentBoard';
import PsychosocialAssessmentBoard from '../intake/PsychosocialAssessmentBoard';
import SpiritualAssessmentBoard from '../intake/SpiritualAssessmentBoard';
import { OrdersHubCard, MedicationOrdersCard, MasterPocReviewCard, CHHAPocCard, CHHAVisitNoteCard, getRnicaColors, getRnicaStyles } from '../components/RNICA';
import {
  getRnicaAssessmentByPatient,
} from '../api/icaAssessments';
import PhysicianOrdersBoard from './PhysicianOrdersBoard';
import CertificationsBoard from './CertificationsBoard';
import F2FBoard from './F2FBoard';
import VisitNoteBoard from '../components/VisitNotes';
import { fetchAssessmentHistory, fetchPatientSummary } from '../api/patientCharts';
import { fetchFacesheet } from '../api/facesheet';
import { listMedications } from '../api/medications';
import { getActivePatientId, setActivePatientId } from '../utils/activePatient';
import { useThemeMode } from '../theme/theme';
import ComplianceHopeBoard from '../intake/ComplianceHopeBoard';
import DischargePlanningBoard from './DischargePlanningBoard';
import IssuesOutcomesBoard from './IssuesOutcomesBoard';
import BereavementBoard from './BereavementBoard';
import BereavementPOCBoard from './BereavementPOCBoard';
import PostDeathBereavementBoard from './PostDeathBereavementBoard';
import BereavementLettersBoard from './BereavementLettersBoard';
import BereavementSupportBoard from './BereavementSupportBoard';
import DocumentsBoard from './DocumentsBoard';
import CommunicationLogBoard from './CommunicationLogBoard';
import FaxesBoard from './FaxesBoard';

const getColors = (mode) => mode === 'light' ? {
  bg: '#f3f8f7',
  panel: '#ffffff',
  muted: '#5f7286',
  text: '#18354c',
  accent: '#0d7d7a',
  border: '#d9e6eb',
} : {
  bg: '#0f172a',
  panel: '#111827',
  muted: '#94a3b8',
  text: '#e2e8f0',
  accent: '#10b7a2',
  border: '#334155',
};

const PatientChart = () => {
  const navigate = useNavigate();
  const { mode } = useThemeMode();
  const colors = getColors(mode);
  const { patientId: routePatientId } = useParams();
  const [activeSection, setActiveSection] = useState('facesheet');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [assessmentHistorySelection, setAssessmentHistorySelection] = useState(null);
  const [compactNavigation, setCompactNavigation] = useState(() => window.matchMedia('(max-width: 1200px)').matches);
  const [navigationOpen, setNavigationOpen] = useState(false);
  const navigationDialogRef = useRef(null);
  const navigationCloseRef = useRef(null);
  const navigationButtonRef = useRef(null);
  const chartContentRef = useRef(null);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 1200px)');
    const handleChange = (event) => {
      setCompactNavigation(event.matches);
      if (!event.matches) setNavigationOpen(false);
    };
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, []);

  const navigateChart = (section) => {
    setActiveSection(section);
    if (compactNavigation) setNavigationOpen(false);
  };

  useEffect(() => {
    if (!navigationOpen) return undefined;
    const chartContent = chartContentRef.current;
    chartContent?.setAttribute('inert', '');
    navigationCloseRef.current?.focus();

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setNavigationOpen(false);
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = navigationDialogRef.current?.querySelectorAll(
        'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      chartContent?.removeAttribute('inert');
      navigationButtonRef.current?.focus();
    };
  }, [navigationOpen]);

  const resolvedPatientId = routePatientId || getActivePatientId() || '';

  useEffect(() => {
    if (!resolvedPatientId) {
      setSummary(null);
      setAssessmentHistorySelection(null);
      setLoading(false);
      return;
    }

    setActivePatientId(resolvedPatientId);
    let mounted = true;
    setLoading(true);

    fetchPatientSummary(resolvedPatientId)
      .then((result) => {
        if (mounted) setSummary(result);
      })
      .catch(() => {
        if (mounted) setSummary(null);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [resolvedPatientId]);

  const [idgAssessmentId, setIdgAssessmentId] = useState(null);
  const [idgAssessmentLoading, setIdgAssessmentLoading] = useState(false);

  const [facesheetData, setFacesheetData] = useState(null);
  const [facesheetLoading, setFacesheetLoading] = useState(false);

  useEffect(() => {
    if (!resolvedPatientId) {
      setFacesheetData(null);
      return;
    }
    let mounted = true;
    setFacesheetLoading(true);
    fetchFacesheet(resolvedPatientId)
      .then((result) => {
        if (mounted) setFacesheetData(result);
      })
      .catch(() => {
        if (mounted) setFacesheetData(null);
      })
      .finally(() => {
        if (mounted) setFacesheetLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [resolvedPatientId]);

  const [medicationRecords, setMedicationRecords] = useState([]);
  const [medicationsLoading, setMedicationsLoading] = useState(false);
  const [medicationsError, setMedicationsError] = useState('');

  useEffect(() => {
    if (!resolvedPatientId) {
      setMedicationRecords([]);
      return;
    }
    let mounted = true;
    setMedicationsLoading(true);
    listMedications(resolvedPatientId)
      .then((result) => {
        if (mounted) {
          setMedicationRecords(Array.isArray(result) ? result : []);
          setMedicationsError('');
        }
      })
      .catch(() => {
        if (mounted) {
          setMedicationRecords([]);
          setMedicationsError('Unable to load medications right now.');
        }
      })
      .finally(() => {
        if (mounted) setMedicationsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [resolvedPatientId]);

  useEffect(() => {
    if (!resolvedPatientId) {
      setIdgAssessmentId(null);
      return;
    }
    let mounted = true;
    setIdgAssessmentLoading(true);
    getRnicaAssessmentByPatient(resolvedPatientId)
      .then((assessment) => {
        if (mounted) setIdgAssessmentId(assessment?.id || assessment?.assessmentId || null);
      })
      .catch(() => {
        if (mounted) setIdgAssessmentId(null);
      })
      .finally(() => {
        if (mounted) setIdgAssessmentLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [resolvedPatientId]);

  const patient = useMemo(() => {
    const patientData = summary?.patient ?? {};
    const primaryCareMember = summary?.care_team?.find((member) => member.primary) || summary?.care_team?.[0];
    const latestVisit = summary?.recent_visits?.[0];

    return {
      name: patientData.full_name || patientData.name || 'No patient selected',
      mrn: patientData.mrn || '—',
      status: patientData.status || 'ACTIVE',
      primaryDx: patientData.primary_diagnosis || '—',
      recentComms: summary?.communication_summary?.latest?.[0]?.summary || 'No recent communication',
      primaryMD: primaryCareMember?.staff_name || 'Provider not assigned',
      lastVisit: latestVisit ? new Date(latestVisit.visit_datetime).toLocaleString([], {
        month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
      }) : 'No recent visit recorded',
    };
  }, [summary]);

  const intakePatient = useMemo(() => {
    const patientData = summary?.patient ?? {};
    const identity = facesheetData?.identity ?? {};
    const insurance = facesheetData?.insurance ?? {};
    const levelOfCare = facesheetData?.level_of_care ?? {};
    const serviceDates = facesheetData?.service_dates ?? {};
    const fullName = (patientData.full_name || patientData.name || '').trim();
    const nameParts = fullName.split(/\s+/).filter(Boolean);
    const lastName = identity.last_name || (nameParts.length > 1 ? nameParts[nameParts.length - 1] : nameParts[0]);
    const firstName = identity.first_name || (nameParts.length > 1 ? nameParts.slice(0, -1).join(' ') : '');
    const dob = identity.dob || null;
    const age = dob
      ? Math.floor((Date.now() - new Date(dob).getTime()) / (365.25 * 24 * 60 * 60 * 1000))
      : null;
    const socDate = serviceDates.soc_date || patientData.soc_date || patientData.hospice_election_date;

    return {
      firstName: firstName || 'Patient',
      lastName: lastName || patientData.mrn || 'Unknown',
      mrn: patientData.mrn || facesheetData?.mrn || '—',
      dob: dob ? new Date(dob).toLocaleDateString() : '—',
      age: age !== null && !Number.isNaN(age) ? age : '—',
      sex: identity.gender || '—',
      payer: insurance.primary_payer || '—',
      status: patientData.admission_status || patientData.status || 'ACTIVE',
      socDate: socDate ? new Date(socDate).toLocaleDateString() : '—',
      levelOfCare: levelOfCare.current_level_of_care || '—',
      levelOfCareEffective: levelOfCare.loc_effective_date
        ? new Date(levelOfCare.loc_effective_date).toLocaleDateString()
        : null,
      hasResponsibleParty: Boolean(facesheetData?.contacts?.responsible_party?.name),
      hasEmergencyContact: Boolean(facesheetData?.contacts?.emergency_contact?.name),
      hasAttendingPhysician: Boolean(facesheetData?.physicians?.attending?.name),
      hasInsurance: Boolean(insurance.primary_payer),
      hasAllergiesDocumented: facesheetData?.clinical?.has_allergies !== null && facesheetData?.clinical?.has_allergies !== undefined,
    };
  }, [summary, facesheetData]);

  const boardCard = {
    backgroundColor: colors.panel,
    border: `1px solid ${colors.border}`,
    borderRadius: 8,
    boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
    padding: 10,
  };

  const boardHeader = {
    color: colors.text,
    fontSize: 15,
    fontWeight: 700,
    marginBottom: 8,
    letterSpacing: 0.2,
  };

  const badge = (tone, label) => ({
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: 999,
    padding: '5px 10px',
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    backgroundColor: tone === 'teal' ? (mode === 'light' ? '#dff8f4' : '#10b7a215') : tone === 'amber' ? (mode === 'light' ? '#f9edd7' : '#f59e0b15') : tone === 'red' ? (mode === 'light' ? '#fbe3e7' : '#ef444415') : (mode === 'light' ? '#dff5ee' : '#05966915'),
    color: tone === 'teal' ? colors.accent : tone === 'amber' ? '#d38a2b' : tone === 'red' ? '#d64d57' : '#2d7b63',
  });

  const MetricCard = ({ label, value, tone = 'teal' }) => (
    <div style={{ ...boardCard, padding: 10, minHeight: 70, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div style={{ color: colors.muted, fontSize: 9, fontWeight: 700, letterSpacing: 0.8, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ color: colors.text, fontSize: 16, fontWeight: 700, lineHeight: 1.2 }}>{value}</div>
      <div style={{ ...badge(tone, 'status'), width: 'fit-content', fontSize: 8.5 }}>{tone === 'teal' ? 'Active' : tone === 'amber' ? 'Watch' : 'Review'}</div>
    </div>
  );

  const CareOverviewBoard = () => {
    const metrics = [
      { label: 'Care status', value: patient.status, tone: 'teal' },
      { label: 'Primary diagnosis', value: patient.primaryDx, tone: 'green' },
      { label: 'Last visit', value: patient.lastVisit, tone: 'amber' },
      { label: 'Primary MD', value: patient.primaryMD, tone: 'teal' },
    ];

    const carePlanFacts = [
      `Primary diagnosis: ${patient.primaryDx}`,
      summary?.patient?.hospice_election_date
        ? `Hospice election date: ${new Date(summary.patient.hospice_election_date).toLocaleDateString()}`
        : null,
      summary?.patient?.admission_status
        ? `Admission status: ${summary.patient.admission_status}`
        : null,
      patient.recentComms && patient.recentComms !== 'No recent communication'
        ? `Recent communication: ${patient.recentComms}`
        : null,
    ].filter(Boolean);

    const disciplineSummary = summary?.care_team ?? [];

    return (
      <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
        <div style={{ ...boardCard, marginBottom: 10, borderLeft: `3px solid ${colors.accent}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <div>
              <div style={{ color: colors.muted, fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 }}>Patient Status</div>
              <div style={{ color: colors.text, fontSize: 20, fontWeight: 700 }}>{patient.name}</div>
            </div>
            <div style={{ ...badge('green', 'status'), fontSize: 8.5 }}>{patient.status}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 8 }}>
            {metrics.map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
          <div style={{ ...boardCard, minHeight: 170 }}>
            <div style={boardHeader}>Current care plan</div>
            {carePlanFacts.length > 0 ? (
              <div style={{ display: 'grid', gap: 7 }}>
                {carePlanFacts.map((item) => (
                  <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', color: colors.text, fontSize: 12.5, lineHeight: 1.4 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 999, backgroundColor: colors.accent, display: 'inline-block', marginTop: 6 }} />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>No care plan details recorded yet.</div>
            )}
          </div>

          <div style={{ ...boardCard, minHeight: 170 }}>
            <div style={boardHeader}>Discipline coverage</div>
            {disciplineSummary.length > 0 ? (
              <div style={{ display: 'grid', gap: 7 }}>
                {disciplineSummary.map((item) => (
                  <div key={`${item.discipline}-${item.staff_name}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.border}`, paddingBottom: 5 }}>
                    <div>
                      <div style={{ color: colors.text, fontSize: 12.5, fontWeight: 700 }}>{item.discipline || '—'}</div>
                      <div style={{ color: colors.muted, fontSize: 10.5 }}>{item.staff_name || 'Not assigned'}{item.service_area ? ` • ${item.service_area}` : ''}</div>
                    </div>
                    <span style={{ ...badge(item.status === 'ACTIVE' ? 'green' : 'amber', 'status'), fontSize: 8.5 }}>{item.status || 'Unknown'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>No care team members assigned yet.</div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const IntakeBoard = () => {
    const overviewFields = [
      ['Admission status', intakePatient.status],
      ['Level of care', intakePatient.levelOfCare],
      ['Payer', intakePatient.payer],
      ['SOC date', intakePatient.socDate],
      ['DOB', intakePatient.dob],
      ['Age / sex', `${intakePatient.age} / ${intakePatient.sex}`],
    ];

    const checklistItems = [
      { label: 'Insurance verification completed', done: intakePatient.hasInsurance },
      { label: 'Primary physician assignment confirmed', done: intakePatient.hasAttendingPhysician },
      { label: 'Responsible party on file', done: intakePatient.hasResponsibleParty },
      { label: 'Emergency contact on file', done: intakePatient.hasEmergencyContact },
      { label: 'Allergy status documented', done: intakePatient.hasAllergiesDocumented },
    ];

    return (
      <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
        {facesheetLoading && (
          <div style={{ color: colors.muted, fontSize: 12.5, marginBottom: 8 }}>Loading facesheet data…</div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
          <div style={{ ...boardCard, minHeight: 170 }}>
            <div style={boardHeader}>Intake & admission overview</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {overviewFields.map(([label, value]) => (
                <div key={label} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: mode === 'light' ? '#f8fbfb' : '#111827' }}>
                  <div style={{ color: colors.muted, fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.8 }}>{label}</div>
                  <div style={{ color: colors.text, fontSize: 12.5, fontWeight: 600, marginTop: 4 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ ...boardCard, minHeight: 170 }}>
            <div style={boardHeader}>Admission checklist</div>
            <div style={{ display: 'grid', gap: 7 }}>
              {checklistItems.map((item) => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, color: colors.text, fontSize: 12.5 }}>
                  <span style={{ width: 14, height: 14, borderRadius: 4, backgroundColor: item.done ? colors.accent : '#94a3b8', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 10 }}>{item.done ? '✓' : '·'}</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const AssessmentBoard = () => {
    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [historyError, setHistoryError] = useState('');

    useEffect(() => {
      if (!resolvedPatientId) {
        setHistory([]);
        setHistoryLoading(false);
        setHistoryError('');
        return undefined;
      }
      let mounted = true;
      setHistoryLoading(true);
      setHistoryError('');
      fetchAssessmentHistory(resolvedPatientId, { sort_order: 'asc', limit: 500 })
        .then((result) => {
          if (!mounted) return;
          const items = (result?.items || []).map((item) => {
            const disciplineTone = item.discipline === 'RN' ? 'teal' : item.discipline === 'MSW' ? 'amber' : 'green';
            let assessmentLabel = item.assessment_type;
            if (item.discipline === 'RN' && item.assessment_type === 'RNICA') assessmentLabel = 'RNICA Admission';
            else if (item.discipline === 'RN' && item.assessment_type === 'UPDATE' && item.phase_hint === 'HUV1') assessmentLabel = 'RN Update - HUV1';
            else if (item.discipline === 'RN' && item.assessment_type === 'UPDATE' && item.phase_hint === 'HUV2') assessmentLabel = 'RN Update - HUV2';
            else if (item.discipline === 'RN' && item.assessment_type === 'UPDATE') assessmentLabel = 'RN Update';
            else if (item.discipline === 'RN' && item.assessment_type === 'RECERT') assessmentLabel = 'RN Re-Cert';
            else if (item.discipline === 'RN' && item.assessment_type === 'RN_RECERT_LEGACY') assessmentLabel = 'RN Re-Cert (Legacy)';
            else if (item.discipline === 'MSW') assessmentLabel = 'MSW ICA';
            else if (item.discipline === 'SC') assessmentLabel = 'SC ICA';
            return {
              ...item,
              disciplineLabel: item.discipline === 'RN' ? 'Nursing' : item.discipline === 'MSW' ? 'Psychosocial' : 'Spiritual',
              disciplineTone,
              assessmentLabel,
              openSection: item.record_url_hint?.section,
              selectedAssessmentId: item.record_url_hint?.assessment_id,
            };
          });
          setHistory(items);
        })
        .catch((error) => {
          if (!mounted) return;
          setHistory([]);
          setHistoryError(error?.message || 'Unable to load assessment audit history.');
        })
        .finally(() => {
          if (mounted) setHistoryLoading(false);
        });
      return () => {
        mounted = false;
      };
    }, [resolvedPatientId]);

    const formatHistoryDate = (value) => {
      if (!value) return '—';
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return '—';
      return parsed.toLocaleDateString([], { month: '2-digit', day: '2-digit', year: 'numeric' });
    };

    const statusTone = (status) => {
      const normalized = String(status || '').toUpperCase();
      if (normalized === 'LOCKED') return 'green';
      if (normalized === 'DRAFT' || normalized === 'IN_PROGRESS' || normalized === 'PENDING') return 'amber';
      if (normalized === 'AMENDED') return 'red';
      return 'teal';
    };

    return (
      <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
        <div style={{ ...boardCard, padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap' }}>
            <div>
              <div style={boardHeader}>Assessment history audit index</div>
              <div style={{ color: colors.muted, fontSize: 12.5, lineHeight: 1.5 }}>
                Combined chronological view across nursing, psychosocial, and spiritual assessment records for audit review.
              </div>
            </div>
            <div style={{ ...badge('teal', 'status'), fontSize: 9 }}>{history.length} record{history.length === 1 ? '' : 's'}</div>
          </div>

          {historyLoading ? (
            <div style={{ color: colors.muted, fontSize: 13 }}>Loading assessment audit history…</div>
          ) : historyError ? (
            <div style={{ color: '#d64d57', fontSize: 13 }}>{historyError}</div>
          ) : history.length === 0 ? (
            <div style={{ color: colors.muted, fontSize: 13 }}>No assessment records are on file for this patient yet.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 960 }}>
                <thead>
                  <tr>
                    {['Discipline', 'Assessment', 'Status', 'Visit Date', 'Locked Date', 'Locked By', 'Action'].map((label) => (
                      <th
                        key={label}
                        style={{
                          textAlign: 'left',
                          padding: '10px 12px',
                          fontSize: 11,
                          textTransform: 'uppercase',
                          letterSpacing: 0.7,
                          color: colors.muted,
                          borderBottom: `1px solid ${colors.border}`,
                        }}
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={`${item.discipline}-${item.record_id}`}>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}` }}>
                        <span style={{ ...badge(item.disciplineTone, 'status'), fontSize: 8.5 }}>{item.disciplineLabel}</span>
                      </td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}`, color: colors.text }}>
                        <div style={{ fontSize: 13, fontWeight: 700 }}>{item.assessmentLabel}</div>
                        <div style={{ color: colors.muted, fontSize: 11.5, marginTop: 4 }}>{item.record_id}</div>
                      </td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}` }}>
                        <span style={{ ...badge(statusTone(item.status), 'status'), fontSize: 8.5 }}>{String(item.status || 'DRAFT').replaceAll('_', ' ')}</span>
                      </td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}`, color: colors.text, fontSize: 12.5 }}>{formatHistoryDate(item.visit_date || item.created_at)}</td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}`, color: colors.text, fontSize: 12.5 }}>{formatHistoryDate(item.locked_at)}</td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}`, color: colors.muted, fontSize: 12.5 }}>—</td>
                      <td style={{ padding: '12px', borderBottom: `1px solid ${colors.border}` }}>
                        <button
                          type="button"
                          onClick={() => {
                            setAssessmentHistorySelection({
                              section: item.openSection,
                              assessmentId: item.selectedAssessmentId,
                            });
                            navigateChart(item.openSection);
                          }}
                          style={{
                            borderRadius: 999,
                            padding: '8px 12px',
                            border: `1px solid ${colors.border}`,
                            backgroundColor: colors.panel,
                            color: colors.accent,
                            fontSize: 12,
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          Open record
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  };

  const TxMedsBoard = () => {
    const dmeVendor = facesheetData?.vendors?.dme;
    return (
      <div style={{ flex: 1, minWidth: 0, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
          <div style={{ ...boardCard }}>
            <div style={boardHeader}>Current medications & treatments</div>
            {medicationsLoading && (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>Loading medications…</div>
            )}
            {!medicationsLoading && medicationsError && (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>{medicationsError}</div>
            )}
            {!medicationsLoading && !medicationsError && medicationRecords.length === 0 && (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>No medications on file for this patient.</div>
            )}
            {!medicationsLoading && !medicationsError && medicationRecords.length > 0 && (
              <div style={{ display: 'grid', gap: 7 }}>
                {medicationRecords.map((med) => (
                  <div key={med.medication_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: mode === 'light' ? '#f8fbfb' : '#111827' }}>
                    <div>
                      <div style={{ color: colors.text, fontWeight: 700, fontSize: 12.5 }}>{med.medication_name}</div>
                      <div style={{ color: colors.muted, fontSize: 10.5 }}>{med.dosage} • {med.route} • {med.frequency}</div>
                    </div>
                    <span style={{ ...badge(med.status === 'active' ? 'teal' : 'amber', 'status'), fontSize: 8.5 }}>{med.status === 'active' ? 'Active' : 'Discontinued'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ ...boardCard }}>
            <div style={boardHeader}>DME vendor</div>
            {dmeVendor?.name ? (
              <div style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: mode === 'light' ? '#f8fbfb' : '#111827' }}>
                <div style={{ color: colors.text, fontWeight: 700, fontSize: 12.5 }}>{dmeVendor.name}</div>
                <div style={{ color: colors.muted, fontSize: 10.5, marginTop: 3 }}>{dmeVendor.phone || 'No phone on file'}</div>
              </div>
            ) : (
              <div style={{ color: colors.muted, fontSize: 12.5 }}>No DME vendor on file for this patient.</div>
            )}
            <div style={{ color: colors.muted, fontSize: 11, marginTop: 8 }}>
              Structured DME/supply order tracking (delivery status per item) is not available yet.
            </div>
          </div>
        </div>
      </div>
    );
  };

  const IDGBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ ...boardCard, marginBottom: 10 }}>
        <div style={boardHeader}>Master plan of care review</div>
        {idgAssessmentLoading && (
          <div style={{ color: colors.muted, fontSize: 11.5 }}>Loading plan of care…</div>
        )}
        {!idgAssessmentLoading && !idgAssessmentId && (
          <div style={{ color: colors.muted, fontSize: 11.5 }}>No plan of care on file for this patient yet.</div>
        )}
        {!idgAssessmentLoading && idgAssessmentId && (
          <MasterPocReviewCard
            assessmentId={idgAssessmentId}
            styles={getRnicaStyles(getRnicaColors(mode))}
            COLORS={getRnicaColors(mode)}
          />
        )}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>IDG meeting summary</div>
          <div style={{ color: colors.muted, fontSize: 12.5 }}>
            Per-discipline IDG meeting notes are not wired to a structured backend record yet. Use the Master Plan of Care review above for the current documented plan.
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Care coordination actions</div>
          <div style={{ color: colors.muted, fontSize: 12.5 }}>
            Structured care coordination action tracking is not available yet.
          </div>
        </div>
      </div>
    </div>
  );

  const POCBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      {idgAssessmentLoading && (
        <div style={{ color: colors.muted, fontSize: 11.5, marginBottom: 10 }}>Loading plan of care…</div>
      )}
      {!idgAssessmentLoading && idgAssessmentId && (
        <div style={{ ...boardCard, marginBottom: 10 }}>
          <div style={boardHeader}>Master plan of care review</div>
          <MasterPocReviewCard
            assessmentId={idgAssessmentId}
            styles={getRnicaStyles(getRnicaColors(mode))}
            COLORS={getRnicaColors(mode)}
          />
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Plan of care goals</div>
          <div style={{ color: colors.muted, fontSize: 12.5 }}>
            {idgAssessmentId
              ? 'Structured POC goal tracking (separate from the Master Plan of Care review above) is not available yet.'
              : 'No plan of care on file for this patient yet.'}
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>POC status</div>
          <div style={{ color: colors.muted, fontSize: 12.5 }}>
            {idgAssessmentId
              ? 'See the Master Plan of Care review above for current status and last review details.'
              : 'No plan of care on file for this patient yet.'}
          </div>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg, fontFamily: "'Inter', sans-serif", color: colors.text }}>
          Loading patient chart...
        </div>
      );
    }

    switch (activeSection) {
      case 'facesheet':
        return <PatientFacesheet patientId={resolvedPatientId} />;
      case 'care-overview':
        return <CareOverviewBoard />;
      case 'consent':
        return <ConsentNotifications patient={intakePatient} />;
      case 'staff-assignment':
        return <StaffAssignment patient={intakePatient} />;
      case 'chart-checklist':
        return <ChartCompletionChecklist patient={intakePatient} />;
      case 'intake':
      case 'demographics':
        return <IntakeBoard />;
      case 'nursing-assessment':
        return <NursingAssessmentBoard patientId={resolvedPatientId} onNavigateToSection={navigateChart} selectedAssessmentId={activeSection === 'nursing-assessment' ? assessmentHistorySelection?.assessmentId : null} />
      case 'psychosocial-assessment':
        return <PsychosocialAssessmentBoard patientId={resolvedPatientId} selectedAssessmentId={activeSection === 'psychosocial-assessment' ? assessmentHistorySelection?.assessmentId : null} />;
      case 'spiritual-assessment':
        return <SpiritualAssessmentBoard patientId={resolvedPatientId} selectedAssessmentId={activeSection === 'spiritual-assessment' ? assessmentHistorySelection?.assessmentId : null} />;
      case 'pain-assessment':
        return <NursingAssessmentBoard patientId={resolvedPatientId} />;
      case 'assessments':
      case 'assessment-history':
        return <AssessmentBoard />;
      case 'visit-notes':
      case 'add-visit':
      case 'my-visit-notes':
      case 'visit-history':
        return <VisitNoteBoard patientId={resolvedPatientId} />;
      case 'tx-meds':
      case 'add-order':
      case 'dme-orders':
        return <OrdersHubCard patientId={resolvedPatientId} />;
      case 'current-meds':
      case 'med-history':
        return (
          <MedicationOrdersCard
            patientId={resolvedPatientId}
            styles={getRnicaStyles(getRnicaColors(mode))}
            COLORS={getRnicaColors(mode)}
          />
        );
      case 'physician-orders':
      case 'add-md-order':
        return <PhysicianOrdersBoard patientId={resolvedPatientId} initialView="add" />;
      case 'order-history':
        return <PhysicianOrdersBoard patientId={resolvedPatientId} initialView="history" />;
      case 'chha-assignment':
        return (
          <CHHAPocCard
            patientId={resolvedPatientId}
            styles={getRnicaStyles(getRnicaColors(mode))}
            COLORS={getRnicaColors(mode)}
          />
        );
      case 'chha-visits':
        return (
          <CHHAVisitNoteCard
            patientId={resolvedPatientId}
            styles={getRnicaStyles(getRnicaColors(mode))}
            COLORS={getRnicaColors(mode)}
          />
        );
      case 'cti':
        return <CertificationsBoard patientId={resolvedPatientId} />;
      case 'f2f':
        return <F2FBoard patientId={resolvedPatientId} />;
      case 'idg':
      case 'add-idg':
      case 'idg-history':
        return <IDGBoard />;
      case 'poc':
      case 'poc-summary':
      case 'poc-goals':
      case 'add-poc':
      case 'poc-history':
        return <POCBoard />;
      case 'compliance':
      case 'lcd-eligibility':
      case 'hope-admission':
      case 'hope-huv1':
      case 'hope-huv2':
      case 'hope-discharge':
      case 'decline-of-status':
        return <ComplianceHopeBoard patientId={resolvedPatientId} activeSection={activeSection} onNavigateToSection={navigateChart} />;
      case 'issues':
        return <IssuesOutcomesBoard patientId={resolvedPatientId} />;
      case 'discharge':
        return <DischargePlanningBoard patientId={resolvedPatientId} />;
      case 'bereavement':
        return <BereavementBoard patientId={resolvedPatientId} />;
      case 'bereavement-poc':
        return <BereavementPOCBoard patientId={resolvedPatientId} />;
      case 'bereavement-post-death':
        return <PostDeathBereavementBoard patientId={resolvedPatientId} />;
      case 'bereavement-letters':
        return <BereavementLettersBoard patientId={resolvedPatientId} />;
      case 'bereavement-support':
        return <BereavementSupportBoard patientId={resolvedPatientId} />;
      case 'all-docs':
      case 'intake-docs':
      case 'other-files':
        return <DocumentsBoard patientId={resolvedPatientId} sectionKey={activeSection} />;
      case 'comm-log':
        return <CommunicationLogBoard patientId={resolvedPatientId} />;
      case 'faxes':
        return <FaxesBoard patientId={resolvedPatientId} />;
      default:
        return (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            backgroundColor: colors.bg, fontFamily: "'Inter', sans-serif",
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: colors.muted, fontSize: 16, marginBottom: 8 }}>
                {activeSection.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
              </div>
              <div style={{ color: colors.muted, fontSize: 13 }}>Content for this section will appear here</div>
              <button
                type="button"
                onClick={() => navigate(`/care-overview?patientId=${encodeURIComponent(resolvedPatientId)}`)}
                style={{ marginTop: 16, background: colors.accent, color: '#ffffff', border: 'none', borderRadius: 8, padding: '8px 12px', cursor: 'pointer' }}
              >
                Open care overview
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100%', maxWidth: '100vw', minWidth: 0, overflow: 'hidden', fontFamily: "'Inter', sans-serif", backgroundColor: colors.bg, color: colors.text }}>
      {(!compactNavigation || navigationOpen) && (
        <>
          {compactNavigation && (
            <div
              aria-hidden="true"
              onClick={() => setNavigationOpen(false)}
              style={{ position: 'fixed', inset: 0, zIndex: 39, border: 0, background: 'rgba(2, 6, 23, 0.62)', cursor: 'pointer' }}
            />
          )}
          <div
            ref={navigationDialogRef}
            role={compactNavigation ? 'dialog' : undefined}
            aria-modal={compactNavigation ? 'true' : undefined}
            aria-label={compactNavigation ? 'Patient chart navigation' : undefined}
            style={compactNavigation ? { position: 'fixed', inset: '0 auto 0 0', zIndex: 40, boxShadow: '12px 0 32px rgba(2, 6, 23, 0.36)' } : undefined}
          >
            {compactNavigation && (
              <button
                ref={navigationCloseRef}
                type="button"
                onClick={() => setNavigationOpen(false)}
                style={{ position: 'absolute', top: 8, right: 8, zIndex: 2, minHeight: 40, padding: '7px 10px', border: `1px solid ${colors.accent}`, borderRadius: 8, background: colors.panel, color: colors.text, fontWeight: 700, cursor: 'pointer' }}
              >
                Close navigation
              </button>
            )}
            <PatientChartSidebar activeSection={activeSection} onNavigate={navigateChart} patient={patient} />
          </div>
        </>
      )}
      <div ref={chartContentRef} style={{ flex: 1, minWidth: 0, width: '100%', height: '100vh', minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}>
        {compactNavigation && (
          <button
            ref={navigationButtonRef}
            type="button"
            onClick={() => setNavigationOpen(true)}
            aria-expanded={navigationOpen}
            style={{
              position: 'sticky', top: 8, left: 8, zIndex: 35, margin: 8, minHeight: 42, padding: '8px 12px',
              border: `1px solid ${colors.accent}`, borderRadius: 8, background: colors.panel, color: colors.text,
              fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}
          >
            Patient chart navigation
          </button>
        )}
        {renderContent()}
      </div>
    </div>
  );
};

export default PatientChart;
