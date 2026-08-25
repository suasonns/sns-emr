import React, { useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import { fetchOwnerSystemHealth } from '../../api/ownerAdmin';

const SEVERITY_COLOR = {
  MINOR: COLORS.green,
  MODERATE: COLORS.orange,
  MAJOR: COLORS.red,
  CRITICAL: COLORS.red,
};

function formatTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatUptime(seconds) {
  if (typeof seconds !== 'number') return '—';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function humanizeAction(action) {
  if (!action) return '—';
  return action
    .toLowerCase()
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export default function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await fetchOwnerSystemHealth();
        if (mounted) setHealth(data);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Failed to load system health');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const reliability = health?.reliability;
  const security = health?.security;
  const dbHealthy = reliability?.db_connected;

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>System Health</h1>
          <p style={S.pageSubtitle}>Real database connectivity, backend uptime, incidents, and security signals.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: dbHealthy ? COLORS.green : COLORS.red, display: 'inline-block' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: dbHealthy ? COLORS.green : COLORS.red }}>
            {loading ? 'Checking…' : dbHealthy ? 'Database Connected' : 'Database Unreachable'}
          </span>
        </div>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginBottom: 16 }}>{error}</div>
      ) : null}

      {/* Reliability Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'DB LATENCY', value: reliability?.db_latency_ms != null ? `${reliability.db_latency_ms}ms` : '—', desc: 'Live SELECT 1 round-trip', dot: COLORS.green },
          { label: 'BACKEND UPTIME', value: formatUptime(reliability?.backend_uptime_seconds), desc: 'Since last process restart', dot: COLORS.green },
          { label: 'DATABASE SIZE', value: reliability?.db_size_pretty || '—', desc: 'Total platform storage', dot: COLORS.blue },
          { label: 'SYSTEM INCIDENTS', value: String(reliability?.system_incidents_total ?? 0), desc: 'All-time recorded incidents', dot: reliability?.system_incidents_total ? COLORS.orange : COLORS.green },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{loading ? '…' : s.value}</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Security Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'FAILED LOGINS (24H)', value: security?.failed_logins_24h ?? 0, dot: security?.failed_logins_24h ? COLORS.orange : COLORS.green },
          { label: 'FAILED LOGINS (7D)', value: security?.failed_logins_7d ?? 0, dot: security?.failed_logins_7d ? COLORS.orange : COLORS.green },
          { label: 'PASSWORD RESETS (7D)', value: security?.password_resets_7d ?? 0, dot: COLORS.blue },
          { label: 'PERMISSION CHANGES (7D)', value: security?.permission_changes_7d ?? 0, dot: COLORS.purple },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{loading ? '…' : s.value}</p>
          </div>
        ))}
      </div>

      {/* Recent Incidents + Security Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>RECENT INCIDENTS</h3>
          {loading ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
          ) : (reliability?.recent_incidents || []).length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>No incidents recorded.</p>
          ) : (
            (reliability.recent_incidents).map((inc) => (
              <div key={inc.incident_id} style={{ display: 'flex', alignItems: 'center', padding: '10px 0', borderBottom: `1px solid ${COLORS.border}` }}>
                <span style={{ flex: 1 }}>
                  <span style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.white }}>{humanizeAction(inc.incident_type)}</span>
                  <span style={{ display: 'block', fontSize: 11, color: COLORS.muted }}>{inc.tenant_name} · {formatTime(inc.created_at)}</span>
                </span>
                <span style={S.badge((SEVERITY_COLOR[inc.incident_severity] || COLORS.muted) + '22', SEVERITY_COLOR[inc.incident_severity] || COLORS.muted)}>{inc.incident_severity}</span>
              </div>
            ))
          )}
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>RECENT SECURITY EVENTS</h3>
          {loading ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
          ) : (security?.recent_events || []).length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 13 }}>No security events recorded.</p>
          ) : (
            (security.recent_events).map((ev) => (
              <div key={ev.log_id} style={{ display: 'flex', alignItems: 'center', padding: '10px 0', borderBottom: `1px solid ${COLORS.border}` }}>
                <span style={{ flex: 1 }}>
                  <span style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.white }}>{humanizeAction(ev.action)}</span>
                  <span style={{ display: 'block', fontSize: 11, color: COLORS.muted }}>{ev.user_display} · {ev.tenant_name}</span>
                </span>
                <span style={{ fontSize: 11, color: COLORS.muted, textAlign: 'right' }}>{formatTime(ev.created_at)}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
