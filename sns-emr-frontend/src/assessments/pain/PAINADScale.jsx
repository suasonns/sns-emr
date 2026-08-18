import React, { useState } from 'react';
import { GuideBox, GuideList, GradientBar, References } from './PainGuide';
import { getPainadInterpretation } from './painScoring';
import PainScoreBadge from './PainScoreBadge';

const COLORS = {
  bg: '#0f172a', card: '#1e293b', border: '#334155', teal: '#10b7a2',
  white: '#ffffff', label: '#94a3b8', text: '#e2e8f0',
  green: '#059669', red: '#ef4444', amber: '#f59e0b',
  greenBg: '#05966915', redBg: '#ef444415', amberBg: '#f59e0b15',
};

const CATEGORIES = [
  {
    name: 'Breathing (Independent of vocalization)',
    scores: [
      'Normal',
      'Occasional labored breathing. Short period of hyperventilation.',
      'Noisy labored breathing. Long period of hyperventilation. Cheyne-Stokes respirations.',
    ],
  },
  {
    name: 'Negative Vocalization',
    scores: [
      'None',
      'Occasional moan or groan. Low-level speech with negative or disapproving quality.',
      'Repeated troubled calling out. Loud moaning or groaning. Crying.',
    ],
  },
  {
    name: 'Facial Expression',
    scores: ['Smiling or inexpressive', 'Sad. Frightened. Frown.', 'Facial grimacing'],
  },
  {
    name: 'Body Language',
    scores: [
      'Relaxed',
      'Tense. Distressed pacing. Fidgeting.',
      'Rigid. Fists clenched. Knees pulled up. Pulling or pushing away. Striking out.',
    ],
  },
  {
    name: 'Consolability',
    scores: [
      'No need to console',
      'Distracted or reassured by voice or touch',
      'Unable to console, distract, or reassure',
    ],
  },
];

const getInterpretation = (total) => {
  const interp = getPainadInterpretation(total);
  if (!interp) return null;
  return { ...interp, bg: `${interp.color}15` };
};

const PAINADScale = ({ value, onChange }) => {
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
    <div style={{ backgroundColor: COLORS.card, borderRadius: 8, padding: 24, borderLeft: `4px solid ${COLORS.teal}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
        <div style={{ color: COLORS.white, fontSize: 15, fontWeight: 700 }}>PAINAD — Pain Assessment in Advanced Dementia</div>
        <PainScoreBadge tool="painad" score={total} />
      </div>
      <div style={{ color: COLORS.label, fontSize: 12, marginBottom: 12 }}>For patients unable to self-report pain (advanced dementia, non-verbal).</div>

      {/* Instructions */}
      <GuideBox title="Instructions" icon="🛈">
        <div style={{ color: COLORS.text, fontSize: 12, lineHeight: 1.6 }}>
          Observe the patient for five minutes before scoring his or her behaviors. Score the behaviors according to the chart below. The patient can be observed under different conditions (e.g., at rest, during a pleasant activity, during caregiving, after the administration of pain medication).
        </div>
      </GuideBox>

      {/* Scoring Table */}
      <div style={{ backgroundColor: COLORS.bg, borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '22%' }} />
            <col style={{ width: '20%' }} />
            <col style={{ width: '24%' }} />
            <col style={{ width: '24%' }} />
            <col style={{ width: '10%' }} />
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
                <td style={{ ...dataCell, fontWeight: 600, color: COLORS.white, fontSize: 11 }}>{cat.name}</td>
                {[0, 1, 2].map((val) => (
                  <td
                    key={val}
                    onClick={() => handleScore(i, val)}
                    style={{
                      ...dataCell, cursor: 'pointer', fontSize: 11,
                      backgroundColor: scores[i] === val ? `${COLORS.teal}15` : 'transparent',
                      border: scores[i] === val ? `1px solid ${COLORS.teal}40` : `1px solid transparent`,
                      borderBottom: `1px solid ${COLORS.border}`,
                      borderRadius: 0,
                    }}
                  >
                    {cat.scores[val]}
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: COLORS.bg, borderRadius: 8, marginBottom: 16 }}>
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
            <span style={{ color: interp.color, fontSize: 20, fontWeight: 800 }}>{total}</span>
          </div>
          <div>
            <div style={{ color: COLORS.white, fontSize: 13, fontWeight: 700 }}>/10</div>
            <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600, backgroundColor: interp.bg, color: interp.color }}>{interp.label}</span>
          </div>
        </div>
      </div>

      {/* Note */}
      <div style={{ color: COLORS.label, fontSize: 10, marginBottom: 16 }}>
        Score ranges (0 No Pain, 1-3 Mild, 4-6 Moderate, 7-10 Severe) are based on a standard 0-10 scale but have not been substantiated in the literature for this tool.
      </div>

      {/* Scoring & Interpretation */}
      <GuideBox title="Scoring & Interpretation">
        <GradientBar />
        <GuideList items={[
          '0 = No Pain (green)',
          '1-3 = Mild Pain (yellow-green)',
          '4-6 = Moderate Pain (amber)',
          '7-10 = Severe Pain (red)',
        ]} />
      </GuideBox>

      {/* Psychometric Properties */}
      <GuideBox title="Psychometric Properties">
        <GuideList items={[
          'Source: Warden V, Hurley AC, Volicer L. Development and psychometric evaluation of the PAINAD scale. J Am Med Dir Assoc. 2003;4(1):9-15.',
          'Target: For patients with advanced dementia who cannot self-report pain.',
          'Administration: Observe patient for 5 minutes. Score each behavior 0-2. Takes < 5 minutes.',
        ]} />
      </GuideBox>

      <References items={['Warden V, Hurley AC, Volicer L. (2003). Development and psychometric evaluation of the Pain Assessment in Advanced Dementia (PAINAD) scale.']} />
    </div>
  );
};

export default PAINADScale;
