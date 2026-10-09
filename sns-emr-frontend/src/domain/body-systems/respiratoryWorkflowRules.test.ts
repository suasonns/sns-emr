import { describe, expect, it } from "vitest";

import { canRecordReview, canSaveDraft, canSign } from "./exceptionRules";
import {
  buildRespiratoryExceptions,
  getSatisfiedRespiratoryRequirementKeys,
  mapRespiratoryOverviewToSituation,
} from "./respiratoryWorkflowRules";

describe("Body Systems — Respiratory overview -> situation mapping", () => {
  it("maps every controlled respiratoryOverview value to a canonical situation", () => {
    expect(mapRespiratoryOverviewToSituation("No Current Respiratory Concern")).toBe("no_current_concern");
    expect(mapRespiratoryOverviewToSituation("Existing Respiratory Findings Review")).toBe("stable_existing");
    expect(mapRespiratoryOverviewToSituation("New or Worsening Respiratory Findings")).toBe("new_or_worsening");
    expect(mapRespiratoryOverviewToSituation("Unable to Assess")).toBe("unable_to_assess");
  });

  it("throws on an unrecognized overview value rather than defaulting a situation", () => {
    expect(() => mapRespiratoryOverviewToSituation("Something Else")).toThrow();
  });
});

describe("Body Systems — Respiratory situation requirement satisfaction", () => {
  it("no_current_concern is satisfied by the selection alone", () => {
    const satisfied = getSatisfiedRespiratoryRequirementKeys("no_current_concern", {});
    expect(satisfied).toContain("current_review_evidence");
  });

  it("stable_existing requires at least one current finding field or a clinical status change", () => {
    expect(getSatisfiedRespiratoryRequirementKeys("stable_existing", {})).not.toContain("current_confirmation");
    expect(
      getSatisfiedRespiratoryRequirementKeys("stable_existing", { sobSeverity: "Mild" }),
    ).toContain("current_confirmation");
    expect(
      getSatisfiedRespiratoryRequirementKeys("stable_existing", { clinicalStatusChange: "Stable / No Change" }),
    ).toContain("current_confirmation");
  });

  it("new_or_worsening requires both a documented change and a documented intervention/response", () => {
    const noneDocumented = getSatisfiedRespiratoryRequirementKeys("new_or_worsening", {});
    expect(noneDocumented).not.toContain("current_finding_or_change");
    expect(noneDocumented).not.toContain("intervention_or_response");

    const changeOnly = getSatisfiedRespiratoryRequirementKeys("new_or_worsening", {
      clinicalStatusChange: "Declining",
    });
    expect(changeOnly).toContain("current_finding_or_change");
    expect(changeOnly).not.toContain("intervention_or_response");

    const both = getSatisfiedRespiratoryRequirementKeys("new_or_worsening", {
      clinicalStatusChange: "Declining",
      treatmentInitiated: true,
    });
    expect(both).toContain("current_finding_or_change");
    expect(both).toContain("intervention_or_response");

    const declinedTreatmentAlsoSatisfiesIntervention = getSatisfiedRespiratoryRequirementKeys("new_or_worsening", {
      clinicalStatusChange: "New Symptom Since Prior Assessment",
      treatmentDeclined: true,
    });
    expect(declinedTreatmentAlsoSatisfiesIntervention).toContain("intervention_or_response");
  });

  it("unable_to_assess requires a reason, and 'Other' requires the free-text reason too", () => {
    expect(getSatisfiedRespiratoryRequirementKeys("unable_to_assess", {})).not.toContain("reason");
    expect(
      getSatisfiedRespiratoryRequirementKeys("unable_to_assess", {
        respiratoryUnableToAssessReason: "Patient unresponsive",
      }),
    ).toContain("reason");
    expect(
      getSatisfiedRespiratoryRequirementKeys("unable_to_assess", { respiratoryUnableToAssessReason: "Other" }),
    ).not.toContain("reason");
    expect(
      getSatisfiedRespiratoryRequirementKeys("unable_to_assess", {
        respiratoryUnableToAssessReason: "Other",
        respiratoryUnableToAssessOther: "Family requested deferral",
      }),
    ).toContain("reason");
  });
});

describe("Body Systems — Respiratory exceptions and blocking policy", () => {
  const assessmentId = "assessment-1";

  it("new_or_worsening with nothing documented raises non-blocking + the one verified gap has no verified equivalent (all informational)", () => {
    const exceptions = buildRespiratoryExceptions(assessmentId, "new_or_worsening", {});
    expect(exceptions.length).toBeGreaterThan(0);
    for (const exception of exceptions) {
      expect(exception.blockingLevel).toBe("informational");
    }
    // Draft is always allowed regardless of open exceptions.
    expect(canSaveDraft(exceptions as never)).toBe(true);
  });

  it("unable_to_assess with no reason raises a record_blocking exception that blocks record review but never blocks draft save", () => {
    const exceptions = buildRespiratoryExceptions(assessmentId, "unable_to_assess", {});
    const blockingOnes = exceptions.filter((exception) => exception.blockingLevel === "record_blocking");
    expect(blockingOnes.length).toBe(1);
    expect(blockingOnes[0]?.type).toBe("unable_to_assess");

    expect(canSaveDraft(exceptions as never)).toBe(true);
    expect(canRecordReview(exceptions as never)).toBe(false);
  });

  it("unable_to_assess with a documented reason no longer raises the record_blocking exception", () => {
    const exceptions = buildRespiratoryExceptions(assessmentId, "unable_to_assess", {
      respiratoryUnableToAssessReason: "Patient unresponsive",
    });
    const blockingOnes = exceptions.filter((exception) => exception.blockingLevel === "record_blocking");
    expect(blockingOnes.length).toBe(0);
    expect(canRecordReview(exceptions as never)).toBe(true);
  });

  it("no_current_concern with the selection alone raises no exceptions", () => {
    const exceptions = buildRespiratoryExceptions(assessmentId, "no_current_concern", {});
    expect(exceptions.length).toBe(0);
    expect(canRecordReview(exceptions as never)).toBe(true);
    expect(canSign(exceptions as never)).toBe(true);
  });

  it("every exception references the respiratory system and the provided assessment id", () => {
    const exceptions = buildRespiratoryExceptions(assessmentId, "new_or_worsening", {});
    for (const exception of exceptions) {
      expect(exception.system).toBe("respiratory");
      expect(exception.bodySystemsAssessmentId).toBe(assessmentId);
      expect(exception.status).toBe("open");
    }
  });
});
