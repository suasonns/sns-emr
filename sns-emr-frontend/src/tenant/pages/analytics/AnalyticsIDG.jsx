import React from 'react';
import { COLORS } from '../../design';

const pastMeetings = [
  { date: 'Aug 12, 2026', patients: 14, attendees: 8, duration: '2h 15m', actions: 3, status: 'Completed' },
  { date: 'Jul 29, 2026', patients: 12, attendees: 7, duration: '1h 50m', actions: 5, status: 'Completed' },
  { date: 'Jul 15, 2026', patients: 15, attendees: 9, duration: '2h 30m', actions: 2, status: 'Completed' },
  { date: 'Jul 01, 2026', patients: 11, attendees: 6, duration: '1h 40m', actions: 4, status: 'Completed' },
  { date: 'Jun 17, 2026', patients: 13, attendees: 8, duration: '2h 05m', actions: 6, status: 'Completed' },
  { date: 'Jun 03, 2026', patients: 10, attendees: 7, duration: '1h 35m', actions: 3, status: 'Completed' },
];

export default function AnalyticsIDG() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.primary, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>Next IDG Meeting</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>August 26, 2026 — 10:00 AM</div>
            <div style={{ fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>Conference Room A · Grace Hospice Care Main Office</div>
          </div>
          <button style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ Schedule IDG Meeting</button>
        </div>
        <div style={{ display: 'flex', gap: 32, marginTop: 20, paddingTop: 16, borderTop: `1px solid ${COLORS.border}`, flexWrap: 'wrap' }}>
          {[
            { label: 'Patients to Review', value: '16' },
            { label: 'Confirmed Attendees', value: '9 / 11' },
            { label: 'Pending Action Items', value: '4' },
            { label: 'Avg Meeting Duration', value: '2h 00m' },
          ].map((stat, index) => (
            <div key={`${stat.label}-${index}`}>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{stat.label}</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{stat.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Past IDG Meetings</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Date', 'Patients Reviewed', 'Attendees', 'Duration', 'Action Items', 'Status'].map((header) => (
                <th key={header} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pastMeetings.map((meeting, index) => (
              <tr key={`${meeting.date}-${index}`} style={{ borderBottom: index < pastMeetings.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{meeting.date}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{meeting.patients}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{meeting.attendees}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{meeting.duration}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 600, color: meeting.actions > 3 ? COLORS.warning : COLORS.text, fontFamily: 'Inter, sans-serif' }}>{meeting.actions}</td>
                <td style={{ padding: '12px 20px' }}>
                  <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.success}18`, color: COLORS.success, fontFamily: 'Inter, sans-serif' }}>{meeting.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
