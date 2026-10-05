import api from "./client";

/**
 * Interdisciplinary continuity workflow client (MSW / CHAPLAIN / VOLUNTEER
 * ONLY). RN / MD / F2F / Hospice Aide refusal pathways are unrelated and
 * continue to use their existing API modules -- do not route them through
 * this file.
 *
 * Mirrors backend/app/api/discipline_services.py exactly (routes, request
 * bodies, response shapes). All state mutation happens server-side via
 * app.services.discipline_service_engine; this module never computes or
 * assumes the next state.
 */

export type ContinuityDiscipline = "MSW" | "CHAPLAIN" | "VOLUNTEER";

// Must match app.models.enums.DisciplineServiceState exactly -- this is
// the literal string the backend projection and events use. A prior
// version of this union used UI-friendly names (OFFERED, PENDING_DECISION,
// ACCEPTED, REFUSED, REOFFER_SCHEDULED) that do not exist on the backend;
// that caused badge-coloring and state labels to silently misclassify
// almost every real state. Corrected during stabilization review.
export type DisciplineServiceState =
  | "NOT_YET_OFFERED"
  | "OFFER_DUE"
  | "OFFERED_AWAITING_DECISION"
  | "ACCEPTED_AWAITING_ACTIVATION"
  | "ACTIVE"
  | "REFUSED_MONITORING_CONTINUES"
  | "REOFFER_DUE"
  | "REOFFERED_AWAITING_DECISION"
  | "PAUSED"
  | "ENDED"
  | "UNABLE_TO_CONTACT"
  | "DECISION_MAKER_UNAVAILABLE";

export type AdmissionStatus = "CURRENT" | "HISTORICAL" | "LEGACY_ADMISSION_UNASSIGNED";

export type DisciplineServiceRecord = {
  id: string;
  tenant_id: string;
  patient_id: string;
  discipline: ContinuityDiscipline;
  current_state: DisciplineServiceState;
  row_version: number;
  last_decision_maker_name: string | null;
  last_decision_maker_relationship: string | null;
  last_information_source: string | null;
  last_offered_at: string | null;
  last_decision_at: string | null;
  last_refused_at: string | null;
  reoffer_due_at: string | null;
  rn_monitoring_assigned_user_id: string | null;
  idg_review_required: boolean;
  idg_review_id: string | null;
  /** Hospice admission (episode) this service belongs to. Null only for
   * legacy rows created before readmission episode-scoping existed. */
  admission_id: string | null;
  /** Server-computed CURRENT / HISTORICAL / LEGACY_ADMISSION_UNASSIGNED
   * label -- never inferred client-side. */
  admission_status: AdmissionStatus;
  created_at: string;
  updated_at: string;
};

export type DisciplineServiceEventRecord = {
  id: string;
  discipline_service_id: string;
  event_type: string;
  from_state: DisciplineServiceState | null;
  to_state: DisciplineServiceState;
  recorded_by_user_id: string | null;
  recorded_by_role: string | null;
  information_source: string | null;
  decision_maker_name: string | null;
  decision_maker_relationship: string | null;
  reason: string | null;
  effective_at: string;
  related_task_id: string | null;
  related_idg_review_id: string | null;
  related_patient_issue_id: string | null;
  corrects_event_id: string | null;
  created_at: string;
};

export type IdgRecommendationStatus = "PENDING" | "ACCEPTED" | "DECLINED";

export type IdgRecommendationRecord = {
  id: string;
  patient_id: string;
  idg_review_id: string;
  discipline_service_id: string | null;
  discipline: string | null;
  recommendation_type: string;
  recommendation_text: string;
  no_direct_visit: boolean;
  status: IdgRecommendationStatus;
  related_patient_issue_id: string | null;
  /** Hospice admission (episode) this recommendation belongs to. Null
   * only for legacy rows created before readmission episode-scoping
   * existed. Immutable after creation -- never updated to follow a later
   * admission, so a recommendation always stays attributed to the
   * episode it was actually created in. */
  admission_id: string | null;
  /** Server-computed CURRENT / HISTORICAL / LEGACY_ADMISSION_UNASSIGNED
   * label -- never inferred client-side. */
  admission_status: AdmissionStatus;
  /** True Plan-of-Care linkage (reuses the existing POCProblem / POCGoal
   * / POCIntervention tables -- no second POC system). Acceptance of the
   * recommendation is distinct from actually applying a POC change,
   * which continues to happen through the existing Plan of Care screens. */
  requires_poc_change: boolean;
  linked_poc_problem_id: string | null;
  linked_poc_goal_id: string | null;
  linked_poc_intervention_id: string | null;
  created_by_user_id: string | null;
  created_at: string;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
};

type BaseActionPayload = {
  expected_row_version?: number;
  idempotency_key?: string;
};

const BASE = "/discipline-services";

export async function listDisciplineServices(patientId: string): Promise<DisciplineServiceRecord[]> {
  const response = await api.get<DisciplineServiceRecord[]>(`${BASE}/patient/${patientId}`);
  return response.data;
}

export async function getDisciplineService(
  patientId: string,
  discipline: ContinuityDiscipline,
): Promise<DisciplineServiceRecord> {
  const response = await api.get<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}`);
  return response.data;
}

export async function listDisciplineServiceEvents(
  patientId: string,
  discipline: ContinuityDiscipline,
): Promise<DisciplineServiceEventRecord[]> {
  const response = await api.get<DisciplineServiceEventRecord[]>(`${BASE}/patient/${patientId}/${discipline}/events`);
  return response.data;
}

export async function identifyDisciplineService(
  patientId: string,
  discipline: ContinuityDiscipline,
): Promise<DisciplineServiceRecord> {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/identify`, {});
  return response.data;
}

export type OfferPayload = BaseActionPayload & { information_source?: string; reason?: string };
export async function offerDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: OfferPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/offer`, payload);
  return response.data;
}

export async function pendingDecision(patientId: string, discipline: ContinuityDiscipline, payload: BaseActionPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/pending-decision`, payload);
  return response.data;
}

export type AcceptPayload = BaseActionPayload & {
  decision_maker_name: string;
  decision_maker_relationship: string;
  information_source?: string;
};
export async function acceptDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: AcceptPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/accept`, payload);
  return response.data;
}

export type RefusePayload = BaseActionPayload & {
  reason: string;
  decision_maker_name: string;
  decision_maker_relationship: string;
  information_source?: string;
  assign_rn_monitoring_user_id?: string;
  requires_idg_review?: boolean;
  related_patient_issue_id?: string;
  create_reoffer_task?: boolean;
  reoffer_due_date?: string;
};
export async function refuseDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: RefusePayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/refuse`, payload);
  return response.data;
}

export async function activateDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: BaseActionPayload = {}) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/activate`, payload);
  return response.data;
}

export type SimpleActionPayload = BaseActionPayload & { reason?: string };
export async function pauseDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: SimpleActionPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/pause`, payload);
  return response.data;
}

export async function resumeDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: BaseActionPayload = {}) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/resume`, payload);
  return response.data;
}

export async function endDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: SimpleActionPayload & { reason: string }) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/end`, payload);
  return response.data;
}

export type WithdrawRefusalPayload = BaseActionPayload & {
  reason: string;
  decision_maker_name: string;
  decision_maker_relationship: string;
};
export async function withdrawRefusal(patientId: string, discipline: ContinuityDiscipline, payload: WithdrawRefusalPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/withdraw-refusal`, payload);
  return response.data;
}

export type ScheduleReofferPayload = BaseActionPayload & { due_date?: string; trigger_description?: string };
export async function scheduleReoffer(patientId: string, discipline: ContinuityDiscipline, payload: ScheduleReofferPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/schedule-reoffer`, payload);
  return response.data;
}

export type ReofferPayload = BaseActionPayload & { information_source?: string };
export async function reofferDisciplineService(patientId: string, discipline: ContinuityDiscipline, payload: ReofferPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/reoffer`, payload);
  return response.data;
}

export async function recordUnableToContact(patientId: string, discipline: ContinuityDiscipline, payload: SimpleActionPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/unable-to-contact`, payload);
  return response.data;
}

export async function recordDecisionMakerUnavailable(patientId: string, discipline: ContinuityDiscipline, payload: SimpleActionPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/decision-maker-unavailable`, payload);
  return response.data;
}

export type CorrectionPayload = {
  corrects_event_id: string;
  reason: string;
  decision_maker_name?: string;
  decision_maker_relationship?: string;
  information_source?: string;
  expected_row_version?: number;
};
export async function recordCorrection(patientId: string, discipline: ContinuityDiscipline, payload: CorrectionPayload) {
  const response = await api.post<DisciplineServiceEventRecord>(`${BASE}/patient/${patientId}/${discipline}/correction`, payload);
  return response.data;
}

export async function assignRnMonitoring(
  patientId: string,
  discipline: ContinuityDiscipline,
  payload: { rn_user_id: string; reason?: string; expected_row_version?: number },
) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/rn-monitoring/assign`, payload);
  return response.data;
}

export async function endRnMonitoring(
  patientId: string,
  discipline: ContinuityDiscipline,
  payload: { reason: string; expected_row_version?: number },
) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/rn-monitoring/end`, payload);
  return response.data;
}

export type CompleteIdgReviewPayload = {
  idg_review_id: string;
  notes?: string;
  expected_row_version?: number;
};
export async function completeIdgReview(patientId: string, discipline: ContinuityDiscipline, payload: CompleteIdgReviewPayload) {
  const response = await api.post<DisciplineServiceRecord>(`${BASE}/patient/${patientId}/${discipline}/idg-review/complete`, payload);
  return response.data;
}

export type IdgReviewAdmissionStatus = AdmissionStatus;

export type PatientIdgReviewSummary = {
  id: string;
  review_date: string | null;
  is_finalized: boolean;
  summary: string | null;
  /** Computed server-side -- never inferred client-side. Restrict the
   * "attach to current recommendation" picker to CURRENT rows; still
   * show HISTORICAL/LEGACY rows for the read-only timeline. */
  admission_status: IdgReviewAdmissionStatus;
};
export async function listPatientIdgReviews(patientId: string): Promise<PatientIdgReviewSummary[]> {
  const response = await api.get<PatientIdgReviewSummary[]>(`${BASE}/idg-reviews/patient/${patientId}`);
  return response.data;
}

export type CreateIdgRecommendationPayload = {
  patient_id: string;
  idg_review_id: string;
  discipline: string;
  recommendation_type: string;
  recommendation_text: string;
  discipline_service_id?: string;
  related_patient_issue_id?: string;
  /** Optional true Plan-of-Care linkage. Server validates ownership
   * (tenant/patient/current-admission) via the existing PlanOfCare ->
   * PlanOfCareVersion -> POCProblem/Goal/Intervention chain -- this
   * client never performs that validation itself. */
  requires_poc_change?: boolean;
  linked_poc_problem_id?: string;
  linked_poc_goal_id?: string;
  linked_poc_intervention_id?: string;
};
export async function createIdgRecommendation(payload: CreateIdgRecommendationPayload): Promise<IdgRecommendationRecord> {
  const response = await api.post<IdgRecommendationRecord>(`${BASE}/idg-recommendations`, payload);
  return response.data;
}

export async function listIdgRecommendations(patientId: string): Promise<IdgRecommendationRecord[]> {
  const response = await api.get<IdgRecommendationRecord[]>(`${BASE}/idg-recommendations/patient/${patientId}`);
  return response.data;
}

export async function acceptIdgRecommendation(recommendationId: string, reviewNotes?: string): Promise<IdgRecommendationRecord> {
  const response = await api.post<IdgRecommendationRecord>(`${BASE}/idg-recommendations/${recommendationId}/accept`, { review_notes: reviewNotes });
  return response.data;
}

export async function declineIdgRecommendation(recommendationId: string, reviewNotes?: string): Promise<IdgRecommendationRecord> {
  const response = await api.post<IdgRecommendationRecord>(`${BASE}/idg-recommendations/${recommendationId}/decline`, { review_notes: reviewNotes });
  return response.data;
}
