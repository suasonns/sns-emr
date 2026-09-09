from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================
# BILLING CYCLE (GET-OR-CREATE)
# =========================================================

class GetOrCreateBillingCycleRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class BillingCycleResponse(BaseModel):
    id: str
    tenant_id: str
    month: int
    year: int
    start_date: str
    end_date: str
    status: str
    created_at: str


# =========================================================
# BILLING GENERATION
# =========================================================

class GeneratePatientBillingRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str
    rate_schedule: Optional[Dict[str, Any]] = Field(default=None)


class GeneratePatientBillingResponse(BaseModel):
    billing_summary_id: str
    patient_id: str
    billing_cycle_id: str

    # ✅ billing state
    status: str
    risk_score: int

    # ✅ metrics
    units: int
    total_minutes: int

    # ✅ core outputs
    loc_summary: Dict[str, Any]
    loc_segments: List[Dict[str, Any]]
    claim_lines: List[Dict[str, Any]]
    revenue_summary: Dict[str, Any]


# =========================================================
# CLAIM EXPORT (JSON STRUCTURE)
# =========================================================

class BuildPatientClaimExportRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str


class BuildPatientClaimExportResponse(BaseModel):
    claim_header: Dict[str, Any]
    patient: Dict[str, Any]
    diagnosis: Dict[str, Any]
    payer: Dict[str, Any]
    provider: Dict[str, Any]
    attending_provider: Dict[str, Any]
    claim_lines: List[Dict[str, Any]]
    export_metadata: Dict[str, Any]


# =========================================================
# BILLING READINESS (chart-completeness gate)
# =========================================================

class PatientBillingReadinessResponse(BaseModel):
    patient_id: str
    period_number: Optional[int]
    ready: bool
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TenantBillingReadinessPatientRow(BaseModel):
    patient_id: str
    mrn: str
    period_number: Optional[int]
    ready: bool
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TenantBillingReadinessReportResponse(BaseModel):
    tenant_id: str
    service_date: str
    total_patients: int
    ready_count: int
    not_ready_count: int
    patients: List[TenantBillingReadinessPatientRow]


# =========================================================
# BATCH BILLING GENERATION (PER AGENCY)
# =========================================================

class BatchGeneratePatientBillingRequest(BaseModel):
    billing_cycle_id: str
    rate_schedule: Optional[Dict[str, Any]] = Field(default=None)
    # Agency tenant to run the batch for. Required for billing-department
    # accounts (the biller's staff), which must explicitly pick an agency
    # from the Biller's Dashboard tenant dropdown; ignored/validated
    # against the caller's own tenant for ordinary agency users.
    tenant_id: Optional[str] = Field(default=None)


class BatchGeneratePatientResult(BaseModel):
    patient_id: str
    mrn: str
    status: str  # GENERATED | SKIPPED_NOT_READY | FAILED
    blockers: List[str] = Field(default_factory=list)
    billing_summary_id: Optional[str] = None
    error: Optional[str] = None


class BatchGeneratePatientBillingResponse(BaseModel):
    billing_cycle_id: str
    total_patients: int
    generated_count: int
    skipped_not_ready_count: int
    failed_count: int
    results: List[BatchGeneratePatientResult]

class BuildPatientClaimEDIRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str

    # ✅ OVERRIDE SYSTEM (CRITICAL)
    override_used: bool = False
    override_reason: Optional[str] = None


class BuildPatientClaimEDIResponse(BaseModel):
    edi_text: str
    claim_control_number: str
    billing_cycle_id: str
    patient_id: str

    # ✅ ALERT SYSTEM (FRONTEND CONSUMES THIS)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # ✅ AUDIT VISIBILITY
    override_used: bool = False


# =========================================================
# SPRINT 2 -- BILLING READINESS OPERATIONAL WORKFLOW
# =========================================================

class ReadinessDashboardCounts(BaseModel):
    READY: int
    AT_RISK: int
    NOT_READY: int
    BLOCKED: int


class ReadinessAttentionPatientRow(BaseModel):
    patient_id: str
    mrn: str
    readiness_status: str
    operational_bucket: str
    blocker_count: int
    warning_count: int


class ReadinessStatusChangeRow(BaseModel):
    patient_id: str
    previous_status: str
    new_status: str
    changed_at: str


class RecentReadinessEvaluationRow(BaseModel):
    patient_id: str
    evaluated_at: str
    readiness_status: str
    triggered_by: str


class ReadinessTrendRow(BaseModel):
    service_date: str
    ready_count: int
    at_risk_count: int
    not_ready_count: int


class TenantReadinessDashboardResponse(BaseModel):
    tenant_id: str
    service_date: str
    counts: ReadinessDashboardCounts
    patients_requiring_attention: List[ReadinessAttentionPatientRow]
    recently_changed_status: List[ReadinessStatusChangeRow]
    recent_evaluations: List[RecentReadinessEvaluationRow]
    readiness_trend: List[ReadinessTrendRow]


class ReadinessQueueRow(BaseModel):
    patient_id: str
    mrn: str
    readiness_status: str
    operational_bucket: str
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    assignment_status: str
    assigned_user_id: Optional[str] = None
    assigned_role: Optional[str] = None
    open_follow_up_count: int
    earliest_due_date: Optional[str] = None


class ReadinessQueueResponse(BaseModel):
    tenant_id: str
    patients: List[ReadinessQueueRow]


class ReadinessVerdictHistoryRow(BaseModel):
    id: str
    evaluated_at: str
    is_ready: bool
    readiness_status: str
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    triggered_by: str


class ReadinessBlockerHistoryRow(BaseModel):
    id: str
    blocker_code: str
    message: str
    status: str
    first_seen_at: str
    last_seen_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None


class ReadinessAuditEventRow(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    actor_user_id: Optional[str] = None
    occurred_at: str
    reason: Optional[str] = None
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Dict[str, Any]
    related_verdict_id: Optional[str] = None


class ReadinessHistoryResponse(BaseModel):
    patient_id: str
    verdicts: List[ReadinessVerdictHistoryRow]
    blocker_history: List[ReadinessBlockerHistoryRow]
    audit_trail: List[ReadinessAuditEventRow]


class UpsertReadinessAssignmentRequest(BaseModel):
    tenant_id: Optional[str] = None
    patient_id: str
    assigned_user_id: Optional[str] = None
    assigned_role: Optional[str] = None
    assignment_status: str = "ASSIGNED"
    related_verdict_id: Optional[str] = None


class ReadinessAssignmentResponse(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    assigned_user_id: Optional[str] = None
    assigned_role: Optional[str] = None
    assigned_date: Optional[str] = None
    assigned_by: Optional[str] = None
    assignment_status: str


class UpsertReadinessFollowUpRequest(BaseModel):
    tenant_id: Optional[str] = None
    patient_id: str
    follow_up_id: Optional[str] = None
    assignment_id: Optional[str] = None
    follow_up_required: bool = True
    status: str = "OPEN"
    due_date: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None
    related_verdict_id: Optional[str] = None


class ReadinessFollowUpResponse(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    assignment_id: Optional[str] = None
    follow_up_required: bool
    status: str
    due_date: Optional[str] = None
    resolved_date: Optional[str] = None
    created_date: str
    notes: Optional[str] = None


class ResolveReadinessBlockerRequest(BaseModel):
    reason: Optional[str] = None


class ReadinessBlockerResponse(BaseModel):
    id: str
    patient_id: str
    blocker_code: str
    message: str
    status: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None