import React, { useState } from 'react';
import { COLORS } from '../design';
import AnalyticsClinical from './analytics/AnalyticsClinical';
import AnalyticsIDG from './analytics/AnalyticsIDG';
import AnalyticsQA from './analytics/AnalyticsQA';
import AnalyticsBereavement from './analytics/AnalyticsBereavement';
import AnalyticsQAPI from './analytics/AnalyticsQAPI';
import AnalyticsAdministrative from './analytics/AnalyticsAdministrative';
import AnalyticsHR from './analytics/AnalyticsHR';
import AnalyticsFinancial from './analytics/AnalyticsFinancial';

const tabs = [
  { label: 'Clinical' },
  { label: 'IDG' },
  { label: 'QA' },
  { label: 'Bereavement' },
  { label: 'QAPI' },
  { label: 'Administrative' },
  { label: 'HR' },
  { label: 'Financial' },
];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('Clinical');

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, margin: 0, fontFamily: 'Inter, sans-serif' }}>Insights</h1>
          <p style={{ fontSize: 14, color: COLORS.textDim, margin: '6px 0 0', fontFamily: 'Inter, sans-serif' }}>
            Clinical, operational, compliance, and financial reporting with export-ready insights.
          </p>
        </div>
        <button style={{
          padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
          background: 'transparent', color: COLORS.text, fontSize: 13, fontWeight: 600,
          cursor: 'pointer', fontFamily: 'Inter, sans-serif',
        }}>Scheduled Exports</button>
      </div>

      <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 24, overflowX: 'auto' }}>
        {tabs.map((tab) => (
          <button
            key={tab.label}
            onClick={() => setActiveTab(tab.label)}
            style={{
              padding: '12px 18px', background: 'transparent', border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
              color: activeTab === tab.label ? COLORS.primary : COLORS.textDim,
              borderBottom: activeTab === tab.label ? `2px solid ${COLORS.primary}` : '2px solid transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'Clinical' && <AnalyticsClinical />}
      {activeTab === 'IDG' && <AnalyticsIDG />}
      {activeTab === 'QA' && <AnalyticsQA />}
      {activeTab === 'Bereavement' && <AnalyticsBereavement />}
      {activeTab === 'QAPI' && <AnalyticsQAPI />}
      {activeTab === 'Administrative' && <AnalyticsAdministrative />}
      {activeTab === 'HR' && <AnalyticsHR />}
      {activeTab === 'Financial' && <AnalyticsFinancial />}
    </div>
  );
}
