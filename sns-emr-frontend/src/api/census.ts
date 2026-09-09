import { getAccessToken } from "./session";
import { ensureFreshAccessToken, redirectToLogin } from "./client";

export type CensusCategory = "ALL" | "ACTIVE" | "DISCHARGED" | "DECEASED" | "REVOKED";

export type CensusPatientRow = {
  patient_id: string;
  mrn: string;
  full_name: string;
  date_of_birth: string | null;
  primary_diagnosis: string | null;
  patient_status: string | null;
  admission_status: string | null;
  admission_at: string | null;
  discharge_date: string | null;
  discharge_reason: string | null;
  attending_physician: string | null;
  payer_name: string | null;
  last_visit_at: string | null;
  census_bucket: string;
};

export type CensusWorkspaceResponse = {
  tenant_id: string;
  patient_count: number;
  patients: CensusPatientRow[];
};

// Session-stability correction: only a 401 (access token expired/invalid)
// attempts the shared single-flight refresh-and-retry; a 403 (tenant
// suspended / role denial) is never treated as session expiration and
// never clears a valid session (see api/dashboard.ts's authorizedFetch
// for the fuller rationale -- this module mirrors the same fix).
async function fetchJson<T>(url: string): Promise<T> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const candidates = [
    `${base}${url}`,
    ...(base ? [`http://localhost:8000${url}`] : []),
  ];

  let lastError: Error | null = null;

  for (const candidate of candidates) {
    try {
      const token = getAccessToken();
      let res = await fetch(candidate, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });

      if (res.status === 401) {
        const newAccessToken = await ensureFreshAccessToken();
        if (!newAccessToken) {
          redirectToLogin();
          throw new Error("Session expired. Please sign in again.");
        }
        res = await fetch(candidate, {
          credentials: "include",
          headers: { Authorization: `Bearer ${newAccessToken}` },
        });
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Session expired. Please sign in again.");
        }
      }

      if (!res.ok) {
        throw new Error(`Request failed: ${url}`);
      }

      return (await res.json()) as T;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(`Request failed: ${url}`);
      if (candidate === candidates[candidates.length - 1]) {
        break;
      }
    }
  }

  throw lastError ?? new Error(`Request failed: ${url}`);
}

export function fetchCensusWorkspace(): Promise<CensusWorkspaceResponse> {
  return fetchJson<CensusWorkspaceResponse>("/audit-dashboard/census");
}

