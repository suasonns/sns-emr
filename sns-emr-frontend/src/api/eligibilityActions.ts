// sns-emr-frontend/src/api/eligibilityActions.ts
//
// Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
// Correction -- Phases A-E operational actions.
//
// Contracts here are a 1:1 mirror of the Pydantic request/response models
// added to backend/app/billing/schemas/billing_schema.py and the endpoints
// in backend/app/billing/api/eligibility_action_router.py. Do not add
// fields here that the backend doesn't send/accept, and do not rename
// anything without updating both sides.
import api from "./client";

function withTenantParam(tenantId?: string | null) {
  return tenantId ? { tenant_id: tenantId } : {};
}

// =========================================================
// SHARED -- Phase C eligibility change impact engine
// =========================================================

export type BillingImpactSummary = {
  admission_gate_status: "CLEAR" | "ADMISSION_REVIEW_REQUIRED" | string;
  billing_readiness_reevaluated: boolean;
  readiness_status: "READY" | "AT_RISK" | "NOT_READY" | null;
  blockers: string[];
  warnings: string[];
};

// =========================================================
// PHASE A -- DOCUMENT UPLOAD WORKFLOW
// POST /billing/eligibility/{patient_id}/documents (multipart/form-data)
// =========================================================

export type EligibilityDocumentActionResponse = {
  id: string;
  patient_id: string;
  document_type: string;
  status: string;
  version: number;
  notes: string | null;
  document_record_id: string;
  supersedes_document_id: string | null;
  uploaded_at: string;
};

export type UploadEligibilityDocumentParams = {
  file: File;
  document_type: string;
  payer_coverage_id?: string | null;
  verification_date?: string | null;
  service_date_from?: string | null;
  service_date_to?: string | null;
  notes?: string | null;
  supersedes_document_id?: string | null;
};

export function uploadEligibilityDocument(
  patientId: string,
  params: UploadEligibilityDocumentParams,
  tenantId?: string | null
): Promise<EligibilityDocumentActionResponse> {
  const form = new FormData();
  form.append("file", params.file);
  form.append("document_type", params.document_type);
  if (params.payer_coverage_id) form.append("payer_coverage_id", params.payer_coverage_id);
  if (params.verification_date) form.append("verification_date", params.verification_date);
  if (params.service_date_from) form.append("service_date_from", params.service_date_from);
  if (params.service_date_to) form.append("service_date_to", params.service_date_to);
  if (params.notes) form.append("notes", params.notes);
  if (params.supersedes_document_id) {
    form.append("supersedes_document_id", params.supersedes_document_id);
  }

  return api
    .post<EligibilityDocumentActionResponse>(
      `/billing/eligibility/${patientId}/documents`,
      form,
      { headers: { "Content-Type": "multipart/form-data" }, params: withTenantParam(tenantId) }
    )
    .then((res) => res.data);
}

// =========================================================
// PHASE B -- REVERIFICATION ACTION WORKFLOW
// POST /billing/eligibility/{patient_id}/verifications
// =========================================================

export type CreateEligibilityVerificationRequest = {
  source_document_id: string;
  status: string;
  verification_date?: string | null;
  verification_method?: string;
  response_reference?: string | null;
  effective_date?: string | null;
  termination_date?: string | null;
  payer_coverage_id?: string | null;
  entitlement_data?: Record<string, unknown> | null;
  payment_routing_data?: Record<string, unknown> | null;
  hospice_utilization_data?: Record<string, unknown> | null;
  notes?: string | null;
  coverage_change_flag?: boolean;
  payer_change_flag?: boolean;
  msp_change_flag?: boolean;
  ma_change_flag?: boolean;
  overlap_concern_flag?: boolean;
};

export type EligibilityVerificationActionResponse = {
  id: string;
  patient_id: string;
  status: string;
  verification_date: string | null;
  source_document_id: string;
  notes: string | null;
  impact: BillingImpactSummary;
};

export function createEligibilityVerification(
  patientId: string,
  payload: CreateEligibilityVerificationRequest,
  tenantId?: string | null
): Promise<EligibilityVerificationActionResponse> {
  return api
    .post<EligibilityVerificationActionResponse>(
      `/billing/eligibility/${patientId}/verifications`,
      { ...payload, tenant_id: tenantId ?? undefined }
    )
    .then((res) => res.data);
}

// =========================================================
// PHASE 3/D SUPPORT -- direct benefit-period determination creation
// POST /billing/eligibility/{patient_id}/benefit-period-determinations
// =========================================================

export type CreateBenefitPeriodDeterminationRequest = {
  determination_status: string;
  admission_id?: string | null;
  eligibility_verification_id?: string | null;
  source_document_id?: string | null;
  prior_hospice_episode_count?: number | null;
  benefit_periods_used?: number | null;
  anticipated_benefit_period_number?: number | null;
  anticipated_period_start_date?: string | null;
  anticipated_period_end_date?: string | null;
  face_to_face_applicability?: boolean | null;
  review_notes?: string | null;
  conflict_reason?: string | null;
  supersedes_determination_id?: string | null;
};

export type BenefitPeriodDeterminationActionResponse = {
  id: string;
  patient_id: string;
  determination_status: string;
  face_to_face_applicability: boolean | null;
  anticipated_benefit_period_number: number | null;
  impact: BillingImpactSummary;
};

export function createBenefitPeriodDetermination(
  patientId: string,
  payload: CreateBenefitPeriodDeterminationRequest,
  tenantId?: string | null
): Promise<BenefitPeriodDeterminationActionResponse> {
  return api
    .post<BenefitPeriodDeterminationActionResponse>(
      `/billing/eligibility/${patientId}/benefit-period-determinations`,
      { ...payload, tenant_id: tenantId ?? undefined }
    )
    .then((res) => res.data);
}

// =========================================================
// PHASE D -- RN REVIEW ACTIONS
// POST /billing/eligibility/{patient_id}/rn-review-actions
// =========================================================

export type RnReviewAction =
  | "APPROVE_DETERMINATION"
  | "REJECT_DETERMINATION"
  | "REQUEST_CLARIFICATION"
  | "UPDATE_BENEFIT_PERIOD"
  | "MARK_F2F_REQUIRED"
  | "MARK_F2F_NOT_REQUIRED"
  | "PLACE_ADMISSION_HOLD"
  | "RELEASE_ADMISSION_HOLD";

export type RnReviewActionRequest = {
  action: RnReviewAction;
  reason: string;
  anticipated_benefit_period_number?: number | null;
  anticipated_period_start_date?: string | null;
  anticipated_period_end_date?: string | null;
};

export function submitRnReviewAction(
  patientId: string,
  payload: RnReviewActionRequest,
  tenantId?: string | null
): Promise<BenefitPeriodDeterminationActionResponse> {
  return api
    .post<BenefitPeriodDeterminationActionResponse>(
      `/billing/eligibility/${patientId}/rn-review-actions`,
      { ...payload, tenant_id: tenantId ?? undefined }
    )
    .then((res) => res.data);
}

// =========================================================
// PHASE E -- BILLER WORKSPACE ACTIONS
// (reverify-eligibility reuses createEligibilityVerification above;
// create-follow-up / track-resolution reuse upsertReadinessFollowUp /
// resolveReadinessBlocker in api/readinessWorkflow.ts -- not duplicated.)
// =========================================================

export type EligibilityActionAckResponse = {
  ok: boolean;
  event_id: string;
  patient_id: string;
  event_type: string;
};

export type EscalationIssueType = "COVERAGE" | "MSP" | "MA";

export function escalateEligibilityIssue(
  patientId: string,
  payload: { issue_type: EscalationIssueType; notes: string; due_date?: string | null },
  tenantId?: string | null
): Promise<EligibilityActionAckResponse> {
  return api
    .post<EligibilityActionAckResponse>(`/billing/eligibility/${patientId}/escalate`, {
      ...payload,
      tenant_id: tenantId ?? undefined,
    })
    .then((res) => res.data);
}

export function requestEligibilityDocumentReview(
  patientId: string,
  payload: { source_document_id: string; notes?: string | null },
  tenantId?: string | null
): Promise<EligibilityActionAckResponse> {
  return api
    .post<EligibilityActionAckResponse>(
      `/billing/eligibility/${patientId}/document-review-requests`,
      { ...payload, tenant_id: tenantId ?? undefined }
    )
    .then((res) => res.data);
}

export function addEligibilityBillingNote(
  patientId: string,
  note: string,
  tenantId?: string | null
): Promise<EligibilityActionAckResponse> {
  return api
    .post<EligibilityActionAckResponse>(`/billing/eligibility/${patientId}/notes`, {
      note,
      tenant_id: tenantId ?? undefined,
    })
    .then((res) => res.data);
}
