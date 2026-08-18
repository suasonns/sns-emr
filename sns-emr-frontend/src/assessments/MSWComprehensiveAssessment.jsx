import React, { useCallback, useState } from "react";
import AssessmentTypeToggle from "../components/AssessmentTypeToggle";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";

// Default (dark) palette — module-level helpers below use this as a
// fallback shape; the main component recomputes theme-aware colors
// from useThemeMode()/getChartColors() and shadows these per render.
const COLORS = {
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

const inputStyle = {
  backgroundColor: COLORS.bg, border: `1px solid ${COLORS.border}`,
  borderRadius: 6, padding: '8px 12px', color: COLORS.white,
  fontSize: 13, fontFamily: "'Inter', sans-serif", outline: 'none', width: '100%',
  boxSizing: 'border-box',
};
const selectStyle = { ...inputStyle, cursor: 'pointer', appearance: 'none' };
const textareaStyle = { ...inputStyle, resize: 'vertical', minHeight: 80, lineHeight: '1.5' };

const cardStyle = {
  backgroundColor: COLORS.card, borderRadius: 8, padding: 24,
  borderLeft: `4px solid ${COLORS.teal}`, marginBottom: 20,
};

const Badge = ({ children, variant = 'teal' }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  const map = {
    green: { bg: COLORS.greenBg, color: COLORS.green },
    red: { bg: COLORS.redBg, color: COLORS.red },
    amber: { bg: COLORS.amberBg, color: COLORS.amber },
    teal: { bg: COLORS.tealBg, color: COLORS.teal },
  };
  const v = map[variant] || map.teal;
  return <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600, backgroundColor: v.bg, color: v.color }}>{children}</span>;
};

const Field = ({ label, children, style: extra }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  return (
    <div style={{ marginBottom: 12, ...extra }}>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: COLORS.label, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>{label}</label>
      {children}
    </div>
  );
};

const SectionCard = ({ number, title, subtitle, onAddIssue, children }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  const cardStyle = {
    backgroundColor: COLORS.card, borderRadius: 8, padding: 24,
    borderLeft: `4px solid ${COLORS.teal}`, marginBottom: 20,
  };
  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ color: COLORS.white, fontSize: 15, fontWeight: 700 }}>{number}. {title}</div>
          {subtitle && <div style={{ color: COLORS.label, fontSize: 12, marginTop: 2 }}>{subtitle}</div>}
        </div>
        <button onClick={onAddIssue} style={{ background: 'none', border: `1px solid ${COLORS.border}`, borderRadius: 6, color: COLORS.teal, padding: '4px 12px', cursor: 'pointer', fontSize: 11, fontWeight: 600 }}>+ Add Issue</button>
      </div>
      {children}
    </div>
  );
};

const CheckboxGroup = ({ options, selected, onChange, columns = 2 }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns}, 1fr)`, gap: '6px 16px' }}>
      {options.map((opt) => (
        <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, color: COLORS.text }}>
          <div style={{
            width: 18, height: 18, borderRadius: 4, flexShrink: 0,
            border: selected.includes(opt) ? 'none' : `2px solid ${COLORS.border}`,
            backgroundColor: selected.includes(opt) ? COLORS.teal : 'transparent',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {selected.includes(opt) && <span style={{ color: COLORS.white, fontSize: 10, fontWeight: 700 }}>✓</span>}
          </div>
          {opt}
        </label>
      ))}
    </div>
  );
};

const RadioGroup = ({ options, value, onChange, inline = true }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  return (
    <div style={{ display: 'flex', flexDirection: inline ? 'row' : 'column', gap: inline ? 16 : 6, flexWrap: 'wrap' }}>
      {options.map((opt) => (
        <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 12, color: COLORS.text }}>
          <div style={{
            width: 16, height: 16, borderRadius: 8, flexShrink: 0,
            border: `2px solid ${value === opt ? COLORS.teal : COLORS.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {value === opt && <div style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: COLORS.teal }} />}
          </div>
          {opt}
        </label>
      ))}
    </div>
  );
};

// All fields start blank/unanswered — this is a live clinical form, not sample data.
const INITIAL_FORM = {
  visitInfo: { visitType: '', visitSchedule: '', visitDate: '', timeIn: '', timeOut: '' },
  pain: { uncomfortable: '', painLevel: '', painTool: '', mentalStatus: '', historian: '', historianOtherName: '', historianOtherRelation: '', narrative: '' },
  psychosocial: {
    maritalStatus: '', childrenUnder21: '', childrenInHome: '',
    familyPcgName: '', familyPcgRelation: '', hiredDuration: '',
    patientLives: '', safetyAssessmentNeeded: false, livingArrangement: '',
    familyCommunication: '', familyRelation: '', familyResponseToIllness: '',
    socialInteraction: '', supportSystem: '',
    supportPersons: [{ name: '', phone: '', for: '' }, { name: '', phone: '', for: '' }],
    communitySupport: '', narrative: '',
  },
  patientDistress: {
    patientResponse: [],
    patientConcerns: [],
    iadl: {
      phoneAccess: '', phoneAlternative: '',
      shopping: '', shopsFor: '',
      mealPrep: '', prepsFor: '',
      housework: '', houseworkFor: '',
      finances: '', financesFor: '',
    },
    anxietyRating: '', anxietyRatedBy: '',
    distressRating: '', distressRatedBy: '',
    narrative: '',
  },
  familyDistress: {
    familyResponse: [],
    abilityToProvideCare: '', willingnessToProvideCare: '',
    familyCrisis: [],
    pcgAnxietyRating: '', pcgAnxietyRatedBy: '',
    narrative: '',
  },
  financialLegal: {
    allNeedsMet: '', isVeteran: '',
    patientLacks: [],
    needsAssistance: [],
    patientCarePaidBy: '',
    livingWill: '', livingWillCopy: '', livingWillHelp: '',
    healthPOA: '', healthPOACopy: '', healthPOAHelp: '',
    healthProxy: '', healthProxyCopy: '', healthProxyHelp: '',
    burialPlans: '', burialHelp: '',
    mortuaryName: '', mortuaryPhone: '',
    mortuaryAddress: '', mortuaryCity: '', mortuaryStateZip: '',
    narrative: '',
  },
  referrals: {
    communityProgram: '', communityAccepted: '',
    therapy: [], volunteerServices: [], communitySupport: '', other: '',
  },
  narrativeFinal: {
    careProvided: [],
    narrative: '',
  },
  signature: {
    staffTitle: '', clinicianName: '',
    signatureDate: '', assessmentComplete: false,
    pcgAcknowledge: false, pcgSignatureName: '', pcgSignatureRelation: '', pcgSignatureDate: '',
    qaReviewBy: '', qaReviewDate: '', qaApproved: false,
  },
};

const MSWComprehensiveAssessment = ({ patientId = "", patient }) => {
  const { mode } = useThemeMode();
  const COLORS = getChartColors(mode);
  const inputStyle = {
    backgroundColor: COLORS.bg, border: `1px solid ${COLORS.border}`,
    borderRadius: 6, padding: '8px 12px', color: COLORS.white,
    fontSize: 13, fontFamily: "'Inter', sans-serif", outline: 'none', width: '100%',
    boxSizing: 'border-box',
  };
  const selectStyle = { ...inputStyle, cursor: 'pointer', appearance: 'none' };
  const textareaStyle = { ...inputStyle, resize: 'vertical', minHeight: 80, lineHeight: '1.5' };
  const cardStyle = {
    backgroundColor: COLORS.card, borderRadius: 8, padding: 24,
    borderLeft: `4px solid ${COLORS.teal}`, marginBottom: 20,
  };
  const [form, setForm] = useState(INITIAL_FORM);
  const [assessmentType, setAssessmentType] = useState('update');
  const [saving, setSaving] = useState(false);
  const [locked, setLocked] = useState(false);

  const pat = patient || {
    firstName: '—', lastName: '—', mrn: '—',
    dob: '—', age: '—', sex: '—', payer: '—',
    status: '—', socDate: '—',
    benefitPeriod: '—',
    primaryDx: '—',
  };

  const updateField = useCallback((section, key, value) => {
    setForm((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }, []);

  const updateNested = useCallback((section, parentKey, key, value) => {
    setForm((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [parentKey]: { ...prev[section][parentKey], [key]: value },
      },
    }));
  }, []);

  const reasonForVisitLabel = assessmentType === 'recert' ? 'Recertification Assessment' : 'Update Assessment';

  return (
    <div style={{ flex: 1, backgroundColor: COLORS.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      {/* Breadcrumb */}
      <div style={{ color: COLORS.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{pat.firstName} {pat.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>Clinical Assessments</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: COLORS.white }}>Psychosocial Assessment</span>
      </div>

      {/* Patient Banner */}
      <div style={{ backgroundColor: COLORS.card, borderRadius: 8, padding: '16px 24px', marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ color: COLORS.white, fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{pat.lastName}, {pat.firstName}</div>
            <div style={{ color: COLORS.label, fontSize: 13 }}>MRN: {pat.mrn} | DOB: {pat.dob} ({pat.age}y) | Sex: {pat.sex} | Payer: {pat.payer}</div>
          </div>
          <Badge variant="green">{pat.status}</Badge>
        </div>
        <div style={{ display: 'flex', gap: 24, marginTop: 12 }}>
          <div><span style={{ color: COLORS.label, fontSize: 10, textTransform: 'uppercase', display: 'block' }}>SOC DATE</span><span style={{ color: COLORS.white, fontSize: 13, fontWeight: 600 }}>{pat.socDate}</span></div>
          <div><span style={{ color: COLORS.label, fontSize: 10, textTransform: 'uppercase', display: 'block' }}>BENEFIT PERIOD</span><span style={{ color: COLORS.white, fontSize: 13, fontWeight: 600 }}>{pat.benefitPeriod}</span></div>
          <div><span style={{ color: COLORS.label, fontSize: 10, textTransform: 'uppercase', display: 'block' }}>PRIMARY DX</span><span style={{ color: COLORS.white, fontSize: 13, fontWeight: 600 }}>{pat.primaryDx}</span></div>
        </div>
      </div>

      {/* Header Bar */}
      <div style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ color: COLORS.white, fontSize: 18, fontWeight: 700 }}>Comprehensive Psychosocial Assessment</div>
          <div style={{ color: COLORS.label, fontSize: 12 }}>Psychosocial support, caregiver burden, resource barriers, and intervention planning</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <AssessmentTypeToggle value={assessmentType} onChange={setAssessmentType} />
          <div style={{ textAlign: 'right' }}>
            <Badge variant={locked ? 'green' : 'amber'}>{locked ? 'COMPLETED' : 'IN PROGRESS'}</Badge>
          </div>
        </div>
      </div>

      {/* Upload Bar */}
      <div style={{ backgroundColor: COLORS.card, borderRadius: 8, padding: '10px 20px', marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: COLORS.text, fontSize: 12 }}>📎 Upload Documents (0)</span>
        <span style={{ color: COLORS.teal, fontSize: 12, cursor: 'pointer' }}>Show Details...</span>
      </div>

      {/* Visit Info */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', gap: 24, marginBottom: 12 }}>
          <Field label="Entered By" style={{ flex: 1 }}><input value="" readOnly style={inputStyle} /></Field>
          <Field label="Staff Assigned" style={{ flex: 1 }}><input value="" readOnly style={inputStyle} /></Field>
          <Field label="Discipline" style={{ flex: 0.5 }}><input value="MSW" readOnly style={inputStyle} /></Field>
          <Field label="Care Level" style={{ flex: 0.5 }}><input value="" readOnly style={inputStyle} /></Field>
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
          <Field label="Type of Visit"><RadioGroup options={['In-Person', 'Telephone', 'Video']} value={form.visitInfo.visitType} onChange={(v) => updateField('visitInfo', 'visitType', v)} /></Field>
          <Field label="Visit"><RadioGroup options={['Scheduled', 'Unscheduled']} value={form.visitInfo.visitSchedule} onChange={(v) => updateField('visitInfo', 'visitSchedule', v)} /></Field>
        </div>
        <Field label="Reason for Visit"><input value={reasonForVisitLabel} readOnly style={{ ...inputStyle, backgroundColor: COLORS.card, cursor: 'default' }} /></Field>
        <div style={{ display: 'flex', gap: 16 }}>
          <Field label="Visit Date" style={{ flex: 1 }}><input value={form.visitInfo.visitDate} onChange={(e) => updateField('visitInfo', 'visitDate', e.target.value)} style={inputStyle} /></Field>
          <Field label="Time In" style={{ flex: 1 }}><input value={form.visitInfo.timeIn} onChange={(e) => updateField('visitInfo', 'timeIn', e.target.value)} style={inputStyle} /></Field>
          <Field label="Time Out" style={{ flex: 1 }}><input value={form.visitInfo.timeOut} onChange={(e) => updateField('visitInfo', 'timeOut', e.target.value)} style={inputStyle} /></Field>
        </div>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* LEFT COLUMN */}
        <div>
          {/* Section 1: Pain */}
          <SectionCard number={1} title="Pain" subtitle="Patient response to illness">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Are you uncomfortable because of pain?">
                <select value={form.pain.uncomfortable} onChange={(e) => updateField('pain', 'uncomfortable', e.target.value)} style={selectStyle}>
                  <option value="">Select</option><option value="No">No</option><option value="Yes">Yes</option>
                </select>
              </Field>
              <Field label="If yes, pain level (0-10)">
                <input type="number" min="0" max="10" value={form.pain.painLevel} onChange={(e) => updateField('pain', 'painLevel', e.target.value)} style={inputStyle} />
              </Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Observed patient mental status">
                <select value={form.pain.mentalStatus} onChange={(e) => updateField('pain', 'mentalStatus', e.target.value)} style={selectStyle}>
                  <option value="">Select</option>
                  {['Awake', 'Confused', 'Withdrawn', 'Overwhelmed', 'Lethargic', 'Comatose'].map((o) => <option key={o}>{o}</option>)}
                </select>
              </Field>
              <Field label="Historian / primary support">
                <select value={form.pain.historian} onChange={(e) => updateField('pain', 'historian', e.target.value)} style={selectStyle}>
                  <option value="">Select</option>
                  {['PCG', 'Patient', 'Family', 'Other'].map((o) => <option key={o}>{o}</option>)}
                </select>
              </Field>
            </div>
            <Field label="Narrative">
              <textarea value={form.pain.narrative} onChange={(e) => updateField('pain', 'narrative', e.target.value)} style={textareaStyle} placeholder="Social worker narrative and support context." />
            </Field>
          </SectionCard>

          {/* Section 2: Psychosocial Circumstances */}
          <SectionCard number={2} title="Psychosocial Circumstances" subtitle="Family, living arrangement, and support systems">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Marital Status"><select value={form.psychosocial.maritalStatus} onChange={(e) => updateField('psychosocial', 'maritalStatus', e.target.value)} style={selectStyle}><option value="">Select</option>{['Single', 'Married', 'Widowed', 'Divorced', 'Separated'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="# Children under 21"><input value={form.psychosocial.childrenUnder21} onChange={(e) => updateField('psychosocial', 'childrenUnder21', e.target.value)} style={inputStyle} /></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Family / PCG Name"><input value={form.psychosocial.familyPcgName} onChange={(e) => updateField('psychosocial', 'familyPcgName', e.target.value)} style={inputStyle} /></Field>
              <Field label="Relation"><input value={form.psychosocial.familyPcgRelation} onChange={(e) => updateField('psychosocial', 'familyPcgRelation', e.target.value)} style={inputStyle} /></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Patient lives"><select value={form.psychosocial.patientLives} onChange={(e) => updateField('psychosocial', 'patientLives', e.target.value)} style={selectStyle}><option value="">Select</option>{['Alone', 'With Family', 'in ALF', 'in SNF', 'Group Home', 'Other'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Living arrangement"><select value={form.psychosocial.livingArrangement} onChange={(e) => updateField('psychosocial', 'livingArrangement', e.target.value)} style={selectStyle}><option value="">Select</option>{['Satisfactory', 'Unsatisfactory', 'Other'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Family communication"><select value={form.psychosocial.familyCommunication} onChange={(e) => updateField('psychosocial', 'familyCommunication', e.target.value)} style={selectStyle}><option value="">Select</option>{['Good', 'Fair', 'Poor', 'Limited'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Family relation"><select value={form.psychosocial.familyRelation} onChange={(e) => updateField('psychosocial', 'familyRelation', e.target.value)} style={selectStyle}><option value="">Select</option>{['Good', 'Fair', 'Poor', 'Strained'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Family response to illness"><select value={form.psychosocial.familyResponseToIllness} onChange={(e) => updateField('psychosocial', 'familyResponseToIllness', e.target.value)} style={selectStyle}><option value="">Select</option>{['Supportive', 'Accepting', 'Denial', 'Overwhelmed', 'Other'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Social interaction"><select value={form.psychosocial.socialInteraction} onChange={(e) => updateField('psychosocial', 'socialInteraction', e.target.value)} style={selectStyle}><option value="">Select</option>{['Satisfactory', 'Limited', 'Isolated', 'Other'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <Field label="Support system"><select value={form.psychosocial.supportSystem} onChange={(e) => updateField('psychosocial', 'supportSystem', e.target.value)} style={selectStyle}><option value="">Select</option>{['Family', 'Friends', 'Community', 'Church', 'None', 'Other'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            {/* Support Persons */}
            <div style={{ marginTop: 8, marginBottom: 8 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Other Support Persons</span>
            </div>
            {form.psychosocial.supportPersons.map((sp, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                <input placeholder="Name" value={sp.name} onChange={(e) => { const arr = [...form.psychosocial.supportPersons]; arr[i] = { ...arr[i], name: e.target.value }; updateField('psychosocial', 'supportPersons', arr); }} style={{ ...inputStyle, flex: 1 }} />
                <input placeholder="Phone" value={sp.phone} onChange={(e) => { const arr = [...form.psychosocial.supportPersons]; arr[i] = { ...arr[i], phone: e.target.value }; updateField('psychosocial', 'supportPersons', arr); }} style={{ ...inputStyle, flex: 1 }} />
              </div>
            ))}
            <Field label="Narrative"><textarea value={form.psychosocial.narrative} onChange={(e) => updateField('psychosocial', 'narrative', e.target.value)} style={textareaStyle} placeholder="Living arrangement, caregiver context, and support notes..." /></Field>
          </SectionCard>

          {/* Section 3: Patient Distress */}
          <SectionCard number={3} title="Patient — Psychosocial Distress/Concerns" subtitle="Select all that apply">
            <div style={{ marginBottom: 16 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>PATIENT RESPONSE TO ILLNESS</span>
              <CheckboxGroup options={['Cannot respond', 'Overwhelmed', 'Fearful', 'Unaware of condition', 'Accepting', 'Depressed', 'Sad', 'Guilt', 'Denial', 'Angry', 'Loss of worth', 'Other']} selected={form.patientDistress.patientResponse} onChange={(v) => updateField('patientDistress', 'patientResponse', v)} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>PATIENT CONCERNS</span>
              <CheckboxGroup options={['Responsibility for others', 'Finances', 'Lacks cognitive ability', 'Suicide risks', 'Inadequate food/supplies', 'Abuse/neglect', 'Substance/alcohol abuse', 'Transfer to another setting', 'Other']} selected={form.patientDistress.patientConcerns} onChange={(v) => updateField('patientDistress', 'patientConcerns', v)} />
            </div>
            {/* IADL Section */}
            <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16, marginBottom: 12 }}>
              <span style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>Instrumental Activities of Daily Living (IADL)</span>
              {[
                { q: 'Phone access & able to make calls?', key: 'phoneAccess', altKey: 'phoneAlternative', altLabel: 'Alternative communication' },
                { q: 'Goes out for shopping?', key: 'shopping', altKey: 'shopsFor', altLabel: 'Who shops?' },
                { q: 'Prepares own meals?', key: 'mealPrep', altKey: 'prepsFor', altLabel: 'Who prepares?' },
                { q: 'Does housework?', key: 'housework', altKey: 'houseworkFor', altLabel: 'Who does housework?' },
                { q: 'Manages own finances?', key: 'finances', altKey: 'financesFor', altLabel: 'Who manages?' },
              ].map((item) => (
                <div key={item.key} style={{ display: 'grid', gridTemplateColumns: '1fr 100px 1fr', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                  <span style={{ color: COLORS.text, fontSize: 12 }}>{item.q}</span>
                  <select value={form.patientDistress.iadl[item.key]} onChange={(e) => updateNested('patientDistress', 'iadl', item.key, e.target.value)} style={{ ...selectStyle, padding: '4px 8px', fontSize: 12 }}>
                    <option value="">—</option><option>Yes</option><option>No</option>
                  </select>
                  <input placeholder={item.altLabel} value={form.patientDistress.iadl[item.altKey]} onChange={(e) => updateNested('patientDistress', 'iadl', item.altKey, e.target.value)} style={{ ...inputStyle, padding: '4px 8px', fontSize: 12 }} />
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Patient Anxiety Rating"><select value={form.patientDistress.anxietyRating} onChange={(e) => updateField('patientDistress', 'anxietyRating', e.target.value)} style={selectStyle}><option value="">Select</option>{['None', 'Mild', 'Moderate', 'Severe'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Distress Rating"><select value={form.patientDistress.distressRating} onChange={(e) => updateField('patientDistress', 'distressRating', e.target.value)} style={selectStyle}><option value="">Select</option>{['None', 'Mild', 'Moderate', 'Severe'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <Field label="Narrative"><textarea value={form.patientDistress.narrative} onChange={(e) => updateField('patientDistress', 'narrative', e.target.value)} style={textareaStyle} placeholder="Patient distress observations..." /></Field>
          </SectionCard>
        </div>

        {/* RIGHT COLUMN */}
        <div>
          {/* Section 4: Family Distress */}
          <SectionCard number={4} title="Family — Psychosocial Distress/Concerns" subtitle="Family response, crisis, and anxiety">
            <div style={{ marginBottom: 16 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>FAMILY RESPONSE TO ILLNESS</span>
              <CheckboxGroup options={['Accepting', 'Depressed', 'Sad', 'Guilt', 'Denial', 'Angry', 'Fearful', 'Despair', 'Overwhelmed', 'Anticipatory grieving', 'Other']} selected={form.familyDistress.familyResponse} onChange={(v) => updateField('familyDistress', 'familyResponse', v)} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Ability to provide care"><select value={form.familyDistress.abilityToProvideCare} onChange={(e) => updateField('familyDistress', 'abilityToProvideCare', e.target.value)} style={selectStyle}><option value="">Select</option>{['Good', 'Fair', 'Poor', 'Unable'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Willingness to provide care"><select value={form.familyDistress.willingnessToProvideCare} onChange={(e) => updateField('familyDistress', 'willingnessToProvideCare', e.target.value)} style={selectStyle}><option value="">Select</option>{['Good', 'Fair', 'Poor', 'Unwilling'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <div style={{ marginBottom: 16 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>FAMILY CRISIS</span>
              <CheckboxGroup options={['None', 'Suicide risks', 'Inadequate food/supplies', 'Financial/legal crisis', 'Significant losses in recent past', 'Substance/alcohol abuse', 'Other']} selected={form.familyDistress.familyCrisis} onChange={(v) => updateField('familyDistress', 'familyCrisis', v)} />
            </div>
            <Field label="PCG / Family Anxiety Rating"><select value={form.familyDistress.pcgAnxietyRating} onChange={(e) => updateField('familyDistress', 'pcgAnxietyRating', e.target.value)} style={selectStyle}><option value="">Select</option>{['None', 'Mild', 'Moderate', 'Severe'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            <Field label="Narrative"><textarea value={form.familyDistress.narrative} onChange={(e) => updateField('familyDistress', 'narrative', e.target.value)} style={textareaStyle} placeholder="Family's response to patient's decline..." /></Field>
          </SectionCard>

          {/* Section 5: Financial/Legal */}
          <SectionCard number={5} title="Financial / Legal Needs" subtitle="Financial strain, advance directives, and mortuary">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="All needs met by patient/family?"><select value={form.financialLegal.allNeedsMet} onChange={(e) => updateField('financialLegal', 'allNeedsMet', e.target.value)} style={selectStyle}><option value="">Select</option><option>Yes</option><option>No</option></select></Field>
              <Field label="Is patient/spouse a veteran?"><select value={form.financialLegal.isVeteran} onChange={(e) => updateField('financialLegal', 'isVeteran', e.target.value)} style={selectStyle}><option value="">Select</option><option>No</option><option>Yes</option></select></Field>
            </div>
            {form.financialLegal.allNeedsMet === 'No' && (
              <>
                <div style={{ marginBottom: 12 }}>
                  <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>PATIENT LACKS</span>
                  <CheckboxGroup options={['Food', 'Utility', 'Clothing', 'Furniture', 'Med/supplies unrelated to illness']} selected={form.financialLegal.patientLacks} onChange={(v) => updateField('financialLegal', 'patientLacks', v)} columns={3} />
                </div>
                <div style={{ marginBottom: 12 }}>
                  <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>NEEDS ASSISTANCE WITH</span>
                  <CheckboxGroup options={['Meals on wheels', 'Food stamps', 'Other']} selected={form.financialLegal.needsAssistance} onChange={(v) => updateField('financialLegal', 'needsAssistance', v)} columns={3} />
                </div>
              </>
            )}
            {/* Advance Directives */}
            <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16, marginBottom: 12 }}>
              <span style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>Planning / Advance Directives</span>
              {[
                { label: 'Living Will', key: 'livingWill', copyKey: 'livingWillCopy', helpKey: 'livingWillHelp' },
                { label: 'Health POA', key: 'healthPOA', copyKey: 'healthPOACopy', helpKey: 'healthPOAHelp' },
                { label: 'Health Proxy', key: 'healthProxy', copyKey: 'healthProxyCopy', helpKey: 'healthProxyHelp' },
              ].map((item) => (
                <div key={item.key} style={{ display: 'grid', gridTemplateColumns: '1fr 80px 100px 80px', gap: 8, marginBottom: 6, alignItems: 'center' }}>
                  <span style={{ color: COLORS.text, fontSize: 12 }}>{item.label}</span>
                  <select value={form.financialLegal[item.key]} onChange={(e) => updateField('financialLegal', item.key, e.target.value)} style={{ ...selectStyle, padding: '4px 6px', fontSize: 11 }}><option value="">—</option>{['Yes', 'No', 'N/A'].map((o) => <option key={o}>{o}</option>)}</select>
                  <select value={form.financialLegal[item.copyKey]} onChange={(e) => updateField('financialLegal', item.copyKey, e.target.value)} style={{ ...selectStyle, padding: '4px 6px', fontSize: 10 }}><option value="">Copy: —</option>{['Yes', 'No', 'N/A'].map((o) => <option key={o} value={o}>Copy: {o}</option>)}</select>
                  <select value={form.financialLegal[item.helpKey]} onChange={(e) => updateField('financialLegal', item.helpKey, e.target.value)} style={{ ...selectStyle, padding: '4px 6px', fontSize: 10 }}><option value="">Help: —</option>{['Yes', 'No', 'N/A'].map((o) => <option key={o} value={o}>Help: {o}</option>)}</select>
                </div>
              ))}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 80px 180px', gap: 8, alignItems: 'center' }}>
                <span style={{ color: COLORS.text, fontSize: 12 }}>Burial Plans</span>
                <select value={form.financialLegal.burialPlans} onChange={(e) => updateField('financialLegal', 'burialPlans', e.target.value)} style={{ ...selectStyle, padding: '4px 6px', fontSize: 11 }}><option value="">—</option>{['Yes', 'No', 'N/A'].map((o) => <option key={o}>{o}</option>)}</select>
                <select value={form.financialLegal.burialHelp} onChange={(e) => updateField('financialLegal', 'burialHelp', e.target.value)} style={{ ...selectStyle, padding: '4px 6px', fontSize: 10 }}><option value="">Help: —</option>{['Yes', 'No', 'N/A'].map((o) => <option key={o} value={o}>Help: {o}</option>)}</select>
              </div>
            </div>
            {/* Mortuary Info */}
            <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16, marginBottom: 12 }}>
              <span style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>Mortuary Information</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Field label="Mortuary Name"><input value={form.financialLegal.mortuaryName} onChange={(e) => updateField('financialLegal', 'mortuaryName', e.target.value)} style={inputStyle} /></Field>
                <Field label="Phone"><input value={form.financialLegal.mortuaryPhone} onChange={(e) => updateField('financialLegal', 'mortuaryPhone', e.target.value)} style={inputStyle} /></Field>
              </div>
              <Field label="Address"><input value={form.financialLegal.mortuaryAddress} onChange={(e) => updateField('financialLegal', 'mortuaryAddress', e.target.value)} style={inputStyle} /></Field>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Field label="City"><input value={form.financialLegal.mortuaryCity} onChange={(e) => updateField('financialLegal', 'mortuaryCity', e.target.value)} style={inputStyle} /></Field>
                <Field label="State-Zip"><input value={form.financialLegal.mortuaryStateZip} onChange={(e) => updateField('financialLegal', 'mortuaryStateZip', e.target.value)} style={inputStyle} /></Field>
              </div>
            </div>
            <Field label="Narrative"><textarea value={form.financialLegal.narrative} onChange={(e) => updateField('financialLegal', 'narrative', e.target.value)} style={textareaStyle} placeholder="Financial/legal planning notes..." /></Field>
          </SectionCard>

          {/* Section 6: Referrals */}
          <SectionCard number={6} title="Referrals" subtitle="Community programs and support services">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Need for community program referral?"><select value={form.referrals.communityProgram} onChange={(e) => updateField('referrals', 'communityProgram', e.target.value)} style={selectStyle}><option value="">Select</option>{['N/A', 'Yes', 'No'].map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Community referral accepted?"><select value={form.referrals.communityAccepted} onChange={(e) => updateField('referrals', 'communityAccepted', e.target.value)} style={selectStyle}><option value="">Select</option>{['N/A', 'Yes', 'No'].map((o) => <option key={o}>{o}</option>)}</select></Field>
            </div>
            <div style={{ marginBottom: 12 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>THERAPY</span>
              <CheckboxGroup options={['Music', 'Art', 'Pet', 'Massage']} selected={form.referrals.therapy} onChange={(v) => updateField('referrals', 'therapy', v)} columns={4} />
            </div>
            <div style={{ marginBottom: 12 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>VOLUNTEER SERVICES</span>
              <CheckboxGroup options={['Companionship', 'Errands', 'Respite', 'Light housekeeping/meals']} selected={form.referrals.volunteerServices} onChange={(v) => updateField('referrals', 'volunteerServices', v)} columns={2} />
            </div>
          </SectionCard>

          {/* Section 7: Narrative */}
          <SectionCard number={7} title="Narrative (Include care provided items)" subtitle="Visit summary and interventions">
            <div style={{ marginBottom: 12 }}>
              <span style={{ color: COLORS.label, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>CARE PROVIDED</span>
              <CheckboxGroup options={['Listening/Emotional support', 'Knowledge related needs', 'Funeral planning', 'Motivational interviewing', 'Cognitive behavioral therapy', 'Positive reinforcement', 'Other']} selected={form.narrativeFinal.careProvided} onChange={(v) => updateField('narrativeFinal', 'careProvided', v)} />
            </div>
            <Field label="Narrative"><textarea value={form.narrativeFinal.narrative} onChange={(e) => updateField('narrativeFinal', 'narrative', e.target.value)} style={{ ...textareaStyle, minHeight: 160 }} placeholder="Visit summary and interventions..." /></Field>
          </SectionCard>

          {/* Signature */}
          <SectionCard number={8} title="Signature" subtitle="Complete and sign">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Staff Title"><input value={form.signature.staffTitle} onChange={(e) => updateField('signature', 'staffTitle', e.target.value)} style={inputStyle} /></Field>
              <Field label="Clinician Name"><input value={form.signature.clinicianName} onChange={(e) => updateField('signature', 'clinicianName', e.target.value)} style={inputStyle} /></Field>
            </div>
            <Field label="Signature Date"><input type="text" value={form.signature.signatureDate} onChange={(e) => updateField('signature', 'signatureDate', e.target.value)} style={inputStyle} /></Field>
            {/* PCG Acknowledgement */}
            <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16, marginTop: 12, marginBottom: 12 }}>
              <span style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>PCG / Patient Acknowledgement</span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginBottom: 8 }}>
                <div style={{ width: 18, height: 18, borderRadius: 4, border: form.signature.pcgAcknowledge ? 'none' : `2px solid ${COLORS.border}`, backgroundColor: form.signature.pcgAcknowledge ? COLORS.teal : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => updateField('signature', 'pcgAcknowledge', !form.signature.pcgAcknowledge)}>
                  {form.signature.pcgAcknowledge && <span style={{ color: COLORS.white, fontSize: 10, fontWeight: 700 }}>✓</span>}
                </div>
                <span style={{ color: COLORS.text, fontSize: 12 }}>Signature of Patient / PCG to acknowledge visit</span>
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Field label="Name"><input value={form.signature.pcgSignatureName} onChange={(e) => updateField('signature', 'pcgSignatureName', e.target.value)} style={inputStyle} /></Field>
                <Field label="Relationship"><input value={form.signature.pcgSignatureRelation} onChange={(e) => updateField('signature', 'pcgSignatureRelation', e.target.value)} style={inputStyle} /></Field>
              </div>
            </div>
            {/* QA Review */}
            <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16 }}>
              <span style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>QA Review</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Field label="Reviewed By"><input value={form.signature.qaReviewBy} onChange={(e) => updateField('signature', 'qaReviewBy', e.target.value)} style={inputStyle} placeholder="MSW Supervisor" /></Field>
                <Field label="Review Date"><input value={form.signature.qaReviewDate} onChange={(e) => updateField('signature', 'qaReviewDate', e.target.value)} style={inputStyle} placeholder="mm/dd/yyyy" /></Field>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginTop: 8 }}>
                <div style={{ width: 18, height: 18, borderRadius: 4, border: form.signature.qaApproved ? 'none' : `2px solid ${COLORS.border}`, backgroundColor: form.signature.qaApproved ? COLORS.green : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => updateField('signature', 'qaApproved', !form.signature.qaApproved)}>
                  {form.signature.qaApproved && <span style={{ color: COLORS.white, fontSize: 10, fontWeight: 700 }}>✓</span>}
                </div>
                <span style={{ color: COLORS.text, fontSize: 12 }}>QA Review Approved</span>
              </label>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <div style={{ width: 18, height: 18, borderRadius: 4, border: form.signature.assessmentComplete ? 'none' : `2px solid ${COLORS.border}`, backgroundColor: form.signature.assessmentComplete ? COLORS.teal : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => updateField('signature', 'assessmentComplete', !form.signature.assessmentComplete)}>
                  {form.signature.assessmentComplete && <span style={{ color: COLORS.white, fontSize: 10, fontWeight: 700 }}>✓</span>}
                </div>
                <span style={{ color: COLORS.text, fontSize: 12 }}>Assessment complete</span>
              </label>
              <button onClick={() => setLocked(true)} disabled={locked} style={{ padding: '6px 16px', backgroundColor: locked ? COLORS.card : COLORS.red, color: COLORS.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: locked ? 'default' : 'pointer', opacity: locked ? 0.5 : 1 }}>{locked ? 'Locked' : 'Lock Assessment'}</button>
            </div>
          </SectionCard>
        </div>
      </div>

      {/* Footer Status + Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 24, paddingTop: 16, borderTop: `1px solid ${COLORS.border}` }}>
        <div style={{ color: COLORS.label, fontSize: 12, fontWeight: 600 }}>
          {locked ? 'LOCKED' : 'IN PROGRESS'} · Documenting as: {reasonForVisitLabel}
        </div>
        <div>
          <button onClick={() => setSaving(true)} style={{ padding: '10px 24px', backgroundColor: COLORS.teal, color: COLORS.white, border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: "'Inter', sans-serif" }}>
            {saving ? 'Saving...' : 'Save Assessment'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MSWComprehensiveAssessment;
