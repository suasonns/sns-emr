import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  uploadVisitRecording,
  fetchPatientRecordings,
  fetchRecordingAudioBlobUrl,
  markRecordingReviewed,
  saveRecordingTranscript,
  retryRecordingTranscription,
} from "../api/visitRecordings";

// Visit audio capture + staff review panel.
//
// Design intent (per product direction): the RN should not have to
// separately fill out HOPE/SFV-style checklists — those get harvested from
// the RNICA itself, which in turn is populated from a natural conversation
// with the patient/family/facility staff. This card is the capture step for
// that conversation: record it, store it securely, and let staff review the
// recording afterward. Speech-to-text (Azure Speech, per current plan) is a
// separate follow-up wiring — transcript_text/status stay blank until that's
// connected; this panel works standalone before that exists.
function formatDuration(seconds) {
  if (seconds == null) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDateTime(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function VisitRecorderCard({ patientId, assessmentId, assessmentType = "RNICA", COLORS, styles, onInsertSymptomSeverity }) {
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [recording, setRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [playingId, setPlayingId] = useState(null);
  const [playingUrl, setPlayingUrl] = useState("");
  const [transcriptDrafts, setTranscriptDrafts] = useState({}); // recordingId -> in-progress textarea value
  const [transcriptSavingId, setTranscriptSavingId] = useState(null);
  const [retryingId, setRetryingId] = useState(null);
  const [insertedSeverityIds, setInsertedSeverityIds] = useState({}); // recordingId -> inserted symptom keys[]

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const startedAtRef = useRef(null);

  const loadHistory = useCallback(() => {
    if (!patientId) return;
    setHistoryLoading(true);
    fetchPatientRecordings(patientId)
      .then((res) => setHistory(res?.recordings || []))
      .catch((err) => console.error("Failed to load visit recordings:", err))
      .finally(() => setHistoryLoading(false));
  }, [patientId]);

  useEffect(() => {
    if (expanded) loadHistory();
  }, [expanded, loadHistory]);

  // Automatic transcription runs server-side after upload; poll while any
  // recording is still in flight (QUEUED/PROCESSING/RETRYING) so staff see
  // it complete without needing to manually refresh or re-record anything.
  useEffect(() => {
    if (!expanded) return undefined;
    const hasInFlight = history.some((r) => ["QUEUED", "PROCESSING", "RETRYING"].includes(r.transcript_status));
    if (!hasInFlight) return undefined;
    const interval = window.setInterval(loadHistory, 4000);
    return () => window.clearInterval(interval);
  }, [expanded, history, loadHistory]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (playingUrl) URL.revokeObjectURL(playingUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStart = async () => {
    setError("");
    if (!consentConfirmed) {
      setError("Confirm consent was obtained before starting the recording.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone recording isn't supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = handleRecordingStopped;
      recorder.start();
      startedAtRef.current = Date.now();
      setElapsedSeconds(0);
      timerRef.current = window.setInterval(() => {
        setElapsedSeconds(Math.floor((Date.now() - startedAtRef.current) / 1000));
      }, 1000);
      setRecording(true);
    } catch (err) {
      console.error("Failed to start recording:", err);
      setError("Could not access the microphone. Check browser permissions.");
    }
  };

  const handleStop = () => {
    mediaRecorderRef.current?.stop();
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecording(false);
  };

  const handleRecordingStopped = async () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    const durationSeconds = startedAtRef.current ? (Date.now() - startedAtRef.current) / 1000 : elapsedSeconds;
    const blob = new Blob(chunksRef.current, { type: mediaRecorderRef.current?.mimeType || "audio/webm" });
    chunksRef.current = [];

    if (blob.size === 0) {
      setError("Recording was empty — nothing was uploaded.");
      return;
    }

    setUploading(true);
    setError("");
    const clientRecordingId = crypto.randomUUID();
    try {
      await uploadVisitRecording({
        patientId,
        audioBlob: blob,
        consentConfirmed: true,
        assessmentId: assessmentId || null,
        assessmentType,
        durationSeconds,
        mimeType: blob.type,
        clientRecordingId,
      });
      setExpanded(true);
      loadHistory();
    } catch (err) {
      console.error("Failed to upload recording:", err);
      setError(err?.response?.data?.detail || "Failed to upload the recording. It was not saved.");
    } finally {
      setUploading(false);
    }
  };

  const handlePlay = async (recordingId) => {
    if (playingId === recordingId) {
      setPlayingId(null);
      if (playingUrl) URL.revokeObjectURL(playingUrl);
      setPlayingUrl("");
      return;
    }
    try {
      const url = await fetchRecordingAudioBlobUrl(recordingId);
      if (playingUrl) URL.revokeObjectURL(playingUrl);
      setPlayingUrl(url);
      setPlayingId(recordingId);
    } catch (err) {
      console.error("Failed to load recording audio:", err);
      setError("Could not load that recording's audio.");
    }
  };

  const handleMarkReviewed = async (recordingId) => {
    try {
      await markRecordingReviewed(recordingId);
      loadHistory();
    } catch (err) {
      console.error("Failed to mark recording reviewed:", err);
    }
  };

  const handleSaveTranscript = async (recordingId) => {
    const text = (transcriptDrafts[recordingId] || "").trim();
    if (!text) {
      setError("Enter the transcript text before saving.");
      return;
    }
    setTranscriptSavingId(recordingId);
    setError("");
    try {
      await saveRecordingTranscript(recordingId, text);
      setTranscriptDrafts((prev) => {
        const next = { ...prev };
        delete next[recordingId];
        return next;
      });
      loadHistory();
    } catch (err) {
      console.error("Failed to save transcript:", err);
      setError(err?.response?.data?.detail || "Failed to save the transcript.");
    } finally {
      setTranscriptSavingId(null);
    }
  };

  const handleRetryTranscription = async (recordingId) => {
    setRetryingId(recordingId);
    setError("");
    try {
      await retryRecordingTranscription(recordingId);
      loadHistory();
    } catch (err) {
      console.error("Failed to retry transcription:", err);
      setError(err?.response?.data?.detail || "Failed to retry transcription.");
    } finally {
      setRetryingId(null);
    }
  };

  const handleInsertSeverity = async (rec) => {
    if (!onInsertSymptomSeverity || !rec?.ai_note_draft?.symptom_severity) return;
    try {
      const insertedKeys = (await onInsertSymptomSeverity(rec.ai_note_draft.symptom_severity, rec.id)) || [];
      setInsertedSeverityIds((prev) => ({ ...prev, [rec.id]: insertedKeys }));
    } catch (err) {
      console.error("Failed to insert AI symptom severity:", err);
      setError("Failed to insert AI-suggested symptom severity into RNICA.");
    }
  };

  const box = styles?.infoBox || { fontSize: 12, padding: 8, borderRadius: 6, background: COLORS?.bg };

  return (
    <div className="visit-recorder-card" style={{ marginBottom: 16, border: `1px solid ${COLORS?.border || "#ddd"}`, borderRadius: 10, overflow: "hidden" }}>
      <button
        type="button"
        className="visit-recorder-card__header"
        aria-expanded={expanded}
        onClick={() => setExpanded((v) => !v)}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "10px 16px", cursor: "pointer", userSelect: "none",
          background: COLORS?.bg, borderBottom: expanded ? `1px solid ${COLORS?.border}` : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="visit-recorder-card__disclosure" style={{ fontSize: 12, color: COLORS?.gray, width: 14, display: "inline-block" }}>{expanded ? "▾" : "▸"}</span>
          <span className="visit-recorder-card__title" style={{ fontSize: 14, fontWeight: 700 }}>🎙️ Visit Recording</span>
          {recording && <span className="visit-recorder-card__state" style={{ fontSize: 11, fontWeight: 700, color: COLORS?.error || "#dc2626" }}>● Recording {formatDuration(elapsedSeconds)}</span>}
        </div>
        <span className="visit-recorder-card__meta" style={{ fontSize: 11, color: COLORS?.gray }}>
          Capture the conversation for later review — HOPE/SFV are harvested from the RNICA, not re-asked separately.
        </span>
      </button>
      {expanded && (
        <div className="visit-recorder-card__body" style={{ padding: 16 }}>
          {!recording && (
            <label className="visit-recorder-card__consent" style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, marginBottom: 10 }}>
              <input
                type="checkbox"
                checked={consentConfirmed}
                onChange={(e) => setConsentConfirmed(e.target.checked)}
                style={{ marginTop: 2 }}
              />
              <span>I informed the patient/family/facility staff that this visit is being recorded for documentation purposes, and consent was obtained.</span>
            </label>
          )}

          <div className="visit-recorder-card__actions" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {!recording ? (
              <button
                type="button"
                className="visit-recorder-card__start"
                onClick={handleStart}
                disabled={uploading}
                style={{
                  padding: "8px 16px", borderRadius: 6, border: `1px solid ${COLORS?.teal || "#0d9488"}`,
                  background: "transparent", color: COLORS?.teal || "#0d9488", fontWeight: 700, fontSize: 13,
                  cursor: uploading ? "default" : "pointer", opacity: uploading ? 0.6 : 1,
                }}
              >
                {uploading ? "Uploading last recording…" : "● Start Recording"}
              </button>
            ) : (
              <button
                type="button"
                className="visit-recorder-card__stop"
                onClick={handleStop}
                style={{
                  padding: "8px 16px", borderRadius: 6, border: "1px solid #dc2626",
                  background: "#dc2626", color: "#fff", fontWeight: 700, fontSize: 13, cursor: "pointer",
                }}
              >
                ■ Stop Recording ({formatDuration(elapsedSeconds)})
              </button>
            )}
          </div>

          {error && <div className="visit-recorder-card__message" role="alert" aria-live="assertive" aria-atomic="true" style={{ ...box, marginTop: 10, color: COLORS?.error || "#dc2626" }}>{error}</div>}

          <div className="visit-recorder-card__history-title" style={{ marginTop: 16, fontSize: 12, fontWeight: 800, color: COLORS?.gray, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Past Recordings
          </div>
          {historyLoading && <p className="visit-recorder-card__message" style={{ color: COLORS?.gray, fontSize: 13 }}>Loading…</p>}
          {!historyLoading && history.length === 0 && (
            <div className="visit-recorder-card__message" style={box}>No recordings on file for this patient yet.</div>
          )}
          {history.map((rec) => (
            <div key={rec.id} style={{ padding: "8px 0", borderBottom: `1px solid ${COLORS?.border || "#eee"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
                <div className="visit-recorder-card__message" style={{ fontSize: 13 }}>
                  {formatDateTime(rec.recorded_at)} — {formatDuration(rec.duration_seconds)}
                  {rec.assessment_type ? ` (${rec.assessment_type})` : ""}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span className="visit-recorder-card__recording-status" style={{
                    fontSize: 10, fontWeight: 700, padding: "2px 6px", borderRadius: 4,
                    color: STATUS_COLORS[rec.transcript_status]?.fg || COLORS?.gray,
                    background: STATUS_COLORS[rec.transcript_status]?.bg || "transparent",
                    border: `1px solid ${STATUS_COLORS[rec.transcript_status]?.border || COLORS?.border}`,
                  }}>
                    {STATUS_LABELS[rec.transcript_status] || rec.transcript_status}
                  </span>
                  <button type="button" onClick={() => handlePlay(rec.id)} style={{ fontSize: 12, padding: "3px 10px", borderRadius: 5, border: `1px solid ${COLORS?.teal || "#0d9488"}`, background: "transparent", color: COLORS?.teal || "#0d9488", cursor: "pointer" }}>
                    {playingId === rec.id ? "Close" : "▶ Play"}
                  </button>
                  {!rec.reviewed_at && (
                    <button type="button" onClick={() => handleMarkReviewed(rec.id)} style={{ fontSize: 12, padding: "3px 10px", borderRadius: 5, border: `1px solid ${COLORS?.border}`, background: "transparent", color: COLORS?.gray, cursor: "pointer" }}>
                      Mark Reviewed
                    </button>
                  )}
                </div>
              </div>
              {rec.reviewed_at && (
                <div className="visit-recorder-card__reviewed" style={{ fontSize: 11, color: COLORS?.gray, marginTop: 2 }}>Reviewed {formatDateTime(rec.reviewed_at)}</div>
              )}
              {playingId === rec.id && (
                <audio controls autoPlay src={playingUrl} style={{ width: "100%", marginTop: 8 }} />
              )}
              {rec.transcript_text && (
                <div className="visit-recorder-card__message" style={{ ...box, marginTop: 8, whiteSpace: "pre-wrap" }}>{rec.transcript_text}</div>
              )}
              {rec.transcript_status === "FAILED" && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ ...box, color: COLORS?.error || "#dc2626", marginBottom: 6 }}>
                    Automatic transcription failed{rec.transcription_error ? `: ${rec.transcription_error}` : "."}
                    {" "}The recording is safe — retry, or enter the transcript manually below as a fallback.
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRetryTranscription(rec.id)}
                    disabled={retryingId === rec.id}
                    style={{ marginBottom: 8, fontSize: 12, padding: "4px 12px", borderRadius: 5, border: `1px solid ${COLORS?.teal || "#0d9488"}`, background: "transparent", color: COLORS?.teal || "#0d9488", cursor: retryingId === rec.id ? "default" : "pointer", opacity: retryingId === rec.id ? 0.6 : 1 }}
                  >
                    {retryingId === rec.id ? "Retrying…" : "↻ Retry Automatic Transcription"}
                  </button>
                  <textarea
                    className="visit-recorder-card__transcript-input"
                    placeholder="Fallback manual transcript entry (automatic speech-to-text failed for this recording). Saving generates an AI note draft for review."
                    value={transcriptDrafts[rec.id] || ""}
                    onChange={(e) => setTranscriptDrafts((prev) => ({ ...prev, [rec.id]: e.target.value }))}
                    rows={3}
                    style={{ width: "100%", fontSize: 12, padding: 6, borderRadius: 6, border: `1px solid ${COLORS?.border || "#ddd"}`, fontFamily: "inherit" }}
                  />
                  <button
                    type="button"
                    onClick={() => handleSaveTranscript(rec.id)}
                    disabled={transcriptSavingId === rec.id}
                    style={{ marginTop: 6, fontSize: 12, padding: "4px 12px", borderRadius: 5, border: `1px solid ${COLORS?.teal || "#0d9488"}`, background: "transparent", color: COLORS?.teal || "#0d9488", cursor: transcriptSavingId === rec.id ? "default" : "pointer", opacity: transcriptSavingId === rec.id ? 0.6 : 1 }}
                  >
                    {transcriptSavingId === rec.id ? "Saving & generating draft…" : "Save Transcript & Generate AI Draft"}
                  </button>
                </div>
              )}
              {rec.ai_note_draft && (
                <div className="visit-recorder-card__note-draft" style={{ ...box, marginTop: 8, background: COLORS?.bgAlt || "#f8fafc" }}>
                  <div style={{ fontWeight: 700, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.03em", color: COLORS?.gray, marginBottom: 4 }}>
                    AI Note Draft — clinician review required before use
                  </div>
                  {rec.ai_note_draft.narrative && (
                    <div style={{ whiteSpace: "pre-wrap", marginBottom: 6 }}>{rec.ai_note_draft.narrative}</div>
                  )}
                  {rec.ai_note_draft.symptom_severity && Object.keys(rec.ai_note_draft.symptom_severity).length > 0 && (
                    <div style={{ marginTop: 6 }}>
                      <div style={{ fontWeight: 700, marginBottom: 2 }}>Suggested HOPE J2051 Symptom Severity:</div>
                      <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {Object.entries(rec.ai_note_draft.symptom_severity).map(([key, val]) => (
                          <li key={key}>
                            {SYMPTOM_SEVERITY_LABELS[key] || key}: {SEVERITY_WORDS[val] || val}
                            {insertedSeverityIds[rec.id]?.includes(key) && <span style={{ color: COLORS?.teal || "#0d9488", fontWeight: 700 }}> — inserted</span>}
                          </li>
                        ))}
                      </ul>
                      {onInsertSymptomSeverity && (
                        <button
                          type="button"
                          onClick={() => handleInsertSeverity(rec)}
                          style={{ marginTop: 6, fontSize: 12, padding: "4px 12px", borderRadius: 5, border: `1px solid ${COLORS?.teal || "#0d9488"}`, background: "transparent", color: COLORS?.teal || "#0d9488", cursor: "pointer" }}
                        >
                          Insert Symptom Severities into RNICA (blank fields only)
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const SYMPTOM_SEVERITY_LABELS = {
  pain: "Pain",
  shortnessOfBreath: "Shortness of Breath",
  nausea: "Nausea",
  vomiting: "Vomiting",
  diarrhea: "Diarrhea",
  constipation: "Constipation",
};

const SEVERITY_WORDS = { "0": "None", "1": "Mild", "2": "Moderate", "3": "Severe" };

const STATUS_LABELS = {
  QUEUED: "Queued for transcription",
  PROCESSING: "Transcribing…",
  RETRYING: "Retrying transcription…",
  COMPLETED: "Transcribed",
  FAILED: "Transcription failed",
};

const STATUS_COLORS = {
  COMPLETED: { fg: "#166534", bg: "#f0fdf4", border: "#bbf7d0" },
  PROCESSING: { fg: "#92400e", bg: "#fffbeb", border: "#fde68a" },
  RETRYING: { fg: "#92400e", bg: "#fffbeb", border: "#fde68a" },
  QUEUED: { fg: "#475569", bg: "#f8fafc", border: "#e2e8f0" },
  FAILED: { fg: "#991b1b", bg: "#fef2f2", border: "#fecaca" },
};
