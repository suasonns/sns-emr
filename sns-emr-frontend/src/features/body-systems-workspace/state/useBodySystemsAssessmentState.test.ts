import { describe, expect, it } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { BODY_SYSTEMS } from "../../../domain/body-systems";
import { useBodySystemsAssessmentState } from "./useBodySystemsAssessmentState";

describe("useBodySystemsAssessmentState", () => {
  it("registers all ten systems in the fixed BODY_SYSTEMS order, never reordered or filtered", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));
    expect(result.current.registryOrder).toEqual(BODY_SYSTEMS);
    expect(Object.keys(result.current.systems)).toHaveLength(10);
    for (const system of BODY_SYSTEMS) {
      expect(result.current.systems[system].reviewState).toBe("not_reviewed");
    }
  });

  it("draft save is always allowed even with open exceptions", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));
    expect(result.current.canSaveDraft).toBe(true);
  });

  it("completing a review with no situation set and no evidence raises a record-blocking exception, not a silent reviewed state", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));

    act(() => {
      result.current.startReview("neurological");
    });
    expect(result.current.systems.neurological.reviewState).toBe("in_progress");

    act(() => {
      result.current.completeReview("neurological");
    });

    expect(result.current.systems.neurological.reviewState).toBe("reviewed_with_exception");
    expect(result.current.canRecordReview).toBe(false);
  });

  it("marking unable_to_assess without a limitation raises the missing-limitation exception and blocks record", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));

    act(() => {
      result.current.startReview("neurological");
      result.current.setSituation("neurological", "unable_to_assess");
    });
    act(() => {
      result.current.completeReview("neurological");
    });

    expect(result.current.systems.neurological.reviewState).toBe("reviewed_with_exception");
    const openExceptions = result.current.exceptions.filter((e) => e.status === "open");
    expect(openExceptions.some((e) => e.type === "unable_to_assess")).toBe(true);
  });

  it("unable_to_assess with a full limitation and no missing requirements resolves to reviewed, never to no_current_concern-style normal", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));

    act(() => {
      result.current.startReview("neurological");
      result.current.setSituation("neurological", "unable_to_assess");
      result.current.setLimitation("neurological", {
        scope: ["orientation"],
        reason: "Patient unresponsive during visit",
        followUpRequired: true,
        responsibleClinicianId: "rn-1",
        timingOrContingency: "Next visit",
      });
      for (const key of [
        "scope",
        "reason",
        "assessed_portion_if_any",
        "follow_up_responsibility",
        "timing_or_contingency",
      ]) {
        result.current.markRequirementSatisfied("neurological", key);
      }
    });

    act(() => {
      result.current.completeReview("neurological");
    });

    expect(result.current.systems.neurological.reviewState).toBe("reviewed");
  });

  it("resolving an exception marks it resolved rather than deleting the audit trail", () => {
    const { result } = renderHook(() => useBodySystemsAssessmentState("assessment-1"));

    act(() => {
      result.current.startReview("respiratory");
      result.current.completeReview("respiratory");
    });
    const exceptionId = result.current.exceptions[0]?.id;
    expect(exceptionId).toBeDefined();

    act(() => {
      result.current.resolveException(exceptionId as string, "Corrected at source");
    });

    const resolved = result.current.exceptions.find((e) => e.id === exceptionId);
    expect(resolved?.status).toBe("resolved");
    expect(resolved?.resolutionNote).toBe("Corrected at source");
  });
});
