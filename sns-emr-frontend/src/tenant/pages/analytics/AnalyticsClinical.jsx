import React, { useState } from 'react';
import { COLORS } from '../../TenantDashboard';
import CustomReportBuilder from './CustomReportBuilder';

/**
 * AnalyticsClinical — Clinical tab inside Analytics.
 *
 * Has TWO views toggled by buttons at the top:
 * 1. "Standard Reports" (default) — The 11 pre-built regulatory report cards
 * 2. "Custom Builder" — The CustomReportBuilder component for ad-hoc reports
 *
 * The toggle buttons are styled as pill buttons. The active one is filled
 * with COLORS.primary (teal), the inactive one is outlined.
 */

const reports = [
 { title: 'Recertification Schedule', frequency: 'Daily', lastRun: 'Last run: Today, 08:00 AM', desc: 'Upcoming patients requiring clinical recertification reviews in the next 15 days.' },
 { title: 'Recertification Timeline', frequency: 'Weekly', lastRun: 'Last run: Oct 24, 2025', desc: 'Longitudinal view of 60-day benefit period milestones and critical regulatory boundaries.' },
 { title: 'Supervisory Visit Compliance', frequency: 'Weekly', lastRun: 'Last run: Yesterday', desc: 'Tracks mandatory 14-day supervisor check-ins for CHHAs and LPNs with alerts.' },
 { title: 'Visit Log', frequency: 'Daily', lastRun: 'Last run: Today, 07:45 AM', desc: 'Full diagnostic database of scheduled, completed, and missed visits by clinical discipline.' },
 { title: 'After-Hours Visit Log', frequency: 'Daily', lastRun: 'Last run: Today, 11:00 AM', desc: 'Comprehensive audit of triage, emergency, and on-call visits occurring after 5:00 PM.' },
 { title: 'Missing Documentation', frequency: 'Daily', lastRun: 'Last run: Today, 08:00 AM', desc: 'Urgent tracker of completed patient visits lacking a corresponding signed clinical note.' },
 { title: 'SIA Eligibility Tracker', frequency: 'Weekly', lastRun: 'Last run: Oct 22, 2025', desc: 'Service Intensity Add-on eligibility metrics for patients in their last 7 days of life.' },
 { title: 'SIA Visit Log', frequency: 'Daily', lastRun: 'Last run: Today, 08:00 AM', desc: 'RN and MSW visit tracking to ensure compliance with end-of-life continuous care mandates.' },
 { title: 'Missed Visit Alerts', frequency: 'Daily', lastRun: 'Last run: Today, 09:00 AM', desc: 'Urgent red-flag notification system for scheduled visits that were skipped or not documented.' },
 { title: 'ICD-10 Reference', frequency: 'Monthly', lastRun: 'Last run: Oct 01, 2025', desc: 'Master index mapping code assignment accuracy and principal hospice diagnosis audits.' },
 { title: 'Medication Reference', frequency: 'Monthly', lastRun: 'Last run: Oct 15, 2025', desc: 'Audit history of formulary drug approvals, dosage frequencies, and cost parameters.' },
];

const freqColor = (f) => {
 switch (f) {
 case 'Daily': return COLORS.primary;
 case 'Weekly': return '#6366f1';
 case 'Monthly': return COLORS.warning;
 default: return COLORS.textDim;
 }
};

export default function AnalyticsClinical() {
 const [view, setView] = useState('standard');

 const toggleBtnStyle = (isActive) => ({
 padding: '8px 18px',
 borderRadius: 8,
 fontWeight: 600,
 fontSize: 13,
 cursor: 'pointer',
 fontFamily: 'Inter, sans-serif',
 border: isActive ? 'none' : `1px solid ${COLORS.border}`,
 background: isActive ? COLORS.primary : 'transparent',
 color: isActive ? '#fff' : COLORS.text,
 });

 return (
 <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
 {/* View Toggle */}
 <div style={{ display: 'flex', gap: 8 }}>
 <button onClick={() => setView('standard')} style={toggleBtnStyle(view === 'standard')}>
 Standard Reports
 </button>
 <button onClick={() => setView('custom')} style={toggleBtnStyle(view === 'custom')}>
 Custom Builder
 </button>
 </div>

 {/* Conditional Content */}
 {view === 'standard' ? (
 <>
 <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif' }}>
 Standard Regulatory Reports ({reports.length} Available)
 </div>
 <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
 {reports.map((r, i) => (
 <div key={i} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
 <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, fontFamily: 'Inter, sans-serif', flex: 1 }}>{r.title}</div>
 <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, flexShrink: 0, background: `${freqColor(r.frequency)}18`, color: freqColor(r.frequency), fontFamily: 'Inter, sans-serif' }}>{r.frequency}</span>
 </div>
 <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 8, fontFamily: 'Inter, sans-serif' }}>{r.lastRun}</div>
 <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.5, marginBottom: 16, fontFamily: 'Inter, sans-serif' }}>{r.desc}</div>
 <div style={{ display: 'flex', gap: 8 }}>
 <button style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Generate</button>
 <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>↓ PDF</button>
 <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>↓ CSV</button>
 </div>
 </div>
 ))}
 </div>
 </>
 ) : (
 <CustomReportBuilder />
 )}
 </div>
 );
}
