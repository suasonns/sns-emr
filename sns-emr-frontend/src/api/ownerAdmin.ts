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

export type AuditLogCategory = "AUTH" | "DATA" | "ADMIN" | "BILLING" | "COMPLIANCE";

export type OwnerAuditLogEntry = {
  log_id: string;
  created_at: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  description: string | null;
  event_metadata: Record<string, unknown> | null;
  user_id: string | null;
  user_display: string;
  user_email: string | null;
  user_role: string | null;
  tenant_id: string;
  tenant_name: string;
  category: AuditLogCategory;
};

export type OwnerAuditLogResponse = {
  logs: OwnerAuditLogEntry[];
  total_count: number;
  limit: number;
  offset: number;
  category_counts: Record<AuditLogCategory, number>;
  window_hours: number;
};

export type OwnerAuditLogParams = {
  search?: string;
  category?: AuditLogCategory;
  tenantId?: string;
  hours?: number;
  limit?: number;
  offset?: number;
};

async function request<T>(
  url: string,
  options: { method?: "GET" | "POST" | "PATCH"; body?: unknown } = {}
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

export type TenantStatus = "ACTIVE" | "INACTIVE" | "SUSPENDED";

export function setOwnerTenantStatus(
  tenantId: string,
  status: TenantStatus
): Promise<{ tenant_id: string; status: TenantStatus }> {
  return request<{ tenant_id: string; status: TenantStatus }>(
    `/api/owner/tenants/${tenantId}/status`,
    { method: "PATCH", body: { status } }
  );
}

export function fetchOwnerAuditLogs(params: OwnerAuditLogParams = {}): Promise<OwnerAuditLogResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.category) qs.set("category", params.category);
  if (params.tenantId) qs.set("tenant_id", params.tenantId);
  qs.set("hours", String(params.hours ?? 24));
  qs.set("limit", String(params.limit ?? 25));
  qs.set("offset", String(params.offset ?? 0));
  return request<OwnerAuditLogResponse>(`/api/owner/audit-logs?${qs.toString()}`);
}

export type PlatformUserStatus = "ACTIVE" | "DISABLED";

export type OwnerPlatformUser = {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  active: boolean;
  tenant_id: string;
  tenant_name: string;
  last_login: string | null;
};

export type OwnerPlatformUserStats = {
  total_users: number;
  active_users: number;
  active_now: number;
  agency_admins: number;
  disabled_users: number;
};

export type OwnerPlatformUsersResponse = {
  users: OwnerPlatformUser[];
  total_count: number;
  limit: number;
  offset: number;
  stats: OwnerPlatformUserStats;
  available_roles: string[];
};

export type OwnerPlatformUsersParams = {
  search?: string;
  role?: string;
  tenantId?: string;
  status?: PlatformUserStatus;
  limit?: number;
  offset?: number;
};

export function fetchOwnerPlatformUsers(
  params: OwnerPlatformUsersParams = {}
): Promise<OwnerPlatformUsersResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.role) qs.set("role", params.role);
  if (params.tenantId) qs.set("tenant_id", params.tenantId);
  if (params.status) qs.set("status", params.status);
  qs.set("limit", String(params.limit ?? 25));
  qs.set("offset", String(params.offset ?? 0));
  return request<OwnerPlatformUsersResponse>(`/api/owner/users?${qs.toString()}`);
}

export function setOwnerPlatformUserActive(
  userId: string,
  active: boolean
): Promise<{ user_id: string; active: boolean }> {
  return request(`/api/owner/users/${userId}`, { method: "PATCH", body: { active } });
}

export type ResetOwnerUserPasswordResponse = {
  user_id: string;
  email: string;
  temporary_password: string;
  reset_link: string;
};

export function resetOwnerPlatformUserPassword(
  userId: string
): Promise<ResetOwnerUserPasswordResponse> {
  return request(`/api/owner/users/${userId}/reset-password`, { method: "POST" });
}

export type OwnerSystemIncident = {
  incident_id: string;
  incident_type: string;
  incident_severity: string;
  incident_date: string | null;
  created_at: string;
  tenant_name: string;
};

export type OwnerSystemReliability = {
  db_connected: boolean;
  db_latency_ms: number | null;
  db_size_pretty: string | null;
  backend_uptime_seconds: number;
  system_incidents_total: number;
  recent_incidents: OwnerSystemIncident[];
};

export type OwnerSecurityEvent = {
  log_id: string;
  created_at: string;
  action: string;
  ip_address: string | null;
  user_display: string;
  tenant_name: string;
};

export type OwnerSecurityHealth = {
  failed_logins_24h: number;
  failed_logins_7d: number;
  password_resets_7d: number;
  permission_changes_7d: number;
  recent_events: OwnerSecurityEvent[];
};

export type OwnerSystemHealthResponse = {
  reliability: OwnerSystemReliability;
  security: OwnerSecurityHealth;
};

export function fetchOwnerSystemHealth(): Promise<OwnerSystemHealthResponse> {
  return request<OwnerSystemHealthResponse>("/api/owner/system-health");
}

export type OwnerAdoptionHealthResponse = {
  dau: number;
  wau: number;
  mau: number;
  total_tenants: number;
  daily_active_trend: { date: string; active_users: number }[];
};

export function fetchOwnerAdoptionHealth(): Promise<OwnerAdoptionHealthResponse> {
  return request<OwnerAdoptionHealthResponse>("/api/owner/adoption-health");
}

// ─── Billing & Licensing (Owner Portal) ──────────────────────────────
// Backed by GET /api/owner/billing-licensing (see
// backend/app/api/owner_billing_licensing.py). Returns real data once
// subscription/invoice/payment rows exist for a tenant; otherwise
// `data_available` is false and BillingLicensing.jsx renders an honest
// "not available yet" state rather than fabricating figures.

export type OwnerBillingKpis = {
  total_monthly_revenue: number | null;
  outstanding_invoice_count: number | null;
  outstanding_invoice_total: number | null;
  active_agencies: number | null;
  licensed_agencies: number | null;
  avg_revenue_per_agency: number | null;
};

export type OwnerBillingClientStatus = "PAID" | "OVERDUE" | "PENDING" | "TRIAL";

export type OwnerBillingClient = {
  tenant_id: string;
  agency_name: string;
  plan_type: string;
  seats_used: number | null;
  seats_licensed: number | null;
  monthly_rate: number | null;
  last_payment_date: string | null;
  status: OwnerBillingClientStatus;
  balance_due: number | null;
};

export type OwnerRevenueByAgency = {
  tenant_id: string;
  agency_name: string;
  amount: number;
  pct_of_top: number;
};

export type OwnerBillingPaymentStatus = "SUCCESS" | "PENDING" | "OVERDUE";

export type OwnerRecentPayment = {
  tenant_id: string;
  agency_name: string;
  occurred_at: string;
  amount: number;
  status: OwnerBillingPaymentStatus;
};

export type OwnerUpcomingOutstanding = {
  tenant_id: string;
  agency_name: string;
  due_date: string;
  amount: number;
  status: "UPCOMING" | "OVERDUE";
};

export type OwnerLicenseAllocation = {
  plan_label: string;
  seats_used: number;
  seats_total: number;
};

export type OwnerBillingLicensingResponse = {
  kpis: OwnerBillingKpis;
  clients: OwnerBillingClient[];
  revenue_by_agency: OwnerRevenueByAgency[];
  recent_payments: OwnerRecentPayment[];
  upcoming_outstandings: OwnerUpcomingOutstanding[];
  license_allocations: OwnerLicenseAllocation[];
  total_seats_used: number | null;
  total_seats_allocated: number | null;
  data_available: boolean;
  unavailable_reason: string | null;
};

export type OwnerBillingLicensingParams = {
  tenantId?: string;
  quarterStart?: string;
  quarterEnd?: string;
};

export function fetchOwnerBillingLicensing(
  params: OwnerBillingLicensingParams = {}
): Promise<OwnerBillingLicensingResponse> {
  const qs = new URLSearchParams();
  if (params.tenantId) qs.set("tenant_id", params.tenantId);
  if (params.quarterStart) qs.set("period_start", params.quarterStart);
  if (params.quarterEnd) qs.set("period_end", params.quarterEnd);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return request<OwnerBillingLicensingResponse>(`/api/owner/billing-licensing${suffix}`);
}
