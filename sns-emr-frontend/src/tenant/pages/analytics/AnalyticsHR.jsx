import React from 'react';
import { COLORS } from '../../design';

const roster = [
  { name: 'Sarah Jenkins', role: 'RN', status: 'On Duty', productivity: '92%' },
  { name: 'Robert Chen', role: 'MSW', status: 'On Duty', productivity: '88%' },
  { name: 'Maria Ramirez', role: 'HHA', status: 'Available', productivity: '81%' },
  { name: 'David Park', role: 'Chaplain', status: 'On Duty', productivity: '90%' },
  { name: 'Emily Watson', role: 'RN', status: 'Pending PTO', productivity: '87%' },
];

const cards = [
  { label: 'Total Staff', value: '38' },
  { label: 'Open Positions', value: '3' },
  { label: 'Expiring Credentials', value: '5' },
  { label: 'Staff Satisfaction', value: '94%' },
];

export default function AnalyticsHR() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        {cards.map((card, index) => (
          <div key={`${card.label}-${index}`} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: '18px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>{card.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Staff Productivity Snapshot</div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Name', 'Role', 'Status', 'Productivity'].map((header) => (
                <th key={header} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 11, color: COLORS.textDim, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {roster.map((person, index) => (
              <tr key={`${person.name}-${index}`} style={{ borderBottom: index < roster.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{person.name}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{person.role}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: person.status === 'Available' ? COLORS.success : COLORS.primary, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{person.status}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{person.productivity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
