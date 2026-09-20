import React from 'react';
import { IconSparkles } from '../shell/icons';

/**
 * Redesigned Owner Dashboard landing page ("SNS Operations Command Center").
 *
 * IMPORTANT — data reality check (do not remove this comment):
 * Only the Agencies pill row is wired to real data (the tenant list already
 * used elsewhere in the Owner Platform). Everything else on this page —
 * the AI-generated Operations Briefing narrative, the Platform Pulse health
 * score / AI-quality figures, the Actions & Insights list, and the Business
 * Snapshot (revenue/adoption/support) — has no backend yet: there is no AI
 * narrative pipeline, no health-scoring service, and no revenue/adoption/
 * support aggregation. This page renders the full approved Figma visual
 * using the same SAMPLE figures the design was reviewed with, so the layout
 * and interaction can be validated, but every AI/metric panel carries a
 * visible "PREVIEW — sample data" badge so nobody mistakes it for live
 * production data. See docs/future-improvements/owner/ for the tracked
 * backend work required to make each section real.
 */

const actionsData = [
  { priority: 'CRITICAL', text: 'Love & Faith Hospice: No admin login for 21 days', action: 'Take Action' },
  { priority: 'HIGH', text: 'North East Billing: Platform onboarding 3 steps remaining', action: 'Take Action' },
  { priority: 'HIGH', text: 'Clinical Notes AI quality drifting – review recommended', action: 'Take Action' },
  { priority: 'MONITOR', text: 'Revenue forecast: $268K next month (+8.3% projected)', insight: 'FYI' },
  { priority: 'MONITOR', text: 'Love & Faith may need onboarding support if inactive past 30 days', insight: 'FYI' },
  { priority: 'MONITOR', text: 'Platform adoption trending up 3% month-over-month', insight: 'FYI' },
];

const priorityStyles = {
  CRITICAL: {
    tag: 'bg-status-critical/10 border border-status-critical/20 text-status-critical',
    row: 'shadow-critical-glow',
  },
  HIGH: {
    tag: 'bg-status-high/10 border border-status-high/20 text-status-high',
    row: 'shadow-high-glow',
  },
  MONITOR: {
    tag: 'bg-status-monitor/10 border border-status-monitor/20 text-status-monitor',
    row: '',
  },
};

const IconInfo = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-text-secondary">
    <rect x="1" y="1" width="12" height="12" rx="3" />
    <path d="M7 5v4M7 3.5v.01" />
  </svg>
);

const IconTrendUp = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 9l3.5-3.5L7 8l4-5" />
    <path d="M8 3h3v3" />
  </svg>
);

const IconExternal = ({ className = '' }) => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9 3L3 9M9 3H5M9 3v4" />
  </svg>
);

function PreviewBadge({ className = '' }) {
  return (
    <span className={`px-2 py-1 rounded-md bg-[var(--owner-preview-badge-bg)] border border-[var(--owner-preview-badge-border)] font-mono font-bold text-[10px] text-status-high ${className}`}>
      PREVIEW — SAMPLE DATA
    </span>
  );
}

function OperationsBriefing() {
  return (
    <section className="p-4 rounded-2xl bg-gradient-to-b from-ai-gradient-start to-ai-bg/60 border border-ai/20 shadow-ai-panel">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2 text-ai">
          <IconSparkles />
          <span className="font-bold text-xs">Operations Briefing</span>
        </div>
        <PreviewBadge />
      </div>

      <h1 className="font-bold text-[28px] text-text-primary mb-2">Good morning, Romel</h1>
      <p className="text-sm leading-relaxed text-text-secondary mb-3">
        Everything is running smoothly. All core services are healthy and{' '}
        <strong className="font-semibold text-text-primary">v2.14.3</strong> deployed without issues.
        One item needs your attention –{' '}
        <strong className="font-semibold text-text-primary">Love &amp; Faith Hospice</strong>, your
        production agency, hasn't had an admin login in 21 days.{' '}
        <strong className="font-semibold text-text-primary">North East Billing</strong>, your
        billing company, has an incomplete platform setup.
      </p>

      <div className="flex gap-3">
        {[
          { text: 'Love & Faith Hospice: Zero activity from admin tier for 21 days.', btn: 'Investigate' },
          { text: 'North East Billing: Platform setup incomplete – 3 of 6 onboarding steps pending.', btn: 'Review Setup' },
        ].map((card) => (
          <div
            key={card.btn}
            className="flex-1 flex items-center justify-between px-3.5 py-2.5 rounded-lg bg-sns-row border border-status-high/20 shadow-[0_4px_12px_rgba(56,189,248,0.06)]"
          >
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <span className="w-2.5 h-2.5 rounded-full bg-status-high shrink-0" />
              <span className="text-sm font-medium text-text-primary truncate">{card.text}</span>
            </div>
            <button
              type="button"
              className="ml-3 shrink-0 px-3 py-1.5 rounded-md bg-[var(--owner-btn-secondary-bg)] border border-[var(--owner-btn-secondary-border)] font-semibold text-xs text-ai cursor-pointer hover:bg-[var(--owner-btn-secondary-hover)] transition-colors"
            >
              {card.btn}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

function PlatformPulse() {
  return (
    <section className="flex items-center gap-3 px-3 py-2.5 min-h-[68px] rounded-xl bg-sns-pulse border border-sns-border shadow-panel">
      <div className="w-12 h-12 relative shrink-0 leading-none">
        <svg width="48" height="48" viewBox="0 0 48 48" className="block">
          <circle cx="24" cy="24" r="19" fill="none" stroke="var(--owner-gauge-track)" strokeWidth="5" />
          <circle
            cx="24" cy="24" r="19" fill="none" stroke="#10B981" strokeWidth="5"
            strokeDasharray={`${2 * Math.PI * 19 * 0.97} ${2 * Math.PI * 19 * 0.03}`}
            strokeLinecap="round" transform="rotate(-90 24 24)"
          />
          <text
            x="24" y="24.5" textAnchor="middle" dominantBaseline="central"
            className="font-mono font-bold text-text-primary" style={{ fontSize: '13px' }} fill="currentColor"
          >
            97
          </text>
        </svg>
      </div>

      <div className="flex flex-col gap-0.5">
        <span className="font-semibold text-[13px] text-text-primary">Healthy</span>
        <div className="flex gap-2 text-[11px] text-text-secondary">
          {['Auth 99.99%', 'Sync <200ms', 'AI 99.7%', 'DB 34%', 'Storage 28%'].map((s, i, a) => (
            <React.Fragment key={s}>
              <span>{s}</span>
              {i < a.length - 1 && <span className="text-text-tertiary">·</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="w-px h-6 bg-sns-border shrink-0" />

      <div className="flex items-center gap-3 px-2.5 py-1.5 rounded-[10px] bg-ai-bg border border-ai/20">
        <span className="font-semibold text-xs text-ai">AI</span>
        <div className="flex gap-2 text-xs font-semibold text-text-primary">
          {['99.7% available', 'Quality 94.2%', '0 guardrail events'].map((m, i, a) => (
            <React.Fragment key={m}>
              <span>{m}</span>
              {i < a.length - 1 && <span className="text-text-secondary font-normal">·</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="w-px h-6 bg-sns-border shrink-0" />

      <div className="flex gap-2">
        <span className="px-2 py-1 rounded-md bg-status-healthy/10 border border-status-healthy/20 font-mono font-bold text-[11px] text-status-healthy">
          v2.14.3 Stable
        </span>
        <span className="px-2 py-1 rounded-md bg-status-high/10 border border-status-high/20 font-mono font-bold text-[11px] text-status-high">
          v2.15.0-rc1 Validating
        </span>
      </div>

      <div className="flex-1" />
      <PreviewBadge />
    </section>
  );
}

function ActionsInsights() {
  return (
    <section className="p-4 rounded-2xl bg-gradient-to-b from-ai-gradient-start to-ai-bg/60 border border-ai/20 shadow-ai-panel">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2 text-ai">
          <IconSparkles />
          <span className="font-bold text-[13px]">Actions &amp; Insights</span>
        </div>
        <PreviewBadge />
      </div>

      <div className="flex flex-col gap-2">
        {actionsData.map((item, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 p-2.5 rounded-[10px] bg-sns-row border border-sns-border ${priorityStyles[item.priority].row}`}
          >
            <span className={`px-2 py-1 rounded-full font-mono font-bold text-[11px] whitespace-nowrap shrink-0 ${priorityStyles[item.priority].tag}`}>
              {item.priority}
            </span>
            <span className="flex-1 text-[13px] font-medium text-text-primary">{item.text}</span>
            {item.action ? (
              <button
                type="button"
                className="shrink-0 px-2.5 py-1 rounded-md bg-transparent border border-ai/20 font-semibold text-[11px] text-ai cursor-pointer shadow-ai-btn hover:bg-ai/5 transition-colors"
              >
                {item.action}
              </button>
            ) : (
              <span className="shrink-0 flex items-center gap-1.5 text-xs text-text-secondary">
                <IconInfo />
                {item.insight}
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function BusinessSnapshot() {
  return (
    <section className="p-4 rounded-2xl bg-sns-pulse border border-sns-border shadow-panel">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-bold text-[13px] text-text-tertiary uppercase tracking-wider">Business Snapshot</h2>
        <PreviewBadge />
      </div>
      <div className="flex gap-3">
        <div className="w-[420px] shrink-0 p-3 rounded-xl bg-sns-column border border-sns-border flex flex-col gap-2">
          <span className="font-semibold text-xs text-text-secondary">Revenue</span>
          <span className="font-mono font-bold text-4xl text-text-primary">$247,500/mo</span>
          <span className="flex items-center gap-1 text-xs font-semibold text-status-healthy">
            <IconTrendUp /> +12% MoM
          </span>
          <span className="text-xs text-status-high">$12,400 at risk – 1 agency delayed</span>
          <span className="text-xs text-text-secondary">Collection rate 94.2%</span>
        </div>

        <div className="w-px self-stretch bg-sns-border my-5 shrink-0" />

        <div className="flex-1 p-3 rounded-xl bg-sns-column border border-sns-border flex flex-col gap-2">
          <span className="font-semibold text-xs text-text-secondary">Adoption</span>
          <span className="font-mono font-bold text-[28px] text-text-primary">87%</span>
          <span className="text-xs text-text-secondary">Overall platform adoption</span>
          <span className="text-xs text-text-secondary">Notes 45% · Sched 89% · Bill 94% · Assess 78%</span>
          <span className="text-xs text-text-secondary">4 of 5 agencies onboarded</span>
          <span className="text-xs text-text-secondary">Training engagement 68%</span>
        </div>

        <div className="w-px self-stretch bg-sns-border my-5 shrink-0" />

        <div className="flex-1 p-3 rounded-xl bg-sns-column border border-sns-border flex flex-col gap-2">
          <span className="font-semibold text-xs text-text-secondary">Support</span>
          <span className="font-mono font-bold text-[28px] text-text-primary">3 open requests</span>
          <span className="text-xs text-status-high">2 new this week</span>
          <span className="text-xs text-status-high">1 agency needs assistance (Love &amp; Faith)</span>
          <span className="text-xs text-status-healthy">0 escalations ✓</span>
          <span className="text-xs text-text-secondary">2 implementation items pending</span>
        </div>
      </div>
    </section>
  );
}

/** Agency pills — the one section wired to real data (falls back to an
 * empty-state message only while tenants are still loading or empty). */
function AgencyPills({ tenants = [], loading }) {
  const pills = tenants.slice(0, 8).map((t) => ({
    name: t.display_name || t.legal_name || 'Unnamed agency',
    value: t.status || '—',
    variant: t.status === 'SUSPENDED' ? 'warning' : 'neutral',
  }));

  return (
    <div>
      <h3 className="font-bold text-[11px] text-text-tertiary uppercase tracking-wider mb-2">Agencies</h3>
      {loading ? (
        <p className="text-xs text-text-secondary">Loading agencies…</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {pills.map((agency) => (
            <div
              key={agency.name}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-full border ${
                agency.variant === 'warning'
                  ? 'bg-status-high/10 border-status-high/20'
                  : 'bg-[var(--owner-pill-neutral-bg)] border-sns-pill-border'
              }`}
            >
              <span className="font-semibold text-[13px] text-text-primary">{agency.name}</span>
              <span className="w-px h-2.5 bg-sns-border" />
              <div className="flex items-center gap-1">
                <span className={`font-bold text-[13px] ${agency.variant === 'warning' ? 'text-status-high' : 'text-text-secondary'}`}>
                  {agency.value}
                </span>
                <IconExternal className={agency.variant === 'warning' ? 'text-status-high' : 'text-text-secondary'} />
              </div>
            </div>
          ))}
          {pills.length === 0 && <span className="text-xs text-text-secondary">No agencies yet.</span>}
        </div>
      )}
    </div>
  );
}

export default function DashboardOverviewV2({ tenants = [], tenantsLoading = false }) {
  return (
    <div className="flex flex-col gap-4 p-4 px-5">
      <OperationsBriefing />
      <PlatformPulse />
      <ActionsInsights />
      <BusinessSnapshot />
      <AgencyPills tenants={tenants} loading={tenantsLoading} />
    </div>
  );
}
