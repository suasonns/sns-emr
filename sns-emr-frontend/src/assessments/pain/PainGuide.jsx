import React from 'react';
import './PainAssessmentTools.css';

// Shared clinical-guidance building blocks used by the pain scale
// components (Numeric / PAINAD / FLACC). These render the same
// "Instructions / Scoring & Interpretation / Psychometric Properties"
// reference panels shown in the Figma spec so nurses unfamiliar with
// a given scale have the guidance right next to the tool.

const COLORS = {
  bg: 'var(--sns-cardSoft)', teal: 'var(--sns-teal)',
  white: 'var(--sns-white)', label: 'var(--sns-dim)', text: 'var(--sns-muted)',
};

export const GuideBox = ({ title, icon, children, style: extra }) => (
  <div className="pain-guide-box" style={{ backgroundColor: COLORS.bg, borderRadius: 8, padding: 16, marginBottom: 16, ...extra }}>
    <div className="pain-guide__title" style={{ color: COLORS.teal, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
      {icon && <span>{icon}</span>}
      {title}
    </div>
    {children}
  </div>
);

export const GuideList = ({ items }) => (
  <ul className="pain-guide__list" style={{ margin: 0, paddingLeft: 18, color: COLORS.text, fontSize: 12, lineHeight: 1.6 }}>
    {items.map((item, i) => (
      <li key={i}>{item}</li>
    ))}
  </ul>
);

export const GradientBar = () => (
  <div style={{
    height: 8, borderRadius: 4, marginBottom: 10,
    background: 'linear-gradient(to right, #059669, #84cc16, #f59e0b, #ef4444)',
  }} />
);

export const References = ({ items }) => (
  <div className="pain-guide__references" style={{ marginTop: 4, color: COLORS.label, fontSize: 10, lineHeight: 1.6 }}>
    <span style={{ color: COLORS.teal, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 10 }}>References: </span>
    {items.join('  ·  ')}
  </div>
);

export default { GuideBox, GuideList, GradientBar, References };
