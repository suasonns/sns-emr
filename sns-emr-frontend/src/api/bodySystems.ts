/**
 * SNS Body Systems — Respiratory API client.
 *
 * Thin wrapper over the backend endpoints added in
 * backend/app/api/routes/body_systems.py
 * (GET/PUT /visits/body-systems/patients/{patientId}/respiratory), using
 * the existing shared axios client (`./client`) so auth/refresh/session
 * handling is identical to every other API module in this folder.
 */
import api from "./client";
import type { AssessmentSituation, SystemReviewState } from "../domain/body-systems";

export interface RespiratoryReviewExceptionDTO {
  id: string;
  type: string;
  message: string;
  blockingLevel: "informational" | "draft_allowed" | "record_blocking" | "signature_blocking";
  fieldPath?: string | null;
}

export interface RespiratoryAssessmentDTO {
  id: string;
  bodySystemsAssessmentId: string;
  assessmentStatus: string;
  system: "respiratory";
  situation: AssessmentSituation | null;
  reviewState: SystemReviewState;
  data: Record<string, unknown>;
  summary: string | null;
  // Unable-to-Assess limitation sub-fields (AssessmentLimitation). All six
  // now have a backend column (SystemAssessment.limitation_*) -- the last
  // two (responsibleClinicianId/timingOrContingency) were added in Phase
  // F1 (migration c3b1d9e0f4a7). See respiratoryPersistenceMapping.ts for
  // the authoritative field-by-field classification.
  limitationScope: string[] | null;
  limitationReason: string | null;
  limitationAssessedPortion: string | null;
  limitationFollowUpRequired: boolean | null;
  limitationResponsibleClinicianId: string | null;
  limitationTimingOrContingency: string | null;
  version: number;
  updatedAt: string | null;
  openReviewExceptions: RespiratoryReviewExceptionDTO[];
}

export interface SaveRespiratoryDraftPayload {
  situation?: AssessmentSituation | null;
  data: Record<string, unknown>;
  summary?: string | null;
  reviewState?: SystemReviewState;
  reviewExceptions?: Array<{
    type: string;
    message: string;
    blockingLevel: string;
    fieldPath?: string;
  }>;
  limitationScope?: string[] | null;
  limitationReason?: string | null;
  limitationAssessedPortion?: string | null;
  limitationFollowUpRequired?: boolean | null;
  limitationResponsibleClinicianId?: string | null;
  limitationTimingOrContingency?: string | null;
  expectedVersion?: number;
}

/** A save rejected because another save happened first (HTTP 409). */
export class RespiratoryStaleVersionError extends Error {
  constructor(message = "This assessment was updated elsewhere. Reload before saving again.") {
    super(message);
    this.name = "RespiratoryStaleVersionError";
  }
}

export async function getRespiratoryAssessment(patientId: string): Promise<RespiratoryAssessmentDTO> {
  const response = await api.get(`/visits/body-systems/patients/${patientId}/respiratory`);
  return response.data as RespiratoryAssessmentDTO;
}

export async function saveRespiratoryDraft(
  patientId: string,
  payload: SaveRespiratoryDraftPayload,
): Promise<RespiratoryAssessmentDTO> {
  try {
    const response = await api.put(`/visits/body-systems/patients/${patientId}/respiratory`, payload);
    return response.data as RespiratoryAssessmentDTO;
  } catch (error) {
    if ((error as { response?: { status?: number } })?.response?.status === 409) {
      throw new RespiratoryStaleVersionError();
    }
    throw error;
  }
}
