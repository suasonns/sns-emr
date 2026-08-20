import React, { useState } from 'react';
import { COLORS } from '../../design';

const qapiReports = [
  { title: 'Comfort Outcomes Measure', frequency: 'Quarterly', lastRun: 'Last Run: Jul 01, 2026', desc: 'Patient comfort and symptom management quality indicators per CMS benchmarks.' },
  { title: 'Unplanned Transfer Rate', frequency: 'Quarterly', lastRun: 'Last Run: Jul 01, 2026', desc: 'Acute care transfers and hospitalization rates against national averages.' },
  { title: 'Infection Surveillance', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Healthcare-associated infection tracking, antibiotic stewardship, and outbreak monitoring.' },
  { title: 'Incident & Safety Report', frequency: 'Monthly', lastRun: 'Last Run: Aug 05, 2026', desc: 'Patient safety events — falls, med errors, adverse events with corrective action tracking.' },
  { title: 'Volunteer Cost Analysis', frequency: 'Quarterly', lastRun: 'Last Run: Jul 01, 2026', desc: 'Volunteer hours vs. paid-staff equivalency for CMS 5% direct-patient-care mandate.' },
  { title: 'CAHPS Performance Export', frequency: 'Quarterly', lastRun: 'Last Run: Jul 01, 2026', desc: 'Patient/family satisfaction scores and survey performance metrics export.' },
  { title: 'HIS Data Quality & Submission', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Hospice Item Set data quality, completeness, and timely CMS submission tracking.' },
  { title: 'Wound Assessment Tracker', frequency: 'Monthly', lastRun: 'Last Run: Aug 10, 2026', desc: 'Wound staging, healing trajectory, and treatment documentation tracking.' },
  { title: 'ABX Compliance Audit', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Patients on antibiotics without corresponding care plan documentation — compliance gap detection.' },
  { title: 'ABN Delivery Performance', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Advance Beneficiary Notice of Non-Coverage delivery and response rate tracking.' },
  { title: 'Census Integrity Audit', frequency: 'Weekly', lastRun: 'Last Run: Aug 14, 2026', desc: 'Cross-reference active census against billing records for data integrity.' },
  { title: 'HQRP Quality Measures', frequency: 'Quarterly', lastRun: 'Last Run: Jul 01, 2026', desc: 'CMS Hospice Quality Reporting Program — NQF-endorsed indicators.' },
  { title: 'Staff Utilization Analysis', frequency: 'Weekly', lastRun: 'Last Run: Aug 14, 2026', desc: 'Clinician productivity and visit-to-capacity ratios per discipline.' },
  { title: 'Staff Performance Index', frequency: 'Monthly', lastRun: 'Last Run: Aug 01, 2026', desc: 'Case visits, documentation speed, mileage, caseload per clinician.' },
  { title: 'eMAR Compliance', frequency: 'Daily', lastRun: 'Last Run: Today, 6:00 AM', desc: 'Electronic medication administration record documentation audit.' },
  { title: 'Patient Acuity Stratification', frequency: 'Weekly', lastRun: 'Last Run: Aug 14, 2026', desc: 'Census stratified by acuity level for staffing and resource allocation.' },
];

const infectionData = [
  { patient: 'Martha Stevens', mrn: 'MRN-48190', type: 'UTI', abx: 'Ciprofloxacin 500mg', startDate: 'Aug 12, 2026', dayOn: 5, culture: 'Pending', status: 'Active' },
  { patient: 'James Miller', mrn: 'MRN-48192', type: 'Pneumonia', abx: 'Azithromycin 250mg', startDate: 'Aug 10, 2026', dayOn: 7, culture: 'E. coli', status: 'Active' },
  { patient: 'Eleanor Vance', mrn: 'MRN-48193', type: 'Wound Infection', abx: 'Cephalexin 500mg', startDate: 'Aug 14, 2026', dayOn: 3, culture: 'MRSA', status: 'Monitoring' },
  { patient: 'Thomas H. Wright', mrn: 'MRN-48194', type: 'Cellulitis', abx: 'Amoxicillin/Clav', startDate: 'Aug 08, 2026', dayOn: 9, culture: 'Staph aureus', status: 'Resolving' },
];

const fallsData = [
  { patient: 'Arthur Pendelton', mrn: 'MRN-48191', date: 'Aug 15, 2026', location: 'Bedroom', injury: 'No injury', witnessed: 'Yes', riskLevel: 'High', followUp: 'MD notified, POC updated' },
  { patient: 'Martha Stevens', mrn: 'MRN-48190', date: 'Aug 11, 2026', location: 'Bathroom', injury: 'Minor bruise — left forearm', witnessed: 'No', riskLevel: 'High', followUp: 'Fall prevention plan revised' },
];

const sentinelData = [
  { patient: 'James Miller', mrn: 'MRN-48192', date: 'Aug 13, 2026', event: 'Unplanned hospitalization — respiratory distress', severity: 'Major', rootCause: 'Under review', corrective: 'Pending IDG review', reportedBy: 'Emily Watson, RN', status: 'Open' },
];

const trackerPills = [
  { key: 'infections', label: 'Infections / ABX', count: 4 },
  { key: 'falls', label: 'Falls', count: 2 },
  { key: 'sentinel', label: 'Sentinel Events', count: 1 },
  { key: 'wounds', label: 'Wounds', count: 6 },
  { key: 'medErrors', label: 'Med Errors', count: 0 },
  { key: 'unsigned', label: 'Unsigned Docs', count: 8 },
  { key: 'overdue', label: 'Overdue Items', count: 5 },
];

const statusColor = (status) => {
  switch (status) { case 'Active': case 'Open': return COLORS.danger; case 'Monitoring': return COLORS.warning; case 'Resolving': return COLORS.success; default: return COLORS.textDim; }
};
const freqColor = (frequency) => {
  switch (frequency) { case 'Daily': return COLORS.primary; case 'Weekly': return '#6366f1'; case 'Monthly': return COLORS.warning; case 'Quarterly': return '#8b5cf6'; default: return COLORS.textDim; }
};
const riskColor = (risk) => (risk === 'High' ? COLORS.danger : risk === 'Medium' ? COLORS.warning : COLORS.success);

export default function AnalyticsQAPI() {
  const [qapiView, setQapiView] = useState('trackers');
  const [activeTracker, setActiveTracker] = useState('infections');

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button onClick={() => setQapiView('trackers')} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, fontFamily: 'Inter, sans-serif', background: qapiView === 'trackers' ? COLORS.primary : COLORS.card, color: qapiView === 'trackers' ? '#fff' : COLORS.textDim }}>Trackers</button>
        <button onClick={() => setQapiView('reports')} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, fontFamily: 'Inter, sans-serif', background: qapiView === 'reports' ? COLORS.primary : COLORS.card, color: qapiView === 'reports' ? '#fff' : COLORS.textDim }}>Reports</button>
      </div>

      {qapiView === 'reports' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
          {qapiReports.map((report, index) => (
            <div key={`${report.title}-${index}`} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif', flex: 1 }}>{report.title}</div>
                <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, flexShrink: 0, background: `${freqColor(report.frequency)}18`, color: freqColor(report.frequency), fontFamily: 'Inter, sans-serif' }}>{report.frequency}</span>
              </div>
              <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 8, fontFamily: 'Inter, sans-serif' }}>{report.lastRun}</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.5, marginBottom: 16, fontFamily: 'Inter, sans-serif' }}>{report.desc}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate Now</button>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Download PDF</button>
                <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Export CSV</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
            {trackerPills.map((group) => (
              <button key={group.key} onClick={() => setActiveTracker(group.key)} style={{ padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, fontFamily: 'Inter, sans-serif', background: activeTracker === group.key ? COLORS.primary : COLORS.card, color: activeTracker === group.key ? '#fff' : COLORS.textDim }}>
                {group.label}
                {group.count > 0 && <span style={{ marginLeft: 6, padding: '2px 7px', borderRadius: 9999, fontSize: 10, fontWeight: 700, background: activeTracker === group.key ? 'rgba(255,255,255,0.25)' : `${COLORS.danger}22`, color: activeTracker === group.key ? '#fff' : COLORS.danger }}>{group.count}</span>}
              </button>
            ))}
          </div>

          {activeTracker === 'infections' && (
            <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
              <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Active Infections & Antibiotic Tracking</span><span style={{ fontSize: 12, color: COLORS.textDim, marginLeft: 12, fontFamily: 'Inter, sans-serif' }}>4 active cases</span></div>
                <button style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ Log New Infection</button>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>{['Patient', 'MRN', 'Type', 'Antibiotic', 'Start', 'Day', 'Culture', 'Status'].map((header) => <th key={header} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>)}</tr></thead>
                <tbody>
                  {infectionData.map((entry, index) => (
                    <tr key={`${entry.patient}-${index}`} style={{ borderBottom: index < infectionData.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }}>
                      <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.patient}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.mrn}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.type}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.primary, fontWeight: 500, fontFamily: 'Inter, sans-serif' }}>{entry.abx}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.startDate}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, fontWeight: 600, color: entry.dayOn > 7 ? COLORS.warning : COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.dayOn}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: entry.culture === 'Pending' ? COLORS.warning : COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.culture}</td>
                      <td style={{ padding: '12px 14px' }}><span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${statusColor(entry.status)}18`, color: statusColor(entry.status), fontFamily: 'Inter, sans-serif' }}>{entry.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTracker === 'falls' && (
            <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
              <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Falls Tracking</span><span style={{ fontSize: 12, color: COLORS.textDim, marginLeft: 12, fontFamily: 'Inter, sans-serif' }}>2 incidents this month</span></div>
                <button style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ Log Fall</button>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>{['Patient', 'MRN', 'Date', 'Location', 'Injury', 'Witnessed', 'Risk', 'Follow-Up'].map((header) => <th key={header} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{header}</th>)}</tr></thead>
                <tbody>
                  {fallsData.map((entry, index) => (
                    <tr key={`${entry.patient}-${index}`} style={{ borderBottom: index < fallsData.length - 1 ? `1px solid ${COLORS.border}` : 'none', cursor: 'pointer' }}>
                      <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.patient}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.mrn}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.date}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.location}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: entry.injury === 'No injury' ? COLORS.success : COLORS.warning, fontFamily: 'Inter, sans-serif' }}>{entry.injury}</td>
                      <td style={{ padding: '12px 14px', fontSize: 12, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{entry.witnessed}</td>
                      <td style={{ padding: '12px 14px' }}><span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: `${riskColor(entry.riskLevel)}18`, color: riskColor(entry.riskLevel), fontFamily: 'Inter, sans-serif' }}>{entry.riskLevel}</span></td>
                      <td style={{ padding: '12px 14px', fontSize: 11, color: COLORS.textDim, fontFamily: 'Inter, sans-serif', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.followUp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTracker === 'sentinel' && (
            <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
              <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>Sentinel Events</span><span style={{ fontSize: 12, color: COLORS.textDim, marginLeft: 12, fontFamily: 'Inter, sans-serif' }}>1 open event</span></div>
                <button style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: COLORS.danger, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>+ Report Sentinel Event</button>
              </div>
              {sentinelData.map((entry, index) => (
                <div key={`${entry.patient}-${index}`} style={{ padding: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div><span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>{entry.patient}</span><span style={{ fontSize: 12, color: COLORS.textDim, marginLeft: 10, fontFamily: 'Inter, sans-serif' }}>{entry.mrn}</span></div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.danger}18`, color: COLORS.danger, fontFamily: 'Inter, sans-serif' }}>{entry.severity}</span>
                      <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.danger}18`, color: COLORS.danger, fontFamily: 'Inter, sans-serif' }}>{entry.status}</span>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: COLORS.text, marginBottom: 12, fontFamily: 'Inter, sans-serif' }}>{entry.event}</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
                    {[{ label: 'Date', value: entry.date }, { label: 'Root Cause', value: entry.rootCause }, { label: 'Corrective Action', value: entry.corrective }, { label: 'Reported By', value: entry.reportedBy }].map((item) => (
                      <div key={item.label}><div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 2, fontFamily: 'Inter, sans-serif' }}>{item.label}</div><div style={{ fontSize: 12, color: COLORS.text, fontWeight: 500, fontFamily: 'Inter, sans-serif' }}>{item.value}</div></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {['wounds', 'medErrors', 'unsigned', 'overdue'].includes(activeTracker) && (
            <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 40, textAlign: 'center' }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, marginBottom: 6, fontFamily: 'Inter, sans-serif' }}>{trackerPills.find((group) => group.key === activeTracker)?.label} Tracker</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, fontFamily: 'Inter, sans-serif' }}>{trackerPills.find((group) => group.key === activeTracker)?.count} items requiring attention</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
