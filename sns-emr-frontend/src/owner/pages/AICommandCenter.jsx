import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

const WORKFLOWS = [
  ['Clinical drafting', 'Operational'],
  ['Billing summarization', 'Operational'],
  ['Assessment review', 'Degraded'],
  ['Transcription pipeline', 'Running'],
];

export default function AICommandCenter() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>AI Command Center</h1>
          <p style={S.pageSubtitle}>Monitor model usage, orchestration status, document generation, and policy controls.</p>
        </div>
        <button type="button" style={S.btn(COLORS.teal)}>RUN WORKFLOW</button>
      </div>

      <div style={S.statsRow}>
        {[
          { label: 'MODELS ACTIVE', value: '4', tone: COLORS.purple },
          { label: 'DRAFTS GENERATED', value: '2,411', tone: COLORS.teal },
          { label: 'AVG QUALITY', value: '94.7%', tone: COLORS.green },
          { label: 'RISK FLAGS', value: '3', tone: COLORS.orange },
        ].map((metric) => (
          <div key={metric.label} style={S.statCard}>
            <span style={S.statDot(metric.tone)} />
            <p style={S.statLabel}>{metric.label}</p>
            <div style={S.statValue}>{metric.value}</div>
            <div style={S.statSub(COLORS.teal)}>Live</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24 }}>
        <div style={{ ...S.card, padding: 18 }}>
          <h3 style={S.cardTitle}>Workflow Overview</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {WORKFLOWS.map(([label, status], index) => (
              <div key={label} style={{ display: 'grid', gridTemplateColumns: '1.7fr 1fr', borderBottom: index < WORKFLOWS.length - 1 ? `1px solid ${COLORS.border}` : 'none', paddingBottom: 8 }}>
                <div style={{ color: COLORS.white, fontWeight: 600 }}>{label}</div>
                <span style={{ ...S.badge(status === 'Operational' || status === 'Running' ? 'rgba(34,197,94,0.12)' : 'rgba(249,115,22,0.12)', status === 'Operational' || status === 'Running' ? COLORS.green : COLORS.orange), width: 'fit-content', justifySelf: 'end' }}>{status}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...S.card, padding: 18 }}>
          <h3 style={S.cardTitle}>Policy Controls</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {[
              ['Document retention', '90 days'],
              ['Bias monitoring', 'Enabled'],
              ['Safety checks', 'Pass'],
              ['Human approval', 'Selective'],
            ].map(([label, value], index, arr) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: index < arr.length - 1 ? `1px solid ${COLORS.border}` : 'none', paddingBottom: 10 }}>
                <span style={{ color: COLORS.muted }}>{label}</span>
                <span style={{ color: COLORS.white, fontWeight: 600 }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
