import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchBillableAgencies, type BillableAgency } from "../../api/dashboard";

type AgencyContextValue = {
  agencies: BillableAgency[];
  selectedAgencyId: string;
  setSelectedAgencyId: (tenantId: string) => void;
  loading: boolean;
  error: string | null;
};

const AgencyContext = createContext<AgencyContextValue | null>(null);

// Shared "which agency am I looking at" state for every page inside the
// Biller's Dashboard sidebar shell -- reuses the real
// resolve_billing_scope_tenant_id-backed /billing/agencies endpoint built
// for the original tenant-scoping work so every page (Dashboard, Visits &
// Notes, POC & Cert, NOE Tracking, ...) shares one agency selection instead
// of each page re-fetching/re-picking its own.
export function AgencyProvider({ children }: { children: ReactNode }) {
  const [agencies, setAgencies] = useState<BillableAgency[]>([]);
  const [selectedAgencyId, setSelectedAgencyId] = useState<string>(
    () => localStorage.getItem("sns-active-agency") || ""
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    fetchBillableAgencies()
      .then((res) => {
        if (!isMounted) return;
        const list = res?.agencies ?? [];
        setAgencies(list);
        setSelectedAgencyId((current) => {
          if (current && list.some((a) => a.tenant_id === current)) return current;
          return list[0]?.tenant_id ?? "";
        });
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load agency list.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (selectedAgencyId) {
      localStorage.setItem("sns-active-agency", selectedAgencyId);
    }
  }, [selectedAgencyId]);

  const value = useMemo(
    () => ({ agencies, selectedAgencyId, setSelectedAgencyId, loading, error }),
    [agencies, selectedAgencyId, loading, error]
  );

  return <AgencyContext.Provider value={value}>{children}</AgencyContext.Provider>;
}

export function useAgency(): AgencyContextValue {
  const ctx = useContext(AgencyContext);
  if (!ctx) {
    throw new Error("useAgency must be used within an AgencyProvider");
  }
  return ctx;
}
