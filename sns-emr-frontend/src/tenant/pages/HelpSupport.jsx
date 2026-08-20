import React, { useMemo, useState } from 'react';
import { COLORS, S } from '../design';

const tabs = [
  { key: 'knowledge', label: 'Knowledge Base' },
  { key: 'tickets', label: 'Submit a Ticket' },
  { key: 'training', label: 'Training' },
  { key: 'status', label: 'System Status' },
  { key: 'release', label: 'Release Notes' },
];

const knowledgeItems = [
  { title: 'Getting Started', count: 12, tone: COLORS.teal },
  { title: 'Clinical Documentation', count: 18, tone: COLORS.blue },
  { title: 'Billing & Claims', count: 9, tone: COLORS.orange },
  { title: 'Compliance & QAPI', count: 14, tone: COLORS.green },
  { title: 'FAQs', count: 7, tone: COLORS.purple },
  { title: 'Video Tutorials', count: 5, tone: COLORS.pink },
  { title: 'API Docs', count: 3, tone: COLORS.yellow },
  { title: 'CMS Guidelines', count: 4, tone: COLORS.red },
];

const ticketRows = [
  { id: '#TCK-1048', subject: 'QIES export access issue', priority: 'High', status: 'Open', owner: 'IT Support' },
  { id: '#TCK-1037', subject: 'Clinical documentation template update', priority: 'Medium', status: 'In Review', owner: 'Clinical Ops' },
  { id: '#TCK-1028', subject: 'Billing file rejected by payer', priority: 'High', status: 'Pending', owner: 'Billing Team' },
  { id: '#TCK-1014', subject: 'Password reset after mobile lockout', priority: 'Low', status: 'Resolved', owner: 'Security' },
];

const trainingModules = [
  { title: 'Initial Intake & Admission Workflow', progress: 92, lessons: 8, duration: '32 min', team: 'All Staff' },
  { title: 'Clinical Documentation Standards', progress: 78, lessons: 10, duration: '41 min', team: 'RN / LVN / SC' },
  { title: 'Billing & Reimbursement Essentials', progress: 64, lessons: 7, duration: '28 min', team: 'Billing' },
  { title: 'QAPI Auditing & Incident Review', progress: 88, lessons: 9, duration: '35 min', team: 'Compliance' },
  { title: 'HIS / HOPE Reporting Workflow', progress: 56, lessons: 6, duration: '24 min', team: 'Clinical Admin' },
  { title: 'Security & Access Management', progress: 100, lessons: 5, duration: '18 min', team: 'All Staff' },
];

const healthServices = [
  { name: 'Authentication', status: 'Healthy', uptime: '99.98%', latency: '148 ms' },
  { name: 'Tenant Dashboard API', status: 'Healthy', uptime: '99.95%', latency: '211 ms' },
  { name: 'Clinical Records', status: 'Degraded', uptime: '98.80%', latency: '432 ms' },
  { name: 'Billing Sync', status: 'Healthy', uptime: '99.91%', latency: '185 ms' },
  { name: 'QAPI Reporting', status: 'Healthy', uptime: '99.97%', latency: '170 ms' },
  { name: 'Document Storage', status: 'Healthy', uptime: '99.96%', latency: '194 ms' },
  { name: 'Notification Queue', status: 'Healthy', uptime: '99.93%', latency: '203 ms' },
  { name: 'Portal Access', status: 'Healthy', uptime: '99.99%', latency: '121 ms' },
];

const incidents = [
  { title: 'Scheduled maintenance window', time: '2026-08-16 10:00 PM', status: 'Completed' },
  { title: 'Billing sync retry backlog', time: '2026-08-15 7:25 AM', status: 'Resolved' },
  { title: 'Clinical docs cache warm-up', time: '2026-08-14 2:15 PM', status: 'Completed' },
];

const releaseNotes = [
  { tag: 'New', title: 'Support portal restructure', detail: 'Improved FAQs, ticketing flow, and quick-access knowledge categories.' },
  { tag: 'Updated', title: 'HIS / HOPE reporting dashboard', detail: 'Added deadline tracking and a cleaner compliance summary view.' },
  { tag: 'Fixed', title: 'Billing claim alerting', detail: 'Resolved missed alerting for rejected or delayed payer responses.' },
  { tag: 'Patch', title: 'Clinical notes validation', detail: 'Reduced false warnings for unsigned progress note exceptions.' },
];

function statusColor(status) {
  if (status === 'Healthy') return COLORS.green;
  if (status === 'Degraded') return COLORS.orange;
  if (status === 'Resolved' || status === 'Completed') return COLORS.teal;
  if (status === 'Open' || status === 'Pending') return COLORS.red;
  if (status === 'In Review') return COLORS.blue;
  return COLORS.muted;
}

export default function HelpSupport() {
  const [activeTab, setActiveTab] = useState('knowledge');

  const content = useMemo(() => {
    switch (activeTab) {
      case 'knowledge':
        return (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {knowledgeItems.map((item) => (
              <div key={item.title} style={{ ...S.card, marginBottom: 0, padding: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ color: COLORS.white, fontWeight: 700, fontSize: 14 }}>{item.title}</span>
                  <span style={{ ...S.badge('rgba(148,163,184,0.12)', COLORS.muted), fontSize: 10 }}>{item.count}</span>
                </div>
                <div style={{ height: 6, borderRadius: 999, background: 'rgba(148,163,184,0.15)', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, item.count * 6)}%`, height: '100%', background: item.tone, borderRadius: 999 }} />
                </div>
              </div>
            ))}
          </div>
        );
      case 'tickets':
        return (
          <div style={{ ...S.card, marginBottom: 0, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '18px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: COLORS.white, fontSize: 16 }}>Recent tickets</h3>
              <button style={{ ...S.btn(COLORS.teal), padding: '8px 14px' }}>New Ticket</button>
            </div>
            <div style={{ display: 'grid' }}>
              {ticketRows.map((row) => (
                <div key={row.id} style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.5fr 0.8fr 0.9fr 1fr', gap: 12, padding: '14px 20px', borderBottom: `1px solid ${COLORS.border}` }}>
                  <span style={{ color: COLORS.white, fontWeight: 700 }}>{row.id}</span>
                  <span style={{ color: COLORS.muted }}>{row.subject}</span>
                  <span style={{ ...S.badge('rgba(148,163,184,0.12)', COLORS.muted), width: 'fit-content' }}>{row.priority}</span>
                  <span style={{ color: statusColor(row.status), fontWeight: 700 }}>{row.status}</span>
                  <span style={{ color: COLORS.dim }}>{row.owner}</span>
                </div>
              ))}
            </div>
          </div>
        );
      case 'training':
        return (
          <div style={{ display: 'grid', gap: 16 }}>
            {trainingModules.map((module) => (
              <div key={module.title} style={{ ...S.card, marginBottom: 0, padding: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 10 }}>
                  <div>
                    <div style={{ color: COLORS.white, fontWeight: 700, marginBottom: 4 }}>{module.title}</div>
                    <div style={{ color: COLORS.dim, fontSize: 12 }}>{module.team}</div>
                  </div>
                  <div style={{ color: COLORS.teal, fontSize: 12, fontWeight: 700 }}>{module.progress}%</div>
                </div>
                <div style={{ height: 8, borderRadius: 999, background: 'rgba(148,163,184,0.15)', overflow: 'hidden', marginBottom: 12 }}>
                  <div style={{ width: `${module.progress}%`, height: '100%', background: COLORS.teal, borderRadius: 999 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: COLORS.muted, fontSize: 12 }}>
                  <span>{module.lessons} lessons</span>
                  <span>{module.duration}</span>
                </div>
              </div>
            ))}
          </div>
        );
      case 'status':
        return (
          <div style={{ display: 'grid', gap: 20 }}>
            <div style={{ ...S.card, marginBottom: 0, padding: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ color: COLORS.white, fontWeight: 700, fontSize: 18 }}>Overall system status</div>
                <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.green), fontSize: 12 }}>Healthy</span>
              </div>
              <div style={{ color: COLORS.muted, fontSize: 13 }}>Last refreshed 2 minutes ago.</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
              {healthServices.map((service) => (
                <div key={service.name} style={{ ...S.card, marginBottom: 0, padding: 18 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <span style={{ color: COLORS.white, fontWeight: 700 }}>{service.name}</span>
                    <span style={{ ...S.badge('rgba(148,163,184,0.12)', statusColor(service.status)), fontSize: 10 }}>{service.status}</span>
                  </div>
                  <div style={{ color: COLORS.dim, fontSize: 12, display: 'grid', gap: 4 }}>
                    <div>Uptime: {service.uptime}</div>
                    <div>Latency: {service.latency}</div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ ...S.card, marginBottom: 0, padding: 18 }}>
              <h3 style={{ color: COLORS.white, margin: '0 0 14px', fontSize: 16 }}>Recent incident log</h3>
              <div style={{ display: 'grid', gap: 12 }}>
                {incidents.map((item) => (
                  <div key={item.title} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: `1px solid ${COLORS.border}`, paddingBottom: 10, gap: 12 }}>
                    <div>
                      <div style={{ color: COLORS.white, fontWeight: 600 }}>{item.title}</div>
                      <div style={{ color: COLORS.dim, fontSize: 12 }}>{item.time}</div>
                    </div>
                    <span style={{ ...S.badge('rgba(148,163,184,0.12)', statusColor(item.status)), fontSize: 10 }}>{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'release':
        return (
          <div style={{ display: 'grid', gap: 16 }}>
            {releaseNotes.map((note) => (
              <div key={note.title} style={{ ...S.card, marginBottom: 0, padding: 18 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                  <span style={{ ...S.badge('rgba(16,183,162,0.12)', COLORS.teal), fontSize: 10 }}>{note.tag}</span>
                  <h3 style={{ color: COLORS.white, margin: 0, fontSize: 16 }}>{note.title}</h3>
                </div>
                <div style={{ color: COLORS.muted, fontSize: 13 }}>{note.detail}</div>
              </div>
            ))}
          </div>
        );
      default:
        return null;
    }
  }, [activeTab]);

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Help & Support</h1>
          <p style={S.pageSubtitle}>Knowledge base, ticketing, training, service status, and app release history.</p>
        </div>
        <div style={{ color: COLORS.dim, fontSize: 12 }}>Support center</div>
      </div>

      <div style={{ ...S.card, marginBottom: 20, padding: '12px 14px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              style={{
                border: 'none',
                borderRadius: 999,
                padding: '9px 14px',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 700,
                background: activeTab === tab.key ? COLORS.teal : 'rgba(148,163,184,0.08)',
                color: activeTab === tab.key ? COLORS.white : COLORS.muted,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {content}
    </div>
  );
}
