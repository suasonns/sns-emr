import React, { useState } from 'react';
import { GuideBox, GuideList, GradientBar, References } from './PainGuide';
import { getNumericInterpretation } from './painScoring';
import PainScoreBadge from './PainScoreBadge';

const COLORS = {
  bg: 'var(--sns-cardSoft)', card: 'var(--sns-card)', border: 'var(--sns-border)', teal: 'var(--sns-teal)',
  white: 'var(--sns-white)', label: 'var(--sns-dim)', text: 'var(--sns-muted)',
};

const SCALE_COLORS = [
  '#059669', '#16a34a', '#65a30d', '#84cc16', '#a3e635',
  '#facc15', '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#b91c1c',
];

const SCALE_LABELS = ['No Pain', '', '', 'Mild', '', '', 'Moderate', '', '', 'Severe', 'Worst'];

const getInterpretation = (score) => {
  const interp = getNumericInterpretation(score);
  if (!interp) return null;
  return { ...interp, bg: `${interp.color}15` };
};

const NumericPainScale = ({ value, onChange }) => {
  const isControlled = typeof onChange === 'function';
  const [internalScore, setInternalScore] = useState(null);
  const selectedScore = isControlled ? (value ?? null) : internalScore;
  const setSelectedScore = (v) => {
    if (isControlled) onChange(v);
    else setInternalScore(v);
  };

  const interp = selectedScore !== null ? getInterpretation(selectedScore) : null;


  return (
    <div className="pain-tool" style={{ backgroundColor: COLORS.card, borderRadius: 8, padding: 24, borderLeft: `4px solid ${COLORS.teal}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
        <div className="pain-tool__title" style={{ color: COLORS.white, fontSize: 15, fontWeight: 700 }}>Numeric Pain Rating Scale (0–10)</div>
        <PainScoreBadge tool="numeric" score={selectedScore} />
      </div>
      <div className="pain-tool__subtitle" style={{ color: COLORS.label, fontSize: 12, marginBottom: 20 }}>Patient self-report scale — select the number that best describes pain intensity.</div>

      {/* Scale Circles */}
      <div className="pain-tool__surface" style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 20, marginBottom: 16 }}>
        <div className="pain-tool__meta" style={{ color: COLORS.label, fontSize: 10, fontWeight: 600, textTransform: 'uppercase', textAlign: 'center', marginBottom: 16, letterSpacing: 0.5 }}>PATIENT SELF-REPORT SCALE</div>
        <div className="pain-tool__scale" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {Array.from({ length: 11 }, (_, i) => (
            <button type="button" className="pain-tool__scale-option" aria-pressed={selectedScore === i} key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer' }} onClick={() => setSelectedScore(i)}>
              <div className="pain-tool__scale-value" style={{
                width: 36, height: 36, borderRadius: 18,
                backgroundColor: selectedScore === i ? SCALE_COLORS[i] : 'transparent',
                border: `2px solid ${SCALE_COLORS[i]}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: selectedScore === i ? COLORS.white : SCALE_COLORS[i],
                fontSize: 14, fontWeight: 700, transition: 'all 0.15s',
              }}>{i}</div>
              {SCALE_LABELS[i] && <span className="pain-tool__meta" style={{ color: COLORS.label, fontSize: 9, marginTop: 4 }}>{SCALE_LABELS[i]}</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Clinical Protocol Guidance */}
      <GuideBox title="Clinical Protocol Guidance" icon="🛈">
        <GuideList items={[
          'Administration: Can be administered verbally (including by telephone) or graphically for self-completion.',
          'Standard prompt: Ask patient: "On a scale of 0 to 10, with 0 being no pain and 10 being the worst pain imaginable, how would you rate your pain?"',
          'Recall Period: Most commonly ask for pain intensity "right now" or "in the last 24 hours," or average pain intensity.',
        ]} />
      </GuideBox>

      {/* Result */}
      {selectedScore !== null && interp && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 16, backgroundColor: COLORS.bg, borderRadius: 8, marginBottom: 16 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 10, backgroundColor: interp.bg,
            border: `2px solid ${interp.color}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span className="pain-tool__score-value" style={{ color: interp.color, fontSize: 22, fontWeight: 800 }}>{selectedScore}</span>
          </div>
          <div>
            <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 700 }}>Score: {selectedScore}/10</div>
            <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600, backgroundColor: interp.bg, color: interp.color, marginTop: 4 }}>{interp.label}</span>
          </div>
        </div>
      )}

      {/* Scoring & Interpretation */}
      <GuideBox title="Scoring & Interpretation">
        <GradientBar />
        <GuideList items={[
          '0 = No Pain (green)',
          '1-3 = Mild Pain (yellow-green)',
          '4-6 = Moderate Pain (amber)',
          '7-10 = Severe Pain (red)',
        ]} />
        <div className="pain-guide__body" style={{ marginTop: 8, color: COLORS.text, fontSize: 12 }}>Higher scores indicate greater pain intensity.</div>
        <div className="pain-tool__meta" style={{ marginTop: 6, color: COLORS.label, fontSize: 11 }}>MCID: A reduction of 2 points (or 30%) is considered clinically important.</div>
      </GuideBox>

      {/* Psychometric Properties */}
      <GuideBox title="Psychometric Properties">
        <GuideList items={[
          'Reliability: High test-retest reliability (r = 0.96 literate, r = 0.95 illiterate) — Ferraz et al.',
          'Validity: Highly correlated with VAS (r = 0.86-0.95) in chronic pain conditions.',
          'Responsiveness: MDC = 2 points on 11-point scale.',
        ]} />
      </GuideBox>

      {/* Target Patient Population */}
      <GuideBox title="Target Patient Population">
        <div className="pain-guide__body" style={{ color: COLORS.text, fontSize: 12, lineHeight: 1.6 }}>
          <div><strong style={{ color: COLORS.white }}>Best for:</strong> Adults and older children who can reliably self-report pain intensity.</div>
          <div>Preferred by chronic pain patients over VAS due to comprehensibility and ease of completion.</div>
          <div>Takes &lt; 1 minute to complete.</div>
        </div>
      </GuideBox>

      <References items={['Hawker GA (2011)', 'Ferraz MB et al. (1990)', 'Farrar JT et al. (2001)']} />
    </div>
  );
};

export default NumericPainScale;
