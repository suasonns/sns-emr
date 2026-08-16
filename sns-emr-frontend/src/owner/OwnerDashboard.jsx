import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  DashboardOverview,
  TenantManagement,
  SystemHealth,
  UserManagement,
  AuditLogs,
  Analytics,
  Settings,
  AICommandCenter,
} from './pages';
import { logout } from '../api/auth';
import { fetchOwnerDashboard } from '../api/dashboard';
import { getCurrentUser, hasOwnerRole } from '../api/session';
import { COLORS, S } from './design';

export { COLORS, S };

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: '📊' },
  { key: 'tenants', label: 'Tenant Management', icon: '🏢' },
  { key: 'health', label: 'System Health', icon: '⚡' },
  { key: 'users', label: 'User Management', icon: '👥' },
  { key: 'audit', label: 'Audit Logs', icon: '📋' },
  { key: 'analytics', label: 'Analytics', icon: '📈' },
  { key: 'settings', label: 'Settings', icon: '⚙️' },
  { key: 'ai', label: 'AI Command Center', icon: '🤖' },
];

const formatMetricValue = (value) => {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 });
  }
  if (typeof value === 'string') return value;
  return '—';
};

export default function OwnerDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const currentUser = getCurrentUser();
  const isAuthorized = !!currentUser && hasOwnerRole(currentUser);
  const userDisplayName = currentUser?.full_name || currentUser?.email || 'Platform Administrator';
  const userRole = currentUser?.role || 'SUPER ADMIN';

  const activeTab = useMemo(() => {
    const section = (location.pathname || '/owner/dashboard').split('/').filter(Boolean).at(-1) || 'dashboard';
    return NAV_ITEMS.some((item) => item.key === section) ? section : 'dashboard';
  }, [location.pathname]);

  useEffect(() => {
    let isMounted = true;

    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError('');
        const nextData = await fetchOwnerDashboard();
        if (isMounted) {
          setDashboardData(nextData);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(loadError?.message || 'Unable to load owner dashboard data.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadDashboard();
    return () => {
      isMounted = false;
    };
  }, []);

  const summaryCards = useMemo(() => {
    const metrics = Array.isArray(dashboardData?.metrics) ? dashboardData.metrics.slice(0, 4) : [];

    return metrics.map((metric, index) => ({
      key: metric.key || `metric-${index}`,
      label: metric.label || 'Metric',
      value: formatMetricValue(metric.value),
      strongLabel: metric.description || 'Owner dashboard metric',
    }));
  }, [dashboardData]);

  const retryLoad = () => {
    setError('');
    setLoading(true);
    fetchOwnerDashboard()
      .then((nextData) => {
        setDashboardData(nextData);
      })
      .catch((loadError) => {
        setError(loadError?.message || 'Unable to load owner dashboard data.');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleTabChange = (key) => {
    navigate(`/owner/${key}`);
  };

  const renderPage = () => {
    const pageProps = { data: dashboardData, loading, error };

    switch (activeTab) {
      case 'dashboard':
        return <DashboardOverview {...pageProps} />;
      case 'tenants':
        return <TenantManagement {...pageProps} />;
      case 'health':
        return <SystemHealth {...pageProps} />;
      case 'users':
        return <UserManagement {...pageProps} />;
      case 'audit':
        return <AuditLogs {...pageProps} />;
      case 'analytics':
        return <Analytics {...pageProps} />;
      case 'settings':
        return <Settings {...pageProps} />;
      case 'ai':
        return <AICommandCenter {...pageProps} />;
      default:
        return <DashboardOverview {...pageProps} />;
    }
  };

  if (!isAuthorized) {
    return (
      <div style={{ ...S.container, alignItems: 'center', justifyContent: 'center', padding: 24 }} role="alert">
        <div style={{ ...S.card, maxWidth: 480, padding: 28 }}>
          <h2 style={{ margin: 0, color: COLORS.white }}>Owner access restricted</h2>
          <p style={{ margin: '12px 0 0', color: COLORS.muted, lineHeight: 1.6 }}>
            This dashboard is limited to platform owner or super-admin accounts. Please sign in with an authorized administrator profile.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ ...S.container, alignItems: 'center', justifyContent: 'center', padding: 24 }} role="status" aria-live="polite">
        <div style={{ ...S.card, maxWidth: 460, padding: 28, textAlign: 'center' }}>
          <div style={{ color: COLORS.teal, fontWeight: 700, fontSize: 16 }}>Loading owner dashboard…</div>
          <div style={{ marginTop: 10, color: COLORS.muted, fontSize: 13 }}>
            Pulling tenant health, platform metrics, and operational status.
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ ...S.container, alignItems: 'center', justifyContent: 'center', padding: 24 }} role="alert">
        <div style={{ ...S.card, maxWidth: 520, padding: 28 }}>
          <h2 style={{ margin: 0, color: COLORS.white }}>Owner dashboard unavailable</h2>
          <p style={{ margin: '12px 0 0', color: COLORS.muted, lineHeight: 1.6 }}>{error}</p>
          <button type="button" onClick={retryLoad} style={{ ...S.btn(COLORS.teal), marginTop: 20 }}>
            Retry loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={S.container}>
      <div style={S.sidebar}>
        <div style={S.logo}>
          <p style={S.logoText}>SNS Hospice Solutions</p>
          <p style={S.logoSub}>PLATFORM OWNER</p>
        </div>

        <div style={S.nav} aria-label="Owner navigation">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              aria-pressed={activeTab === item.key}
              aria-current={activeTab === item.key ? 'page' : undefined}
              style={S.navItem(activeTab === item.key)}
              onClick={() => handleTabChange(item.key)}
            >
              <span style={S.navIcon}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>

        <div style={S.userBadge}>
          <p style={S.userName}>{userDisplayName}</p>
          <p style={S.userRole}>{userRole.toUpperCase()}</p>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            style={{
              marginTop: 10,
              width: '100%',
              background: 'transparent',
              color: COLORS.muted,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: '8px 10px',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      <div style={S.main}>
        {summaryCards.length > 0 && (
          <div style={S.statsRow} aria-live="polite">
            {summaryCards.map((stat, index) => (
              <div key={stat.key || index} style={S.statCard}>
                <span style={S.statDot(index % 2 === 0 ? COLORS.teal : COLORS.purple)} />
                <p style={S.statLabel}>{stat.label}</p>
                <div style={S.statValue}>{stat.value}</div>
                <div style={S.statSub(COLORS.teal)}>{stat.strongLabel}</div>
              </div>
            ))}
          </div>
        )}

        {renderPage()}
      </div>
    </div>
  );
}
