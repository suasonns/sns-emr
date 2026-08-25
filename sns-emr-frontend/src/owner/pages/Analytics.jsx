import React, { useEffect, useState } from 'react';
import { COLORS, S } from '../design';
import { fetchOwnerAdoptionHealth } from '../../api/ownerAdmin';

function formatDay(iso) {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const res = await fetchOwnerAdoptionHealth();
        if (mounted) setData(res);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Failed to load adoption data');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const trend = data?.daily_active_trend || [];
  const maxActive = Math.max(1, ...trend.map((d) => d.active_users));

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Platform Analytics</h1>
          <p style={S.pageSubtitle}>Real platform adoption: who's actually logging in and using SNS.</p>
        </div>
      </div>

      {error ? (
        <div style={{ ...S.card, borderColor: COLORS.orange, color: COLORS.orange, fontSize: 13, marginBottom: 16 }}>{error}</div>
      ) : null}

      {/* Stats */}
      <div style={S.statsRow}>
        {[
          { label: 'DAILY ACTIVE USERS', value: data?.dau ?? 0, desc: 'Distinct logins, last 24h', dot: COLORS.green },
          { label: 'WEEKLY ACTIVE USERS', value: data?.wau ?? 0, desc: 'Distinct logins, last 7 days', dot: COLORS.blue },
          { label: 'MONTHLY ACTIVE USERS', value: data?.mau ?? 0, desc: 'Distinct logins, last 30 days', dot: COLORS.purple },
          { label: 'TOTAL TENANTS', value: data?.total_tenants ?? 0, desc: 'Registered agencies', dot: COLORS.green },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <div style={S.statDot(s.dot)} />
            <p style={{ fontSize: 11, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={S.statValue}>{loading ? '…' : s.value}</p>
            <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Daily Active Users Trend */}
      <div style={S.card}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.white, margin: '0 0 4px' }}>DAILY ACTIVE USERS (LAST 14 DAYS)</h3>
        <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 24px' }}>Distinct users with a successful login each day, from the real audit trail.</p>
        {loading ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</p>
        ) : trend.length === 0 ? (
          <p style={{ color: COLORS.muted, fontSize: 13 }}>No login activity recorded in this window.</p>
        ) : (
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: 180, padding: '0 8px', gap: 4 }}>
            {trend.map((d) => (
              <div key={d.date} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, flex: 1 }}>
                <span style={{ fontSize: 11, color: COLORS.muted }}>{d.active_users}</span>
                <div style={{ width: '60%', height: Math.max(4, (d.active_users / maxActive) * 140), background: COLORS.teal, borderRadius: 4 }} />
                <span style={{ fontSize: 10, color: COLORS.muted }}>{formatDay(d.date)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
