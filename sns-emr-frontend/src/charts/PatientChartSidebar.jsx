import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useThemeMode } from '../theme/theme';

const getColors = (mode) => mode === 'light' ? {
  bg: '#edf5f4',
  card: '#ffffff',
  border: '#d7e4ea',
  teal: '#0d7d7a',
  white: '#18354c',
  label: '#607388',
  text: '#1d2d3d',
  hover: '#edf6f7',
  activeBg: '#dcf7f4',
  success: '#2b7f62',
  surface: '#eaf3f5',
  soft: '#f7fbfb',
  subtle: '#eef6f8',
} : {
  bg: '#0f172a',
  card: '#111827',
  border: '#2d3a4a',
  teal: '#10b7a2',
  white: '#f8fafc',
  label: '#9aaab9',
  text: '#e2e8f0',
  hover: '#1a2636',
  activeBg: '#112b2b',
  success: '#34d399',
  surface: '#111d2d',
  soft: '#121f2f',
  subtle: '#172637',
};

const navSections = [
  { label: 'Facesheet', key: 'facesheet', children: [] },
  { label: 'Care Overview', key: 'care-overview', children: [] },
  { label: 'Intake & Admission', key: 'intake', children: [
    { label: 'Consent & Notifications', key: 'consent' },
    { label: 'Chart Completion Checklist', key: 'chart-checklist' },
    { label: 'Staff Assignment', key: 'staff-assignment' },
  ] },
  { label: 'Clinical Assessments', key: 'assessments', children: [
    { label: 'Nursing Assessment', key: 'nursing-assessment' },
    { label: 'Spiritual Assessment', key: 'spiritual-assessment' },
    { label: 'Psychosocial Assessment', key: 'psychosocial-assessment' },
    { label: 'Assessment History', key: 'assessment-history' },
  ] },
  { label: 'Visit Notes', key: 'visit-notes', children: [
    { label: 'Add New Visit', key: 'add-visit' },
    { label: 'My Visit Notes', key: 'my-visit-notes' },
    { label: 'Visit History', key: 'visit-history' },
  ] },
  { label: 'Tx / Meds / DME', key: 'tx-meds', children: [
    { label: 'Add New Order', key: 'add-order' },
    { label: 'Current Medications', key: 'current-meds' },
    { label: 'Medication History', key: 'med-history' },
    { label: 'DME Orders', key: 'dme-orders' },
  ] },
  { label: 'Physician Orders', key: 'physician-orders', children: [
    { label: 'Add New MD Order', key: 'add-md-order' },
    { label: 'CTI (Cert / Recert)', key: 'cti' },
    { label: 'F2F Visit Notes', key: 'f2f' },
    { label: 'Order History', key: 'order-history' },
  ] },
  { label: 'IDG', key: 'idg', children: [
    { label: 'Add New IDG', key: 'add-idg' },
    { label: 'IDG History', key: 'idg-history' },
  ] },
  { label: 'Plan of Care (POC)', key: 'poc', children: [
    { label: 'POC Summary', key: 'poc-summary' },
    { label: 'POC Goals & Interventions', key: 'poc-goals' },
    { label: 'Add / Update POC', key: 'add-poc' },
    { label: 'POC History', key: 'poc-history' },
  ] },
  { label: 'Home Health Aide (CHHA)', key: 'chha', children: [
    { label: 'CHHA Assignment', key: 'chha-assignment' },
    { label: 'CHHA Visits', key: 'chha-visits' },
    { label: 'CHHA Notes History', key: 'chha-notes' },
    { label: 'CHHA CC Visit', key: 'chha-cc' },
  ] },
  { label: 'Volunteer Services', key: 'volunteer', children: [] },
  { label: 'Bereavement', key: 'bereavement', children: [] },
  { label: 'Compliance & HOPE', key: 'compliance', children: [
    { label: 'LCD Eligibility', key: 'lcd-eligibility' },
    { label: 'HOPE - Admission', key: 'hope-admission' },
    { label: 'HOPE - HUV1', key: 'hope-huv1' },
    { label: 'HOPE - HUV2', key: 'hope-huv2' },
    { label: 'HOPE - Discharge', key: 'hope-discharge' },
    { label: 'Decline of Status', key: 'decline-of-status' },
  ] },
  { label: 'Issues & Outcomes', key: 'issues', children: [] },
  { label: 'Incident Logs', key: 'incidents', children: [] },
  { label: 'Documents & Images', key: 'documents', children: [
    { label: 'All Documents', key: 'all-docs' },
    { label: 'Intake Docs', key: 'intake-docs' },
    { label: 'Other Files', key: 'other-files' },
  ] },
  { label: 'Communication Log', key: 'comm-log', children: [] },
  { label: 'Discharge Planning', key: 'discharge', children: [] },
  { label: 'Care Team', key: 'care-team', children: [] },
  { label: 'Faxes', key: 'faxes', children: [] },
  { label: 'Visit Calendar', key: 'visit-calendar', children: [] },
];

const PatientChartSidebar = ({ activeSection = 'facesheet', onNavigate, patient }) => {
  const { mode } = useThemeMode();
  const COLORS = getColors(mode);
  const navigate = useNavigate();
  const [expandedSections, setExpandedSections] = useState([
    'intake', 'assessments', 'visit-notes', 'tx-meds', 'physician-orders', 'idg', 'poc', 'chha', 'compliance', 'documents',
  ]);

  const toggleSection = (key) => {
    setExpandedSections((prev) => prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]);
  };

  const handleClick = (key, hasChildren) => {
    if (hasChildren) toggleSection(key);
    else onNavigate?.(key);
  };

  const pat = patient || {
    name: 'Loren B Shields',
    mrn: '054/782',
    status: 'ACTIVE',
    primaryDx: 'G31.1 (Senile Degen.)',
    recentComms: 'Maria Shields - 08/14',
    primaryMD: 'Dr. Robert Hayes, MD',
    lastVisit: '08/10/2026 - RN Visit',
  };

  return (
    <div style={{ width: 'clamp(200px, 21vw, 240px)', minWidth: 180, maxWidth: '28vw', height: '100vh', backgroundColor: COLORS.bg, borderRight: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: "'Inter', sans-serif" }}>
      <div style={{ padding: '10px 10px 8px', borderBottom: `1px solid ${COLORS.border}`, backgroundColor: COLORS.soft }}>
        <button
          onClick={() => navigate('/portal')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            background: 'none',
            border: `1px solid ${COLORS.border}`,
            borderRadius: 6,
            color: COLORS.teal,
            fontSize: 10.5,
            fontWeight: 600,
            padding: '4px 8px',
            marginBottom: 8,
            cursor: 'pointer',
            width: '100%',
          }}
        >
          ← Dashboard
        </button>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ color: COLORS.white, fontSize: 13, fontWeight: 700, lineHeight: 1.2 }}>{pat.name}</span>
          <span style={{ backgroundColor: COLORS.success, color: '#ffffff', fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 4, letterSpacing: 0.4 }}>{pat.status}</span>
        </div>
        <span style={{ color: COLORS.label, fontSize: 10, marginTop: 3, display: 'block', letterSpacing: 0.2 }}>MRN: {pat.mrn}</span>
      </div>

      <div style={{ padding: '8px 10px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 10, backgroundColor: COLORS.subtle }}>
        {[
          { label: 'Primary Dx', value: pat.primaryDx },
          { label: 'Recent Comms', value: pat.recentComms },
          { label: 'Primary MD', value: pat.primaryMD },
          { label: 'Last Visit', value: pat.lastVisit },
        ].map((item) => (
          <div key={item.label} style={{ display: 'grid', gridTemplateColumns: '66px 1fr', gap: 6, alignItems: 'center', marginBottom: 4 }}>
            <span style={{ color: COLORS.label, fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.6 }}>{item.label}</span>
            <span style={{ color: COLORS.text, fontSize: 10, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.value}</span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0', backgroundColor: COLORS.bg }}>
        {navSections.map((section) => {
          const isExpanded = expandedSections.includes(section.key);
          const hasChildren = section.children.length > 0;
          const isActive = activeSection === section.key;
          return (
            <div key={section.key}>
              <div
                onClick={() => handleClick(section.key, hasChildren)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '5px 10px 5px 12px',
                  cursor: 'pointer',
                  backgroundColor: isActive ? COLORS.activeBg : 'transparent',
                  borderLeft: isActive ? `2px solid ${COLORS.teal}` : '2px solid transparent',
                  boxShadow: isActive ? `inset 0 1px 0 ${COLORS.border}` : 'none',
                  transition: 'background-color 0.15s ease',
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = COLORS.hover; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
              >
                {hasChildren && <span style={{ color: COLORS.label, fontSize: 9, marginRight: 5, transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.15s', display: 'inline-block', width: 10 }}>▶</span>}
                <span style={{ color: isActive ? COLORS.teal : COLORS.text, fontSize: 11.5, fontWeight: isActive ? 700 : 500, marginLeft: hasChildren ? 0 : 13 }}>{section.label}</span>
              </div>
              {hasChildren && isExpanded && section.children.map((child) => {
                const isChildActive = activeSection === child.key;
                return (
                  <div
                    key={child.key}
                    onClick={() => onNavigate?.(child.key)}
                    style={{
                      padding: '4px 10px 4px 30px',
                      cursor: 'pointer',
                      backgroundColor: isChildActive ? COLORS.activeBg : 'transparent',
                      borderLeft: isChildActive ? `2px solid ${COLORS.teal}` : '2px solid transparent',
                    }}
                    onMouseEnter={(e) => { if (!isChildActive) e.currentTarget.style.backgroundColor = COLORS.hover; }}
                    onMouseLeave={(e) => { if (!isChildActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <span style={{ color: isChildActive ? COLORS.teal : COLORS.label, fontSize: 10.5, fontWeight: isChildActive ? 600 : 400 }}>{child.label}</span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      <div style={{ padding: '8px 10px', borderTop: `1px solid ${COLORS.border}`, fontSize: 9, backgroundColor: COLORS.surface }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ color: COLORS.label, letterSpacing: 0.7, fontWeight: 700 }}>DISCHARGE STATUS</span>
          <span style={{ color: COLORS.success, fontWeight: 700 }}>ACTIVE</span>
        </div>
        {[
          { label: 'RN Visit', value: '3 days ago' },
          { label: 'MSW Visit', value: '1 week ago' },
          { label: 'SC Visit', value: '4 days ago' },
        ].map((v) => (
          <div key={v.label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
            <span style={{ color: COLORS.label }}>{v.label}</span>
            <span style={{ color: COLORS.text }}>{v.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PatientChartSidebar;
