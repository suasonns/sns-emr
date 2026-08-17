import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PatientChartSidebar from './PatientChartSidebar';
import PatientFacesheet from './PatientFacesheet';
import ConsentNotifications from '../intake/ConsentNotifications';
import StaffAssignment from '../intake/StaffAssignment';
import ChartCompletionChecklist from '../intake/ChartCompletionChecklist';
import { fetchPatientSummary } from '../api/patientCharts';
import { getActivePatientId, setActivePatientId } from '../utils/activePatient';
import { useThemeMode } from '../theme/theme';

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

  const resolvedPatientId = routePatientId || getActivePatientId() || '';

  useEffect(() => {
    if (!resolvedPatientId) {
      setSummary(null);
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
    const fullName = (patientData.full_name || patientData.name || '').trim();
    const nameParts = fullName.split(/\s+/).filter(Boolean);
    const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : nameParts[0];
    const firstName = nameParts.length > 1 ? nameParts.slice(0, -1).join(' ') : '';

    return {
      firstName: firstName || 'Patient',
      lastName: lastName || patientData.mrn || 'Unknown',
      mrn: patientData.mrn || '—',
      dob: patientData.dob || '—',
      age: patientData.age || '—',
      sex: patientData.sex || '—',
      payer: patientData.payer || '—',
      status: patientData.status || 'ACTIVE',
      socDate: patientData.soc_date
        ? new Date(patientData.soc_date).toLocaleDateString()
        : (patientData.hospice_election_date || '—'),
      benefitPeriod: patientData.benefit_period || '—',
    };
  }, [summary]);

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

    const disciplineSummary = [
      { label: 'RN', detail: 'Care plan review • 3 days ago', status: 'Synced' },
      { label: 'LVN', detail: 'Skilled nursing due • Thu 9:00 AM', status: 'Scheduled' },
      { label: 'MSW', detail: 'Psychosocial check-in • Fri 10:30 AM', status: 'Confirmed' },
      { label: 'SC', detail: 'Spiritual care follow-up • Sat 2:00 PM', status: 'Scheduled' },
      { label: 'CHHA', detail: 'Aide support • Tue/Thu', status: 'Planned' },
    ];

    return (
      <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
        <div style={{ ...boardCard, marginBottom: 10, borderLeft: `3px solid ${colors.accent}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <div>
              <div style={{ color: colors.muted, fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 }}>Patient Status</div>
              <div style={{ color: colors.text, fontSize: 20, fontWeight: 700 }}>{patient.name}</div>
            </div>
            <div style={{ ...badge('green', 'status'), fontSize: 8.5 }}>Active census</div>
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
            <div style={{ display: 'grid', gap: 7 }}>
              {[
                'Primary diagnosis: Senile degeneration of brain (G31.1)',
                'Admissions and benefit period reviewed; active hospice care remains in place.',
                'Symptom burden monitored with current interdisciplinary team assignments.',
                'Recent communication indicates caregiver support remains stable and engaged.',
              ].map((item) => (
                <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', color: colors.text, fontSize: 12.5, lineHeight: 1.4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, backgroundColor: colors.accent, display: 'inline-block', marginTop: 6 }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ ...boardCard, minHeight: 170 }}>
            <div style={boardHeader}>Discipline coverage</div>
            <div style={{ display: 'grid', gap: 7 }}>
              {disciplineSummary.map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.border}`, paddingBottom: 5 }}>
                  <div>
                    <div style={{ color: colors.text, fontSize: 12.5, fontWeight: 700 }}>{item.label}</div>
                    <div style={{ color: colors.muted, fontSize: 10.5 }}>{item.detail}</div>
                  </div>
                  <span style={{ ...badge(item.status === 'Synced' ? 'teal' : item.status === 'Confirmed' ? 'green' : 'amber', 'status'), fontSize: 8.5 }}>{item.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const IntakeBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard, minHeight: 170 }}>
          <div style={boardHeader}>Intake & admission overview</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              ['Referral source', 'Physician / Family referral'],
              ['Admission status', 'Active hospice enrollment'],
              ['Benefit period', '01/15/2026 – 07/14/2026'],
              ['Payer', 'Medicare / Medi-Cal'],
              ['SOC date', '01/15/2026'],
              ['Level of care', 'Routine home care'],
            ].map(([label, value]) => (
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
            {[
              'Consent and Medicare / hospice notice reviewed',
              'Patient demographics verified',
              'Primary physician assignment confirmed',
              'Insurance verification completed',
              'Initial nursing assessment pending sign-off',
            ].map((item, index) => (
              <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, color: colors.text, fontSize: 12.5 }}>
                <span style={{ width: 14, height: 14, borderRadius: 4, backgroundColor: index < 4 ? colors.accent : '#94a3b8', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 10 }}>{index < 4 ? '✓' : '·'}</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const AssessmentBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
        {[
          {
            title: 'RN Assessment',
            status: 'Updated',
            tone: 'teal',
            items: ['Pain and symptom review complete', 'Care goals and teaching reviewed', 'Medication reconciliation signed'],
          },
          {
            title: 'Psychosocial Assessment',
            status: 'Due',
            tone: 'amber',
            items: ['Caregiver stress screening', 'Support system assessment', 'Coping and adjustment review'],
          },
          {
            title: 'Spiritual Assessment',
            status: 'Complete',
            tone: 'green',
            items: ['Spiritual needs identified', 'Chaplain and family support plan', 'Faith preference noted'],
          },
        ].map((section) => (
          <div key={section.title} style={{ ...boardCard, minHeight: 190 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={boardHeader}>{section.title}</div>
              <span style={{ ...badge(section.tone, 'status'), fontSize: 8.5 }}>{section.status}</span>
            </div>
            <div style={{ display: 'grid', gap: 7 }}>
              {section.items.map((item) => (
                <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', color: colors.text, fontSize: 12.5, lineHeight: 1.4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, backgroundColor: colors.accent, display: 'inline-block', marginTop: 6 }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const VisitNotesBoard = () => (
    <div style={{ flex: 1, minWidth: 0, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Visit notes timeline</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['RN Visit', 'Symptom management reviewed; patient remains alert and comfortable.', '08/14/2026 • 9:10 AM'],
              ['LVN Skilled Nursing', 'Medication review and wound status follow-up completed.', '08/11/2026 • 10:45 AM'],
              ['MSW', 'Caregiver support and resource follow-up documented.', '08/09/2026 • 2:00 PM'],
              ['SC', 'Spiritual support and prayer request addressed.', '08/08/2026 • 1:30 PM'],
            ].map(([title, detail, stamp]) => (
              <div key={title} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: mode === 'light' ? '#f8fbfb' : '#111827' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                  <div style={{ color: colors.text, fontSize: 12.5, fontWeight: 700 }}>{title}</div>
                  <span style={{ ...badge('teal', 'status'), fontSize: 8.5 }}>{stamp}</span>
                </div>
                <div style={{ color: colors.muted, fontSize: 11.5, lineHeight: 1.5 }}>{detail}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Visit queue</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['RN', 'Today • 9:00 AM', 'Scheduled'],
              ['LVN', 'Thu • 9:30 AM', 'Pending'],
              ['MSW', 'Fri • 1:00 PM', 'Confirmed'],
              ['SC', 'Sat • 2:30 PM', 'Planned'],
            ].map(([staff, time, status]) => (
              <div key={staff} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.border}`, paddingBottom: 5 }}>
                <div>
                  <div style={{ color: colors.text, fontWeight: 700, fontSize: 12.5 }}>{staff}</div>
                  <div style={{ color: colors.muted, fontSize: 10.5 }}>{time}</div>
                </div>
                <span style={{ ...badge(status === 'Scheduled' ? 'teal' : status === 'Confirmed' ? 'green' : 'amber', 'status'), fontSize: 8.5 }}>{status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const TxMedsBoard = () => (
    <div style={{ flex: 1, minWidth: 0, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Current medications & treatments</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['Morphine Sulfate', 'PRN • 5 mg', 'Last updated 08/15'],
              ['Atropine eye drops', 'Daily • 1 drop', 'Active'],
              ['Oxygen therapy', 'As needed', 'Review with MD'],
              ['Pain management regimen', 'Per hospice policy', 'Reviewed'],
            ].map(([name, dose, status]) => (
              <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8, backgroundColor: mode === 'light' ? '#f8fbfb' : '#111827' }}>
                <div>
                  <div style={{ color: colors.text, fontWeight: 700, fontSize: 12.5 }}>{name}</div>
                  <div style={{ color: colors.muted, fontSize: 10.5 }}>{dose}</div>
                </div>
                <span style={{ ...badge('teal', 'status'), fontSize: 8.5 }}>{status}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>DME / supplies</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['Hospital bed', 'Delivered', 'Ready'],
              ['Oxygen concentrator', 'Ordered', 'Pending'],
              ['Incontinence supplies', 'On hand', 'Available'],
              ['Wheelchair', 'Reviewed', 'Ready'],
            ].map(([item, status, state]) => (
              <div key={item} style={{ borderBottom: `1px solid ${colors.border}`, paddingBottom: 5 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ color: colors.text, fontWeight: 700, fontSize: 12.5 }}>{item}</div>
                  <span style={{ ...badge(status === 'Delivered' ? 'green' : status === 'Ordered' ? 'amber' : 'teal', 'status'), fontSize: 8.5 }}>{status}</span>
                </div>
                <div style={{ color: colors.muted, fontSize: 10.5, marginTop: 3 }}>{state}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const IDGBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>IDG meeting summary</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['RN', 'Symptom burden and care plan status reviewed'],
              ['MSW', 'Family support and resource concerns addressed'],
              ['SC', 'Spiritual care plan discussed and updated'],
              ['Chaplain / volunteer', 'Community support and bereavement planning addressed'],
            ].map(([disc, note]) => (
              <div key={disc} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8 }}>
                <div style={{ color: colors.text, fontWeight: 700, marginBottom: 4, fontSize: 12.5 }}>{disc}</div>
                <div style={{ color: colors.muted, fontSize: 11.5 }}>{note}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Care coordination actions</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              'Follow-up with family on medication review.',
              'Confirm aide hours and home support schedule.',
              'Review psychosocial risk factors with MSW.',
              'Coordinate with physician on PRN medication plan.',
            ].map((item) => (
              <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', color: colors.text, fontSize: 12.5 }}>
                <span style={{ width: 8, height: 8, borderRadius: 999, backgroundColor: colors.accent, display: 'inline-block', marginTop: 6 }} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const POCBoard = () => (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
        <div style={{ ...boardCard }}>
          <div style={boardHeader}>Plan of care goals</div>
          <div style={{ display: 'grid', gap: 7 }}>
            {[
              ['Symptom management', 'Maintain comfort and minimize pain burden through medication management and RN follow-up.'],
              ['Psychosocial support', 'Support caregiver coping and ensure access to psychosocial interventions and resources.'],
              ['Spiritual care', 'Honor faith preferences and provide chaplaincy support aligned with patient/family goals.'],
            ].map(([goal, detail]) => (
              <div key={goal} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, padding: 8 }}>
                <div style={{ color: colors.text, fontWeight: 700, marginBottom: 4, fontSize: 12.5 }}>{goal}</div>
                <div style={{ color: colors.muted, fontSize: 11.5, lineHeight: 1.5 }}>{detail}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...boardCard }}>
          <div style={boardHeader}>POC status</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {[
              ['Status', 'Active'],
              ['Updated', '08/15/2026'],
              ['Reviewed by', 'RN Case Manager'],
              ['Next review', '09/05/2026'],
            ].map(([label, value]) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: `1px solid ${colors.border}`, paddingBottom: 5 }}>
                <span style={{ color: colors.muted, fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.8 }}>{label}</span>
                <span style={{ color: colors.text, fontSize: 12.5, fontWeight: 600 }}>{value}</span>
              </div>
            ))}
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
        return <PatientFacesheet />;
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
      case 'assessments':
      case 'nursing-assessment':
      case 'spiritual-assessment':
      case 'psychosocial-assessment':
      case 'assessment-history':
        return <AssessmentBoard />;
      case 'visit-notes':
      case 'add-visit':
      case 'my-visit-notes':
      case 'visit-history':
        return <VisitNotesBoard />;
      case 'tx-meds':
      case 'add-order':
      case 'current-meds':
      case 'med-history':
      case 'dme-orders':
        return <TxMedsBoard />;
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
      <PatientChartSidebar activeSection={activeSection} onNavigate={setActiveSection} patient={patient} />
      <div style={{ flex: 1, minWidth: 0, width: '100%', height: '100vh', minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}>
        {renderContent()}
      </div>
    </div>
  );
};

export default PatientChart;
