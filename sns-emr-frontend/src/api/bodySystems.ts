/**
 * SNS Body Systems — Respiratory API client.
 *
 * Thin wrapper over the backend endpoints added in
 * backend/app/api/routes/body_systems.py
 * (GET/PUT /visits/body-systems/rnica/{assessmentId}/respiratory), using
 * the existing shared axios client (`./client`) so auth/refresh/session
 * handling is identical to every other API module in this folder.
 *
 * Scoped by RNICA episode (`assessmentId` — the same id the rest of the
 * app already calls `assessmentId` for `/rnica/{assessmentId}` routes),
 * NOT by patient alone: two RNICA episodes for the same patient must
 * never read or write each other's Respiratory record.
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
  rnicaAssessmentId: string;
  assessmentStatus: string;
  system: "respiratory";
  situation: AssessmentSituation | null;
  reviewState: SystemReviewState;
  data: Record<string, unknown>;
  summary: string | null;
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
  expectedVersion?: number;
}

/** A save rejected because another save happened first (HTTP 409). */
export class RespiratoryStaleVersionError extends Error {
  constructor(message = "This assessment was updated elsewhere. Reload before saving again.") {
    super(message);
    this.name = "RespiratoryStaleVersionError";
  }
}

/**
 * A completion attempt rejected by the SERVER's own anti-forgery check
 * (HTTP 422 with a structured `missingRequirements` list) — distinct from
 * a plain validation error, so callers can surface the exact same
 * blocking messages the client-side `getRespiratoryReviewCompletion`
 * would have shown, confirming client and server agreed.
 */
export class RespiratoryCompletionRejectedError extends Error {
  readonly missingRequirements: string[];
  constructor(message: string, missingRequirements: string[]) {
    super(message);
    this.name = "RespiratoryCompletionRejectedError";
    this.missingRequirements = missingRequirements;
  }
}

export async function getRespiratoryAssessment(assessmentId: string): Promise<RespiratoryAssessmentDTO> {
  const response = await api.get(`/visits/body-systems/rnica/${assessmentId}/respiratory`);
  return response.data as RespiratoryAssessmentDTO;
}

export async function saveRespiratoryDraft(
  assessmentId: string,
  payload: SaveRespiratoryDraftPayload,
): Promise<RespiratoryAssessmentDTO> {
  try {
    const response = await api.put(`/visits/body-systems/rnica/${assessmentId}/respiratory`, payload);
    return response.data as RespiratoryAssessmentDTO;
  } catch (error) {
    const status = (error as { response?: { status?: number; data?: unknown } })?.response?.status;
    if (status === 409) {
      throw new RespiratoryStaleVersionError();
    }
    if (status === 422) {
      const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      if (detail && typeof detail === "object" && "missingRequirements" in (detail as Record<string, unknown>)) {
        const detailObj = detail as { message?: string; missingRequirements?: string[] };
        throw new RespiratoryCompletionRejectedError(
          detailObj.message ?? "Cannot complete review: required fields are missing.",
          detailObj.missingRequirements ?? [],
        );
      }
    }
    throw error;
  }
}
