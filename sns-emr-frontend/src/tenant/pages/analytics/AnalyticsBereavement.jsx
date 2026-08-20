import React from 'react';
import { COLORS } from '../../design';

const bereaved = [
  { family: 'Stevens Family', deceased: 'Robert Stevens', dod: 'Jul 02, 2026', risk: 'High', nextContact: 'Aug 20, 2026', type: '3-Month Check-In', counselor: 'Robert Chen, MSW', status: 'Scheduled' },
  { family: 'Hall Family', deceased: 'Richard Hall', dod: 'Jun 15, 2026', risk: 'Medium', nextContact: 'Aug 18, 2026', type: 'Phone Call', counselor: 'Robert Chen, MSW', status: 'Due' },
  { family: 'Park Family', deceased: 'Sung Park', dod: 'May 28, 2026', risk: 'Low', nextContact: 'Aug 28, 2026', type: '3-Month Letter', counselor: 'Lisa Adams, MSW', status: 'Scheduled' },
  { family: 'Williams Family', deceased: 'Grace Williams', dod: 'Apr 10, 2026', risk: 'High', nextContact: 'Aug 22, 2026', type: 'Home Visit', counselor: 'Robert Chen, MSW', status: 'Overdue' },
  { family: 'Torres Family', deceased: 'Manuel Torres', dod: 'Mar 20, 2026', risk: 'Medium', nextContact: 'Sep 01, 2026', type: '6-Month Letter', counselor: 'Lisa Adams, MSW', status: 'Scheduled' },
  { family: 'Jackson Family', deceased: 'Annie Jackson', dod: 'Jul 18, 2026', risk: 'High', nextContact: 'Aug 19, 2026', type: '1-Month Follow-Up', counselor: 'Robert Chen, MSW', status: 'Due' },
  { family: 'Nguyen Family', deceased: 'Linh Nguyen', dod: 'Feb 14, 2026', risk: 'Low', nextContact: 'Sep 14, 2026', type: 'Anniversary Letter', counselor: 'Lisa Adams, MSW', status: 'Scheduled' },
];

const templates = [
  { name: 'Initial Condolence Letter', lastEdited: 'Aug 01, 2026', uses: 24 },
  { name: '1-Month Follow-Up Letter', lastEdited: 'Jul 20, 2026', uses: 18 },
  { name: '3-Month Check-In Letter', lastEdited: 'Jul 15, 2026', uses: 12 },
  { name: '6-Month Follow-Up Letter', lastEdited: 'Jun 30, 2026', uses: 8 },
  { name: 'Anniversary Remembrance Letter', lastEdited: 'Jun 15, 2026', uses: 6 },
  { name: 'Support Group Invitation', lastEdited: 'May 20, 2026', uses: 14 },
];

const riskColor = (risk) => (risk === 'High' ? COLORS.danger : risk === 'Medium' ? COLORS.warning : COLORS.success);
const statusColor = (status) => {
  switch (status) {
    case 'Overdue': return COLORS.danger;
    case 'Due': return COLORS.warning;
    case 'Scheduled': return COLORS.primary;
    case 'Completed': return COLORS.success;
    default: return COLORS.textDim;
  }
};

export default function AnalyticsBereavement() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        {[
          { label: 'Active Bereavement Cases', value: '14', sub: 'In 13-month program' },
          { label: 'Letters Due This Month', value: '6', sub: 'Across all families' },
          { label: 'High Risk Families', value: '4', sub: 'Require enhanced follow-up' },
          { label: 'Contacts Completed (Aug)', value: '9', sub: 'Phone, visit, or letter' },
        ].map((stat, index) => (
          <div key={`${stat.label}-${index}`} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{stat.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{stat.value}</div>
            <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 2, fontFamily: 'Inter, sans-serif' }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Bereavement Follow-Up Schedule</span>
          <button style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ Add Family</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Family', 'Patient (Deceased)', 'Date of Death', 'Risk Level', 'Next Contact', 'Contact Type', 'Counselor', 'Status'].map((header) => (
                <th key={header} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bereaved.map((entry, index) => (
              <tr key={`${entry.family}-${index}`} style={{ borderBottom: index < bereaved.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }}>
                <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.family}</td>
                <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.deceased}</td>
                <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.dod}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: `${riskColor(entry.risk)}18`, color: riskColor(entry.risk), fontFamily: 'Inter, sans-serif' }}>{entry.risk}</span>
                </td>
                <td style={{ padding: '12px 14px', fontSize: 12, fontWeight: 500, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.nextContact}</td>
                <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.type}</td>
                <td style={{ padding: '12px 14px', fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.counselor}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: `${statusColor(entry.status)}18`, color: statusColor(entry.status), fontFamily: 'Inter, sans-serif' }}>{entry.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Letter Templates</div>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 2, fontFamily: 'Inter, sans-serif' }}>Manage bereavement correspondence templates and letterhead configuration.</div>
          </div>
          <button style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ New Template</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
          {templates.map((template, index) => (
            <div key={`${template.name}-${index}`} style={{ padding: '14px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{template.name}</div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 10, fontFamily: 'Inter, sans-serif' }}>Last edited: {template.lastEdited} · Used {template.uses} times</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{ fontSize: 12, color: COLORS.primary, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Edit</span>
                <span style={{ fontSize: 12, color: COLORS.textDim, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Preview</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
