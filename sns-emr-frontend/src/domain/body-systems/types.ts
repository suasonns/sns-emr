/**
 * SNS Body Systems — domain types.
 *
 * Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * (sections 4.1-4.4). These types are transcribed verbatim from the approved
 * specification. Do not add fields inferred from Figma sample content, mock
 * dates/counts, or specific patient facts shown in the reference screenshots
 * in that same folder — only the specification (and an approved field
 * inventory, where referenced) defines business rules. See that folder's
 * README for the interpretation rule.
 *
 * This module is intentionally decoupled from the existing production
 * RNICA.jsx / RNICACommandWorkspace.jsx implementation, which uses its own
 * ad hoc, untyped legacy system keys ("skin", "infection") and situation
 * strings. The canonical identifiers above (`integumentary`,
 * `infection_immunological`) are the approved domain model and are never
 * renamed to match the legacy keys. The only sanctioned bridge between the
 * two is the narrow, exhaustive, typed adapter in `legacyRNICAAdapter.ts` —
 * no other module in this folder may reference the legacy keys.
 */

// ---------------------------------------------------------------------------
// 4.1 Core enums
// ---------------------------------------------------------------------------

export const BODY_SYSTEMS = [
  "neurological",
  "respiratory",
  "cardiovascular",
  "nutrition",
  "gastrointestinal",
  "genitourinary",
  "musculoskeletal",
  "integumentary",
  "infection_immunological",
  "endocrine",
] as const;

export type BodySystemCode = (typeof BODY_SYSTEMS)[number];

/**
 * Display labels are intentionally separate from the stable
 * `BodySystemCode` identifiers so presentational copy can never silently
 * redefine (or be confused with) the canonical domain model. See
 * `legacyRNICAAdapter.ts` for the separate, narrow mapping to legacy RNICA
 * runtime identifiers ("skin", "infection") — that adapter is the only
 * place canonical and legacy identifiers may meet.
 */
export const BODY_SYSTEM_LABELS: Record<BodySystemCode, string> = {
  neurological: "Neurological",
  respiratory: "Respiratory",
  cardiovascular: "Cardiovascular",
  nutrition: "Nutrition",
  gastrointestinal: "Gastrointestinal",
  genitourinary: "Genitourinary",
  musculoskeletal: "Musculoskeletal",
  integumentary: "Integumentary",
  infection_immunological: "Infection / Immunological",
  endocrine: "Endocrine",
};

export type VisitMode = "admission_comprehensive" | "routine_rn" | "recertification";

export type AssessmentSituation =
  | "no_current_concern"
  | "stable_existing"
  | "new_or_worsening"
  | "unable_to_assess";

export type SystemReviewState = "not_reviewed" | "in_progress" | "reviewed" | "reviewed_with_exception";

export type EvidenceSourceType =
  | "rn_observation"
  | "patient_report"
  | "caregiver_report"
  | "prior_clinical_record"
  | "external_record"
  | "device_measurement"
  | "ai_extraction";

export type ExceptionType =
  | "unreviewed_system"
  | "required_field_missing"
  | "partial_scope"
  | "unable_to_assess"
  | "source_missing"
  | "date_time_missing"
  | "conflicting_evidence"
  | "nurse_judgment_required"
  | "low_confidence_ai"
  | "follow_up_missing";

// ---------------------------------------------------------------------------
// 4.2 Primary entities
// ---------------------------------------------------------------------------

export interface BodySystemsAssessment {
  id: string;
  patientId: string;
  visitId: string;
  visitMode: VisitMode;
  status: "draft" | "ready_for_review" | "recorded" | "signed";
  startedAt: string;
  recordedAt?: string;
  recordedBy?: string;
  signedAt?: string;
  signedBy?: string;
  version: number;
}

export interface SystemAssessment {
  id: string;
  bodySystemsAssessmentId: string;
  system: BodySystemCode;
  situation?: AssessmentSituation;
  reviewState: SystemReviewState;
  assessedAt?: string;
  assessedBy?: string;
  limitation?: AssessmentLimitation;
  summary?: string;
  version: number;
}

export interface ClinicalFinding {
  id: string;
  systemAssessmentId: string;
  ownerSystem: BodySystemCode;
  findingType: string;
  value: unknown;
  currentState: "present" | "absent" | "unknown" | "not_assessed";
  changeState?: "baseline" | "stable" | "improved" | "worsened" | "new" | "resolved" | "unknown";
  observedAt?: string;
  sourceEvidenceIds: string[];
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
  version: number;
}

export interface Evidence {
  id: string;
  sourceType: EvidenceSourceType;
  sourceRecordId?: string;
  sourceDateTime?: string;
  excerpt?: string;
  enteredBy?: string;
  enteredAt: string;
  status: "current" | "historical" | "proposed" | "rejected";
}

export interface Intervention {
  id: string;
  systemAssessmentId: string;
  description: string;
  performedAt?: string;
  response?: string;
  performedBy?: string;
}

export interface FollowUp {
  id: string;
  systemAssessmentId: string;
  responsibleRole?: string;
  responsibleClinicianId?: string;
  timing?: string;
  contingency?: string;
  status: "needed" | "planned" | "completed" | "not_needed";
}

export interface AssessmentLimitation {
  scope: string[];
  reason: string;
  assessedPortion?: string;
  followUpRequired: boolean;
  responsibleClinicianId?: string;
  timingOrContingency?: string;
}

export interface ReviewException {
  id: string;
  bodySystemsAssessmentId: string;
  system: BodySystemCode;
  type: ExceptionType;
  fieldPath?: string;
  message: string;
  blockingLevel: "informational" | "draft_allowed" | "record_blocking" | "signature_blocking";
  status: "open" | "resolved" | "waived";
  resolvedAt?: string;
  resolvedBy?: string;
  resolutionNote?: string;
}

// ---------------------------------------------------------------------------
// 4.3 Wound entities
// ---------------------------------------------------------------------------

export interface WoundRecord {
  id: string;
  systemAssessmentId: string;
  label: string;
  locationText: string;
  bodyRegionCode?: string;
  bodyDiagramMarker?: BodyDiagramMarker;
  woundType: string;
  stage?: string;
  lengthCm?: number;
  widthCm?: number;
  depthCm?: number;
  undermining?: string;
  tunneling?: string;
  woundBed?: string;
  drainage?: string;
  odor?: string;
  periwound?: string;
  dressing?: string;
  changeFromPrior?: string;
  assessedAt: string;
  assessedBy: string;
  priorWoundRecordId?: string;
  version: number;
}

export interface BodyDiagramMarker {
  view: "anterior" | "posterior" | "left_lateral" | "right_lateral";
  normalizedX: number;
  normalizedY: number;
  label: string;
}

export interface BradenAssessment {
  id: string;
  systemAssessmentId: string;
  sensoryPerception: number;
  moisture: number;
  activity: number;
  mobility: number;
  nutrition: number;
  frictionShear: number;
  total: number;
  assessedAt: string;
  assessedBy: string;
  riskFollowUp?: string;
}

// ---------------------------------------------------------------------------
// 4.4 AI entities
// ---------------------------------------------------------------------------

export interface AIExtractionRun {
  id: string;
  visitId: string;
  sourceEvidenceId: string;
  modelMetadata: Record<string, string>;
  createdAt: string;
  status: "proposed" | "partially_reviewed" | "completed" | "dismissed";
}

export interface AISuggestion {
  id: string;
  extractionRunId: string;
  ownerSystem: BodySystemCode;
  targetFieldPath: string;
  proposedValue: unknown;
  confidence?: "low" | "medium" | "high";
  sourceExcerpt: string;
  disposition: "pending" | "accepted" | "edited" | "rejected";
  reviewedBy?: string;
  reviewedAt?: string;
}
