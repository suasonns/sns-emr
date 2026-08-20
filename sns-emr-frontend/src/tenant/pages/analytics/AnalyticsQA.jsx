import React from 'react';
import { COLORS } from '../../design';

const pendingReviews = [
  { doc: 'Nursing Visit Note', patient: 'Martha Stevens', clinician: 'Sarah Jenkins, RN', submitted: 'Aug 15, 2026', days: 2, priority: 'High' },
  { doc: 'MSW Assessment', patient: 'Arthur Pendelton', clinician: 'Robert Chen, MSW', submitted: 'Aug 14, 2026', days: 3, priority: 'Medium' },
  { doc: 'Aide Visit Documentation', patient: 'Eleanor Vance', clinician: 'Maria Ramirez, HHA', submitted: 'Aug 14, 2026', days: 3, priority: 'Low' },
  { doc: 'Chaplain Spiritual Care', patient: 'James Miller', clinician: 'David Park, Chaplain', submitted: 'Aug 13, 2026', days: 4, priority: 'Medium' },
  { doc: 'Comprehensive Assessment', patient: 'Thomas H. Wright', clinician: 'Emily Watson, RN', submitted: 'Aug 12, 2026', days: 5, priority: 'High' },
  { doc: 'Nursing Visit Note', patient: 'Dorothy Chen', clinician: 'Sarah Jenkins, RN', submitted: 'Aug 11, 2026', days: 6, priority: 'High' },
];

const lateSubmissions = [
  { clinician: 'Maria Ramirez, HHA', docType: 'Aide Visit Documentation', patient: 'Eleanor Vance', dueDate: 'Aug 10, 2026', daysLate: 7, status: 'Overdue' },
  { clinician: 'Robert Chen, MSW', docType: 'Bereavement Follow-Up', patient: 'Family of R. Hall', dueDate: 'Aug 12, 2026', daysLate: 5, status: 'Overdue' },
  { clinician: 'Emily Watson, RN', docType: 'Recertification POC', patient: 'James Miller', dueDate: 'Aug 14, 2026', daysLate: 3, status: 'Warning' },
  { clinician: 'David Park, Chaplain', docType: 'Spiritual Care Note', patient: 'Arthur Pendelton', dueDate: 'Aug 15, 2026', daysLate: 2, status: 'Warning' },
];

const ePrescriptions = [
  { medication: 'Morphine Sulfate 15mg', patient: 'Martha Stevens', prescriber: 'Dr. Albert Chen', requested: 'Aug 16, 2026', status: 'Awaiting Signature' },
  { medication: 'Lorazepam 0.5mg', patient: 'James Miller', prescriber: 'Dr. Allen Patel', requested: 'Aug 15, 2026', status: 'Awaiting Signature' },
  { medication: 'Haloperidol 1mg', patient: 'Thomas H. Wright', prescriber: 'Dr. Albert Chen', requested: 'Aug 15, 2026', status: 'Sent to Pharmacy' },
];

const priorityColor = (priority) => {
  switch (priority) {
    case 'High': return COLORS.danger;
    case 'Medium': return COLORS.warning;
    case 'Low': return COLORS.primary;
    default: return COLORS.textDim;
  }
};

export default function AnalyticsQA() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        {[
          { label: 'Pending Reviews', value: '6', color: COLORS.warning },
          { label: 'Late Submissions', value: '4', color: COLORS.danger },
          { label: 'Completion Rate', value: '87%', color: COLORS.success },
          { label: 'ePrescriptions Pending', value: '3', color: '#6366f1' },
        ].map((stat, index) => (
          <div key={`${stat.label}-${index}`} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 4, fontFamily: 'Inter, sans-serif' }}>{stat.label}</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: stat.color, fontFamily: 'Inter, sans-serif' }}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Pending Reviews</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {['Document', 'Patient', 'Clinician', 'Days', 'Priority'].map((header) => (
                  <th key={header} style={{ padding: '8px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pendingReviews.map((review, index) => (
                <tr key={`${review.doc}-${index}`} style={{ borderBottom: index < pendingReviews.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }}>
                  <td style={{ padding: '10px 14px', fontSize: 12, fontWeight: 500, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{review.doc}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{review.patient}</td>
                  <td style={{ padding: '10px 14px', fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{review.clinician}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12, fontWeight: 600, color: review.days > 4 ? COLORS.danger : COLORS.text, fontFamily: 'Inter, sans-serif' }}>{review.days}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: `${priorityColor(review.priority)}18`, color: priorityColor(review.priority), fontFamily: 'Inter, sans-serif' }}>{review.priority}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Late Submission Tracker</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {['Clinician', 'Document', 'Patient', 'Days Late', 'Status'].map((header) => (
                  <th key={header} style={{ padding: '8px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lateSubmissions.map((entry, index) => (
                <tr key={`${entry.clinician}-${index}`} style={{ borderBottom: index < lateSubmissions.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                  <td style={{ padding: '10px 14px', fontSize: 12, fontWeight: 500, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.clinician}</td>
                  <td style={{ padding: '10px 14px', fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.docType}</td>
                  <td style={{ padding: '10px 14px', fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.patient}</td>
                  <td style={{ padding: '10px 14px', fontSize: 12, fontWeight: 600, color: entry.daysLate > 4 ? COLORS.danger : COLORS.warning, fontFamily: 'Inter, sans-serif' }}>{entry.daysLate}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: entry.status === 'Overdue' ? `${COLORS.danger}18` : `${COLORS.warning}18`, color: entry.status === 'Overdue' ? COLORS.danger : COLORS.warning, fontFamily: 'Inter, sans-serif' }}>{entry.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Pending ePrescriptions</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Medication', 'Patient', 'Prescriber', 'Requested', 'Status'].map((header) => (
                <th key={header} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ePrescriptions.map((entry, index) => (
              <tr key={`${entry.medication}-${index}`} style={{ borderBottom: index < ePrescriptions.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 600, color: COLORS.primary, fontFamily: 'Inter, sans-serif' }}>{entry.medication}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.patient}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.prescriber}</td>
                <td style={{ padding: '12px 20px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.requested}</td>
                <td style={{ padding: '12px 20px' }}>
                  <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: entry.status === 'Awaiting Signature' ? `${COLORS.warning}18` : `${COLORS.success}18`, color: entry.status === 'Awaiting Signature' ? COLORS.warning : COLORS.success, fontFamily: 'Inter, sans-serif' }}>{entry.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
