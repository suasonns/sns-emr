import { clearAccessToken, clearCurrentUser, getAccessToken } from "./session";

// src/api/dashboard.ts

// =========================================================
// CORE TYPES
// =========================================================

export type DashboardMetric = {
  key: string;
  label: string;
  value: number;
};

export type DashboardTaskItem = {
  task_id: string;
  patient_id: string;
  task_type: string;
  status: string;
  due_date: string | null;
  due_at: string | null;
  clinical_note_id: string | null;
  incident_id: string | null;
};

export type DashboardIncidentItem = {
  incident_id: string;
  patient_id: string;
  incident_type: string;
  incident_severity: string;
  incident_date: string | null;
  clinical_note_id: string | null;
};

export type DashboardNoteFlagItem = {
  note_id: string;
  patient_id: string;
  encounter_date: string | null;
  discipline: string | null;
  visit_type: string | null;
  note_category: string | null;
  incident_required: boolean;
  incident_status: string | null;
  red_flags: string[];
  needs_clarification: string[];
};

export type DashboardPatientBlocker = {
  patient_id: string;
  blockers: string[];
};

export type DashboardOrderItem = {
  order_id: string;
  patient_id: string;
  patient_name: string;
  order_category: string;
  order_text: string;
  status: string;
  source_type: string;
  ordered_by_provider_name: string;
  ordered_by_provider_role: string;
  entered_by_name: string | null;
  ordered_at: string | null;
  signed_by_name: string | null;
  signed_at: string | null;
};

// =========================================================
// DASHBOARD RESPONSES
// =========================================================

export type ClinicalComplianceDashboardResponse = {
  metrics: DashboardMetric[];
  task_type_counts: Record<string, number>;
  incident_type_counts: Record<string, number>;
  open_tasks: DashboardTaskItem[];
  pending_incidents: DashboardIncidentItem[];
  flagged_notes: DashboardNoteFlagItem[];
  blocked_patients: DashboardPatientBlocker[];
  unsigned_orders: DashboardOrderItem[];
  all_orders: DashboardOrderItem[];
};

export type ClinicalAlertMetric = {
  key: string;
  label: string;
  value: number;
};

export type ClinicalAlertRow = {
  alert_id: string;
  priority: string;
  alert_type: string;
  patient_id: string;
  patient_name: string;
  description: string;
  generated: string | null;
  status: string;
  source_type: string;
};

export type ClinicalAlertsResponse = {
  metrics: ClinicalAlertMetric[];
  alerts: ClinicalAlertRow[];
};

export type TenantDashboardResponse = {
  tenant_id: string;
  tenant_name?: string;
  ai_enabled: boolean;
  billing_enabled: boolean;
  dashboard: ClinicalComplianceDashboardResponse;
};

export type OwnerTenantSummary = {
  tenant_id: string;
  tenant_name: string;
  open_tasks: number;
  incidents: number;
  blocked_patients: number;
};

export type OwnerDashboardResponse = {
  metrics: DashboardMetric[];
  total_tenants: number;
  active_tasks: number;
  system_incidents: number;
  clinical_notes: number;
  recent_incidents?: DashboardIncidentItem[];
  tenant_summary?: OwnerTenantSummary[];
};

export type BillingDashboardResponse = {
  metrics: DashboardMetric[];
  payments_received: number;
  denied_claims: number;
  claims_pending_payment: number;
  remittance_files_processed: number;
  billing_holds: Array<Record<string, unknown>>;
};

export type ClaimLifecycleResponse = {
  metrics: DashboardMetric[];
  ready: number;
  sent: number;
  accepted: number;
  paid: number;
  denied: number;
};

export type SidebarAlertCounts = {
  tasks: number;
  incidents: number;
  blockers: number;
};

export type PatientComplianceDetailResponse = {
  patient_id: string;
  blocked: boolean;
  blockers: string[];
  tasks: {
    task_id: string;
    task_type: string;
    status: string;
  }[];
  incidents: {
    incident_id: string;
    incident_type: string;
    incident_severity: string;
  }[];
  notes: {
    note_id: string;
    discipline: string;
    visit_type: string;
    note_category: string;
  }[];
};

// =========================================================
// FETCH UTIL
// =========================================================

async function fetchJson<T>(url: string): Promise<T> {
  const token = getAccessToken();
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const candidates = [
    `${base}${url}`,
    ...(base ? [`http://localhost:8000${url}`] : []),
  ];

  let lastError: Error | null = null;

  for (const candidate of candidates) {
    try {
      const res = await fetch(candidate, {
        credentials: "include",
        headers: token
          ? {
              Authorization: `Bearer ${token}`,
            }
          : undefined,
      });

      if (res.status === 401 || res.status === 403) {
        clearAccessToken();
        clearCurrentUser();
        throw new Error("Session expired. Please sign in again.");
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

// =========================================================
// DASHBOARD CALLS
// =========================================================

function withTenantId(url: string, tenantId?: string | null): string {
  if (!tenantId) return url;
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}tenant_id=${encodeURIComponent(tenantId)}`;
}

export function fetchTenantDashboard(): Promise<TenantDashboardResponse> {
  return fetchJson<TenantDashboardResponse>("/api/dashboard/tenant");
}

export function fetchOwnerDashboard(tenantId?: string | null): Promise<OwnerDashboardResponse> {
  return fetchJson<OwnerDashboardResponse>(withTenantId("/api/dashboard/owner", tenantId));
}

export function fetchClinicalComplianceDashboard(): Promise<ClinicalComplianceDashboardResponse> {
  return fetchJson<ClinicalComplianceDashboardResponse>("/api/dashboard/clinical-compliance");
}

export function fetchClinicalAlerts(): Promise<ClinicalAlertsResponse> {
  return fetchJson<ClinicalAlertsResponse>("/api/dashboard/clinical-alerts");
}

export function fetchBillingDashboard(tenantId?: string | null): Promise<BillingDashboardResponse> {
  return fetchJson<BillingDashboardResponse>(withTenantId("/api/dashboard/billing", tenantId));
}

export function fetchClaimLifecycle(tenantId?: string | null): Promise<ClaimLifecycleResponse> {
  return fetchJson<ClaimLifecycleResponse>(withTenantId("/api/dashboard/claim-lifecycle", tenantId));
}

export type BillableAgency = {
  tenant_id: string;
  legal_name: string;
  display_name: string;
  tenant_type: string;
  status: string;
  billing_enabled: boolean;
};

export function fetchBillableAgencies(): Promise<{ agencies: BillableAgency[] }> {
  return fetchJson<{ agencies: BillableAgency[] }>("/billing/agencies");
}

// =========================================================
// PHASE 1 BILLING READ-ONLY PAGES (Visits & Notes / POC & Cert / NOE)
// =========================================================

export type VisitNoteRow = {
  note_id: string;
  patient_id: string | null;
  patient_name: string | null;
  mrn: string | null;
  visit_id: string | null;
  visit_datetime: string | null;
  visit_type: string | null;
  visit_status: string | null;
  note_type: string | null;
  discipline: string | null;
  status: string | null;
  encounter_date: string | null;
  entered_at: string | null;
  author_name: string | null;
  signed_by: string | null;
  signed_at: string | null;
  finalized_at: string | null;
  requires_countersign: boolean;
  countersigned_by: string | null;
  countersigner_name: string | null;
  countersigned_at: string | null;
  is_late_entry: boolean;
  documentation_complete: boolean;
};

export type VisitsNotesResponse = {
  tenant_id: string;
  count: number;
  visits_notes: VisitNoteRow[];
};

export function fetchVisitsNotes(
  tenantId?: string | null,
  params?: { unsigned_only?: boolean; status?: string; limit?: number }
): Promise<VisitsNotesResponse> {
  const search = new URLSearchParams();
  if (params?.unsigned_only) search.set("unsigned_only", "true");
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/visits-notes${query ? `?${query}` : ""}`;
  return fetchJson<VisitsNotesResponse>(withTenantId(base, tenantId));
}

export type PocCertificationRow = {
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  benefit_period: {
    id: string;
    benefit_type: string;
    period_number: number;
    start_date: string | null;
    end_date: string | null;
    is_current: boolean;
    noe_submitted_date: string | null;
    noe_exception_reason: string | null;
  };
  certification: {
    id: string;
    cert_type: string;
    status: string;
    signed_at: string | null;
    effective_date: string | null;
    expires_at: string | null;
    signed_by_role: string | null;
  } | null;
  plan_of_care: {
    id: string;
    status: string;
    current_version_number: number | null;
    physician_approval_status: string | null;
    physician_approval_date: string | null;
    physician_name: string | null;
  } | null;
  f2f_encounter: {
    id: string;
    encounter_date: string | null;
    status: string;
    performed_by_role: string | null;
    attested_at: string | null;
  } | null;
  billing_ready: boolean;
};

export type PocCertificationResponse = {
  tenant_id: string;
  count: number;
  poc_certification_status: PocCertificationRow[];
};

export function fetchPocCertificationStatus(
  tenantId?: string | null,
  params?: { current_period_only?: boolean; limit?: number }
): Promise<PocCertificationResponse> {
  const search = new URLSearchParams();
  if (params?.current_period_only === false) search.set("current_period_only", "false");
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/poc-certification-status${query ? `?${query}` : ""}`;
  return fetchJson<PocCertificationResponse>(withTenantId(base, tenantId));
}

export type NoeTrackingRow = {
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  benefit_period_id: string;
  election_date: string | null;
  noe_submitted_date: string | null;
  noe_exception_reason: string | null;
  noe_filed: boolean;
  is_late: boolean;
  is_exempt: boolean;
  non_covered_start: string | null;
  non_covered_end: string | null;
  non_covered_days: number | null;
  penalty_reason: string | null;
};

export type NoeTrackingResponse = {
  tenant_id: string;
  count: number;
  late_count: number;
  unfiled_count: number;
  noe_tracking: NoeTrackingRow[];
};

export function fetchNoeTracking(
  tenantId?: string | null,
  params?: { late_only?: boolean; unfiled_only?: boolean; limit?: number }
): Promise<NoeTrackingResponse> {
  const search = new URLSearchParams();
  if (params?.late_only) search.set("late_only", "true");
  if (params?.unfiled_only) search.set("unfiled_only", "true");
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/noe-tracking${query ? `?${query}` : ""}`;
  return fetchJson<NoeTrackingResponse>(withTenantId(base, tenantId));
}

export type BillingReadinessPatientRow = {
  patient_id: string;
  mrn: string | null;
  period_number: number | null;
  ready: boolean;
  blockers: string[];
  warnings: string[];
};

export type TenantBillingReadinessReport = {
  tenant_id: string;
  service_date: string;
  total_patients: number;
  ready_count: number;
  not_ready_count: number;
  patients: BillingReadinessPatientRow[];
};

export function fetchTenantBillingReadinessReport(
  tenantId?: string | null,
  serviceDate?: string
): Promise<TenantBillingReadinessReport> {
  const search = new URLSearchParams();
  search.set("service_date", serviceDate || new Date().toISOString().slice(0, 10));
  const base = `/billing/readiness-report?${search.toString()}`;
  return fetchJson<TenantBillingReadinessReport>(withTenantId(base, tenantId));
}

export function fetchPatientComplianceDetail(
  patientId: string
): Promise<PatientComplianceDetailResponse> {
  return fetchJson<PatientComplianceDetailResponse>(
    `/api/dashboard/clinical-compliance/patients/${patientId}`
  );
}

// =========================================================
// SIDEBAR ALERTS
// =========================================================

function metricValue(metrics: DashboardMetric[], key: string): number {
  return metrics.find((m) => m.key === key)?.value ?? 0;
}

export async function fetchSidebarAlertCounts(
  role: string
): Promise<SidebarAlertCounts> {
  const normalized = role.toUpperCase();

  if (normalized === "OWNER") {
    const data = await fetchOwnerDashboard();

    const blockers = (data.tenant_summary ?? []).reduce(
      (sum, item) => sum + (item.blocked_patients ?? 0),
      0
    );

    return {
      tasks: data.active_tasks ?? metricValue(data.metrics, "tasks"),
      incidents:
        data.system_incidents ?? metricValue(data.metrics, "incidents"),
      blockers,
    };
  }

  if (
    normalized === "TENANT_ADMIN" ||
    normalized === "CLINICIAN" ||
    normalized === "DPCS" ||
    normalized === "ADMINISTRATOR" ||
    normalized === "DPCS_ADMINISTRATOR"
  ) {
    const data = await fetchTenantDashboard();

    return {
      tasks: metricValue(data.dashboard.metrics, "open_tasks"),
      incidents: metricValue(data.dashboard.metrics, "pending_incidents"),
      blockers: metricValue(
        data.dashboard.metrics,
        "idg_blocked_patients"
      ),
    };
  }

  if (normalized === "BILLER" || normalized === "BILLING") {
    // A billing-department account without a selected agency tenant has
    // no single tenant to summarize (they may serve many agencies) -- the
    // sidebar badge is best-effort only, so treat that as "nothing to
    // show yet" rather than surfacing an error.
    try {
      const data = await fetchBillingDashboard();
      return {
        tasks: data.claims_pending_payment ?? 0,
        incidents: data.denied_claims ?? 0,
        blockers: data.denied_claims ?? 0,
      };
    } catch {
      return { tasks: 0, incidents: 0, blockers: 0 };
    }
  }

  return {
    tasks: 0,
    incidents: 0,
    blockers: 0,
  };
}
