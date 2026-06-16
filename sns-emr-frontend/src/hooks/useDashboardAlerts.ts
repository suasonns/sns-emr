
// src/hooks/useDashboardAlerts.ts

import { useEffect, useMemo, useState } from 'react';
import { fetchSidebarAlertCounts, SidebarAlertCounts } from '../api/dashboard';

const DEFAULT_COUNTS: SidebarAlertCounts = {
  tasks: 0,
  incidents: 0,
  blockers: 0,
};

export function severityForCount(count: number): 'success' | 'warning' | 'error' {
  if (count <= 0) return 'success';
  if (count < 3) return 'warning';
  return 'error';
}

export function useDashboardAlerts(role: string, refreshMs = 30000) {
  const [counts, setCounts] = useState<SidebarAlertCounts>(DEFAULT_COUNTS);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const next = await fetchSidebarAlertCounts(role);
        if (!mounted) return;
        setCounts(next);
        setError('');
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : 'Failed to load alerts');
      } finally {
        if (!mounted) return;
        setLoading(false);
      }
    };

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, refreshMs);

    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [role, refreshMs]);

  const total = useMemo(
    () => counts.tasks + counts.incidents + counts.blockers,
    [counts]
  );

  return {
    counts,
    total,
    loading,
    error,
  };
}
