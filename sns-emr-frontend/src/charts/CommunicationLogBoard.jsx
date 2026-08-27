import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import {
  listPatientCommunicationLog,
  createCommunicationLogEntry,
  acknowledgeCommunicationLogEntry,
  verifyCommunicationLogEntry,
  resolveCommunicationLogEntry,
} from "../api/communicationsLog";

const input = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.white,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};

const EVENT_TYPE_OPTIONS = [
  "Phone Call",
  "Comm Note",
  "On-Call Note",
  "Patient Notification",
  "Check Status",
  "Progress Note",
  "Reminder",
  "Bereavement Note",
  "Vol Note",
];

const FOCUS_AREA_OPTIONS = [
  "ADL",
  "Pain",
  "Neurological/Mental",
  "Family",
  "Environment/Safety",
  "Medication",
  "Equipment/Supplies",
  "Other",
];

const STATUS_COLOR = {
  RECEIVED: COLORS.orange,
  ACKNOWLEDGED: COLORS.teal,
  VERIFIED: COLORS.blue,
  RESOLVED: COLORS.green,
};

const NEXT_ACTION = {
  RECEIVED: { label: "Acknowledge", next: "ACKNOWLEDGED", fn: acknowledgeCommunicationLogEntry },
  ACKNOWLEDGED: { label: "Verify", next: "VERIFIED", fn: verifyCommunicationLogEntry },
  VERIFIED: { label: "Resolve", next: "RESOLVED", fn: resolveCommunicationLogEntry },
};

function fmtDateTime(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function toDatetimeLocalValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function CommLogRow({ entry, onAction, actioning }) {
  const statusColor = STATUS_COLOR[entry.status] || COLORS.dim;
  const nextAction = NEXT_ACTION[entry.status];
  const workflowNotes = entry.details?.workflow_notes || [];

  return (
    <div
      style={{
        border: `1px solid ${COLORS.border}`,
        borderRadius: 10,
        padding: 14,
        marginBottom: 10,
        background: COLORS.card,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 600 }}>{entry.event_type}</div>
          <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 4 }}>
            Event time {fmtDateTime(entry.event_time)} · Logged {fmtDateTime(entry.created_at)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {entry.focus_area && <span style={S.badge(`${COLORS.teal}22`, COLORS.teal)}>{entry.focus_area}</span>}
          <span style={S.badge(`${statusColor}22`, statusColor)}>{entry.status}</span>
        </div>
      </div>

      <div style={{ color: COLORS.white, fontSize: 13, marginTop: 10, whiteSpace: "pre-wrap" }}>
        {entry.summary}
      </div>

      {workflowNotes.length > 0 && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${COLORS.border}` }}>
          {workflowNotes.map((wn, idx) => (
            <div key={idx} style={{ color: COLORS.dim, fontSize: 11, marginBottom: 4 }}>
              {wn.status} · {fmtDateTime(wn.recorded_at)}
              {wn.note ? ` — ${wn.note}` : ""}
            </div>
          ))}
        </div>
      )}

      {nextAction && (
        <div style={{ marginTop: 10 }}>
          <button
            type="button"
            style={S.btnOutline}
            disabled={actioning === entry.id}
            onClick={() => onAction(entry, nextAction)}
          >
            {actioning === entry.id ? "Working…" : nextAction.label}
          </button>
        </div>
      )}
    </div>
  );
}

export default function CommunicationLogBoard({ patientId }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actioning, setActioning] = useState(null);

  const [eventType, setEventType] = useState(EVENT_TYPE_OPTIONS[0]);
  const [focusArea, setFocusArea] = useState("");
  const [eventTime, setEventTime] = useState(() => toDatetimeLocalValue(new Date()));
  const [summary, setSummary] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const data = await listPatientCommunicationLog(patientId);
      setEntries(data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load communication log.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!patientId || !summary.trim()) return;

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      const created = await createCommunicationLogEntry({
        patient_id: patientId,
        event_type: eventType,
        focus_area: focusArea || null,
        event_time: new Date(eventTime).toISOString(),
        summary: summary.trim(),
      });
      setEntries((prev) => [created, ...prev]);
      setSummary("");
      setFocusArea("");
      setEventTime(toDatetimeLocalValue(new Date()));
      setMessage("Communication log entry recorded.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to record this entry.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAction = async (entry, nextAction) => {
    setActioning(entry.id);
    setError("");
    setMessage("");
    try {
      const updated = await nextAction.fn(entry.id);
      setEntries((prev) => prev.map((e) => (e.id === entry.id ? updated : e)));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to update this entry.");
    } finally {
      setActioning(null);
    }
  };

  if (loading) {
    return <div style={{ padding: 20, color: COLORS.dim, fontSize: 13 }}>Loading communication log…</div>;
  }

  return (
    <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
      <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 16px 0" }}>Communication Log</h2>

      <form onSubmit={handleSubmit} style={{ ...S.card, padding: 14, marginBottom: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Type</label>
            <select style={input} value={eventType} onChange={(e) => setEventType(e.target.value)}>
              {EVENT_TYPE_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Focus area</label>
            <select style={input} value={focusArea} onChange={(e) => setFocusArea(e.target.value)}>
              <option value="">—</option>
              {FOCUS_AREA_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Event time</label>
            <input
              type="datetime-local"
              style={input}
              value={eventTime}
              onChange={(e) => setEventTime(e.target.value)}
            />
          </div>
        </div>
        <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Summary</label>
        <textarea
          style={{ ...input, minHeight: 70, resize: "vertical" }}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder="What happened, who was contacted, and any follow-up needed…"
        />
        <div style={{ marginTop: 10 }}>
          <button type="submit" style={S.btn(COLORS.teal)} disabled={submitting || !summary.trim()}>
            {submitting ? "Logging…" : "Log Communication"}
          </button>
        </div>
      </form>

      {error && <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 12 }}>{error}</div>}
      {message && <div style={{ color: COLORS.teal, fontSize: 13, marginBottom: 12 }}>{message}</div>}

      {entries.length === 0 ? (
        <div style={{ color: COLORS.dim, fontSize: 13 }}>No communication log entries yet.</div>
      ) : (
        entries.map((entry) => (
          <CommLogRow key={entry.id} entry={entry} onAction={handleAction} actioning={actioning} />
        ))
      )}
    </div>
  );
}
