import { clearAccessToken, clearCurrentUser, getAccessToken } from "./session";

// src/api/ownerAdmin.ts
// Platform-owner-only tenant onboarding calls.

export type OwnerTenantSummary = {
  tenant_id: string;
  legal_name: string;
  display_name: string;
  tenant_type: string;
  status: string;
  ai_enabled: boolean;
  billing_enabled: boolean;
  created_at: string;
  user_count: number;
  patient_count: number;
};

export type CreateTenantPayload = {
  legal_name: string;
  display_name?: string;
  npi: string;
  ein?: string;
  ptan?: string;
  tenant_type: "PRODUCTION" | "TRAINING" | "DEV";
  admin_email: string;
  admin_full_name: string;
  admin_password: string;
  admin_role: "DPCS_ADMINISTRATOR" | "ADMINISTRATOR" | "DPCS";
};

export type CreateTenantResponse = {
  tenant_id: string;
  legal_name: string;
  display_name: string;
  billing_enabled: boolean;
  admin_user: { id: string; email: string; role: string };
};

async function request<T>(
  url: string,
  options: { method?: "GET" | "POST"; body?: unknown } = {}
): Promise<T> {
  const token = getAccessToken();
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const candidates = [`${base}${url}`, ...(base ? [`http://localhost:8000${url}`] : [])];

  let lastError: Error | null = null;

  for (const candidate of candidates) {
    try {
      const res = await fetch(candidate, {
        method: options.method ?? "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      });

      if (res.status === 401) {
        clearAccessToken();
        clearCurrentUser();
        throw new Error("Session expired. Please sign in again.");
      }

      if (!res.ok) {
        let detail = `Request failed: ${url}`;
        try {
          const errBody = await res.json();
          detail = errBody?.detail ?? detail;
        } catch {
          // ignore body-parse failures
        }
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
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

export function fetchOwnerTenants(): Promise<{ tenants: OwnerTenantSummary[] }> {
  return request<{ tenants: OwnerTenantSummary[] }>("/api/owner/tenants");
}

export function createOwnerTenant(payload: CreateTenantPayload): Promise<CreateTenantResponse> {
  return request<CreateTenantResponse>("/api/owner/tenants", { method: "POST", body: payload });
}
