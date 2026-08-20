import React, { useState } from 'react';
import { GuideBox, GuideList, GradientBar, References } from './PainGuide';
import { getFlaccInterpretation } from './painScoring';
import PainScoreBadge from './PainScoreBadge';

const COLORS = {
  bg: 'var(--sns-cardSoft)', card: 'var(--sns-card)', border: 'var(--sns-border)', teal: 'var(--sns-teal)',
  white: 'var(--sns-white)', label: 'var(--sns-dim)', text: 'var(--sns-muted)',
};

const CATEGORIES = [
  {
    name: 'Face',
    scores: [
      'No particular expression or smile',
      'Occasional grimace or frown, withdrawn, disinterested',
      'Frequent to constant quivering chin, clenched jaw',
    ],
  },
  {
    name: 'Legs',
    scores: ['Normal position or relaxed', 'Uneasy, restless, tense', 'Kicking or legs drawn up'],
  },
  {
    name: 'Activity',
    scores: [
      'Lying quietly, normal position, moves easily',
      'Squirming, shifting back and forth, tense',
      'Arched, rigid, or jerking',
    ],
  },
  {
    name: 'Cry',
    scores: [
      'No cry (awake or asleep)',
      'Moans or whimpers, occasional complaint',
      'Crying steadily, screams or sobs, frequent complaints',
    ],
  },
  {
    name: 'Consolability',
    scores: [
      'Content, relaxed',
      'Reassured by occasional touching, hugging, or being talked to, distractible',
      'Difficult to console or comfort',
    ],
  },
];

const getInterpretation = (total) => {
  const interp = getFlaccInterpretation(total);
  if (!interp) return null;
  return { ...interp, bg: `${interp.color}15` };
};

const FLACCScale = ({ value, onChange }) => {
  const isControlled = Array.isArray(value) && typeof onChange === 'function';
  const [internalScores, setInternalScores] = useState([0, 0, 0, 0, 0]);
  const scores = isControlled ? value : internalScores;

  const total = scores.reduce((sum, s) => sum + (Number(s) || 0), 0);
  const interp = getInterpretation(total);

  const handleScore = (catIndex, val) => {
    const updated = [...scores];
    updated[catIndex] = val;
    if (isControlled) onChange(updated);
    else setInternalScores(updated);
  };

  const headerCell = { padding: '10px 8px', fontSize: 11, fontWeight: 700, color: COLORS.teal, textAlign: 'center', borderBottom: `1px solid ${COLORS.border}` };
  const dataCell = { padding: '10px 8px', fontSize: 12, color: COLORS.text, borderBottom: `1px solid ${COLORS.border}`, verticalAlign: 'top', lineHeight: '1.4' };

  return (
    <div className="pain-tool" style={{ backgroundColor: COLORS.card, borderRadius: 8, padding: 24, borderLeft: `4px solid ${COLORS.teal}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
        <div className="pain-tool__title" style={{ color: COLORS.white, fontSize: 15, fontWeight: 700 }}>FLACC — Behavioral Pain Assessment Scale</div>
        <PainScoreBadge tool="flacc" score={total} />
      </div>
      <div className="pain-tool__subtitle" style={{ color: COLORS.label, fontSize: 12, marginBottom: 12 }}>For infants, young children, and non-verbal critical care patients.</div>

      {/* Instructions */}
      <GuideBox title="Instructions" icon="🛈">
        <div className="pain-guide__body" style={{ color: COLORS.text, fontSize: 12, lineHeight: 1.6 }}>
          Observe the patient for 1–2 minutes. Score each behavioral category on a 0–2 scale. The patient can be observed under different conditions. Total score determines pain severity.
        </div>
      </GuideBox>

      {/* Scoring Table */}
      <div className="pain-tool__surface pain-tool__table" style={{ backgroundColor: COLORS.bg, borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '18%' }} />
            <col style={{ width: '22%' }} />
            <col style={{ width: '24%' }} />
            <col style={{ width: '24%' }} />
            <col style={{ width: '12%' }} />
          </colgroup>
          <thead>
            <tr style={{ backgroundColor: COLORS.card }}>
              <th style={{ ...headerCell, textAlign: 'left', color: COLORS.white }}>Behavior</th>
              <th style={headerCell}>0</th>
              <th style={headerCell}>1</th>
              <th style={headerCell}>2</th>
              <th style={{ ...headerCell, color: COLORS.white }}>Score</th>
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map((cat, i) => (
              <tr key={i}>
                <td style={{ ...dataCell, fontWeight: 600, color: COLORS.white, fontSize: 12 }}>{cat.name}</td>
                {[0, 1, 2].map((val) => (
                  <td key={val} style={{ ...dataCell, padding: 0 }}>
                    <button
                      type="button"
                      className="pain-tool__option"
                      aria-pressed={scores[i] === val}
                      aria-label={`${cat.name}, score ${val}: ${cat.scores[val]}`}
                      onClick={() => handleScore(i, val)}
                    >
                      {cat.scores[val]}
                    </button>
                  </td>
                ))}
                <td style={{ ...dataCell, textAlign: 'center' }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 6, margin: '0 auto',
                    backgroundColor: COLORS.card, border: `1px solid ${COLORS.border}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: COLORS.white, fontSize: 14, fontWeight: 700,
                  }}>{scores[i]}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Total Score */}
      <div className="pain-tool__surface pain-tool__summary" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: COLORS.bg, borderRadius: 8, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {scores.map((s, i) => (
            <React.Fragment key={i}>
              <div style={{
                width: 28, height: 28, borderRadius: 4, backgroundColor: COLORS.card,
                border: `1px solid ${COLORS.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: COLORS.white, fontSize: 12, fontWeight: 600,
              }}>{s}</div>
              {i < 4 && <span style={{ color: COLORS.label, fontSize: 14, fontWeight: 600 }}>+</span>}
            </React.Fragment>
          ))}
          <span style={{ color: COLORS.label, fontSize: 14, fontWeight: 600, marginLeft: 4 }}>=</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 10, backgroundColor: interp.bg,
            border: `2px solid ${interp.color}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span className="pain-tool__score-value" style={{ color: interp.color, fontSize: 20, fontWeight: 800 }}>{total}</span>
          </div>
          <div>
            <div style={{ color: COLORS.white, fontSize: 13, fontWeight: 700 }}>/10</div>
            <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600, backgroundColor: interp.bg, color: interp.color }}>{interp.label}</span>
          </div>
        </div>
      </div>

      {/* Score Legend */}
      <div className="pain-tool__meta" style={{ color: COLORS.label, fontSize: 10, marginBottom: 16 }}>
        0 = Relaxed/Comfortable · 1-3 = Mild Discomfort · 4-6 = Moderate Pain · 7-10 = Severe Pain
      </div>

      {/* Scoring & Interpretation */}
      <GuideBox title="Scoring & Interpretation">
        <GradientBar />
        <GuideList items={[
          '0 = Relaxed/Comfortable (green)',
          '1-3 = Mild Discomfort (yellow-green)',
          '4-6 = Moderate Pain (amber)',
          '7-10 = Severe Pain (red)',
        ]} />
        <div className="pain-guide__body" style={{ marginTop: 8, color: COLORS.text, fontSize: 12 }}>
          These ranges are based on a standard 0-10 scale of pain, but have not been substantiated for this tool.
        </div>
      </GuideBox>

      {/* Psychometric Properties */}
      <GuideBox title="Psychometric Properties">
        <GuideList items={[
          'Source: Merkel S, Voepel-Lewis T, Shayevitz JR, Malviya S. (1997). The FLACC: a behavioral scale for scoring postoperative pain in young children.',
          'Target: For infants, young children, and non-verbal critical care patients.',
          'Administration: Observe patient for 1-2 minutes. Score each behavior 0-2. Takes < 3 minutes.',
        ]} />
      </GuideBox>

      <References items={['Merkel S, Voepel-Lewis T, Shayevitz JR, Malviya S. (1997). The FLACC: a behavioral scale for scoring postoperative pain in young children.']} />
    </div>
  );
};

export default FLACCScale;
