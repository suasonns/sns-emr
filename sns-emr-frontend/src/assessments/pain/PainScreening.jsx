import React, { useState } from 'react';
import NumericPainScale from './NumericPainScale';
import PAINADScale from './PAINADScale';
import FLACCScale from './FLACCScale';

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

const cardStyle = {
  backgroundColor: COLORS.card,
  borderRadius: 8,
  padding: 24,
  borderLeft: `4px solid ${COLORS.teal}`,
  marginBottom: 20,
};

const radioGroupStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  marginTop: 8,
};

const RadioOption = ({ name, value, selected, onChange, label }) => (
  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: COLORS.text }}>
    <div style={{
      width: 18, height: 18, borderRadius: 9, flexShrink: 0,
      border: `2px solid ${selected === value ? COLORS.teal : COLORS.border}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {selected === value && <div style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.teal }} />}
    </div>
    <span>{label}</span>
  </label>
);

const Badge = ({ children, variant = 'teal' }) => {
  const map = {
    green: { bg: COLORS.greenBg, color: COLORS.green },
    red: { bg: COLORS.redBg, color: COLORS.red },
    amber: { bg: COLORS.amberBg, color: COLORS.amber },
    teal: { bg: COLORS.tealBg, color: COLORS.teal },
  };
  const v = map[variant] || map.teal;
  return <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600, backgroundColor: v.bg, color: v.color }}>{children}</span>;
};

const PainScreening = ({ patient, patientType = 'adult' }) => {
  const [canVerbalize, setCanVerbalize] = useState('');
  const [isUncomfortable, setIsUncomfortable] = useState('');
  const [neuropathicPain, setNeuropathicPain] = useState('');
  const [activeScale, setActiveScale] = useState(null);

  const pat = patient || {
    firstName: 'LOREN B', lastName: 'SHIELDS', mrn: '054/782',
    dob: '03/15/1948', age: 78, sex: 'M', payer: 'Medicare',
    status: 'ACTIVE', socDate: '01/15/2026',
    benefitPeriod: '01/15/2026 – 07/14/2026',
    primaryDx: 'Senile degeneration of brain (G31.1)',
  };

  const handleVerbalizeChange = (val) => {
    setCanVerbalize(val);
    setActiveScale(null);
    if (val === 'no') {
      if (patientType === 'pediatric') {
        setActiveScale('flacc');
      } else {
        setActiveScale('painad');
      }
    }
  };

  const handleUncomfortableChange = (val) => {
    setIsUncomfortable(val);
    if (val === 'yes' && (canVerbalize === 'yes_reliably' || canVerbalize === 'sometimes')) {
      setActiveScale('numeric');
    } else if (val === 'no') {
      setActiveScale(null);
    }
  };

  const getScaleRecommendation = () => {
    if (canVerbalize === 'no') {
      return patientType === 'pediatric'
        ? { scale: 'flacc', label: 'FLACC Scale recommended (non-verbal patient, pediatric)', variant: 'amber' }
        : { scale: 'painad', label: 'PAINAD Scale recommended (non-verbal patient, geriatric)', variant: 'amber' };
    }
    if ((canVerbalize === 'yes_reliably' || canVerbalize === 'sometimes') && isUncomfortable === 'yes') {
      return { scale: 'numeric', label: 'Numeric Pain Rating Scale (0-10) recommended', variant: 'green' };
    }
    if (isUncomfortable === 'no') {
      return { scale: null, label: 'Patient reports no pain — document and reassess', variant: 'green' };
    }
    return null;
  };

  const recommendation = getScaleRecommendation();

  return (
    <div style={{ flex: 1, backgroundColor: COLORS.bg, padding: 24, overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      {/* Breadcrumb */}
      <div style={{ color: COLORS.label, fontSize: 13, marginBottom: 16 }}>
        <span>Patient List</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>{pat.firstName} {pat.lastName}</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span>Clinical Assessments</span><span style={{ margin: '0 8px' }}>&gt;</span>
        <span style={{ color: COLORS.white }}>Pain Assessment</span>
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

      {/* Header */}
      <div style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px' }}>
        <div>
          <div style={{ color: COLORS.white, fontSize: 18, fontWeight: 700 }}>Pain Screening & Assessment</div>
          <div style={{ color: COLORS.label, fontSize: 12 }}>HOPE J0900 / J0915 — Pain verbalization screening and scale selection</div>
        </div>
        <Badge variant="teal">HOPE ITEM</Badge>
      </div>

      {/* Pain Screening Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Left: Screening Questions */}
        <div>
          {/* J0900 — Can the patient verbalize pain? */}
          <div style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 700 }}>Can the patient verbalize pain?</div>
              <Badge variant="teal">HOPE J0900</Badge>
            </div>
            <div style={radioGroupStyle}>
              <RadioOption name="verbalize" value="no" selected={canVerbalize} onChange={() => handleVerbalizeChange('no')} label="No" />
              <RadioOption name="verbalize" value="yes_reliably" selected={canVerbalize} onChange={() => handleVerbalizeChange('yes_reliably')} label="Yes, reliably" />
              <RadioOption name="verbalize" value="sometimes" selected={canVerbalize} onChange={() => handleVerbalizeChange('sometimes')} label="Sometimes" />
              <RadioOption name="verbalize" value="unable" selected={canVerbalize} onChange={() => handleVerbalizeChange('unable')} label="Unable to determine" />
            </div>
          </div>

          {/* J0915 — Is the patient uncomfortable? (only if can verbalize) */}
          {(canVerbalize === 'yes_reliably' || canVerbalize === 'sometimes') && (
            <div style={cardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 700 }}>Is the patient uncomfortable because of pain?</div>
                <Badge variant="teal">HOPE J0915</Badge>
              </div>
              <div style={radioGroupStyle}>
                <RadioOption name="uncomfortable" value="no" selected={isUncomfortable} onChange={() => handleUncomfortableChange('no')} label="No" />
                <RadioOption name="uncomfortable" value="yes" selected={isUncomfortable} onChange={() => handleUncomfortableChange('yes')} label="Yes" />
                <RadioOption name="uncomfortable" value="unable" selected={isUncomfortable} onChange={() => handleUncomfortableChange('unable')} label="Unable to determine" />
              </div>
            </div>
          )}

          {/* Neuropathic Pain */}
          <div style={cardStyle}>
            <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Neuropathic pain present?</div>
            <div style={{ display: 'flex', gap: 16 }}>
              <RadioOption name="neuropathic" value="no" selected={neuropathicPain} onChange={() => setNeuropathicPain('no')} label="No" />
              <RadioOption name="neuropathic" value="yes" selected={neuropathicPain} onChange={() => setNeuropathicPain('yes')} label="Yes" />
            </div>
            {neuropathicPain === 'yes' && (
              <div style={{ marginTop: 12, padding: '8px 12px', backgroundColor: COLORS.amberBg, borderRadius: 6, border: `1px solid ${COLORS.amber}30` }}>
                <span style={{ color: COLORS.amber, fontSize: 12, fontWeight: 600 }}>⚠ Neuropathic pain identified — consider adjuvant therapy (gabapentin, pregabalin, duloxetine)</span>
              </div>
            )}
          </div>

          {/* Scale Selection Logic */}
          {recommendation && (
            <div style={{ ...cardStyle, borderLeftColor: recommendation.variant === 'green' ? COLORS.green : COLORS.amber }}>
              <div style={{ color: COLORS.label, fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>SCALE RECOMMENDATION</div>
              <Badge variant={recommendation.variant}>{recommendation.label}</Badge>
              {recommendation.scale && (
                <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => setActiveScale('numeric')}
                    style={{
                      padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      fontFamily: "'Inter', sans-serif",
                      backgroundColor: activeScale === 'numeric' ? COLORS.teal : 'transparent',
                      color: activeScale === 'numeric' ? COLORS.white : COLORS.teal,
                      border: `1px solid ${COLORS.teal}`,
                    }}
                  >NRS (0-10)</button>
                  <button
                    onClick={() => setActiveScale('painad')}
                    style={{
                      padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      fontFamily: "'Inter', sans-serif",
                      backgroundColor: activeScale === 'painad' ? COLORS.teal : 'transparent',
                      color: activeScale === 'painad' ? COLORS.white : COLORS.teal,
                      border: `1px solid ${COLORS.teal}`,
                    }}
                  >PAINAD</button>
                  <button
                    onClick={() => setActiveScale('flacc')}
                    style={{
                      padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      fontFamily: "'Inter', sans-serif",
                      backgroundColor: activeScale === 'flacc' ? COLORS.teal : 'transparent',
                      color: activeScale === 'flacc' ? COLORS.white : COLORS.teal,
                      border: `1px solid ${COLORS.teal}`,
                    }}
                  >FLACC</button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Active Scale Display */}
        <div>
          {!activeScale && (
            <div style={{ ...cardStyle, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
              <div style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.tealBg, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <span style={{ fontSize: 20 }}>📋</span>
              </div>
              <div style={{ color: COLORS.label, fontSize: 14, textAlign: 'center' }}>Complete the screening questions to determine<br />the appropriate pain assessment scale.</div>
            </div>
          )}
          {activeScale === 'numeric' && <NumericPainScale />}
          {activeScale === 'painad' && <PAINADScale />}
          {activeScale === 'flacc' && <FLACCScale />}
        </div>
      </div>
    </div>
  );
};

export default PainScreening;
