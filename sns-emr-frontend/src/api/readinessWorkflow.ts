// sns-emr-frontend/src/api/readinessWorkflow.ts
//
// Sprint 2 -- Billing Readiness Operational Workflow.
//
// Contracts here are a 1:1 mirror of the Pydantic response models in
// backend/app/billing/schemas/billing_schema.py (Sprint2 section) and the
// endpoints in backend/app/billing/api/readiness_workflow_router.py. Do not
// add fields here that the backend doesn't send, and do not rename anything
// -- these types are the frontend half of the documented contract in
// docs/planning/eligibility_traceability_epic.md.
import api from "./client";

function withTenantParam(tenantId?: string | null) {
  return tenantId ? { tenant_id: tenantId } : {};
}

// =========================================================
// SHARED
// =========================================================

export type ReadinessStatus = "READY" | "AT_RISK" | "NOT_READY";
export type OperationalBucket = "READY" | "AT_RISK" | "NOT_READY" | "BLOCKED";
export type AssignmentStatus = "UNASSIGNED" | "ASSIGNED" | "IN_PROGRESS" | "COMPLETED";
export type FollowUpStatus = "OPEN" | "IN_PROGRESS" | "BLOCKED" | "RESOLVED";
export type BlockerCode =
  | "MISSING_CERTIFICATION"
  | "MISSING_FACE_TO_FACE"
  | "MISSING_PHYSICIAN_SIGNATURE"
  | "MISSING_DOCUMENTATION"
  | "BENEFIT_PERIOD_ISSUE"
  | "OTHER";
export type BlockerRecordStatus = "OPEN" | "RESOLVED";

// =========================================================
// DASHBOARD -- GET /billing/readiness-dashboard
// =========================================================

export type ReadinessDashboardCounts = {
  READY: number;
  AT_RISK: number;
  NOT_READY: number;
  BLOCKED: number;
};

export type ReadinessAttentionPatientRow = {
  patient_id: string;
  mrn: string;
  readiness_status: ReadinessStatus;
  operational_bucket: OperationalBucket;
  blocker_count: number;
  warning_count: number;
};

export type ReadinessStatusChangeRow = {
  patient_id: string;
  mrn: string;
  previous_status: ReadinessStatus;
  new_status: ReadinessStatus;
  changed_at: string;
};

export type RecentReadinessEvaluationRow = {
  patient_id: string;
  mrn: string;
  evaluated_at: string;
  readiness_status: ReadinessStatus;
  triggered_by: string;
};

export type ReadinessTrendRow = {
  service_date: string;
  ready_count: number;
  at_risk_count: number;
  not_ready_count: number;
};

export type TenantReadinessDashboardResponse = {
  tenant_id: string;
  service_date: string;
  counts: ReadinessDashboardCounts;
  patients_requiring_attention: ReadinessAttentionPatientRow[];
  recently_changed_status: ReadinessStatusChangeRow[];
  recent_evaluations: RecentReadinessEvaluationRow[];
  readiness_trend: ReadinessTrendRow[];
};

export function fetchReadinessDashboard(
  serviceDate: string,
  tenantId?: string | null
): Promise<TenantReadinessDashboardResponse> {
  return api
    .get<TenantReadinessDashboardResponse>("/billing/readiness-dashboard", {
      params: { service_date: serviceDate, ...withTenantParam(tenantId) },
    })
    .then((res) => res.data);
}

// =========================================================
// OPERATIONAL QUEUE -- GET /billing/readiness-queue
// =========================================================

export type ReadinessQueueRow = {
  patient_id: string;
  mrn: string;
  readiness_status: ReadinessStatus;
  operational_bucket: OperationalBucket;
  blockers: string[];
  warnings: string[];
  assignment_status: AssignmentStatus;
  assigned_user_id: string | null;
  assigned_role: string | null;
  open_follow_up_count: number;
  earliest_due_date: string | null;
};

export type ReadinessQueueResponse = {
  tenant_id: string;
  patients: ReadinessQueueRow[];
};

export type ReadinessQueueFilters = {
  status?: OperationalBucket;
  assignmentStatus?: AssignmentStatus;
  due?: "SOON" | "OVERDUE";
};

export function fetchReadinessQueue(
  tenantId?: string | null,
  filters: ReadinessQueueFilters = {}
): Promise<ReadinessQueueResponse> {
  return api
    .get<ReadinessQueueResponse>("/billing/readiness-queue", {
      params: {
        ...withTenantParam(tenantId),
        ...(filters.status ? { status: filters.status } : {}),
        ...(filters.assignmentStatus ? { assignment_status: filters.assignmentStatus } : {}),
        ...(filters.due ? { due: filters.due } : {}),
      },
    })
    .then((res) => res.data);
}

// =========================================================
// READINESS HISTORY (read-only) -- GET /billing/readiness-history/{patient_id}
// =========================================================

export type ReadinessVerdictHistoryRow = {
  id: string;
  evaluated_at: string;
  is_ready: boolean;
  readiness_status: ReadinessStatus;
  blockers: string[];
  warnings: string[];
  triggered_by: string;
};

export type ReadinessBlockerHistoryRow = {
  id: string;
  blocker_code: BlockerCode;
  message: string;
  status: BlockerRecordStatus;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_reason: string | null;
};

export type ReadinessAuditEventRow = {
  id: string;
  entity_type: "BLOCKER" | "ASSIGNMENT" | "FOLLOW_UP";
  entity_id: string;
  event_type: string;
  actor_user_id: string | null;
  occurred_at: string;
  reason: string | null;
  previous_value: Record<string, unknown> | null;
  new_value: Record<string, unknown>;
  related_verdict_id: string | null;
};

export type ReadinessHistoryResponse = {
  patient_id: string;
  verdicts: ReadinessVerdictHistoryRow[];
  blocker_history: ReadinessBlockerHistoryRow[];
  audit_trail: ReadinessAuditEventRow[];
};

export function fetchReadinessHistory(
  patientId: string,
  tenantId?: string | null
): Promise<ReadinessHistoryResponse> {
  return api
    .get<ReadinessHistoryResponse>(`/billing/readiness-history/${patientId}`, {
      params: withTenantParam(tenantId),
    })
    .then((res) => res.data);
}

// =========================================================
// ASSIGNMENTS -- POST /billing/readiness-assignments
// =========================================================

export type ReadinessAssignmentResponse = {
  id: string;
  tenant_id: string;
  patient_id: string;
  assigned_user_id: string | null;
  assigned_role: string | null;
  assigned_date: string | null;
  assigned_by: string | null;
  assignment_status: AssignmentStatus;
};

export type UpsertReadinessAssignmentRequest = {
  patient_id: string;
  assigned_user_id?: string | null;
  assigned_role?: string | null;
  assignment_status?: AssignmentStatus;
  related_verdict_id?: string | null;
};

export function upsertReadinessAssignment(
  payload: UpsertReadinessAssignmentRequest,
  tenantId?: string | null
): Promise<ReadinessAssignmentResponse> {
  return api
    .post<ReadinessAssignmentResponse>("/billing/readiness-assignments", {
      ...payload,
      tenant_id: tenantId ?? undefined,
    })
    .then((res) => res.data);
}

// =========================================================
// FOLLOW-UPS -- POST /billing/readiness-followups
// =========================================================

export type ReadinessFollowUpResponse = {
  id: string;
  tenant_id: string;
  patient_id: string;
  assignment_id: string | null;
  follow_up_required: boolean;
  status: FollowUpStatus;
  due_date: string | null;
  resolved_date: string | null;
  created_date: string;
  notes: string | null;
};

export type UpsertReadinessFollowUpRequest = {
  patient_id: string;
  follow_up_id?: string | null;
  assignment_id?: string | null;
  follow_up_required?: boolean;
  status?: FollowUpStatus;
  due_date?: string | null;
  notes?: string | null;
  reason?: string | null;
  related_verdict_id?: string | null;
};

export function upsertReadinessFollowUp(
  payload: UpsertReadinessFollowUpRequest,
  tenantId?: string | null
): Promise<ReadinessFollowUpResponse> {
  return api
    .post<ReadinessFollowUpResponse>("/billing/readiness-followups", {
      ...payload,
      tenant_id: tenantId ?? undefined,
    })
    .then((res) => res.data);
}

// =========================================================
// MANUAL BLOCKER RESOLUTION -- POST /billing/readiness-blockers/{id}/resolve
// =========================================================

export type ReadinessBlockerResponse = {
  id: string;
  patient_id: string;
  blocker_code: BlockerCode;
  message: string;
  status: BlockerRecordStatus;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_reason: string | null;
};

export function resolveReadinessBlocker(
  blockerId: string,
  reason: string | undefined,
  tenantId?: string | null
): Promise<ReadinessBlockerResponse> {
  return api
    .post<ReadinessBlockerResponse>(
      `/billing/readiness-blockers/${blockerId}/resolve`,
      { reason },
      { params: withTenantParam(tenantId) }
    )
    .then((res) => res.data);
}
