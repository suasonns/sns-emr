import React from 'react';
import { COLORS, S } from '../OwnerDashboard';

const ANOMALIES = [
  {
    icon: '🔴',
    title: 'DENIAL SPIKE — Valley Hospice',
    time: '2 hours ago',
    desc: 'Denial rate jumped from 6.1% to 8.2% in 14 days. Root cause: Missing F2F documentation on 12 claims.',
    severity: 'SEVERITY: HIGH',
    sevColor: COLORS.red,
    action: 'Investigate',
  },
  {
    icon: '🟠',
    title: 'BILLING BOTTLENECK — Sunrise Health',
    time: '6 hours ago',
    desc: '38 patients not-ready status for >7 days. Blocker: unsigned clinical notes (14 patients). 23% above normal.',
    severity: 'SEVERITY: MEDIUM',
    sevColor: COLORS.orange,
    action: 'View Details',
  },
  {
    icon: '🟡',
    title: 'USAGE DROP — Pacific Hospice',
    time: '1 day ago',
    desc: 'Daily active users dropped 34% over 2 weeks. Last admin login: 12 days ago. Potential churn indicator.',
    severity: 'SEVERITY: LOW',
    sevColor: COLORS.blue,
    action: 'Contact Tenant',
  },
];

const PREDICTIONS = [
  { label: 'MRR Forecast', current: '$147.2K', predicted: '$156.8K', change: '+6.5%', changeColor: COLORS.teal },
  { label: 'Claims Volume', current: '2,847/mo', predicted: '3,120/mo', change: '+9.6%', changeColor: COLORS.teal },
  { label: 'Denial Rate', current: '4.3%', predicted: '3.8%', change: '-0.5%', changeColor: COLORS.green },
  { label: 'Clean Claim Rate', current: '92.1%', predicted: '94.3%', change: '+2.2%', changeColor: COLORS.teal },
  { label: 'Churn Probability', current: '0 tenants', predicted: '2 tenants', change: '8.3%', changeColor: COLORS.red },
  { label: 'NOE Compliance', current: '96.2%', predicted: '97.1%', change: '+0.9%', changeColor: COLORS.teal },
];

const RECOMMENDATIONS = [
  { impact: 'HIGH IMPACT', impactColor: COLORS.red, desc: 'Send compliance alert to Valley Hospice about F2F documentation gaps — could reduce denial rate by 2.1%' },
  { impact: 'HIGH IMPACT', impactColor: COLORS.red, desc: 'Schedule retention call with Pacific Hospice — churn probability: 67% without intervention' },
  { impact: 'MEDIUM IMPACT', impactColor: COLORS.orange, desc: 'Enable automated POC expiry reminders for 4 agencies with >5% expired POCs' },
  { impact: 'MEDIUM IMPACT', impactColor: COLORS.orange, desc: 'Upgrade Sunrise Health plan from Professional to Enterprise — usage patterns indicate readiness' },
  { impact: 'LOW IMPACT', impactColor: COLORS.teal, desc: 'Archive 3 inactive tenant accounts (no login >90 days) to clean up system resources' },
];

const ACTIVITY_LOG = [
  { time: '2:14 PM', type: 'Anomaly', typeColor: COLORS.red, desc: 'Denial spike detected', tenant: 'Valley Hospice', result: 'Alert created', resultColor: COLORS.red },
  { time: '1:45 PM', type: 'Prediction', typeColor: COLORS.blue, desc: 'Revenue forecast updated', tenant: 'All tenants', result: 'MRR +6.5%', resultColor: COLORS.teal },
  { time: '12:30 PM', type: 'Recommendation', typeColor: COLORS.purple, desc: 'POC compliance alert', tenant: 'Comfort Care', result: 'Auto-sent', resultColor: COLORS.teal },
  { time: '11:15 AM', type: 'Analysis', typeColor: COLORS.orange, desc: 'Billing readiness scan', tenant: 'All tenants', result: '3 issues found', resultColor: COLORS.orange },
  { time: '10:00 AM', type: 'Prediction', typeColor: COLORS.blue, desc: 'Churn risk recalculated', tenant: 'Pacific Hospice', result: 'Risk: 67%', resultColor: COLORS.red },
  { time: '9:30 AM', type: 'Anomaly', typeColor: COLORS.red, desc: 'Usage drop detected', tenant: 'Pacific Hospice', result: 'Alert created', resultColor: COLORS.red },
  { time: '8:00 AM', type: 'System', typeColor: COLORS.green, desc: 'Daily AI analysis completed', tenant: 'Platform', result: '847 predictions', resultColor: COLORS.teal },
];

const QUICK_PROMPTS = ['Denial trends', 'Revenue forecast', 'Compliance risks', 'Tenant health', 'System performance', 'Billing bottlenecks'];

export default function AICommandCenter() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>AI Command Center</h1>
          <p style={S.pageSubtitle}>Intelligent platform monitoring, anomaly detection, and natural language analytics across all tenants</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', background: COLORS.green + '22', borderRadius: 20 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: COLORS.green }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.green }}>AI Engine: Active</span>
          </span>
          <span style={{ fontSize: 12, color: COLORS.muted }}>Last Analysis: 2 min ago</span>
        </div>
      </div>

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'ACTIVE ANOMALIES', value: '3', sub: 'Requiring immediate audit', subExtra: '● Pulsing', subExtraColor: COLORS.red, dot: COLORS.red },
          { label: 'PREDICTIONS GENERATED', value: '847', sub: '90-day pipeline insights', dot: COLORS.green },
          { label: 'RECOMMENDATIONS', value: '12', sub: 'Ranked auto-action opportunities', dot: COLORS.green },
          { label: 'AI CONFIDENCE SCORE', value: '94.2%', sub: 'Overall analysis model health', dot: COLORS.green },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <p style={{ fontSize: 10, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
              {s.subExtra && <span style={{ fontSize: 10, fontWeight: 600, color: s.subExtraColor }}>● Pulsing</span>}
            </div>
            <p style={S.statValue}>{s.value}</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.sub}</p>
          </div>
        ))}
      </div>

      {/* AI Chat + Active Anomalies */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* AI Chat */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>SNS AI Assistant — Platform Intelligence</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>Ask questions about your platform in natural language</p>

          {/* User message */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <div style={{ background: COLORS.teal + '22', border: `1px solid ${COLORS.teal}44`, borderRadius: 12, padding: '12px 16px', maxWidth: '80%' }}>
              <p style={{ fontSize: 13, color: COLORS.white, margin: 0 }}>Which agencies have the highest denial rates this quarter?</p>
            </div>
          </div>

          {/* AI response */}
          <div style={{ background: COLORS.bg, borderRadius: 12, padding: 16, marginBottom: 16, border: `1px solid ${COLORS.border}` }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: 0, whiteSpace: 'pre-line', lineHeight: 1.6 }}>
{`Based on Q3 2026 data across all 24 active tenants:

Highest Denial Rates:
1. Valley Hospice — 8.2% (↑ 2.1% from Q2)
2. Aspen Health — 7.4% (↑ 0.8% from Q2)
3. Harbor Hospice — 6.1% (stable)

Platform Average: 4.3%

Key Finding: Valley Hospice denial spike is driven by 73% increase in "Missing F2F" denials. Recommend triggering compliance alert to their admin.`}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, padding: '8px 12px', background: COLORS.orange + '15', borderRadius: 8, border: `1px solid ${COLORS.orange}33` }}>
              <span style={{ color: COLORS.orange }}>●</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.orange }}>Suggested Action: Send compliance notification to Valley Hospice</span>
            </div>
            <button style={{ ...S.btn(COLORS.teal), marginTop: 12, fontSize: 11, padding: '8px 16px' }}>Execute Action</button>
          </div>

          {/* Quick prompts */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
            {QUICK_PROMPTS.map((p, i) => (
              <span key={i} style={{ padding: '6px 12px', borderRadius: 16, border: `1px solid ${COLORS.border}`, fontSize: 11, color: COLORS.muted, cursor: 'pointer' }}>{p}</span>
            ))}
          </div>

          {/* Input */}
          <div style={{ display: 'flex', gap: 8 }}>
            <input style={{ ...S.searchBar, paddingLeft: 12, flex: 1 }} placeholder="Ask about tenants, billing, compliance, revenue, system health..." readOnly />
            <button style={{ ...S.btn(COLORS.teal), padding: '10px 14px', borderRadius: '50%', fontSize: 16 }}>→</button>
          </div>
        </div>

        {/* Active Anomalies */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>ACTIVE ANOMALIES</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>AI-detected issues requiring attention</p>
          {ANOMALIES.map((a, i) => (
            <div key={i} style={{ padding: 16, background: COLORS.bg, borderRadius: 10, marginBottom: 12, border: `1px solid ${COLORS.border}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.white }}>{a.icon} {a.title}</span>
                <span style={{ fontSize: 11, color: COLORS.muted }}>{a.time}</span>
              </div>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 12px', lineHeight: 1.5 }}>{a.desc}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: a.sevColor }}>{a.severity}</span>
                <button style={{ ...S.btn(COLORS.teal), padding: '6px 16px', fontSize: 11 }}>{a.action}</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Predictions + Recommendations */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Predictions */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>REVENUE & COMPLIANCE PREDICTIONS</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>90-day forecast based on current trends</p>
          {PREDICTIONS.map((p, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: i < PREDICTIONS.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <span style={{ fontSize: 13, color: COLORS.muted, flex: 1 }}>{p.label}</span>
              <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted }}>{p.current}</span>
              <span style={{ fontSize: 13, color: COLORS.dim }}>→</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.white }}>{p.predicted}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: p.changeColor, minWidth: 40, textAlign: 'right' }}>{p.change}</span>
            </div>
          ))}
        </div>

        {/* Recommendations */}
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>AUTOMATED RECOMMENDATIONS</h3>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>AI-generated action items ranked by impact</p>
          {RECOMMENDATIONS.map((r, i) => (
            <div key={i} style={{ padding: '12px 0', borderBottom: i < RECOMMENDATIONS.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={S.badge(r.impactColor + '22', r.impactColor)}>{r.impact}</span>
                <span style={{ fontSize: 11, color: COLORS.muted }}>Status: Pending</span>
              </div>
              <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 8px', lineHeight: 1.5 }}>{r.desc}</p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button style={{ ...S.btn(COLORS.teal), padding: '5px 14px', fontSize: 11 }}>Approve</button>
                <button style={{ ...S.btnOutline, padding: '5px 14px', fontSize: 11 }}>Dismiss</button>
              </div>
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted }}>Auto-execute approved recommendations</span>
            <div style={{ width: 44, height: 24, borderRadius: 12, background: COLORS.border, position: 'relative', cursor: 'pointer' }}>
              <div style={{ width: 18, height: 18, borderRadius: '50%', background: COLORS.muted, position: 'absolute', top: 3, left: 3 }} />
            </div>
          </div>
        </div>
      </div>

      {/* AI Engine Activity Log */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>AI ENGINE ACTIVITY LOG</h3>
        <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 20px' }}>Recent automated system operations and predictions</p>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['TIME', 'TYPE', 'DESCRIPTION', 'TENANT', 'RESULT'].map(h => (
                <th key={h} style={{ ...S.tableHeader, textAlign: 'left' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ACTIVITY_LOG.map((a, i) => (
              <tr key={i}>
                <td style={S.tableCell}>{a.time}</td>
                <td style={{ ...S.tableCell }}><span style={S.badge(a.typeColor + '22', a.typeColor)}>{a.type}</span></td>
                <td style={S.tableCell}>{a.desc}</td>
                <td style={S.tableCell}>{a.tenant}</td>
                <td style={{ ...S.tableCell, fontWeight: 600, color: a.resultColor }}>{a.result}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ fontSize: 12, color: COLORS.muted }}>Showing 1-7 of 42 AI system activities</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={{ ...S.btnOutline, padding: '6px 14px', fontSize: 11 }}>Previous</button>
            <button style={{ ...S.btnOutline, padding: '6px 14px', fontSize: 11 }}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
