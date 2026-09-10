import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import VisitRecorderCard from "./VisitRecorderCard";

const mocks = vi.hoisted(() => ({
  fetchPatientRecordings: vi.fn(),
  uploadVisitRecording: vi.fn(),
  fetchRecordingAudioBlobUrl: vi.fn(),
  markRecordingReviewed: vi.fn(),
  saveRecordingTranscript: vi.fn(),
  retryRecordingTranscription: vi.fn(),
}));

vi.mock("../api/visitRecordings", () => ({
  uploadVisitRecording: mocks.uploadVisitRecording,
  fetchPatientRecordings: mocks.fetchPatientRecordings,
  fetchRecordingAudioBlobUrl: mocks.fetchRecordingAudioBlobUrl,
  markRecordingReviewed: mocks.markRecordingReviewed,
  saveRecordingTranscript: mocks.saveRecordingTranscript,
  retryRecordingTranscription: mocks.retryRecordingTranscription,
}));

vi.mock("../api/offlineRecordingQueue", () => ({
  queueRecording: vi.fn(),
  removeQueuedRecording: vi.fn(),
  listQueuedRecordings: vi.fn().mockResolvedValue([]),
  markQueuedAttempt: vi.fn(),
}));

const COMPLETED_RECORDING = {
  id: "rec-1",
  patient_id: "patient-1",
  transcript_status: "COMPLETED",
  transcript_provider: "azure_speech",
  transcript_text: "Patient reports stable pain control, ambulating with assistance.",
  ai_note_draft: {
    narrative: "Patient reports stable pain control and is ambulating with assistance today.",
    symptom_severity: {},
    structured_findings: [],
  },
};

describe("VisitRecorderCard auto-insert narrative", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchPatientRecordings.mockResolvedValue({ recordings: [COMPLETED_RECORDING] });
  });

  it("auto-inserts a completed AI note draft narrative without a manual click", async () => {
    const onInsertNarrative = vi.fn().mockResolvedValue(true);

    render(
      <VisitRecorderCard
        patientId="patient-1"
        assessmentId="assessment-1"
        onInsertNarrative={onInsertNarrative}
        onInsertSymptomSeverity={vi.fn()}
        COLORS={{}}
        styles={{}}
      />
    );

    // Auto-insert requires no click on any "Insert" control -- the effect
    // itself calls onInsertNarrative once history reports a COMPLETED
    // transcript with a ready ai_note_draft.narrative.
    await waitFor(() => {
      expect(onInsertNarrative).toHaveBeenCalledTimes(1);
    });
    expect(onInsertNarrative).toHaveBeenCalledWith(COMPLETED_RECORDING.ai_note_draft.narrative, COMPLETED_RECORDING.id);
  });

  it("does not overwrite an existing narrative (guard preserved) and shows the manual fallback", async () => {
    // onInsertNarrative resolves false exactly like the real
    // handleInsertAiNarrative does when formData.diagnoses.clinicalNarrative
    // already has content -- the guard that must never be bypassed.
    const onInsertNarrative = vi.fn().mockResolvedValue(false);

    render(
      <VisitRecorderCard
        patientId="patient-1"
        assessmentId="assessment-1"
        onInsertNarrative={onInsertNarrative}
        onInsertSymptomSeverity={vi.fn()}
        COLORS={{}}
        styles={{}}
      />
    );

    await waitFor(() => {
      expect(onInsertNarrative).toHaveBeenCalledTimes(1);
    });

    // Expand the card (collapsed by default) to see the draft/fallback UI.
    fireEvent.click(screen.getByText("🎙️ Visit Recording"));

    // Auto-insert was attempted but the guard blocked it (existing text
    // preserved) -- the manual fallback button must still be offered.
    await screen.findByText(/Insert into Clinical Narrative \(blank only\)/i);
  });

  it("only attempts auto-insert once per recording even across repeated history polls", async () => {
    const onInsertNarrative = vi.fn().mockResolvedValue(true);

    const { rerender } = render(
      <VisitRecorderCard
        patientId="patient-1"
        assessmentId="assessment-1"
        onInsertNarrative={onInsertNarrative}
        onInsertSymptomSeverity={vi.fn()}
        COLORS={{}}
        styles={{}}
      />
    );

    await waitFor(() => {
      expect(onInsertNarrative).toHaveBeenCalledTimes(1);
    });

    // Simulate the 4s poll re-fetching the exact same history again.
    rerender(
      <VisitRecorderCard
        patientId="patient-1"
        assessmentId="assessment-1"
        onInsertNarrative={onInsertNarrative}
        onInsertSymptomSeverity={vi.fn()}
        COLORS={{}}
        styles={{}}
      />
    );

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(onInsertNarrative).toHaveBeenCalledTimes(1);
  });
});
