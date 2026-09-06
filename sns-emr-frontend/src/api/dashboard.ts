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

export type BillingQueueRow = {
  claim_id?: string;
  billing_cycle_id: string;
  patient_id: string;
  patient_name?: string | null;
  patient_mrn?: string | null;
  payer_name?: string | null;
  tenant_name?: string | null;
  tenant_id?: string | null;
  total_charge?: number | null;
  total_units?: number | null;
  risk_score?: number | null;
  status: string;
  service_date?: string | null;
  claim_control_number?: string | null;
  exported_at?: string | null;
  last_status_reason?: string | null;
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

async function postJson<T>(url: string, body: unknown): Promise<T> {
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
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (res.status === 401 || res.status === 403) {
        clearAccessToken();
        clearCurrentUser();
        throw new Error("Session expired. Please sign in again.");
      }

      if (!res.ok) {
        let detail = `Request failed: ${url}`;
        try {
          const payload = await res.json();
          if (payload?.detail) detail = payload.detail;
        } catch {
          // ignore -- fall back to the generic message
        }
        throw new Error(detail);
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

export class DashboardApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "DashboardApiError";
    this.status = status;
  }
}

async function facilityFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const candidates = [`${base}${url}`, ...(base ? [`http://localhost:8000${url}`] : [])];

  let lastError: Error | null = null;
  for (const candidate of candidates) {
    try {
      const requestHeaders = (init?.headers ?? {}) as Record<string, string>;
      const response = await fetch(candidate, {
        credentials: "include",
        ...init,
        headers: {
          ...requestHeaders,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (response.status === 401) {
        clearAccessToken();
        clearCurrentUser();
        throw new DashboardApiError(401, "Session expired. Please sign in again.");
      }

      if (!response.ok) {
        let detail = `Request failed: ${url}`;
        try {
          const payload = await response.json();
          if (payload?.detail) detail = String(payload.detail);
        } catch {
          // ignore and keep generic detail
        }
        throw new DashboardApiError(response.status, detail);
      }

      return (await response.json()) as T;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(`Request failed: ${url}`);
      if (candidate === candidates[candidates.length - 1]) break;
    }
  }

  throw lastError ?? new Error(`Request failed: ${url}`);
}

async function facilityPost<T>(url: string, body: unknown): Promise<T> {
  return facilityFetch<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
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

export function fetchBillingQueue(tenantId?: string | null): Promise<BillingQueueRow[]> {
  return fetchJson<BillingQueueRow[]>(withTenantId("/billing/queue", tenantId));
}

export function fetchClaimLifecycle(tenantId?: string | null): Promise<ClaimLifecycleResponse> {
  return fetchJson<ClaimLifecycleResponse>(withTenantId("/api/dashboard/claim-lifecycle", tenantId));
}

export type DenialsAppealsSummaryResponse = {
  open_denials: number;
  appealed_denials: number;
  overturned_denials: number;
  upheld_denials: number;
  written_off_denials: number;
  total_denied_amount: number;
  open_denied_amount: number;
  total_recovered_amount: number;
  top_denial_codes: {
    carc_code: string | null;
    reason_description: string | null;
    case_count: number;
    total_amount: number;
  }[];
};

export function fetchDenialsAppealsSummary(
  tenantId?: string | null
): Promise<DenialsAppealsSummaryResponse> {
  return fetchJson<DenialsAppealsSummaryResponse>(
    withTenantId("/api/dashboard/denials-appeals", tenantId)
  );
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

// AR Aging Report -- pure calculation over existing claims/payment/
// adjustment/denial records (see backend aging_report_service). No new
// data store. Buckets are fixed: 0-30 / 31-60 / 61-90 / 91-120 / 120+.
export type AgingBucketTotal = {
  bucket: string;
  total_outstanding: string;
  claim_count: number;
};

export type AgingPayerTotal = {
  payer_name: string;
  total_outstanding: string;
  claim_count: number;
  by_bucket: Record<string, string>;
};

export type AgingAgencyTotal = {
  tenant_id: string;
  agency_name: string;
  total_outstanding: string;
  claim_count: number;
  by_bucket: Record<string, string>;
};

export type AgingClaimRow = {
  claim_id: string;
  tenant_id: string;
  agency_name: string;
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  payer_name: string;
  claim_control_number: string | null;
  status: string;
  total_charge: string;
  posted_payments: string;
  adjustments: string;
  write_offs: string;
  outstanding_balance: string;
  exported_at: string | null;
  days_outstanding: number;
  bucket: string;
};

export type AgingReportResponse = {
  as_of: string;
  summary: {
    total_outstanding: string;
    claim_count: number;
    average_days_outstanding: number;
  };
  by_bucket: AgingBucketTotal[];
  by_payer: AgingPayerTotal[];
  by_agency: AgingAgencyTotal[];
  claims: AgingClaimRow[];
};

export function fetchAgingReport(
  tenantId?: string | null,
  params?: { tenant_ids?: string[]; all_agencies?: boolean; as_of?: string }
): Promise<AgingReportResponse> {
  const search = new URLSearchParams();
  if (params?.tenant_ids && params.tenant_ids.length > 0) search.set("tenant_ids", params.tenant_ids.join(","));
  if (params?.all_agencies) search.set("all_agencies", "true");
  if (params?.as_of) search.set("as_of", params.as_of);
  const query = search.toString();
  const base = `/billing/aging-report${query ? `?${query}` : ""}`;
  return fetchJson<AgingReportResponse>(withTenantId(base, tenantId));
}

// Credit Balance Report -- claim-level overpayment detection + patient/
// account summary, plus a controlled case-lifecycle workflow (see backend
// credit_balance_service / credit_balance_case_service). Claim-level is
// the authoritative grain; patient_accounts is a summary only and never
// nets away/suppresses an individual claim's credit balance.
export type Money = { amount: string; currency: string };

export type CreditBalancePatientAccount = {
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  tenant_id: string;
  agency_name: string;
  payer_names: string[];
  // Billing context surfaced from existing PatientPayer.priority_order /
  // is_primary -- not a new payer subsystem. Null when not resolvable.
  primary_payer_name: string | null;
  secondary_payer_name: string | null;
  total_charges: Money;
  total_payments: Money;
  total_adjustments: Money;
  total_write_offs: Money;
  total_positive_ar: Money;
  total_credit_balance: Money;
  net_patient_account_balance: Money;
  claims_with_credit: number;
  oldest_unresolved_credit: string | null;
};

export type CreditBalanceClaimItem = {
  claim_id: string;
  tenant_id: string;
  agency_name: string;
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  payer_name: string;
  // Billing context surfaced from existing PatientPayer.priority_order /
  // is_primary -- a claim may be billed to a payer that differs from the
  // patient's on-file primary (e.g. billed to Medicare while the
  // patient's primary changed since), so both are shown.
  primary_payer_name: string | null;
  secondary_payer_name: string | null;
  // "If available" operational fields -- amounts posted specifically by
  // the primary/secondary payer (matched via the posting remittance's
  // payer_name). Zero, not fabricated, when nothing posted yet.
  primary_payer_paid: Money;
  secondary_payer_paid: Money;
  most_recent_payment_date: string | null;
  claim_control_number: string | null;
  status: string;
  total_charge: Money;
  posted_payments: Money;
  adjustments: Money;
  write_offs: Money;
  credit_amount: Money;
  exported_at: string | null;
  payment_count: number;
  // Mechanical detection only (2+ payments with the exact same amount) --
  // never a system-inferred root cause. See reason_code on the case for
  // the human-reviewed determination (DUPLICATE_PAYMENT / POSTING_ERROR /
  // COB_ISSUE / MSP_ISSUE / RECOUPMENT_TIMING / OTHER).
  potential_duplicate_payment: boolean;
  medicare_classification: string;
  data_completeness: string;
  case_id: string | null;
  case_status: string;
  reason_code: string | null;
};

export type CreditBalanceReportResponse = {
  generated_at: string;
  as_of_date: string;
  summary: {
    total_potential_credits: Money;
    claim_count: number;
    patient_count: number;
  };
  patient_accounts: CreditBalancePatientAccount[];
  claim_credit_items: CreditBalanceClaimItem[];
};

export function fetchCreditBalanceReport(
  tenantId?: string | null,
  params?: { tenant_ids?: string[]; all_agencies?: boolean; as_of?: string }
): Promise<CreditBalanceReportResponse> {
  const search = new URLSearchParams();
  if (params?.tenant_ids && params.tenant_ids.length > 0) search.set("tenant_ids", params.tenant_ids.join(","));
  if (params?.all_agencies) search.set("all_agencies", "true");
  if (params?.as_of) search.set("as_of", params.as_of);
  const query = search.toString();
  const base = `/billing/credit-balance/report${query ? `?${query}` : ""}`;
  return fetchJson<CreditBalanceReportResponse>(withTenantId(base, tenantId));
}

export type CreditBalanceCaseEvent = {
  action: string;
  previous_status: string | null;
  new_status: string | null;
  reason: string;
  performed_by: string;
  source_transaction_reference: string | null;
  amount_before: string | null;
  amount_after: string | null;
  created_at: string | null;
};

export type CreditBalanceCase = {
  case_id: string;
  tenant_id: string;
  claim_id: string;
  patient_id: string;
  status: string;
  medicare_classification: string;
  reason_code: string | null;
  // Billing context surfaced from existing PatientPayer.priority_order /
  // is_primary -- not a new payer subsystem. Null when not resolvable.
  primary_payer_name: string | null;
  secondary_payer_name: string | null;
  credit_amount_at_detection: Money;
  amount_repaid: Money;
  amount_recouped: Money;
  amount_reallocated: Money;
  repayment_method: string | null;
  assigned_to: string | null;
  notes: string | null;
  detected_at: string | null;
  review_started_at: string | null;
  identified_at: string | null;
  confirmed_at: string | null;
  repayment_due_at: string | null;
  repaid_at: string | null;
  recouped_at: string | null;
  reallocated_at: string | null;
  resolved_at: string | null;
  events: CreditBalanceCaseEvent[];
};

export function fetchCreditBalanceCases(
  tenantId?: string | null,
  params?: { tenant_ids?: string[]; all_agencies?: boolean; status?: string; medicare_reportable?: string }
): Promise<{ cases: CreditBalanceCase[] }> {
  const search = new URLSearchParams();
  if (params?.tenant_ids && params.tenant_ids.length > 0) search.set("tenant_ids", params.tenant_ids.join(","));
  if (params?.all_agencies) search.set("all_agencies", "true");
  if (params?.status) search.set("status", params.status);
  if (params?.medicare_reportable) search.set("medicare_reportable", params.medicare_reportable);
  const query = search.toString();
  const base = `/billing/credit-balance/cases${query ? `?${query}` : ""}`;
  return fetchJson<{ cases: CreditBalanceCase[] }>(withTenantId(base, tenantId));
}

export function openCreditBalanceCase(claimId: string): Promise<CreditBalanceCase> {
  return postJson<CreditBalanceCase>("/billing/credit-balance/cases", { claim_id: claimId });
}

// Enumerated root-cause reason codes a biller may select when confirming a
// case (e.g. after reviewing a "Potential Duplicate Payment" flag). The
// system never infers one of these automatically -- see
// app.billing.services.credit_balance_case_service.DUPLICATE_PAYMENT_REASON_CODES.
export function fetchCreditBalanceReasonCodes(): Promise<{ reason_codes: string[] }> {
  return fetchJson<{ reason_codes: string[] }>("/billing/credit-balance/reason-codes");
}

export function performCreditBalanceCaseAction(
  caseId: string,
  payload: {
    action: string;
    reason: string;
    source_transaction_reference?: string;
    amount?: string;
    repayment_due_at?: string;
    repayment_method?: string;
    reason_code?: string;
    medicare_classification?: string;
  }
): Promise<CreditBalanceCase> {
  return postJson<CreditBalanceCase>(`/billing/credit-balance/cases/${caseId}/actions`, payload);
}

// Facility & Residence Payment Visibility -- expected facility/room-and-
// board/share-of-cost obligations reconciled against the *existing*
// Payment/RemittanceAdvice pipeline. See
// app.billing.services.facility_payment_service. Nothing here duplicates
// payment or remittance data; allocations only reference existing IDs.
export type FacilityPaymentAging = {
  aging_status: string;
  aging_bucket: string | null;
  days_outstanding: number | null;
  aging_basis_date?: string | null;
  aging_basis_source?: string | null;
};

export type FacilityPaymentExpectation = {
  id: string;
  tenant_id: string;
  patient_id: string;
  patient_pos_id: string | null;
  patient_name: string | null;
  mrn: string | null;
  agency_name: string | null;
  facility_name_snapshot: string | null;
  residence_type_snapshot: string | null;
  room_number_snapshot: string | null;
  residence_start_date_snapshot: string | null;
  residence_end_date_snapshot: string | null;
  expected_funding_source_snapshot: string | null;
  expected_payer_name_snapshot: string | null;
  primary_payer_name_snapshot: string | null;
  secondary_payer_name_snapshot: string | null;
  responsibility_category: string;
  expected_funding_source: string;
  expected_amount: string;
  currency: string;
  frequency: string | null;
  service_period_start: string;
  service_period_end: string;
  due_date: string | null;
  due_date_source: string;
  payment_term_verified: boolean;
  authorization_reference: string | null;
  contract_reference: string | null;
  share_of_cost_amount: string | null;
  status: string;
  version_number: number;
  row_version: number;
  supersedes_expectation_id: string | null;
  superseded_by_expectation_id: string | null;
  correction_reason: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;
  cancelled_by: string | null;
  notes: string | null;
  source: string;
  client_request_id: string | null;
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  reconciliation_status: string;
  amount_received: string;
  outstanding_amount: string;
  most_recent_payment_date: string | null;
  aging: FacilityPaymentAging;
};

export type FacilityPaymentAllocation = {
  id: string;
  tenant_id: string;
  facility_payment_expectation_id: string;
  payment_id: string | null;
  remittance_advice_id: string | null;
  claim_id: string | null;
  payment_adjustment_id: string | null;
  payer_name: string | null;
  amount_applied: string;
  payment_date: string | null;
  allocation_status: string;
  flagged_for_review: boolean;
  flagged_reason: string | null;
  match_basis: string;
  notes: string | null;
  reconciled_by: string | null;
  reconciled_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type FacilityPaymentAuditEntry = {
  id: string;
  entity_type: string;
  entity_id: string;
  field_name: string;
  previous_value: string | null;
  new_value: string | null;
  user_id: string | null;
  role: string | null;
  reason: string | null;
  supporting_reference: string | null;
  correlation_id: string | null;
  created_at: string | null;
};

export type FacilityPaymentExpectationDetail = FacilityPaymentExpectation & {
  allocations?: FacilityPaymentAllocation[];
  audit_summary?: {
    total_entries: number;
    entries: FacilityPaymentAuditEntry[];
  };
};

export type FacilityPaymentExpectationHistoryItem = {
  id: string;
  version_number: number;
  status: string;
  correction_reason: string | null;
  cancellation_reason: string | null;
  created_by: string | null;
  corrected_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type FacilityPaymentExpectationHistoryResponse = {
  current_expectation_id: string;
  items: FacilityPaymentExpectationHistoryItem[];
};

export type FacilitySnapshotDiffField = {
  snapshot: string | null;
  current: string | null;
  changed: boolean;
};

export type FacilityPaymentResidenceSnapshotDiffResponse = {
  expectation_id: string;
  patient_id: string;
  patient_pos_id: string | null;
  has_changes: boolean;
  fields: Record<string, FacilitySnapshotDiffField>;
};

export type FacilityPaymentExpectationCreatePayload = {
  patient_id: string;
  patient_pos_id?: string;
  responsibility_category: string;
  expected_funding_source: string;
  expected_amount: string;
  currency?: string;
  frequency?: string;
  service_period_start: string;
  service_period_end: string;
  due_date?: string;
  authorization_reference?: string;
  contract_reference?: string;
  share_of_cost_amount?: string;
  source?: string;
  expected_payer_name_snapshot?: string;
  notes?: string;
  client_request_id?: string;
};

export type FacilityPaymentExpectationCorrectPayload = {
  patient_pos_id?: string;
  responsibility_category?: string;
  expected_funding_source?: string;
  expected_amount?: string;
  currency?: string;
  frequency?: string;
  service_period_start?: string;
  service_period_end?: string;
  due_date?: string;
  authorization_reference?: string;
  contract_reference?: string;
  share_of_cost_amount?: string;
  source?: string;
  expected_payer_name_snapshot?: string;
  notes?: string;
  expected_row_version?: number;
  correction_reason: string;
};

export function fetchFacilityPaymentExpectations(
  tenantId?: string | null,
  params?: {
    tenant_ids?: string[];
    all_agencies?: boolean;
    patient_id?: string;
    status?: string;
    reconciliation_status?: string;
    responsibility_category?: string;
    funding_source?: string;
    residence_type?: string;
    aging_bucket?: string;
    service_period_start?: string;
    service_period_end?: string;
  }
): Promise<{ count: number; items: FacilityPaymentExpectation[] }> {
  const search = new URLSearchParams();
  if (params?.tenant_ids && params.tenant_ids.length > 0) search.set("tenant_ids", params.tenant_ids.join(","));
  if (params?.all_agencies) search.set("all_agencies", "true");
  if (params?.patient_id) search.set("patient_id", params.patient_id);
  if (params?.status) search.set("status", params.status);
  if (params?.reconciliation_status) search.set("reconciliation_status", params.reconciliation_status);
  if (params?.responsibility_category) search.set("responsibility_category", params.responsibility_category);
  if (params?.funding_source) search.set("funding_source", params.funding_source);
  if (params?.residence_type) search.set("residence_type", params.residence_type);
  if (params?.aging_bucket) search.set("aging_bucket", params.aging_bucket);
  if (params?.service_period_start) search.set("service_period_start", params.service_period_start);
  if (params?.service_period_end) search.set("service_period_end", params.service_period_end);
  const query = search.toString();
  const base = `/billing/facility-payments/expectations${query ? `?${query}` : ""}`;
  return facilityFetch(withTenantId(base, tenantId));
}

export function createFacilityPaymentExpectation(
  payload: FacilityPaymentExpectationCreatePayload,
  tenantId?: string | null
): Promise<FacilityPaymentExpectationDetail> {
  return facilityPost<FacilityPaymentExpectationDetail>(
    withTenantId("/billing/facility-payments/expectations", tenantId),
    payload
  );
}

export function correctFacilityPaymentExpectation(
  expectationId: string,
  payload: FacilityPaymentExpectationCorrectPayload
): Promise<FacilityPaymentExpectationDetail> {
  return facilityPost<FacilityPaymentExpectationDetail>(
    `/billing/facility-payments/expectations/${expectationId}/correct`,
    payload
  );
}

export function activateFacilityPaymentExpectation(
  expectationId: string,
  payload: { expected_row_version?: number }
): Promise<FacilityPaymentExpectationDetail> {
  return facilityPost<FacilityPaymentExpectationDetail>(
    `/billing/facility-payments/expectations/${expectationId}/activate`,
    payload
  );
}

export function cancelFacilityPaymentExpectation(
  expectationId: string,
  payload: { cancellation_reason: string; force?: boolean; expected_row_version?: number }
): Promise<FacilityPaymentExpectationDetail> {
  return facilityPost<FacilityPaymentExpectationDetail>(
    `/billing/facility-payments/expectations/${expectationId}/cancel`,
    payload
  );
}

export function fetchFacilityPaymentExpectationDetail(
  expectationId: string
): Promise<FacilityPaymentExpectationDetail> {
  return facilityFetch<FacilityPaymentExpectationDetail>(
    `/billing/facility-payments/expectations/${expectationId}`
  );
}

export function fetchFacilityPaymentExpectationHistory(
  expectationId: string
): Promise<FacilityPaymentExpectationHistoryResponse> {
  return facilityFetch<FacilityPaymentExpectationHistoryResponse>(
    `/billing/facility-payments/expectations/${expectationId}/history`
  );
}

export function fetchFacilityPaymentResidenceSnapshotDiff(
  expectationId: string
): Promise<FacilityPaymentResidenceSnapshotDiffResponse> {
  return facilityFetch<FacilityPaymentResidenceSnapshotDiffResponse>(
    `/billing/facility-payments/expectations/${expectationId}/residence-snapshot-diff`
  );
}

export function fetchFacilityPaymentCandidates(
  expectationId: string
): Promise<{ count: number; items: FacilityPaymentAllocation[] }> {
  return facilityFetch(`/billing/facility-payments/expectations/${expectationId}/candidates`);
}

export function confirmFacilityPaymentAllocation(allocationId: string): Promise<FacilityPaymentAllocation> {
  return facilityPost<FacilityPaymentAllocation>(`/billing/facility-payments/allocations/${allocationId}/confirm`, {});
}

export function reverseFacilityPaymentAllocation(
  allocationId: string,
  reason: string
): Promise<FacilityPaymentAllocation> {
  return facilityPost<FacilityPaymentAllocation>(`/billing/facility-payments/allocations/${allocationId}/reverse`, {
    reason,
  });
}

export type FacilityCollectionsReportRow = {
  agency_name: string;
  patient_name: string | null;
  mrn: string | null;
  facility_name_snapshot: string | null;
  residence_type_snapshot: string | null;
  service_period: { start: string; end: string };
  responsibility_category: string;
  expected_funding_source: string;
  primary_payer_name: string | null;
  secondary_payer_name: string | null;
  expected_amount: string;
  amount_received: string;
  outstanding_amount: string;
  most_recent_payment_date: string | null;
  due_date: string | null;
  due_date_source: string;
  payment_term_verified: boolean;
  days_outstanding: number | null;
  status: string;
  reconciliation_status: string;
  aging_bucket: string | null;
  expectation_id: string;
};

export type FacilityCollectionsReportResponse = {
  rows: FacilityCollectionsReportRow[];
  summary: {
    total_expected: string;
    total_received: string;
    total_outstanding: string;
    partially_paid_count: number;
    unmatched_payments_count: number;
    overdue_obligations_count: number;
    reconciliation_exceptions_count: number;
    collection_rate: string;
  };
};

export function fetchFacilityCollectionsReport(
  tenantId?: string | null,
  params?: {
    tenant_ids?: string[];
    all_agencies?: boolean;
    residence_type?: string;
    funding_source?: string;
    payer_name?: string;
    responsibility_category?: string;
    reconciliation_status?: string;
    aging_bucket?: string;
    service_period_start?: string;
    service_period_end?: string;
  }
): Promise<FacilityCollectionsReportResponse> {
  const search = new URLSearchParams();
  if (params?.tenant_ids && params.tenant_ids.length > 0) search.set("tenant_ids", params.tenant_ids.join(","));
  if (params?.all_agencies) search.set("all_agencies", "true");
  if (params?.residence_type) search.set("residence_type", params.residence_type);
  if (params?.funding_source) search.set("funding_source", params.funding_source);
  if (params?.payer_name) search.set("payer_name", params.payer_name);
  if (params?.responsibility_category) search.set("responsibility_category", params.responsibility_category);
  if (params?.reconciliation_status) search.set("reconciliation_status", params.reconciliation_status);
  if (params?.aging_bucket) search.set("aging_bucket", params.aging_bucket);
  if (params?.service_period_start) search.set("service_period_start", params.service_period_start);
  if (params?.service_period_end) search.set("service_period_end", params.service_period_end);
  const query = search.toString();
  const base = `/billing/facility-payments/collections-report${query ? `?${query}` : ""}`;
  return facilityFetch(withTenantId(base, tenantId));
}

export type FacilityCollectionAlert = {
  id: string;
  tenant_id: string;
  patient_id: string | null;
  facility_payment_expectation_id: string | null;
  alert_type: string;
  severity: string;
  expected_amount: string | null;
  received_amount: string | null;
  outstanding_amount: string | null;
  due_date: string | null;
  days_outstanding: number | null;
  status: string;
  assigned_to: string | null;
  resolution_evidence: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export function fetchFacilityCollectionAlerts(
  tenantId?: string | null,
  status?: string
): Promise<{ count: number; items: FacilityCollectionAlert[] }> {
  const search = new URLSearchParams();
  if (status) search.set("status", status);
  const query = search.toString();
  const base = `/billing/facility-payments/alerts${query ? `?${query}` : ""}`;
  return facilityFetch(withTenantId(base, tenantId));
}

export function resolveFacilityCollectionAlert(
  alertId: string,
  resolutionEvidence: string
): Promise<FacilityCollectionAlert> {
  return facilityPost<FacilityCollectionAlert>(`/billing/facility-payments/alerts/${alertId}/resolve`, {
    resolution_evidence: resolutionEvidence,
  });
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
// CLAIMS MANAGEMENT
// =========================================================

export type ClaimRow = {
  claim_id: string;
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  payer_name: string | null;
  service_date: string | null;
  total_charge: number | null;
  total_units: number | null;
  status: string | null;
  claim_control_number: string | null;
  last_status_reason: string | null;
  created_at: string | null;
  days_in_status: number | null;
};

export type ClaimsResponse = {
  tenant_id: string;
  count: number;
  total_claims: number;
  submitted_count: number;
  accepted_count: number;
  denied_count: number;
  lifecycle: { draft: number; submitted: number; accepted: number; paid: number; denied: number };
  claims: ClaimRow[];
};

export function fetchClaims(
  tenantId?: string | null,
  params?: { status?: string; payer_name?: string; limit?: number }
): Promise<ClaimsResponse> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.payer_name) search.set("payer_name", params.payer_name);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/claims${query ? `?${query}` : ""}`;
  return fetchJson<ClaimsResponse>(withTenantId(base, tenantId));
}

// =========================================================
// DENIALS & APPEALS
// =========================================================

export type DenialRow = {
  denial_id: string;
  claim_id: string;
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  payer_name: string | null;
  denial_date: string | null;
  carc_code: string | null;
  reason_description: string | null;
  denied_amount: number | null;
  status: string | null;
  appeal_status_label: string | null;
  appeal_deadline: string | null;
  days_elapsed: number | null;
};

export type DenialsResponse = {
  tenant_id: string;
  count: number;
  total_denials: number;
  appeals_filed: number;
  appeal_rate: number | null;
  overturn_rate: number | null;
  avg_resolution_days: number | null;
  reason_breakdown: { reason: string; count: number; percent: number }[];
  denials: DenialRow[];
};

export function fetchDenials(
  tenantId?: string | null,
  params?: { reason?: string; payer_name?: string; status?: string; limit?: number }
): Promise<DenialsResponse> {
  const search = new URLSearchParams();
  if (params?.reason) search.set("reason", params.reason);
  if (params?.payer_name) search.set("payer_name", params.payer_name);
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/denials${query ? `?${query}` : ""}`;
  return fetchJson<DenialsResponse>(withTenantId(base, tenantId));
}

// =========================================================
// ELIGIBILITY VERIFICATION
// =========================================================

export type EligibilityRosterRow = {
  insurance_id: string;
  patient_id: string;
  patient_name: string | null;
  mrn: string | null;
  payer_name: string | null;
  subscriber_id: string | null;
  eligibility_status: string | null;
  verified_at: string | null;
  next_verification_due: string | null;
};

export type EligibilityRosterResponse = {
  tenant_id: string;
  count: number;
  total_active: number;
  eligible_count: number;
  pending_count: number;
  inactive_count: number;
  roster: EligibilityRosterRow[];
  upcoming_reverifications: {
    insurance_id: string;
    mrn: string | null;
    patient_name: string | null;
    next_verification_due: string | null;
    days_until_due: number;
  }[];
};

export function fetchEligibilityRoster(
  tenantId?: string | null,
  params?: { payer_name?: string; status?: string; limit?: number }
): Promise<EligibilityRosterResponse> {
  const search = new URLSearchParams();
  if (params?.payer_name) search.set("payer_name", params.payer_name);
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/eligibility-roster${query ? `?${query}` : ""}`;
  return fetchJson<EligibilityRosterResponse>(withTenantId(base, tenantId));
}

// =========================================================
// PAYMENT POSTING
// =========================================================

export type RemittanceRow = {
  era_id: string;
  payer_name: string | null;
  received_at: string | null;
  claim_count: number | null;
  total_paid_amount: number | null;
  status: string | null;
  file_name: string | null;
};

export type RemittancesResponse = {
  tenant_id: string;
  count: number;
  total_payments_mtd: number;
  era_received_count: number;
  posted_count: number;
  pending_manual_match_count: number;
  payer_breakdown: { payer_name: string; total_paid: number }[];
  unmatched_payments: {
    payment_id: string;
    claim_control_number: string | null;
    patient_name: string | null;
    paid_amount: number | null;
    match_status: string | null;
  }[];
  remittances: RemittanceRow[];
};

export function fetchRemittances(
  tenantId?: string | null,
  params?: { payer_name?: string; status?: string; limit?: number }
): Promise<RemittancesResponse> {
  const search = new URLSearchParams();
  if (params?.payer_name) search.set("payer_name", params.payer_name);
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  const base = `/billing/remittances${query ? `?${query}` : ""}`;
  return fetchJson<RemittancesResponse>(withTenantId(base, tenantId));
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
