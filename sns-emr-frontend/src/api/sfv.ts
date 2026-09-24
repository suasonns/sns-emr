import axios from "axios";
import api from "./client";

// =========================================================
// Symptom Follow-Up Visit (SFV) completion -- the ONE authoritative
// frontend-callable path (P3-009/P3-017 continuation). Backed by:
//   GET  /visits/sfv-requirements?patientId=...
//   POST /visits/sfv-requirements/{id}/complete
// See backend/app/api/visits.py (list_sfv_requirements,
// complete_sfv_requirement) and docs/tenant-platform/
// SFV_FRONTEND_BACKEND_PARITY_MATRIX.md.
//
// The browser NEVER supplies clinician, tenant, or patient identity for
// the completion decision -- only the persisted completionVisitId. All
// other decision inputs are derived server-side.
// =========================================================

export type SfvRequirementStatus = "OPEN" | "COMPLETED" | "OVERDUE" | "CANCELLED";

export interface SfvRequirementSummary {
  sfvRequirementId: string;
  patientId: string;
  triggerVisitId: string;
  /** SFV ownership remediation (docs/tenant-platform/
   * P0_SFV_OWNERSHIP_REMEDIATION.md): "INITIAL_RN_ICA" | "HUV1" | "HUV2" --
   * the HOPE timepoint that actually triggered this requirement. Paired
   * with triggerVisitId to resolve the ONE requirement owned by a specific
   * HOPE record, instead of a patient-wide "most recent" lookup. */
  triggerSourceType: string;
  triggerDatetime?: string | null;
  completionVisitId?: string | null;
  status: SfvRequirementStatus;
  dueAt?: string | null;
  completedAt?: string | null;
  /** HOPE J2053 -- the completion visit's own ClinicalNote.content
   * .symptom_impact, keyed by the shared 8-symptom vocabulary (see
   * VisitNoteSymptomImpact in api/visitNotes.ts). Null/undefined when
   * the requirement has no completion visit yet, or that visit's note
   * has not documented symptom impact. */
  symptomImpact?: Record<string, string> | null;
  /** True if at least one symptomImpact key has a documented value.
   * Used to enforce the J2053 export-readiness rule: a COMPLETED SFV
   * with no symptom impact documented is not export-ready. */
  symptomImpactDocumented?: boolean;
  /** HOPE J2052C ownership fix (issue #146): the CMS-coded reason SFV
   * was not completed (1=declined, 2=unavailable, 3=unable to contact,
   * 9=none of the above), sourced from THIS requirement row -- never
   * the triggering RN ICA/HUV assessment -- and attributed to whoever
   * actually attempted the SFV. Null unless status === "NOT_COMPLETED". */
  reasonCode?: string | null;
  reasonRecordedAt?: string | null;
  reasonRecordedVisitId?: string | null;
}

export interface SfvCompletionAuthor {
  userId?: string | null;
  displayName?: string | null;
}

export interface SfvCompletionResult {
  sfvRequirementId: string;
  patientId: string;
  triggerVisitId: string;
  completionVisitId?: string | null;
  status: SfvRequirementStatus;
  completedAt?: string | null;
  completedBy?: SfvCompletionAuthor | null;
}

/** Structured backend error code, per the SFV backend API contract.
 * Only the codes the backend actually returns today -- do not add
 * fabricated codes the server cannot produce. */
export type SfvErrorCode =
  | "SFV_REQUIREMENT_NOT_FOUND"
  | "COMPLETION_VISIT_NOT_FOUND"
  | "PATIENT_MISMATCH"
  | "TENANT_MISMATCH"
  | "SAME_VISIT_NOT_ALLOWED"
  | "COMPLETION_BEFORE_TRIGGER"
  | "VISIT_NOT_ELIGIBLE"
  | "CLINICIAN_NOT_AUTHORIZED"
  | "REASON_CODE_INVALID"
  | "INVALID_STATE_FOR_CORRECTION"
  | "UNKNOWN";

export class SfvApiError extends Error {
  code: SfvErrorCode;

  constructor(code: SfvErrorCode, message: string) {
    super(message);
    this.code = code;
    this.name = "SfvApiError";
  }
}

/** User-facing copy for each structured error code (directive section
 * 12). PATIENT_MISMATCH/TENANT_MISMATCH intentionally do not reveal
 * which record exists elsewhere -- same wording as an inaccessible
 * record, matching the backend's own 404-not-403 convention. */
export function describeSfvError(code: SfvErrorCode): string {
  switch (code) {
    case "SAME_VISIT_NOT_ALLOWED":
      return "SFV follow-up must be documented in a separate visit from the triggering RNICA encounter.";
    case "COMPLETION_BEFORE_TRIGGER":
      return "The selected follow-up visit occurred before the symptom trigger.";
    case "PATIENT_MISMATCH":
    case "TENANT_MISMATCH":
    case "COMPLETION_VISIT_NOT_FOUND":
      return "The selected visit cannot be used for this SFV requirement.";
    case "CLINICIAN_NOT_AUTHORIZED":
      return "You are not authorized to complete this follow-up visit.";
    case "VISIT_NOT_ELIGIBLE":
      return "This visit does not meet the requirements to complete the SFV (e.g. must be in-person, RN or LVN discipline).";
    case "SFV_REQUIREMENT_NOT_FOUND":
      return "This SFV requirement could not be found.";
    case "REASON_CODE_INVALID":
      return "Select a valid reason (Declined, Unavailable, Unable to Contact, or None of the Above).";
    case "INVALID_STATE_FOR_CORRECTION":
      return "Only a previously recorded \"not completed\" outcome can be corrected.";
    default:
      return "Unable to complete this SFV requirement.";
  }
}

function toSfvApiError(error: unknown, fallback: string): SfvApiError {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    const structured = detail && typeof detail === "object" ? (detail as { error?: { code?: string; message?: string } }).error : null;
    if (structured?.code) {
      return new SfvApiError(structured.code as SfvErrorCode, structured.message || fallback);
    }
  }
  return new SfvApiError("UNKNOWN", error instanceof Error ? error.message : fallback);
}

export async function listSfvRequirements(patientId: string): Promise<SfvRequirementSummary[]> {
  try {
    const response = await api.get<SfvRequirementSummary[]>("/visits/sfv-requirements", {
      params: { patientId },
    });
    return response.data;
  } catch (error) {
    throw toSfvApiError(error, "Unable to load symptom follow-up status.");
  }
}

/** The ONE mutation path for SFV completion. Never call the backend SFV
 * endpoint directly from another component -- go through this function
 * so error parsing and the request shape stay in one place. */
export async function completeSfvRequirement(
  sfvRequirementId: string,
  completionVisitId: string
): Promise<SfvCompletionResult> {
  try {
    const response = await api.post<SfvCompletionResult>(
      `/visits/sfv-requirements/${sfvRequirementId}/complete`,
      { completionVisitId }
    );
    return response.data;
  } catch (error) {
    throw toSfvApiError(error, "Unable to complete this SFV requirement.");
  }
}

/** HOPE J2052C ownership fix (issue #146). The ONE mutation path for
 * recording the J2052A = No outcome. Attributes the CMS-coded reason to
 * the attempt visit/clinician, never the triggering RN ICA/HUV
 * assessment -- mirrors `completeSfvRequirement`'s contract. */
export interface SfvNotCompletedResult {
  sfvRequirementId: string;
  patientId: string;
  triggerVisitId: string;
  status: SfvRequirementStatus;
  reasonCode?: string | null;
  reasonRecordedAt?: string | null;
  reasonRecordedBy?: SfvCompletionAuthor | null;
}

export async function recordSfvNotCompleted(
  sfvRequirementId: string,
  attemptVisitId: string,
  reasonCode: string
): Promise<SfvNotCompletedResult> {
  try {
    const response = await api.post<SfvNotCompletedResult>(
      `/visits/sfv-requirements/${sfvRequirementId}/not-completed`,
      { attemptVisitId, reasonCode }
    );
    return response.data;
  } catch (error) {
    throw toSfvApiError(error, "Unable to record this SFV outcome.");
  }
}

export interface SfvCorrectReasonResult {
  sfvRequirementId: string;
  priorReasonCode?: string | null;
  newReasonCode: string;
  correctedAt: string;
}

/** HOPE J2052C ownership fix (issue #146). Append-only correction to a
 * previously recorded reason code -- the prior value is preserved
 * server-side (SfvOutcomeCorrection), never overwritten silently. */
export async function correctSfvReasonCode(
  sfvRequirementId: string,
  newReasonCode: string,
  correctionReason: string
): Promise<SfvCorrectReasonResult> {
  try {
    const response = await api.post<SfvCorrectReasonResult>(
      `/visits/sfv-requirements/${sfvRequirementId}/correct-reason`,
      { newReasonCode, correctionReason }
    );
    return response.data;
  } catch (error) {
    throw toSfvApiError(error, "Unable to correct this SFV outcome.");
  }
}
