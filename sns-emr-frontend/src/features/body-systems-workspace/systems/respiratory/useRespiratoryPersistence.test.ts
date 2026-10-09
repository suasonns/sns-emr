/**
 * Proof points for `useRespiratoryPersistence`: loading, no-draft, loaded,
 * unsaved, saving, saved, validation-error, auth-error, stale-conflict, and
 * network-error states, plus reload discarding local state.
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  RespiratoryStaleVersionError,
  type RespiratoryAssessmentDTO,
} from "../../../../api/bodySystems";
import { useRespiratoryPersistence } from "./useRespiratoryPersistence";

vi.mock("../../../../api/bodySystems", async () => {
  const actual = await vi.importActual<typeof import("../../../../api/bodySystems")>("../../../../api/bodySystems");
  return {
    ...actual,
    getRespiratoryAssessment: vi.fn(),
    saveRespiratoryDraft: vi.fn(),
  };
});

import { getRespiratoryAssessment, saveRespiratoryDraft } from "../../../../api/bodySystems";

const mockGet = vi.mocked(getRespiratoryAssessment);
const mockSave = vi.mocked(saveRespiratoryDraft);

function makeAssessment(overrides: Partial<RespiratoryAssessmentDTO> = {}): RespiratoryAssessmentDTO {
  return {
    id: "sa-1",
    bodySystemsAssessmentId: "bsa-1",
    assessmentStatus: "draft",
    system: "respiratory",
    situation: null,
    reviewState: "not_reviewed",
    data: {},
    summary: null,
    limitationScope: null,
    limitationReason: null,
    limitationAssessedPortion: null,
    limitationFollowUpRequired: null,
    version: 1,
    updatedAt: null,
    openReviewExceptions: [],
    ...overrides,
  };
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("useRespiratoryPersistence", () => {
  it("1. starts in loading status", () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    expect(result.current.status).toBe("loading");
  });

  it("2. resolves to no_draft_yet for a fresh, never-saved assessment", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));
  });

  it("3. resolves to draft_loaded when a prior save already exists", async () => {
    mockGet.mockResolvedValue(makeAssessment({ situation: "stable_existing", version: 2 }));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("draft_loaded"));
    expect(result.current.assessment?.situation).toBe("stable_existing");
  });

  it("4. markDirty transitions a loaded draft to unsaved", async () => {
    mockGet.mockResolvedValue(makeAssessment({ situation: "stable_existing" }));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("draft_loaded"));

    act(() => result.current.markDirty());
    expect(result.current.status).toBe("unsaved");
  });

  it("5. save transitions through saving to saved and updates the assessment/version", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    mockSave.mockResolvedValue(makeAssessment({ situation: "no_current_concern", version: 2 }));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    await act(async () => {
      await result.current.save({ situation: "no_current_concern", data: {} });
    });

    expect(result.current.status).toBe("saved");
    expect(result.current.assessment?.version).toBe(2);
    expect(mockSave).toHaveBeenCalledWith(
      "patient-1",
      expect.objectContaining({ situation: "no_current_concern", expectedVersion: 1 }),
    );
  });

  it("6. a stale-version save sets status to stale_conflict without discarding the caller's input", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    mockSave.mockRejectedValue(new RespiratoryStaleVersionError());
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    await act(async () => {
      await expect(result.current.save({ data: { dyspnea: "mild" } })).rejects.toThrow();
    });

    expect(result.current.status).toBe("stale_conflict");
    expect(result.current.errorMessage).toContain("updated elsewhere");
  });

  it("7. a 422 save response sets status to validation_error", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    mockSave.mockRejectedValue({ response: { status: 422 } });
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    await act(async () => {
      await expect(result.current.save({ data: {} })).rejects.toBeTruthy();
    });

    expect(result.current.status).toBe("validation_error");
  });

  it("8. a 401 save response sets status to auth_error", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    mockSave.mockRejectedValue({ response: { status: 401 } });
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    await act(async () => {
      await expect(result.current.save({ data: {} })).rejects.toBeTruthy();
    });

    expect(result.current.status).toBe("auth_error");
  });

  it("9. a response-less (network) save failure sets status to network_error", async () => {
    mockGet.mockResolvedValue(makeAssessment());
    mockSave.mockRejectedValue(new Error("ECONNRESET"));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    await act(async () => {
      await expect(result.current.save({ data: {} })).rejects.toBeTruthy();
    });

    expect(result.current.status).toBe("network_error");
  });

  it("10. a GET failure on initial load sets network_error status", async () => {
    mockGet.mockRejectedValue(new Error("ECONNRESET"));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("network_error"));
  });

  it("11. reload re-fetches and discards the prior in-memory assessment", async () => {
    mockGet.mockResolvedValueOnce(makeAssessment({ version: 1 }));
    const { result } = renderHook(() => useRespiratoryPersistence("patient-1"));
    await waitFor(() => expect(result.current.status).toBe("no_draft_yet"));

    mockGet.mockResolvedValueOnce(makeAssessment({ situation: "new_or_worsening", version: 5 }));
    await act(async () => {
      await result.current.reload();
    });

    expect(result.current.assessment?.version).toBe(5);
    expect(result.current.assessment?.situation).toBe("new_or_worsening");
  });
});
