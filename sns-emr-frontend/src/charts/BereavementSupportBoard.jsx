import React, { useCallback, useEffect, useMemo, useState } from "react";
import { COLORS, S } from "../tenant/design";
import {
  fetchBereavementSupportSummary,
  fetchBereavementSupportCalendar,
  listBereavementCommunicationNotes,
  createBereavementCommunicationNote,
} from "../api/bereavementSupport";

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

const RISK_LEVEL_COLOR = {
  LOW: COLORS.green,
  MODERATE: COLORS.orange,
  HIGH: COLORS.red,
};

const CONTACT_TYPE_LABEL = {
  PHONE: "Phone Call",
  VISIT: "Visit",
  LETTER: "Letter/Card",
  EMAIL: "Email",
  OTHER: "Other",
};

const CONTACT_TYPE_OPTIONS = Object.entries(CONTACT_TYPE_LABEL).map(([value, label]) => ({ value, label }));

const PLACE_OF_DEATH_LABEL = {
  HOME: "Home",
  INPATIENT_HOSPICE: "Inpatient Hospice",
  HOSPITAL: "Hospital",
  NURSING_FACILITY: "Nursing Facility",
  OTHER: "Other",
};

function fmtDate(value) {
  if (!value) return "—";
  const d = new Date(`${value}T00:00:00`);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function fmtDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function yn(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "—";
}

function SummaryPanel({ summary, loading }) {
  if (loading) {
    return <div style={{ ...S.card, color: COLORS.muted, fontSize: 13 }}>Loading bereavement support summary...</div>;
  }
  if (!summary) return null;

  const { primary_bereaved: pb, death_facts: df, risk_level, goals, interventions, other_interventions } = summary;
  const riskColor = RISK_LEVEL_COLOR[risk_level] || COLORS.dim;

  return (
    <div style={S.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>
          Primary Bereaved &amp; Death Facts
        </h3>
        {risk_level && (
          <span style={{ ...S.badge(`${riskColor}20`, riskColor) }}>{risk_level} risk</span>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase", marginBottom: 8 }}>
            Primary Bereaved Contact
          </div>
          {pb ? (
            pb.no_family ? (
              <div style={{ color: COLORS.muted, fontSize: 13, fontStyle: "italic" }}>No family/bereaved contact on record.</div>
            ) : (
              <div style={{ fontSize: 13, color: COLORS.textPrimary, display: "grid", gap: 4 }}>
                <div style={{ fontWeight: 600 }}>
                  {[pb.primary_first_name, pb.primary_last_name].filter(Boolean).join(" ") || "Not recorded"}
                </div>
                <div style={{ color: COLORS.muted }}>{pb.primary_relationship_to_patient || "Relationship not recorded"}</div>
                <div style={{ color: COLORS.muted }}>{pb.primary_cell_phone || pb.primary_home_phone || "No phone on file"}</div>
                <div style={{ color: COLORS.muted }}>{pb.primary_email || "No email on file"}</div>
                {(pb.primary_address || pb.primary_city) && (
                  <div style={{ color: COLORS.muted }}>
                    {[pb.primary_address, pb.primary_city, pb.primary_state, pb.primary_zip].filter(Boolean).join(", ")}
                  </div>
                )}
                <div style={{ color: COLORS.muted }}>Primary caregiver: {yn(pb.primary_was_caregiver)}</div>
              </div>
            )
          ) : (
            <div style={{ color: COLORS.muted, fontSize: 13, fontStyle: "italic" }}>
              Not yet recorded — complete a Bereavement POC or Post-Death Assessment first.
            </div>
          )}
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase", marginBottom: 8 }}>
            Death Facts
          </div>
          {df ? (
            <div style={{ fontSize: 13, color: COLORS.textPrimary, display: "grid", gap: 4 }}>
              <div>Date of death: <strong>{fmtDate(df.date_of_death)}</strong></div>
              <div style={{ color: COLORS.muted }}>Place: {PLACE_OF_DEATH_LABEL[df.place_of_death] || "Not recorded"}</div>
              <div style={{ color: COLORS.muted }}>Expected: {yn(df.death_expected)}</div>
              <div style={{ color: COLORS.muted }}>Caregiver present: {yn(df.pcg_present_at_death)}</div>
              <div style={{ color: COLORS.muted }}>Family present: {yn(df.family_present_at_death)}</div>
              {df.funeral_home_name && <div style={{ color: COLORS.muted }}>Funeral home: {df.funeral_home_name}</div>}
            </div>
          ) : (
            <div style={{ color: COLORS.muted, fontSize: 13, fontStyle: "italic" }}>
              Not yet recorded — complete a Post-Death Bereavement Assessment.
            </div>
          )}
        </div>
      </div>

      {(goals?.length > 0 || interventions?.length > 0) && (
        <div style={{ marginTop: 20, paddingTop: 16, borderTop: `1px solid ${COLORS.border}` }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            {goals?.length > 0 && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase", marginBottom: 8 }}>
                  Active Goals
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  {goals.filter((g) => g.selected).map((g) => (
                    <div key={g.key} style={{ fontSize: 13, color: COLORS.textPrimary }}>
                      • {g.label}
                      {g.target_date && <span style={{ color: COLORS.dim }}> (by {fmtDate(g.target_date)})</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {interventions?.length > 0 && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase", marginBottom: 8 }}>
                  Active Interventions
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  {interventions.filter((i) => i.selected).map((i) => (
                    <div key={i.key} style={{ fontSize: 13, color: COLORS.textPrimary }}>• {i.label}</div>
                  ))}
                  {other_interventions && (
                    <div style={{ fontSize: 13, color: COLORS.muted, fontStyle: "italic" }}>{other_interventions}</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function monthMatrix(year, month) {
  // month is 0-indexed. Builds a 6-week grid starting on Sunday.
  const first = new Date(year, month, 1);
  const startWeekday = first.getDay();
  const gridStart = new Date(year, month, 1 - startWeekday);
  const weeks = [];
  let cursor = new Date(gridStart);
  for (let w = 0; w < 6; w += 1) {
    const days = [];
    for (let d = 0; d < 7; d += 1) {
      days.push(new Date(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }
    weeks.push(days);
  }
  return weeks;
}

function toDateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function BereavementCalendar({ events, loading }) {
  const today = useMemo(() => new Date(), []);
  const [cursor, setCursor] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));

  const eventsByDay = useMemo(() => {
    const map = {};
    for (const ev of events || []) {
      if (!ev.due_date) continue;
      (map[ev.due_date] = map[ev.due_date] || []).push(ev);
    }
    return map;
  }, [events]);

  const weeks = useMemo(() => monthMatrix(cursor.getFullYear(), cursor.getMonth()), [cursor]);
  const monthLabel = cursor.toLocaleDateString(undefined, { year: "numeric", month: "long" });

  return (
    <div style={S.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Bereavement Calendar</h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button
            type="button"
            style={S.btnOutline}
            onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}
          >
            ‹ Prev
          </button>
          <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white, minWidth: 140, textAlign: "center" }}>
            {monthLabel}
          </span>
          <button
            type="button"
            style={S.btnOutline}
            onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}
          >
            Next ›
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: COLORS.muted, fontSize: 13 }}>Loading calendar...</div>
      ) : (
        <>
          <div style={{ display: "flex", gap: 16, marginBottom: 10, fontSize: 11 }}>
            {["LOW", "MODERATE", "HIGH"].map((lvl) => (
              <span key={lvl} style={{ display: "flex", alignItems: "center", gap: 4, color: COLORS.muted }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_LEVEL_COLOR[lvl], display: "inline-block" }} />
                {lvl}
              </span>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 1, background: COLORS.border, borderRadius: 8, overflow: "hidden" }}>
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <div key={d} style={{ background: COLORS.card, padding: "6px 8px", fontSize: 10, fontWeight: 700, color: COLORS.dim, textTransform: "uppercase" }}>
                {d}
              </div>
            ))}
            {weeks.map((week, wi) => (
              <React.Fragment key={wi}>
                {week.map((day) => {
                  const key = toDateKey(day);
                  const inMonth = day.getMonth() === cursor.getMonth();
                  const isToday = toDateKey(today) === key;
                  const dayEvents = eventsByDay[key] || [];
                  return (
                    <div
                      key={key}
                      style={{
                        background: COLORS.card,
                        minHeight: 84,
                        padding: 6,
                        opacity: inMonth ? 1 : 0.35,
                        border: isToday ? `1px solid ${COLORS.teal}` : "1px solid transparent",
                      }}
                    >
                      <div style={{ fontSize: 11, color: isToday ? COLORS.teal : COLORS.dim, fontWeight: isToday ? 700 : 400, marginBottom: 4 }}>
                        {day.getDate()}
                      </div>
                      <div style={{ display: "grid", gap: 2 }}>
                        {dayEvents.slice(0, 3).map((ev) => (
                          <div
                            key={ev.item_key + ev.tracker_id}
                            title={`${ev.label} (${ev.status})`}
                            style={{
                              fontSize: 9,
                              padding: "2px 4px",
                              borderRadius: 4,
                              background: `${RISK_LEVEL_COLOR[ev.risk_level] || COLORS.dim}20`,
                              color: RISK_LEVEL_COLOR[ev.risk_level] || COLORS.dim,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              textDecoration: ev.status === "SENT" ? "line-through" : "none",
                            }}
                          >
                            {ev.label}
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div style={{ fontSize: 9, color: COLORS.dim }}>+{dayEvents.length - 3} more</div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function CommunicationLog({ patientId, notes, loading, onCreated }) {
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    contact_date: new Date().toISOString().slice(0, 10),
    contact_type: "PHONE",
    contact_with: "",
    summary: "",
  });

  const submit = useCallback(async () => {
    if (!form.summary.trim()) {
      setError("Summary is required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createBereavementCommunicationNote(patientId, {
        contact_date: form.contact_date,
        contact_type: form.contact_type,
        contact_with: form.contact_with || null,
        summary: form.summary.trim(),
      });
      setForm({ contact_date: new Date().toISOString().slice(0, 10), contact_type: "PHONE", contact_with: "", summary: "" });
      setShowForm(false);
      onCreated();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save communication note.");
    } finally {
      setSaving(false);
    }
  }, [form, patientId, onCreated]);

  return (
    <div style={S.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: 0 }}>Communication Note Log</h3>
        <button type="button" style={S.btn(COLORS.teal)} onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "+ Log Contact"}
        </button>
      </div>

      {showForm && (
        <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
            <div>
              <label style={{ fontSize: 11, color: COLORS.dim, display: "block", marginBottom: 4 }}>Contact Date</label>
              <input
                type="date"
                style={input}
                value={form.contact_date}
                onChange={(e) => setForm((f) => ({ ...f, contact_date: e.target.value }))}
              />
            </div>
            <div>
              <label style={{ fontSize: 11, color: COLORS.dim, display: "block", marginBottom: 4 }}>Contact Type</label>
              <select
                style={input}
                value={form.contact_type}
                onChange={(e) => setForm((f) => ({ ...f, contact_type: e.target.value }))}
              >
                {CONTACT_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, color: COLORS.dim, display: "block", marginBottom: 4 }}>Contact With (optional)</label>
              <input
                type="text"
                style={input}
                placeholder="e.g. Primary bereaved -- Jane Doe"
                value={form.contact_with}
                onChange={(e) => setForm((f) => ({ ...f, contact_with: e.target.value }))}
              />
            </div>
          </div>
          <label style={{ fontSize: 11, color: COLORS.dim, display: "block", marginBottom: 4 }}>Summary</label>
          <textarea
            style={{ ...input, minHeight: 70, resize: "vertical" }}
            value={form.summary}
            onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
            placeholder="What was discussed, family status/coping, follow-up needed..."
          />
          {error && <div style={{ color: COLORS.red, fontSize: 12, marginTop: 8 }}>{error}</div>}
          <div style={{ marginTop: 12 }}>
            <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={submit}>
              {saving ? "Saving..." : "Save Note"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ color: COLORS.muted, fontSize: 13 }}>Loading communication log...</div>
      ) : notes.length === 0 ? (
        <div style={{ color: COLORS.muted, fontSize: 13, fontStyle: "italic" }}>
          No contacts logged yet. Every phone call, visit, letter, or email with the bereaved family should be recorded here.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {notes.map((note) => (
            <div key={note.id} style={{ borderBottom: `1px solid ${COLORS.border}`, paddingBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ ...S.badge("rgba(16,183,162,0.12)", COLORS.teal), fontSize: 10 }}>
                    {CONTACT_TYPE_LABEL[note.contact_type] || note.contact_type}
                  </span>
                  <strong style={{ color: COLORS.white, fontSize: 13 }}>{fmtDate(note.contact_date)}</strong>
                  {note.contact_with && <span style={{ color: COLORS.muted, fontSize: 12 }}>· {note.contact_with}</span>}
                </div>
                <span style={{ color: COLORS.dim, fontSize: 11 }}>Logged {fmtDateTime(note.created_at)}</span>
              </div>
              <div style={{ color: COLORS.textPrimary, fontSize: 13, marginTop: 4 }}>{note.summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function BereavementSupportBoard({ patientId }) {
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [calendarLoading, setCalendarLoading] = useState(true);
  const [notes, setNotes] = useState([]);
  const [notesLoading, setNotesLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const loadAll = useCallback(() => {
    setSummaryLoading(true);
    setCalendarLoading(true);
    setNotesLoading(true);
    setLoadError("");

    fetchBereavementSupportSummary(patientId)
      .then(setSummary)
      .catch((err) => setLoadError(err?.response?.data?.detail || "Failed to load bereavement support summary."))
      .finally(() => setSummaryLoading(false));

    fetchBereavementSupportCalendar(patientId)
      .then((data) => setCalendarEvents(data.events || []))
      .catch(() => {})
      .finally(() => setCalendarLoading(false));

    listBereavementCommunicationNotes(patientId)
      .then(setNotes)
      .catch(() => {})
      .finally(() => setNotesLoading(false));
  }, [patientId]);

  useEffect(() => {
    if (patientId) loadAll();
  }, [patientId, loadAll]);

  const refreshNotes = useCallback(() => {
    setNotesLoading(true);
    listBereavementCommunicationNotes(patientId)
      .then(setNotes)
      .catch(() => {})
      .finally(() => setNotesLoading(false));
  }, [patientId]);

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Post-Death Bereavement Support</h1>
          <p style={S.pageSubtitle}>
            Ongoing 13-month post-death family support: primary bereaved &amp; death facts, active goals, the
            scheduled touchpoint calendar, and a complete communication log -- the automated replacement for
            the paper bereavement binder.
          </p>
        </div>
      </div>

      {loadError && <div style={{ ...S.card, color: COLORS.red }}>{loadError}</div>}

      <SummaryPanel summary={summary} loading={summaryLoading} />
      <BereavementCalendar events={calendarEvents} loading={calendarLoading} />
      <CommunicationLog patientId={patientId} notes={notes} loading={notesLoading} onCreated={refreshNotes} />
    </div>
  );
}
