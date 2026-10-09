import React, { useCallback, useEffect, useState } from "react";
import {
  getMedicareNonCoveredReview,
  updateMedicareNonCoveredReview,
  getElectionAddendumCandidates,
} from "../api/icaAssessments";

// SECTION 12 — Medicare Non-Covered Items Review. Recertification
// Assessment only. The CMS hospice recertification determination of
// whether any previously or newly identified non-covered items, services,
// or drugs exist for the next benefit period. Stored as a section of the
// shared RN ICA form_data JSONB (see app/api/routes/rnica_poc.py) -- this
// is NOT a second assessment/table; it only appears on this one shared
// Comprehensive RN Assessment when Reason For Assessment = Recertification.
const OUTCOMES = [
  { value: "", label: "Select a determination..." },
  { value: "NO_ITEMS_IDENTIFIED", label: "No non-covered items identified" },
  { value: "PRIOR_REVIEWED_ACCURATE", label: "Prior non-covered items reviewed, still accurate" },
  { value: "CHANGED", label: "Prior non-covered items have changed" },
  { value: "NEW_ITEM_IDENTIFIED", label: "New non-covered item identified" },
  { value: "UNABLE_TO_COMPLETE", label: "Unable to complete this review" },
];

export default function MedicareNonCoveredReviewPanel({ assessmentId, locked, COLORS }) {
  const [review, setReview] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [form, setForm] = useState({
    outcome: "",
    explanation: "",
    blockingReason: "",
    followUp: "",
    planOfCareChangeAffectsNonCoveredItems: false,
    electionAddendumRequestId: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let mounted = true;
    if (!assessmentId) {
      setLoading(false);
      return () => {
        mounted = false;
      };
    }
    setLoading(true);
    Promise.all([
      getMedicareNonCoveredReview(assessmentId).catch(() => null),
      getElectionAddendumCandidates(assessmentId).catch(() => null),
    ])
      .then(([reviewResult, candidatesResult]) => {
        if (!mounted) return;
        const existing = reviewResult?.medicareNonCoveredReview || null;
        setReview(existing);
        if (existing) {
          setForm({
            outcome: existing.outcome || "",
            explanation: existing.explanation || "",
            blockingReason: existing.blockingReason || "",
            followUp: existing.followUp || "",
            planOfCareChangeAffectsNonCoveredItems: Boolean(existing.planOfCareChangeAffectsNonCoveredItems),
            electionAddendumRequestId: existing.electionAddendumRequestId || "",
          });
        }
        setCandidates(candidatesResult?.candidates || []);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [assessmentId]);

  const handleSave = useCallback(async () => {
    if (!assessmentId || !form.outcome) return;
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const result = await updateMedicareNonCoveredReview(assessmentId, {
        outcome: form.outcome,
        explanation: form.explanation || undefined,
        blockingReason: form.blockingReason || undefined,
        followUp: form.followUp || undefined,
        planOfCareChangeAffectsNonCoveredItems: form.planOfCareChangeAffectsNonCoveredItems,
        electionAddendumRequestId: form.electionAddendumRequestId || null,
      });
      setReview(result?.medicareNonCoveredReview || null);
      setSaved(true);
    } catch (err) {
      setError(err?.message || "Unable to save Medicare Non-Covered Items Review.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, form]);

  const colors = COLORS || {};
  const cardStyle = {
    border: `1px solid ${colors.border || "#1E293B"}`,
    borderRadius: 10,
    padding: 16,
    marginTop: 12,
    background: colors.white || "#FFFFFF",
  };
  const labelStyle = { fontSize: 12, fontWeight: 700, color: colors.dark || "#0F172A", display: "block", marginBottom: 4 };
  const fieldStyle = { width: "100%", padding: "8px 10px", borderRadius: 6, border: `1px solid ${colors.border || "#1E293B"}`, fontSize: 13, marginBottom: 12 };

  if (!assessmentId) {
    return (
      <div style={cardStyle}>
        <div style={labelStyle}>Medicare Non-Covered Items Review</div>
        <div style={{ fontSize: 12, color: colors.gray || "#64748B" }}>
          Save the assessment once before completing the Medicare Non-Covered Items Review.
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={cardStyle}>
        <div style={labelStyle}>Medicare Non-Covered Items Review</div>
        <div style={{ fontSize: 12, color: colors.gray || "#64748B" }}>Loading...</div>
      </div>
    );
  }

  const isLocked = Boolean(locked);

  return (
    <div style={cardStyle} data-testid="medicare-non-covered-review-panel">
      <div style={labelStyle}>Medicare Non-Covered Items Review</div>
      <div style={{ fontSize: 11, color: colors.gray || "#64748B", marginBottom: 12 }}>
        Required for Recertification: the CMS hospice determination of non-covered items, services, or
        drugs for the upcoming benefit period.
      </div>

      {isLocked && review ? (
        <div style={{ fontSize: 13 }}>
          <div><strong>Determination:</strong> {OUTCOMES.find((o) => o.value === review.outcome)?.label || review.outcome}</div>
          {review.explanation && <div><strong>Explanation:</strong> {review.explanation}</div>}
          {review.blockingReason && <div><strong>Blocking reason:</strong> {review.blockingReason}</div>}
          {review.followUp && <div><strong>Follow-up:</strong> {review.followUp}</div>}
          {review.reviewedAt && <div style={{ color: colors.gray || "#64748B" }}>Reviewed {new Date(review.reviewedAt).toLocaleString()}</div>}
        </div>
      ) : (
        <>
          <label style={labelStyle} htmlFor="medicare-review-outcome">Determination</label>
          <select
            id="medicare-review-outcome"
            style={fieldStyle}
            value={form.outcome}
            disabled={isLocked}
            onChange={(e) => setForm((prev) => ({ ...prev, outcome: e.target.value }))}
          >
            {OUTCOMES.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>

          {(form.outcome === "CHANGED" || form.outcome === "NEW_ITEM_IDENTIFIED") && (
            <>
              <label style={labelStyle} htmlFor="medicare-review-explanation">Explanation (required)</label>
              <textarea
                id="medicare-review-explanation"
                style={{ ...fieldStyle, minHeight: 72 }}
                value={form.explanation}
                disabled={isLocked}
                onChange={(e) => setForm((prev) => ({ ...prev, explanation: e.target.value }))}
              />
            </>
          )}

          {form.outcome === "UNABLE_TO_COMPLETE" && (
            <>
              <label style={labelStyle} htmlFor="medicare-review-blocking-reason">Blocking reason (required)</label>
              <input
                id="medicare-review-blocking-reason"
                style={fieldStyle}
                value={form.blockingReason}
                disabled={isLocked}
                onChange={(e) => setForm((prev) => ({ ...prev, blockingReason: e.target.value }))}
              />
              <label style={labelStyle} htmlFor="medicare-review-follow-up">Follow-up needed (required)</label>
              <input
                id="medicare-review-follow-up"
                style={fieldStyle}
                value={form.followUp}
                disabled={isLocked}
                onChange={(e) => setForm((prev) => ({ ...prev, followUp: e.target.value }))}
              />
            </>
          )}

          <label style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
            <input
              type="checkbox"
              checked={form.planOfCareChangeAffectsNonCoveredItems}
              disabled={isLocked}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, planOfCareChangeAffectsNonCoveredItems: e.target.checked }))
              }
            />
            A plan-of-care change affects the non-covered items list
          </label>

          {form.planOfCareChangeAffectsNonCoveredItems && candidates.length > 0 && (
            <>
              <label style={labelStyle} htmlFor="medicare-review-addendum">
                Link to an existing Election Addendum request (optional — never creates a new one)
              </label>
              <select
                id="medicare-review-addendum"
                style={fieldStyle}
                value={form.electionAddendumRequestId}
                disabled={isLocked}
                onChange={(e) => setForm((prev) => ({ ...prev, electionAddendumRequestId: e.target.value }))}
              >
                <option value="">None</option>
                {candidates.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.triggerType || "Election Addendum"} — {candidate.workflowStatus}
                  </option>
                ))}
              </select>
            </>
          )}

          {error && <div style={{ color: colors.error || "#DC2626", fontSize: 12, marginBottom: 8 }}>{error}</div>}
          {saved && !error && <div style={{ color: colors.teal || "#0D9488", fontSize: 12, marginBottom: 8 }}>Saved.</div>}

          <button
            type="button"
            onClick={handleSave}
            disabled={isLocked || saving || !form.outcome}
            style={{
              fontSize: 12,
              fontWeight: 700,
              padding: "8px 14px",
              borderRadius: 6,
              border: "none",
              background: colors.teal || "#0D9488",
              color: "#FFFFFF",
              cursor: isLocked || saving || !form.outcome ? "not-allowed" : "pointer",
              opacity: isLocked || saving || !form.outcome ? 0.6 : 1,
            }}
          >
            {saving ? "Saving..." : "Save Medicare Review"}
          </button>
        </>
      )}
    </div>
  );
}
