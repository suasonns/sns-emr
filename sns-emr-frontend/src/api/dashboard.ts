import { getAccessToken } from "./session";

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

// ✅ UPDATED FOR 835
export type BillingDashboardResponse = {
  metrics: DashboardMetric[];
  payments_received: number;
  denied_claims: number;
  claims_pending_payment: number;
  remittance_files_processed: number;
  billing_holds: Array<Record<string, unknown>>;
};

// ✅ STEP 13 — CLAIM LIFECYCLE
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
  const res = await fetch(url, {
    credentials: "include",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });

  if (!res.ok) {
    throw new Error(`Request failed: ${url}`);
  }

  return res.json();
}

// =========================================================
// DASHBOARD CALLS
// =========================================================

export function fetchTenantDashboard(): Promise<TenantDashboardResponse> {
  return fetchJson<TenantDashboardResponse>("/api/dashboard/tenant");
}

export function fetchOwnerDashboard(): Promise<OwnerDashboardResponse> {
  return fetchJson<OwnerDashboardResponse>("/api/dashboard/owner");
}

export function fetchClinicalComplianceDashboard(): Promise<ClinicalComplianceDashboardResponse> {
  return fetchJson<ClinicalComplianceDashboardResponse>("/api/dashboard/clinical-compliance");
}

export function fetchClinicalAlerts(): Promise<ClinicalAlertsResponse> {
  return fetchJson<ClinicalAlertsResponse>("/api/dashboard/clinical-alerts");
}

export function fetchBillingDashboard(): Promise<BillingDashboardResponse> {
  return fetchJson<BillingDashboardResponse>("/api/dashboard/billing");
}

// ✅ STEP 13 — CLAIM LIFECYCLE API
export function fetchClaimLifecycle(): Promise<ClaimLifecycleResponse> {
  return fetchJson<ClaimLifecycleResponse>("/api/dashboard/claim-lifecycle");
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

  if (normalized === "TENANT_ADMIN" || normalized === "CLINICIAN") {
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

  if (normalized === "BILLER") {
    const data = await fetchBillingDashboard();

    return {
      tasks: data.claims_pending_payment ?? 0,
      incidents: data.denied_claims ?? 0,
      blockers: data.denied_claims ?? 0,
    };
  }

  return {
    tasks: 0,
    incidents: 0,
    blockers: 0,
  };
}
