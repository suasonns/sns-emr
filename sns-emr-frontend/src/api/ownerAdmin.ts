import { getAccessToken } from "./session";
import { ensureFreshAccessToken, redirectToLogin } from "./client";

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
  financials_enabled: boolean;
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
  financials_enabled: boolean;
  admin_user: { id: string; email: string; role: string };
};

export type AuditLogCategory = "AUTH" | "DATA" | "ADMIN" | "BILLING" | "COMPLIANCE";

export type AuditLogSeverity = "INFO" | "WARNING" | "HIGH" | "CRITICAL";

export type OwnerAuditLogEntry = {
  log_id: string;
  created_at: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  description: string | null;
  event_metadata: Record<string, unknown> | null;
  // Real request-trace id (audit_logs.request_id) -- NOT an auth/login
  // session id (no session tracking exists yet). Surfaced as "Request ID"
  // in the UI, never labeled "Session ID", to avoid implying data we don't
  // actually have.
  request_id: string | null;
  user_id: string | null;
  user_display: string;
  user_email: string | null;
  user_role: string | null;
  tenant_id: string;
  tenant_name: string;
  category: AuditLogCategory;
  // Centralized, backend-authoritative severity resolution (see
  // _severity_for_event in backend/app/api/owner_admin.py). Context-aware
  // for OWNER_SET_TENANT_STATUS and OWNER_CHANGED_STAFF_ROLE (depends on
  // real event_metadata), a flat table for everything else. The frontend
  // never recomputes or overrides this value.
  severity: AuditLogSeverity;
  // Role-derived permission diff for OWNER_CHANGED_STAFF_ROLE events,
  // computed server-side from the same authoritative RBAC source SNS
  // Staff & Access uses (app.core.roles.capabilities_for_role). null for
  // every other event, or when there isn't a real previous/new role pair.
  affected_permissions: {
    previous_role: string;
    new_role: string;
    added: string[];
    removed: string[];
  } | null;
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
  // Exact entity_type match (e.g. "user"). Used by the SNS Staff &
  // Access page's Audit tab to scope to staff/identity lifecycle events
  // only, without duplicating the standalone Audit Logs page's full feed.
  entityType?: string;
  // Exact entity_id match. Used by the Audit Logs Event Details drawer to
  // fetch the full Related Events history for one record (not just the
  // currently loaded page).
  entityId?: string;
  hours?: number;
  limit?: number;
  offset?: number;
};

async function request<T>(
  url: string,
  options: { method?: "GET" | "POST" | "PATCH"; body?: unknown } = {}
): Promise<T> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  // NOTE: intentionally no localhost:8000 fallback here. A silent fallback
  // to a hardcoded local dev backend previously masked real production
  // errors -- e.g. a real 422 from the actual API would still fail over to
  // a CORS-blocked localhost request, and that generic CORS/network
  // rejection ("Failed to fetch") replaced the real, actionable error
  // message in the UI. Always call the configured API base and let real
  // failures surface with their real detail.
  const target = `${base}${url}`;

  const buildInit = (token: string | null) => ({
    method: options.method ?? "GET",
    credentials: "include" as RequestCredentials,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  let res = await fetch(target, buildInit(getAccessToken()));

  // Session-stability correction: attempt exactly one shared,
  // single-flight token refresh before treating a 401 as a
  // confirmed session expiration (see api/dashboard.ts's
  // authorizedFetch for the fuller rationale).
  if (res.status === 401) {
    const newAccessToken = await ensureFreshAccessToken();
    if (!newAccessToken) {
      redirectToLogin();
      throw new Error("Session expired. Please sign in again.");
    }
    res = await fetch(target, buildInit(newAccessToken));
    if (res.status === 401) {
      redirectToLogin();
      throw new Error("Session expired. Please sign in again.");
    }
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

export type OwnerTenantFinancialsPayload = {
  financials_enabled: boolean;
  billing_provider_organization_id?: string;
  effective_start_at?: string;
  effective_end_at?: string | null;
  service_scopes?: BillingProviderServiceScopeGrant[];
  change_reason?: string;
};

export type OwnerTenantFinancialsResponse = {
  tenant_id: string;
  financials_enabled: boolean;
  current_assignment: {
    assignment_id: string;
    billing_provider_organization_id: string;
    relationship_status: BillingProviderAssignmentStatus;
    effective_start_at: string | null;
    effective_end_at: string | null;
    service_scopes: BillingProviderServiceScopeGrant[];
  } | null;
};

export function setOwnerTenantFinancials(
  tenantId: string,
  payload: OwnerTenantFinancialsPayload
): Promise<OwnerTenantFinancialsResponse> {
  return request<OwnerTenantFinancialsResponse>(
    `/api/owner/tenants/${tenantId}/financials`,
    { method: "PATCH", body: payload }
  );
}

export type BillingProviderOrganizationStatus = "ACTIVE" | "INACTIVE";

export type BillingProviderOrganization = {
  id: string;
  name: string;
  organization_type: string;
  status: BillingProviderOrganizationStatus;
  notes: string | null;
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type BillingProviderOrganizationPayload = {
  name: string;
  organization_type: string;
  status: BillingProviderOrganizationStatus;
  notes?: string;
};

export function fetchBillingProviderOrganizations(): Promise<{
  organizations: BillingProviderOrganization[];
}> {
  return request<{ organizations: BillingProviderOrganization[] }>(
    "/api/owner/billing-providers/organizations"
  );
}

export function createBillingProviderOrganization(
  payload: BillingProviderOrganizationPayload
): Promise<BillingProviderOrganization> {
  return request<BillingProviderOrganization>("/api/owner/billing-providers/organizations", {
    method: "POST",
    body: payload,
  });
}

export function updateBillingProviderOrganization(
  organizationId: string,
  payload: BillingProviderOrganizationPayload
): Promise<BillingProviderOrganization> {
  return request<BillingProviderOrganization>(
    `/api/owner/billing-providers/organizations/${organizationId}`,
    { method: "PATCH", body: payload }
  );
}

export const BILLING_PROVIDER_SERVICE_SCOPES = [
  "BILLING_READINESS",
  "CLAIMS",
  "NOE_TRACKING",
  "ELIGIBILITY",
  "AUTHORIZATION_TRACKING",
  "PAYMENT_POSTING",
  "PAYMENT_RECONCILIATION",
  "FACILITY_COLLECTIONS",
  "CREDIT_BALANCES",
  "AGING_REPORT",
  "DENIALS_APPEALS",
  "EDI",
  "BILLING_REPORTS",
  "CAP_MONITORING",
  "FINANCIAL_MONITORING",
] as const;
export const BILLING_PROVIDER_PERMISSION_LEVELS = ["VIEW", "EDIT"] as const;

export type BillingProviderServiceScope = (typeof BILLING_PROVIDER_SERVICE_SCOPES)[number];
export type BillingProviderPermissionLevel =
  (typeof BILLING_PROVIDER_PERMISSION_LEVELS)[number];
export type BillingProviderServiceScopeGrant = {
  scope: BillingProviderServiceScope;
  permission_level: BillingProviderPermissionLevel;
};
export type BillingProviderAssignmentStatus =
  | "ACTIVE"
  | "SUSPENDED"
  | "TERMINATED"
  | "PENDING";

export type BillingProviderAssignment = {
  id: string;
  billing_provider_organization_id: string;
  billing_provider_organization_name: string | null;
  tenant_id: string;
  tenant_display_name: string | null;
  tenant_legal_name: string | null;
  relationship_status: BillingProviderAssignmentStatus;
  effective_start_at: string | null;
  effective_end_at: string | null;
  service_scope: BillingProviderServiceScopeGrant[];
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type BillingProviderAssignmentPayload = {
  billing_provider_organization_id: string;
  tenant_id: string;
  relationship_status: BillingProviderAssignmentStatus;
  effective_start_at: string;
  effective_end_at?: string | null;
  service_scope: BillingProviderServiceScopeGrant[];
};

export function fetchBillingProviderAssignments(params?: {
  tenant_id?: string;
  billing_provider_organization_id?: string;
}): Promise<{ assignments: BillingProviderAssignment[] }> {
  const qs = new URLSearchParams();
  if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
  if (params?.billing_provider_organization_id) {
    qs.set("billing_provider_organization_id", params.billing_provider_organization_id);
  }
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return request<{ assignments: BillingProviderAssignment[] }>(
    `/api/owner/billing-providers/assignments${suffix}`
  );
}

export function createBillingProviderAssignment(
  payload: BillingProviderAssignmentPayload
): Promise<BillingProviderAssignment> {
  return request<BillingProviderAssignment>("/api/owner/billing-providers/assignments", {
    method: "POST",
    body: payload,
  });
}

export function updateBillingProviderAssignment(
  assignmentId: string,
  payload: BillingProviderAssignmentPayload
): Promise<BillingProviderAssignment> {
  return request<BillingProviderAssignment>(
    `/api/owner/billing-providers/assignments/${assignmentId}`,
    { method: "PATCH", body: payload }
  );
}

export function fetchOwnerAuditLogs(params: OwnerAuditLogParams = {}): Promise<OwnerAuditLogResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.category) qs.set("category", params.category);
  if (params.tenantId) qs.set("tenant_id", params.tenantId);
  if (params.entityType) qs.set("entity_type", params.entityType);
  if (params.entityId) qs.set("entity_id", params.entityId);
  qs.set("hours", String(params.hours ?? 24));
  qs.set("limit", String(params.limit ?? 25));
  qs.set("offset", String(params.offset ?? 0));
  return request<OwnerAuditLogResponse>(`/api/owner/audit-logs?${qs.toString()}`);
}

export type PlatformUserStatus = "ACTIVE" | "SUSPENDED" | "DISABLED" | "REMOVED";

export type PlatformAccountType =
  | "HUMAN_STAFF"
  | "SERVICE_ACCOUNT"
  | "AUTOMATION_ACCOUNT"
  | "API_CLIENT";

// Real, backend-enforced per-row action visibility (app.core.roles.role_can()
// and the OWNER-only gates on set_platform_user_active /
// reset_platform_user_password). Never re-derive these client-side --
// always trust what the list endpoint returns.
export type OwnerPlatformUserAllowedActions = {
  edit_profile: boolean;
  assign_role: boolean;
  activate: boolean;
  suspend: boolean;
  disable: boolean;
  revoke_access: boolean;
  reset_password: boolean;
  remove: boolean;
};

// SNS Hospice Solutions platform staff only (app.core.roles.PLATFORM_ROLES
// on the backend) -- never a tenant-agency or billing-organization user.
export type OwnerPlatformUser = {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  active: boolean;
  // Distinct 4-state lifecycle (ACTIVE/SUSPENDED/DISABLED/REMOVED) --
  // the authoritative status for SNS Staff & Access UI/workflows.
  platform_staff_status: PlatformUserStatus;
  department: string | null;
  account_type: PlatformAccountType;
  job_title: string | null;
  platform: string;
  responsible_owner_id: string | null;
  responsible_owner_name: string | null;
  purpose: string | null;
  scope: string | null;
  last_login: string | null;
  access_level: string;
  allowed_actions: OwnerPlatformUserAllowedActions;
};

// Full detail record returned by POST/GET/PATCH /api/owner/users(/{id}...)
// -- superset of OwnerPlatformUser with profile/audit/capability fields.
export type OwnerPlatformStaffDetail = {
  user_id: string;
  email: string;
  full_name: string;
  first_name: string | null;
  middle_name: string | null;
  last_name: string | null;
  role: string;
  access_level: string;
  department: string | null;
  account_type: PlatformAccountType;
  active: boolean;
  // Distinct 4-state lifecycle (ACTIVE/SUSPENDED/DISABLED/REMOVED) --
  // the authoritative status for SNS Staff & Access UI/workflows.
  platform_staff_status: PlatformUserStatus;
  phone: string | null;
  address_street: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  start_date: string | null;
  notes: string | null;
  job_title: string | null;
  platform: string;
  responsible_owner_id: string | null;
  responsible_owner_name: string | null;
  purpose: string | null;
  scope: string | null;
  must_change_password: boolean;
  created_by: string | null;
  created_at: string | null;
  updated_by: string | null;
  updated_at: string | null;
  last_login: string | null;
  // Platform Owner succession/continuity signal: true only when this
  // account is the single remaining active OWNER. Drives the explicit
  // "Final Platform Owner -- protected" safeguard notice in the Access
  // tab; the hard 409 protections themselves live server-side regardless
  // of this flag.
  is_final_active_owner: boolean;
  // Real, backend-derived `staff.*` capability names this role is
  // granted -- see app.core.roles.capabilities_for_role(). Rendered as-is
  // in the Access tab; never hardcoded/relabeled with invented text.
  capabilities: string[];
  temporary_password?: string;
  reset_link?: string;
};

export type OwnerPlatformUserStats = {
  total_users: number;
  active_users: number;
  active_now: number;
  privileged_accounts: number;
  disabled_users: number;
  active_owners: number;
  service_accounts: number;
  automation_accounts: number;
  api_clients: number;
};

export type OwnerPlatformUsersResponse = {
  users: OwnerPlatformUser[];
  total_count: number;
  limit: number;
  offset: number;
  stats: OwnerPlatformUserStats;
  available_roles: string[];
  // Derived Access Level per role (never independently editable) --
  // see app.core.roles.ACCESS_LEVEL_FOR_ROLE.
  access_levels_by_role: Record<string, string>;
  available_departments: string[];
  available_platforms: string[];
  // Department-scoped Job Title catalog (Platform > Department > Job
  // Title > Platform Role > Access Level). Keyed by department code;
  // departments absent from this map have no catalog yet and accept
  // free-text job titles.
  job_titles_by_department: Record<string, string[]>;
  available_account_types: PlatformAccountType[];
  // The signed-in actor's own real, backend-derived capability grants --
  // use this (not a hardcoded role list) to show/hide "+ Add Staff" etc.
  actor_capabilities: string[];
};

export type OwnerPlatformUsersParams = {
  search?: string;
  role?: string;
  status?: PlatformUserStatus;
  department?: string;
  platform?: string;
  accountType?: PlatformAccountType | string;
  // Comma-joined-on-the-wire list of account types (e.g. Service Accounts
  // tab passing ["SERVICE_ACCOUNT", "AUTOMATION_ACCOUNT"]) -- distinct
  // from the single-value accountType filter above.
  accountTypes?: (PlatformAccountType | string)[];
  limit?: number;
  offset?: number;
};

export function fetchOwnerPlatformUsers(
  params: OwnerPlatformUsersParams = {}
): Promise<OwnerPlatformUsersResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.role) qs.set("role", params.role);
  if (params.status) qs.set("status", params.status);
  if (params.department) qs.set("department", params.department);
  if (params.platform) qs.set("platform", params.platform);
  if (params.accountType) qs.set("account_type", params.accountType);
  if (params.accountTypes?.length) qs.set("account_types", params.accountTypes.join(","));
  qs.set("limit", String(params.limit ?? 25));
  qs.set("offset", String(params.offset ?? 0));
  return request<OwnerPlatformUsersResponse>(`/api/owner/users?${qs.toString()}`);
}

export function fetchOwnerPlatformStaffDetail(
  userId: string
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}`);
}

export type OwnerPlatformStaffAuditEvent = {
  log_id: string;
  created_at: string;
  action: string;
  description: string | null;
  event_metadata: Record<string, unknown> | null;
  actor_user_id: string | null;
  actor_full_name: string | null;
  actor_email: string | null;
};

export function fetchOwnerPlatformStaffAuditHistory(
  userId: string
): Promise<{ events: OwnerPlatformStaffAuditEvent[] }> {
  return request<{ events: OwnerPlatformStaffAuditEvent[] }>(`/api/owner/users/${userId}/audit`);
}

export type CreatePlatformStaffPayload = {
  email: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  role: string;
  department?: string;
  account_type?: PlatformAccountType;
  phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  start_date?: string;
  notes?: string;
  job_title?: string;
  platform?: string;
  responsible_owner_id?: string;
  purpose?: string;
  scope?: string;
};

export function createOwnerPlatformStaff(
  payload: CreatePlatformStaffPayload
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>("/api/owner/users", {
    method: "POST",
    body: payload,
  });
}

export type UpdatePlatformStaffProfilePayload = {
  first_name: string;
  last_name: string;
  middle_name?: string;
  department?: string;
  phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  start_date?: string;
  notes?: string;
  job_title?: string;
  platform?: string;
  responsible_owner_id?: string;
  purpose?: string;
  scope?: string;
};

export function updateOwnerPlatformStaffProfile(
  userId: string,
  payload: UpdatePlatformStaffProfilePayload
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}/profile`, {
    method: "PATCH",
    body: payload,
  });
}

export function updateOwnerPlatformStaffRole(
  userId: string,
  role: string
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}/role`, {
    method: "PATCH",
    body: { role },
  });
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

// Distinct ACTIVE / SUSPENDED / DISABLED lifecycle transition (Phase
// UM-3). REMOVED is intentionally not settable here -- see
// removeOwnerPlatformStaff below, which requires a reason and is a
// one-way soft-removal, not a reversible status.
export type SettablePlatformStaffStatus = "ACTIVE" | "SUSPENDED" | "DISABLED";

export function setOwnerPlatformStaffStatus(
  userId: string,
  status: SettablePlatformStaffStatus,
  reason?: string
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}/status`, {
    method: "PATCH",
    body: { status, reason },
  });
}

// Revoke Access is a distinct action from Suspend/Disable, with its own
// audit trail entry -- resolves to the DISABLED status for human staff.
export function revokeOwnerPlatformStaffAccess(
  userId: string,
  reason?: string
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}/revoke-access`, {
    method: "POST",
    body: { reason },
  });
}

// Remove Staff -- soft-removal only (platform_staff_status -> REMOVED,
// active -> false). Never hard-deletes; identity, audit history, and
// historical attribution all survive. Requires a reason.
export function removeOwnerPlatformStaff(
  userId: string,
  reason: string
): Promise<OwnerPlatformStaffDetail> {
  return request<OwnerPlatformStaffDetail>(`/api/owner/users/${userId}/remove`, {
    method: "POST",
    body: { reason },
  });
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
