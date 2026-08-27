import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import {
  createPatientIssue,
  listPatientIssues,
  updatePatientIssue,
} from "../api/patientIssues";
import type { PatientIssueRecord } from "../api/patientIssues";
import { useThemeMode } from "../theme/theme";

type IssuesOutcomesBoardProps = {
  patientId: string;
};

type NewIssueFormState = {
  category: string;
  description: string;
  identified_date: string;
};

type ResolveFormState = {
  outcome_notes: string;
  resolved_date: string;
};

const todayIso = () => new Date().toISOString().slice(0, 10);

const getColors = (mode: string) => (mode === "light" ? {
  bg: "#f3f8f7",
  panel: "#ffffff",
  muted: "#5f7286",
  text: "#18354c",
  accent: "#0d7d7a",
  border: "#d9e6eb",
  surface: "#f8fbfb",
  success: "#2d7b63",
  warning: "#d38a2b",
  danger: "#d64d57",
} : {
  bg: "#0f172a",
  panel: "#111827",
  muted: "#94a3b8",
  text: "#e2e8f0",
  accent: "#10b7a2",
  border: "#334155",
  surface: "#162132",
  success: "#34d399",
  warning: "#f59e0b",
  danger: "#fb7185",
});

const formatDate = (value: string | null | undefined) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
};

const statusTone = (status: PatientIssueRecord["status"]) => {
  if (status === "RESOLVED") return "green";
  if (status === "ONGOING") return "amber";
  return "teal";
};

export default function IssuesOutcomesBoard({ patientId }: IssuesOutcomesBoardProps) {
  const { mode } = useThemeMode();
  const colors = getColors(mode);
  const [issues, setIssues] = useState<PatientIssueRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [resolvingIssueId, setResolvingIssueId] = useState<string | null>(null);
  const [resolveDrafts, setResolveDrafts] = useState<Record<string, ResolveFormState>>({});
  const [form, setForm] = useState<NewIssueFormState>({
    category: "clinical",
    description: "",
    identified_date: todayIso(),
  });

  const boardCard = {
    backgroundColor: colors.panel,
    border: `1px solid ${colors.border}`,
    borderRadius: 8,
    boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
    padding: 14,
  };

  const boardHeader = {
    color: colors.text,
    fontSize: 15,
    fontWeight: 700,
    marginBottom: 8,
    letterSpacing: 0.2,
  };

  const badge = (tone: "teal" | "amber" | "green") => ({
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "5px 10px",
    fontSize: 10.5,
    fontWeight: 700,
    letterSpacing: 0.3,
    textTransform: "uppercase" as const,
    backgroundColor:
      tone === "teal"
        ? mode === "light" ? "#dff8f4" : "#10b7a215"
        : tone === "amber"
          ? mode === "light" ? "#f9edd7" : "#f59e0b15"
          : mode === "light" ? "#dff5ee" : "#05966915",
    color:
      tone === "teal"
        ? colors.accent
        : tone === "amber"
          ? colors.warning
          : colors.success,
  });

  const loadIssues = async () => {
    if (!patientId) {
      setIssues([]);
      setLoading(false);
      setError("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const records = await listPatientIssues(patientId);
      setIssues(records);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "Unable to load issues and outcomes right now.";
      setIssues([]);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadIssues();
  }, [patientId]);

  const counts = useMemo(() => {
    return issues.reduce(
      (accumulator, issue) => {
        accumulator.total += 1;
        if (issue.status === "OPEN") accumulator.open += 1;
        else if (issue.status === "ONGOING") accumulator.ongoing += 1;
        else accumulator.resolved += 1;
        return accumulator;
      },
      { total: 0, open: 0, ongoing: 0, resolved: 0 },
    );
  }, [issues]);

  const handleCreateIssue = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!patientId || !form.description.trim() || !form.category.trim()) return;
    setSaving(true);
    setError("");
    try {
      await createPatientIssue(patientId, {
        category: form.category.trim(),
        description: form.description.trim(),
        identified_date: form.identified_date,
      });
      setForm({ category: "clinical", description: "", identified_date: todayIso() });
      await loadIssues();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save this issue.");
    } finally {
      setSaving(false);
    }
  };

  const beginResolve = (issueId: string) => {
    setResolvingIssueId(issueId);
    setResolveDrafts((current) => ({
      ...current,
      [issueId]: current[issueId] ?? { outcome_notes: "", resolved_date: todayIso() },
    }));
  };

  const handleResolveIssue = async (issueId: string, event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const draft = resolveDrafts[issueId];
    if (!draft || !draft.outcome_notes.trim()) return;
    setSaving(true);
    setError("");
    try {
      await updatePatientIssue(issueId, {
        status: "RESOLVED",
        outcome_notes: draft.outcome_notes.trim(),
        resolved_date: draft.resolved_date,
      });
      setResolvingIssueId(null);
      setResolveDrafts((current) => {
        const next = { ...current };
        delete next[issueId];
        return next;
      });
      await loadIssues();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to resolve this issue.");
    } finally {
      setSaving(false);
    }
  };

  if (!patientId) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: colors.bg, color: colors.text, fontFamily: "'Inter', sans-serif" }}>
        Select a patient to view issues and outcomes.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, backgroundColor: colors.bg, padding: 12, overflowY: "auto", fontFamily: "'Inter', sans-serif" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginBottom: 10 }}>
        {[
          { label: "Total issues", value: counts.total, tone: "teal" as const },
          { label: "Open", value: counts.open, tone: "teal" as const },
          { label: "Ongoing", value: counts.ongoing, tone: "amber" as const },
          { label: "Resolved", value: counts.resolved, tone: "green" as const },
        ].map((metric) => (
          <div key={metric.label} style={{ ...boardCard, padding: 12 }}>
            <div style={{ color: colors.muted, fontSize: 9, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase" }}>{metric.label}</div>
            <div style={{ color: colors.text, fontSize: 22, fontWeight: 700, marginTop: 8 }}>{metric.value}</div>
            <div style={{ marginTop: 10, ...badge(metric.tone), width: "fit-content" }}>{metric.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 360px) minmax(0, 1fr)", gap: 10, alignItems: "start" }}>
        <div style={boardCard}>
          <div style={boardHeader}>Log new issue</div>
          <div style={{ color: colors.muted, fontSize: 12.5, lineHeight: 1.5, marginBottom: 12 }}>
            Track active clinical, psychosocial, spiritual, caregiver, or safety concerns directly in the chart.
          </div>
          <form onSubmit={handleCreateIssue} style={{ display: "grid", gap: 10 }}>
            <label style={{ display: "grid", gap: 5 }}>
              <span style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.7 }}>Category</span>
              <input
                type="text"
                value={form.category}
                onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
                placeholder="clinical"
                style={{ borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.surface, color: colors.text, padding: "10px 12px", fontSize: 13 }}
              />
            </label>
            <label style={{ display: "grid", gap: 5 }}>
              <span style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.7 }}>Issue description</span>
              <textarea
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                rows={5}
                placeholder="Describe the patient issue or barrier that needs follow-up."
                style={{ borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.surface, color: colors.text, padding: "10px 12px", fontSize: 13, resize: "vertical" }}
              />
            </label>
            <label style={{ display: "grid", gap: 5 }}>
              <span style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.7 }}>Identified date</span>
              <input
                type="date"
                value={form.identified_date}
                onChange={(event) => setForm((current) => ({ ...current, identified_date: event.target.value }))}
                style={{ borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.surface, color: colors.text, padding: "10px 12px", fontSize: 13 }}
              />
            </label>
            <button
              type="submit"
              disabled={saving || !form.category.trim() || !form.description.trim()}
              style={{
                border: "none",
                borderRadius: 999,
                padding: "10px 14px",
                backgroundColor: colors.accent,
                color: "#ffffff",
                fontWeight: 700,
                fontSize: 12.5,
                cursor: saving ? "wait" : "pointer",
                opacity: saving || !form.category.trim() || !form.description.trim() ? 0.7 : 1,
              }}
            >
              {saving ? "Saving…" : "Log issue"}
            </button>
          </form>
        </div>

        <div style={boardCard}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", marginBottom: 12, flexWrap: "wrap" }}>
            <div>
              <div style={boardHeader}>Issues & outcomes</div>
              <div style={{ color: colors.muted, fontSize: 12.5, lineHeight: 1.5 }}>
                Real-time problem list for this hospice patient, ordered by identified date.
              </div>
            </div>
            <div style={{ ...badge("teal"), fontSize: 9 }}>{counts.total} item{counts.total === 1 ? "" : "s"}</div>
          </div>

          {error ? <div style={{ color: colors.danger, fontSize: 12.5, marginBottom: 10 }}>{error}</div> : null}
          {loading ? (
            <div style={{ color: colors.muted, fontSize: 13 }}>Loading issues and outcomes…</div>
          ) : issues.length === 0 ? (
            <div style={{ color: colors.muted, fontSize: 13 }}>No issues are on file for this patient yet.</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {issues.map((issue) => {
                const resolveDraft = resolveDrafts[issue.id];
                const isResolving = resolvingIssueId === issue.id;
                return (
                  <div key={issue.id} style={{ border: `1px solid ${colors.border}`, borderRadius: 10, padding: 12, backgroundColor: colors.surface }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
                          <span style={{ ...badge(statusTone(issue.status)) }}>{issue.status}</span>
                          <span style={{ color: colors.muted, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.7 }}>{issue.category}</span>
                        </div>
                        <div style={{ color: colors.text, fontSize: 14, fontWeight: 700, marginBottom: 6 }}>{issue.description}</div>
                        <div style={{ color: colors.muted, fontSize: 12.5 }}>
                          Identified {formatDate(issue.identified_date)}
                          {issue.resolved_date ? ` • Resolved ${formatDate(issue.resolved_date)}` : ""}
                        </div>
                        {issue.outcome_notes ? (
                          <div style={{ color: colors.text, fontSize: 12.5, lineHeight: 1.5, marginTop: 10 }}>
                            <strong>Outcome:</strong> {issue.outcome_notes}
                          </div>
                        ) : null}
                      </div>
                      {issue.status !== "RESOLVED" ? (
                        <button
                          type="button"
                          onClick={() => beginResolve(issue.id)}
                          style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.accent, padding: "9px 12px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}
                        >
                          Mark resolved
                        </button>
                      ) : null}
                    </div>

                    {isResolving && resolveDraft ? (
                      <form onSubmit={(event) => void handleResolveIssue(issue.id, event)} style={{ display: "grid", gap: 10, marginTop: 12, paddingTop: 12, borderTop: `1px solid ${colors.border}` }}>
                        <label style={{ display: "grid", gap: 5 }}>
                          <span style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.7 }}>Outcome notes</span>
                          <textarea
                            value={resolveDraft.outcome_notes}
                            onChange={(event) => setResolveDrafts((current) => {
                              const existing = current[issue.id] ?? { outcome_notes: "", resolved_date: todayIso() };
                              return {
                                ...current,
                                [issue.id]: { ...existing, outcome_notes: event.target.value },
                              };
                            })}
                            rows={4}
                            placeholder="Document what was done and the resulting outcome."
                            style={{ borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "10px 12px", fontSize: 13, resize: "vertical" }}
                          />
                        </label>
                        <label style={{ display: "grid", gap: 5, maxWidth: 220 }}>
                          <span style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.7 }}>Resolved date</span>
                          <input
                            type="date"
                            value={resolveDraft.resolved_date}
                            onChange={(event) => setResolveDrafts((current) => {
                              const existing = current[issue.id] ?? { outcome_notes: "", resolved_date: todayIso() };
                              return {
                                ...current,
                                [issue.id]: { ...existing, resolved_date: event.target.value },
                              };
                            })}
                            style={{ borderRadius: 8, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "10px 12px", fontSize: 13 }}
                          />
                        </label>
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                          <button
                            type="submit"
                            disabled={saving || !resolveDraft.outcome_notes.trim()}
                            style={{ border: "none", borderRadius: 999, padding: "10px 14px", backgroundColor: colors.accent, color: "#ffffff", fontWeight: 700, fontSize: 12.5, cursor: saving ? "wait" : "pointer", opacity: saving || !resolveDraft.outcome_notes.trim() ? 0.7 : 1 }}
                          >
                            {saving ? "Saving…" : "Save resolution"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setResolvingIssueId(null)}
                            style={{ borderRadius: 999, border: `1px solid ${colors.border}`, backgroundColor: colors.panel, color: colors.text, padding: "10px 14px", fontWeight: 600, fontSize: 12.5, cursor: "pointer" }}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
