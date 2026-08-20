import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  uploadVisitRecording,
  fetchPatientRecordings,
  fetchRecordingAudioBlobUrl,
  markRecordingReviewed,
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

export default function VisitRecorderCard({ patientId, assessmentId, assessmentType = "RNICA", COLORS, styles }) {
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
    try {
      await uploadVisitRecording({
        patientId,
        audioBlob: blob,
        consentConfirmed: true,
        assessmentId: assessmentId || null,
        assessmentType,
        durationSeconds,
        mimeType: blob.type,
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

  const box = styles?.infoBox || { fontSize: 12, padding: 8, borderRadius: 6, background: COLORS?.bg };

  return (
    <div style={{ marginBottom: 16, border: `1px solid ${COLORS?.border || "#ddd"}`, borderRadius: 10, overflow: "hidden" }}>
      <div
        onClick={() => setExpanded((v) => !v)}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "10px 16px", cursor: "pointer", userSelect: "none",
          background: COLORS?.bg, borderBottom: expanded ? `1px solid ${COLORS?.border}` : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: COLORS?.gray, width: 14, display: "inline-block" }}>{expanded ? "▾" : "▸"}</span>
          <span style={{ fontSize: 14, fontWeight: 700 }}>🎙️ Visit Recording</span>
          {recording && <span style={{ fontSize: 11, fontWeight: 700, color: COLORS?.error || "#dc2626" }}>● Recording {formatDuration(elapsedSeconds)}</span>}
        </div>
        <span style={{ fontSize: 11, color: COLORS?.gray }}>
          Capture the conversation for later review — HOPE/SFV are harvested from the RNICA, not re-asked separately.
        </span>
      </div>
      {expanded && (
        <div style={{ padding: 16 }}>
          {!recording && (
            <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, marginBottom: 10 }}>
              <input
                type="checkbox"
                checked={consentConfirmed}
                onChange={(e) => setConsentConfirmed(e.target.checked)}
                style={{ marginTop: 2 }}
              />
              <span>I informed the patient/family/facility staff that this visit is being recorded for documentation purposes, and consent was obtained.</span>
            </label>
          )}

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {!recording ? (
              <button
                type="button"
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

          {error && <div style={{ ...box, marginTop: 10, color: COLORS?.error || "#dc2626" }}>{error}</div>}

          <div style={{ marginTop: 16, fontSize: 12, fontWeight: 800, color: COLORS?.gray, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Past Recordings
          </div>
          {historyLoading && <p style={{ color: COLORS?.gray, fontSize: 13 }}>Loading…</p>}
          {!historyLoading && history.length === 0 && (
            <div style={box}>No recordings on file for this patient yet.</div>
          )}
          {history.map((rec) => (
            <div key={rec.id} style={{ padding: "8px 0", borderBottom: `1px solid ${COLORS?.border || "#eee"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
                <div style={{ fontSize: 13 }}>
                  {formatDateTime(rec.recorded_at)} — {formatDuration(rec.duration_seconds)}
                  {rec.assessment_type ? ` (${rec.assessment_type})` : ""}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: "2px 6px", borderRadius: 4,
                    color: rec.transcript_status === "complete" ? "#166534" : COLORS?.gray,
                    background: rec.transcript_status === "complete" ? "#f0fdf4" : "transparent",
                    border: `1px solid ${rec.transcript_status === "complete" ? "#bbf7d0" : COLORS?.border}`,
                  }}>
                    {rec.transcript_status === "not_transcribed" ? "Not yet transcribed" : rec.transcript_status}
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
                <div style={{ fontSize: 11, color: COLORS?.gray, marginTop: 2 }}>Reviewed {formatDateTime(rec.reviewed_at)}</div>
              )}
              {playingId === rec.id && (
                <audio controls autoPlay src={playingUrl} style={{ width: "100%", marginTop: 8 }} />
              )}
              {rec.transcript_text && (
                <div style={{ ...box, marginTop: 8, whiteSpace: "pre-wrap" }}>{rec.transcript_text}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
