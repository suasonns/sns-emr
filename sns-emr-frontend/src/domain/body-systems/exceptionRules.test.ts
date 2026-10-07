import { describe, expect, it } from "vitest";

import type { ReviewException } from "./types";
import {
  aiPatchViolatesAuditFieldRestriction,
  aiSuggestionAcceptanceIsComplete,
  allTenSystemsCreated,
  bradenTotalIsDerivedFromSubscales,
  buildConflictingEvidenceException,
  buildLowConfidenceAIException,
  buildMissingDateTimeException,
  buildMissingFollowUpException,
  buildMissingLimitationException,
  buildMissingSourceException,
  buildNurseJudgmentRequiredException,
  buildPartialScopeException,
  buildRequiredFieldMissingException,
  buildUnreviewedSystemException,
  canRecordReview,
  canSaveDraft,
  canSign,
  findingIsNotSilentlyDefaulted,
  getOpenExceptions,
  limitationHasReason,
  reviewIsBackedByCurrentEvidence,
  woundMarkerAloneSatisfiesWoundRecord,
} from "./exceptionRules";

describe("Body Systems — required invariants", () => {
  it("confirms all ten systems are present", () => {
    const allTen = [
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
    expect(allTenSystemsCreated(allTen.map((system) => ({ system })))).toBe(true);
    expect(allTenSystemsCreated(allTen.slice(0, 9).map((system) => ({ system })))).toBe(false);
  });

  it("requires at least one current-status evidence record to back a review", () => {
    expect(reviewIsBackedByCurrentEvidence([{ status: "historical" }])).toBe(false);
    expect(reviewIsBackedByCurrentEvidence([{ status: "historical" }, { status: "current" }])).toBe(true);
    expect(reviewIsBackedByCurrentEvidence([])).toBe(false);
  });

  it("does not let a present/absent finding be silently defaulted without evidence", () => {
    expect(findingIsNotSilentlyDefaulted({ currentState: "absent", sourceEvidenceIds: [] })).toBe(false);
    expect(findingIsNotSilentlyDefaulted({ currentState: "absent", sourceEvidenceIds: ["ev-1"] })).toBe(true);
    expect(findingIsNotSilentlyDefaulted({ currentState: "not_assessed", sourceEvidenceIds: [] })).toBe(true);
  });

  it("flags an AI patch that tries to set audit/identity fields", () => {
    expect(aiPatchViolatesAuditFieldRestriction({ assessedBy: "ai" })).toBe(true);
    expect(aiPatchViolatesAuditFieldRestriction({ recordedBy: "ai" })).toBe(true);
    expect(aiPatchViolatesAuditFieldRestriction({ signedBy: "ai", signedAt: "now" })).toBe(true);
    expect(aiPatchViolatesAuditFieldRestriction({ summary: "text" })).toBe(false);
  });

  it("requires every field for a complete AI suggestion acceptance record", () => {
    expect(
      aiSuggestionAcceptanceIsComplete({
        source: "ai_extraction",
        reviewer: "nurse-1",
        reviewedAt: "2026-01-01T00:00:00Z",
        originalProposedValue: "x",
        acceptedOrEditedValue: "x",
      }),
    ).toBe(true);
    expect(aiSuggestionAcceptanceIsComplete({ source: "ai_extraction" })).toBe(false);
  });

  it("requires a non-empty reason for a limitation", () => {
    expect(limitationHasReason({ reason: "" })).toBe(false);
    expect(limitationHasReason({ reason: "   " })).toBe(false);
    expect(limitationHasReason({ reason: "Patient declined exam." })).toBe(true);
  });

  it("never lets a wound marker alone satisfy wound documentation", () => {
    expect(
      woundMarkerAloneSatisfiesWoundRecord({
        bodyDiagramMarker: { view: "anterior", normalizedX: 0.5, normalizedY: 0.5, label: "L sacrum" },
        locationText: "",
        woundType: "",
      }),
    ).toBe(false);
    expect(
      woundMarkerAloneSatisfiesWoundRecord({
        bodyDiagramMarker: { view: "anterior", normalizedX: 0.5, normalizedY: 0.5, label: "L sacrum" },
        locationText: "Sacrum",
        woundType: "Pressure injury",
      }),
    ).toBe(true);
  });

  it("requires Braden total to equal the sum of its subscales", () => {
    const base = { sensoryPerception: 3, moisture: 3, activity: 3, mobility: 3, nutrition: 3, frictionShear: 3 };
    expect(bradenTotalIsDerivedFromSubscales({ ...base, total: 18 })).toBe(true);
    expect(bradenTotalIsDerivedFromSubscales({ ...base, total: 20 })).toBe(false);
  });
});

describe("Body Systems — exception generators", () => {
  const assessmentId = "bsa-1";

  it("builds an unreviewed-system exception", () => {
    const exception = buildUnreviewedSystemException(assessmentId, "neurological", "record_blocking");
    expect(exception.type).toBe("unreviewed_system");
    expect(exception.blockingLevel).toBe("record_blocking");
    expect(exception.status).toBe("open");
  });

  it("builds a missing-limitation exception for unable-to-assess without a limitation", () => {
    const exception = buildMissingLimitationException(assessmentId, "respiratory", "record_blocking");
    expect(exception.type).toBe("unable_to_assess");
  });

  it("builds a partial-scope exception with caller-supplied blocking level", () => {
    const exception = buildPartialScopeException(
      assessmentId,
      "musculoskeletal",
      { scope: ["gait"], reason: "Patient fatigued" },
      "signature_blocking",
    );
    expect(exception.type).toBe("partial_scope");
    expect(exception.blockingLevel).toBe("signature_blocking");
    expect(exception.message).toContain("gait");
  });

  it("builds required-field-missing, missing-source, and missing-date-time exceptions", () => {
    expect(buildRequiredFieldMissingException(assessmentId, "cardiovascular", "edema.severity", "record_blocking").type).toBe(
      "required_field_missing",
    );
    expect(buildMissingSourceException(assessmentId, "cardiovascular", "edema.severity", "informational").type).toBe(
      "source_missing",
    );
    expect(buildMissingDateTimeException(assessmentId, "cardiovascular", "edema.severity", "informational").type).toBe(
      "date_time_missing",
    );
  });

  it("builds conflicting-evidence, nurse-judgment-required, low-confidence-AI, and missing-follow-up exceptions", () => {
    expect(buildConflictingEvidenceException(assessmentId, "gastrointestinal", "bowel_status", "record_blocking").type).toBe(
      "conflicting_evidence",
    );
    expect(
      buildNurseJudgmentRequiredException(assessmentId, "endocrine", "Conflicting insulin regimen reports.", "draft_allowed")
        .type,
    ).toBe("nurse_judgment_required");
    expect(buildLowConfidenceAIException(assessmentId, "infection_immunological", "active_infection_status", "signature_blocking").type).toBe(
      "low_confidence_ai",
    );
    expect(buildMissingFollowUpException(assessmentId, "genitourinary", "record_blocking").type).toBe("follow_up_missing");
  });
});

describe("Body Systems — blocking policy", () => {
  const exceptions: ReviewException[] = [
    {
      id: "e1",
      bodySystemsAssessmentId: "bsa-1",
      system: "cardiovascular",
      type: "required_field_missing",
      message: "x",
      blockingLevel: "record_blocking",
      status: "open",
    },
    {
      id: "e2",
      bodySystemsAssessmentId: "bsa-1",
      system: "respiratory",
      type: "low_confidence_ai",
      message: "y",
      blockingLevel: "signature_blocking",
      status: "open",
    },
  ];

  it("always allows draft save regardless of open exceptions", () => {
    expect(canSaveDraft(exceptions)).toBe(true);
    expect(canSaveDraft([])).toBe(true);
  });

  it("blocks recording while a record_blocking exception is open", () => {
    expect(canRecordReview(exceptions)).toBe(false);
    expect(canRecordReview([exceptions[1]])).toBe(true);
  });

  it("blocks signing while a signature_blocking exception is open", () => {
    expect(canSign(exceptions)).toBe(false);
    expect(canSign([exceptions[0]])).toBe(true);
  });

  it("unblocks recording/signing once the relevant exceptions are resolved", () => {
    const resolved = exceptions.map((exception) => ({ ...exception, status: "resolved" as const }));
    expect(canRecordReview(resolved)).toBe(true);
    expect(canSign(resolved)).toBe(true);
    expect(getOpenExceptions(resolved)).toEqual([]);
  });

  it("returns only the still-open exceptions", () => {
    const mixed = [exceptions[0], { ...exceptions[1], status: "resolved" as const }];
    expect(getOpenExceptions(mixed)).toEqual([exceptions[0]]);
  });
});
