import React, { useCallback, useEffect, useMemo, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { listBereavementAssessments } from "../api/bereavement";
import { listBereavementPOCs } from "../api/bereavementPoc";
import {
  listBereavementLetterTrackers,
  createBereavementLetterTracker,
  updateBereavementLetterTracker,
  updateBereavementLetterItem,
} from "../api/bereavementLetters";

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

const TRACKER_STATUS_COLOR = {
  ACTIVE: COLORS.teal,
  COMPLETE: COLORS.green,
  DISCONTINUED: COLORS.dim,
};

const ITEM_STATUS_COLOR = {
  SENT: COLORS.teal,
  OVERDUE: COLORS.red,
  DUE_SOON: COLORS.orange,
  UPCOMING: COLORS.dim,
  UNSCHEDULED: COLORS.dim,
  SKIPPED: COLORS.dim,
};

const ITEM_STATUS_LABEL = {
  SENT: "✓ Sent",
  OVERDUE: "⚠ Overdue",
  DUE_SOON: "Due Soon",
  UPCOMING: "Upcoming",
  UNSCHEDULED: "Unscheduled",
  SKIPPED: "Not Included",
};

const CONTACT_TYPE_LABEL = { LETTER: "Letter/Card", PHONE: "Phone Call", VISIT: "Visit" };

const SENT_METHOD_OPTIONS = [
  { value: "MAIL", label: "Mailed" },
  { value: "EMAIL", label: "Emailed" },
  { value: "PHONE", label: "Phone" },
  { value: "IN_PERSON", label: "In Person" },
  { value: "OTHER", label: "Other" },
];

function fmtDate(value) {
  if (!value) return "—";
  return value;
}

function daysLabel(item) {
  if (item.status === "OVERDUE" && item.due_date) {
    const days = Math.max(0, Math.round((new Date() - new Date(item.due_date)) / 86400000));
    return `${days}d overdue`;
  }
  if (item.status === "DUE_SOON" && item.due_date) {
    const days = Math.max(0, Math.round((new Date(item.due_date) - new Date()) / 86400000));
    return days === 0 ? "Due today" : `Due in ${days}d`;
  }
  return null;
}

function ItemRow({ item, onSave, disabled }) {
  const [editing, setEditing] = useState(false);
  const [sentDate, setSentDate] = useState(item.sent_date || new Date().toISOString().slice(0, 10));
  const [sentMethod, setSentMethod] = useState(item.sent_method || (item.contact_type === "PHONE" ? "PHONE" : "MAIL"));
  const [notes, setNotes] = useState(item.notes || "");
  const [saving, setSaving] = useState(false);

  const isSent = item.status === "SENT";
  const badgeColor = ITEM_STATUS_COLOR[item.status] || COLORS.dim;
  const days = daysLabel(item);

  const handleMarkSent = async () => {
    setSaving(true);
    try {
      await onSave(item.key, { sent_date: sentDate, sent_method: sentMethod, notes });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleUnmark = async () => {
    setSaving(true);
    try {
      await onSave(item.key, { clear_sent: true });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleIncluded = async (checked) => {
    setSaving(true);
    try {
      await onSave(item.key, { included: checked });
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
      <td style={{ ...S.tableCell, verticalAlign: "top" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
          {!item.required && (
            <input
              type="checkbox"
              checked={Boolean(item.included)}
              disabled={disabled || saving || isSent}
              onChange={(e) => handleToggleIncluded(e.target.checked)}
              title="Include this optional touchpoint"
              style={{ marginTop: 3 }}
            />
          )}
          <div>
            <div style={{ color: COLORS.white, fontSize: 13, fontWeight: 600 }}>{item.label}</div>
            <div style={{ color: COLORS.dim, fontSize: 11 }}>
              {CONTACT_TYPE_LABEL[item.contact_type] || item.contact_type}
              {!item.required && <span> · Optional</span>}
            </div>
          </div>
        </div>
      </td>
      <td style={{ ...S.tableCell, verticalAlign: "top" }}>{fmtDate(item.due_date)}</td>
      <td style={{ ...S.tableCell, verticalAlign: "top" }}>
        <span style={S.badge(`${badgeColor}22`, badgeColor)}>{ITEM_STATUS_LABEL[item.status] || item.status}</span>
        {days && <div style={{ color: badgeColor, fontSize: 11, marginTop: 4 }}>{days}</div>}
      </td>
      <td style={{ ...S.tableCell, verticalAlign: "top" }}>
        {isSent ? (
          <div>
            <div style={{ color: COLORS.white, fontSize: 12 }}>{fmtDate(item.sent_date)}</div>
            <div style={{ color: COLORS.dim, fontSize: 11 }}>
              {SENT_METHOD_OPTIONS.find((m) => m.value === item.sent_method)?.label || item.sent_method}
            </div>
            {item.notes && <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 2, fontStyle: "italic" }}>{item.notes}</div>}
          </div>
        ) : (
          <span style={{ color: COLORS.dim, fontSize: 12 }}>—</span>
        )}
      </td>
      <td style={{ ...S.tableCell, verticalAlign: "top", minWidth: 190 }}>
        {item.status === "SKIPPED" ? (
          <span style={{ color: COLORS.dim, fontSize: 12 }}>Not tracked</span>
        ) : isSent ? (
          <button type="button" style={S.btnOutline} disabled={disabled || saving} onClick={handleUnmark}>
            Undo
          </button>
        ) : editing ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <input type="date" style={input} value={sentDate} onChange={(e) => setSentDate(e.target.value)} />
            <select style={input} value={sentMethod} onChange={(e) => setSentMethod(e.target.value)}>
              {SENT_METHOD_OPTIONS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
            <input style={input} placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <div style={{ display: "flex", gap: 6 }}>
              <button type="button" style={S.btn(COLORS.teal)} disabled={saving} onClick={handleMarkSent}>
                {saving ? "Saving…" : "Confirm Sent"}
              </button>
              <button type="button" style={S.btnOutline} disabled={saving} onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button type="button" style={S.btn(COLORS.teal)} disabled={disabled || saving} onClick={() => setEditing(true)}>
            Mark Sent
          </button>
        )}
      </td>
    </tr>
  );
}

export default function BereavementLettersBoard({ patientId }) {
  const [trackers, setTrackers] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [pocs, setPOCs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);

  const [view, setView] = useState("list"); // "list" | "detail"
  const [activeTracker, setActiveTracker] = useState(null);
  const [discontinueReason, setDiscontinueReason] = useState("");
  const [showDiscontinue, setShowDiscontinue] = useState(false);

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [trackerData, assessmentData, pocData] = await Promise.all([
        listBereavementLetterTrackers(patientId),
        listBereavementAssessments(patientId),
        listBereavementPOCs(patientId),
      ]);
      setTrackers(trackerData);
      setAssessments(assessmentData);
      setPOCs(pocData);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load bereavement letters trackers.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const mostRecentAssessment = assessments[0] || null;
  const mostRecentPOC = pocs[0] || null;

  const handleCreate = async () => {
    setCreating(true);
    setError("");
    setMessage("");
    try {
      const created = await createBereavementLetterTracker({
        patient_id: patientId,
        bereavement_poc_id: mostRecentPOC?.id || null,
        bereavement_assessment_id: mostRecentAssessment?.id || null,
        date_of_death: mostRecentPOC?.date_of_death || null,
        risk_level: mostRecentPOC?.risk_level || mostRecentAssessment?.risk_level || null,
      });
      setTrackers((prev) => [created, ...prev]);
      setActiveTracker(created);
      setView("detail");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to start a bereavement letters tracker.");
    } finally {
      setCreating(false);
    }
  };

  const openTracker = (tracker) => {
    setActiveTracker(tracker);
    setShowDiscontinue(false);
    setDiscontinueReason("");
    setMessage("");
    setError("");
    setView("detail");
  };

  const refreshActive = (updated) => {
    setActiveTracker(updated);
    setTrackers((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  };

  const handleItemSave = async (itemKey, payload) => {
    try {
      const updated = await updateBereavementLetterItem(activeTracker.id, itemKey, payload);
      refreshActive(updated);
      setMessage("Saved.");
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to update this touchpoint.");
      throw err;
    }
  };

  const handleDiscontinue = async () => {
    try {
      const updated = await updateBereavementLetterTracker(activeTracker.id, {
        status: "DISCONTINUED",
        discontinued_reason: discontinueReason || null,
      });
      refreshActive(updated);
      setShowDiscontinue(false);
      setMessage("Tracker discontinued. It will no longer generate alerts.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to discontinue this tracker.");
    }
  };

  const handleReactivate = async () => {
    try {
      const updated = await updateBereavementLetterTracker(activeTracker.id, { status: "ACTIVE" });
      refreshActive(updated);
      setMessage("Tracker reactivated.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to reactivate this tracker.");
    }
  };

  const sortedItems = useMemo(() => {
    if (!activeTracker) return [];
    return [...activeTracker.items].sort((a, b) => a.month_offset_days - b.month_offset_days);
  }, [activeTracker]);

  if (loading) {
    return <div style={{ padding: 20, color: COLORS.dim, fontSize: 13 }}>Loading bereavement letters tracker…</div>;
  }

  if (view === "list") {
    return (
      <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Bereavement Letters Tracker</h2>
            <p style={{ color: COLORS.dim, fontSize: 13, margin: 0, maxWidth: 640 }}>
              Replaces the paper/binder-based tracking of the CMS-required 13-month post-death contact schedule
              (COP 418.64(d)) with due-date automation and overdue/due-soon alerts, per bereaved family.
            </p>
          </div>
          <button type="button" style={S.btn(COLORS.teal)} disabled={creating} onClick={handleCreate}>
            {creating ? "Starting…" : "+ Start New Tracker"}
          </button>
        </div>

        {error && (
          <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={S.card}>
          {trackers.length === 0 ? (
            <div style={{ color: COLORS.dim, fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No bereavement letters tracker started yet. Start one to auto-generate the 13-month contact schedule
              from the date of death (or the linked Bereavement POC).
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={S.tableHeader}>Date of Death</th>
                  <th style={S.tableHeader}>Risk Level</th>
                  <th style={S.tableHeader}>Status</th>
                  <th style={S.tableHeader}>Progress</th>
                  <th style={S.tableHeader}>Alerts</th>
                  <th style={S.tableHeader} />
                </tr>
              </thead>
              <tbody>
                {trackers.map((t) => (
                  <tr key={t.id}>
                    <td style={S.tableCell}>{fmtDate(t.date_of_death)}</td>
                    <td style={S.tableCell}>
                      {t.risk_level ? (
                        <span style={S.badge(`${RISK_LEVEL_COLOR[t.risk_level]}22`, RISK_LEVEL_COLOR[t.risk_level])}>
                          {t.risk_level}
                        </span>
                      ) : "—"}
                    </td>
                    <td style={S.tableCell}>
                      <span style={S.badge(`${TRACKER_STATUS_COLOR[t.status]}22`, TRACKER_STATUS_COLOR[t.status])}>
                        {t.status}
                      </span>
                    </td>
                    <td style={S.tableCell}>
                      {t.summary.sent_count} / {t.summary.active_items} sent
                    </td>
                    <td style={S.tableCell}>
                      {t.summary.overdue_count > 0 && (
                        <span style={{ ...S.badge(`${COLORS.red}22`, COLORS.red), marginRight: 6 }}>
                          {t.summary.overdue_count} overdue
                        </span>
                      )}
                      {t.summary.due_soon_count > 0 && (
                        <span style={S.badge(`${COLORS.orange}22`, COLORS.orange)}>{t.summary.due_soon_count} due soon</span>
                      )}
                      {t.summary.overdue_count === 0 && t.summary.due_soon_count === 0 && (
                        <span style={{ color: COLORS.dim, fontSize: 12 }}>—</span>
                      )}
                    </td>
                    <td style={S.tableCell}>
                      <button type="button" style={S.btnOutline} onClick={() => openTracker(t)}>
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  }

  const summary = activeTracker.summary;

  return (
    <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <button type="button" style={{ ...S.btnOutline, marginBottom: 10 }} onClick={() => { setView("list"); load(); }}>
            ← Back to Trackers
          </button>
          <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 4px" }}>Bereavement Letters Tracker</h2>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ color: COLORS.dim, fontSize: 13 }}>Date of Death: {fmtDate(activeTracker.date_of_death)}</span>
            {activeTracker.risk_level && (
              <span style={S.badge(`${RISK_LEVEL_COLOR[activeTracker.risk_level]}22`, RISK_LEVEL_COLOR[activeTracker.risk_level])}>
                {activeTracker.risk_level} risk
              </span>
            )}
            <span style={S.badge(`${TRACKER_STATUS_COLOR[activeTracker.status]}22`, TRACKER_STATUS_COLOR[activeTracker.status])}>
              {activeTracker.status}
            </span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {activeTracker.status === "DISCONTINUED" ? (
            <button type="button" style={S.btnOutline} onClick={handleReactivate}>
              Reactivate
            </button>
          ) : (
            <button type="button" style={S.btnOutline} onClick={() => setShowDiscontinue((v) => !v)}>
              Discontinue…
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ background: `${COLORS.red}22`, border: `1px solid ${COLORS.red}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.red, fontSize: 13 }}>
          {error}
        </div>
      )}
      {message && (
        <div style={{ background: `${COLORS.teal}22`, border: `1px solid ${COLORS.teal}66`, borderRadius: 8, padding: "10px 14px", marginBottom: 16, color: COLORS.teal, fontSize: 13 }}>
          {message}
        </div>
      )}

      {showDiscontinue && (
        <div style={{ ...S.card, marginBottom: 16 }}>
          <div style={{ fontSize: 13, color: COLORS.white, fontWeight: 600, marginBottom: 8 }}>
            Discontinue this tracker
          </div>
          <input
            style={input}
            placeholder="Reason (e.g. family requested no further contact)"
            value={discontinueReason}
            onChange={(e) => setDiscontinueReason(e.target.value)}
          />
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button type="button" style={S.btn(COLORS.red)} onClick={handleDiscontinue}>
              Confirm Discontinue
            </button>
            <button type="button" style={S.btnOutline} onClick={() => setShowDiscontinue(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <div style={{ ...S.card, flex: "1 1 140px", padding: 14, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.teal }}>{summary.sent_count}</div>
          <div style={{ fontSize: 11, color: COLORS.dim, textTransform: "uppercase" }}>Sent</div>
        </div>
        <div style={{ ...S.card, flex: "1 1 140px", padding: 14, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.red }}>{summary.overdue_count}</div>
          <div style={{ fontSize: 11, color: COLORS.dim, textTransform: "uppercase" }}>Overdue</div>
        </div>
        <div style={{ ...S.card, flex: "1 1 140px", padding: 14, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.orange }}>{summary.due_soon_count}</div>
          <div style={{ fontSize: 11, color: COLORS.dim, textTransform: "uppercase" }}>Due Soon</div>
        </div>
        <div style={{ ...S.card, flex: "1 1 140px", padding: 14, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.white }}>{summary.upcoming_count}</div>
          <div style={{ fontSize: 11, color: COLORS.dim, textTransform: "uppercase" }}>Upcoming</div>
        </div>
      </div>

      <div style={S.card}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={S.tableHeader}>Touchpoint</th>
              <th style={S.tableHeader}>Due Date</th>
              <th style={S.tableHeader}>Status</th>
              <th style={S.tableHeader}>Completion</th>
              <th style={S.tableHeader}>Action</th>
            </tr>
          </thead>
          <tbody>
            {sortedItems.map((item) => (
              <ItemRow
                key={item.key}
                item={item}
                disabled={activeTracker.status === "DISCONTINUED"}
                onSave={handleItemSave}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
