import React from 'react';
import { COLORS } from '../../design';

const records = [
  { label: 'Open Orders', value: '41' },
  { label: 'Pending Referrals', value: '17' },
  { label: 'Late Notes', value: '9' },
  { label: 'Active Contracts', value: '6' },
];

const tasks = [
  { title: 'Census cleanup review', owner: 'Operations', due: 'Today' },
  { title: 'Vendor file renewals', owner: 'Finance', due: 'Tomorrow' },
  { title: 'Compliance sign-off', owner: 'QA', due: 'Aug 18' },
  { title: 'Staff credential audit', owner: 'HR', due: 'Aug 22' },
];

export default function AnalyticsAdministrative() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        {records.map((record, index) => (
          <div key={`${record.label}-${index}`} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: '18px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>{record.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{record.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Administrative Action Queue</div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Task', 'Owner', 'Due'].map((header) => (
                <th key={header} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 11, color: COLORS.textDim, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tasks.map((task, index) => (
              <tr key={`${task.title}-${index}`} style={{ borderBottom: index < tasks.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{task.title}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{task.owner}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.warning, fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>{task.due}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
