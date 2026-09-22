import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useAssessmentAutosave } from "./useAssessmentAutosave";

// Regression coverage for a real defect: opening an RNICA screen with no
// existing assessmentId (e.g. "Nursing Assessment" with nothing selected
// yet) was silently creating a brand-new blank DRAFT record via the
// background autosave timer, purely because auto-populated defaults
// differed from the empty baseline snapshotted at mount -- with zero
// clinician input. Fixed by requiring an explicit `userEditedRef.current`
// flag (set only by the real field-update path) before the timer is
// allowed to create a new record. Background UPDATEs to an already-real
// assessmentId must remain unaffected by this flag.
describe("useAssessmentAutosave draft-duplication guard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not create a new assessment on the background timer when the clinician has not edited anything", async () => {
    const saveFn = vi.fn().mockResolvedValue({ assessmentId: "new-id" });
    const updateFn = vi.fn().mockResolvedValue(undefined);
    const userEditedRef = { current: false };

    renderHook(() =>
      useAssessmentAutosave({
        formData: { demographics: { firstName: "Auto-populated" } },
        assessmentId: null,
        locked: false,
        saving: false,
        saveFn,
        updateFn,
        patientId: "patient-1",
        intervalMs: 30000,
        userEditedRef,
      })
    );

    await vi.advanceTimersByTimeAsync(30000);
    await vi.advanceTimersByTimeAsync(30000);

    expect(saveFn).not.toHaveBeenCalled();
    expect(updateFn).not.toHaveBeenCalled();
  });

  it("creates the assessment via the background timer once the clinician has actually edited a field", async () => {
    const saveFn = vi.fn().mockResolvedValue({ assessmentId: "new-id" });
    const updateFn = vi.fn().mockResolvedValue(undefined);
    const userEditedRef = { current: true };

    renderHook(() =>
      useAssessmentAutosave({
        formData: { demographics: { firstName: "Typed by RN" } },
        assessmentId: null,
        locked: false,
        saving: false,
        saveFn,
        updateFn,
        patientId: "patient-1",
        intervalMs: 30000,
        userEditedRef,
      })
    );

    await vi.advanceTimersByTimeAsync(30000);

    expect(saveFn).toHaveBeenCalledTimes(1);
  });

  it("still background-updates an already-existing assessment even when userEditedRef is false", async () => {
    const saveFn = vi.fn().mockResolvedValue({ assessmentId: "new-id" });
    const updateFn = vi.fn().mockResolvedValue(undefined);
    const userEditedRef = { current: false };

    renderHook(() =>
      useAssessmentAutosave({
        formData: { demographics: { firstName: "Loaded from server" } },
        assessmentId: "existing-id",
        locked: false,
        saving: false,
        saveFn,
        updateFn,
        patientId: "patient-1",
        intervalMs: 30000,
        userEditedRef,
      })
    );

    await vi.advanceTimersByTimeAsync(30000);

    expect(updateFn).toHaveBeenCalledTimes(1);
    expect(saveFn).not.toHaveBeenCalled();
  });
});
