import React, { useCallback, useEffect, useState } from "react";
import "./rn-ica/design-system/RnicaTailwind.css";
import {
  getMedicareNonCoveredReview,
  updateMedicareNonCoveredReview,
  getElectionAddendumCandidates,
} from "../api/icaAssessments";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Checkbox } from "./ui/checkbox";
import { Button } from "./ui/button";
import { Alert } from "./ui/alert";
import { Badge } from "./ui/badge";

// SECTION 12 — Medicare Non-Covered Items Review. Recertification
// Assessment only. The CMS hospice recertification determination of
// whether any previously or newly identified non-covered items, services,
// or drugs exist for the next benefit period. Stored as a section of the
// shared RN ICA form_data JSONB (see app/api/routes/rnica_poc.py) -- this
// is NOT a second assessment/table; it only appears on this one shared
// Comprehensive RN Assessment when Reason For Assessment = Recertification.
//
// Refactored onto shadcn/ui primitives (Card/Label/Input/Textarea/Checkbox/
// Button/Alert/Badge, all restyled to the rnica-* theme tokens) per the
// approved RNICA Figma reference and SNS shadcn/ui adoption rule
// (docs/governance/SNS_RNICA_SHADCN_UI_ADOPTION_RULE.md). The "Determination" field
// intentionally stays a native <select> (restyled, not the Radix-based
// ui/select.tsx) -- a short flat option list needs no custom listbox, and
// a native select keeps full built-in keyboard/AT support plus the
// existing test suite's native change-event semantics.
const OUTCOMES = [
  { value: "", label: "Select a determination..." },
  { value: "NO_ITEMS_IDENTIFIED", label: "No non-covered items identified" },
  { value: "PRIOR_REVIEWED_ACCURATE", label: "Prior non-covered items reviewed, still accurate" },
  { value: "CHANGED", label: "Prior non-covered items have changed" },
  { value: "NEW_ITEM_IDENTIFIED", label: "New non-covered item identified" },
  { value: "UNABLE_TO_COMPLETE", label: "Unable to complete this review" },
];

const selectClassName =
  "flex h-9 w-full rounded-md border border-solid border-rnica-border bg-rnica-inputBg px-3 py-1 text-sm text-rnica-text " +
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing " +
  "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-rnica-bgAlt mb-3";

export default function MedicareNonCoveredReviewPanel({ assessmentId, locked }) {
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

  if (!assessmentId) {
    return (
      <Card className="mt-3">
        <CardHeader>
          <CardTitle>Medicare Non-Covered Items Review</CardTitle>
        </CardHeader>
        <CardContent className="pt-0 text-xs text-rnica-muted">
          Save the assessment once before completing the Medicare Non-Covered Items Review.
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="mt-3">
        <CardHeader>
          <CardTitle>Medicare Non-Covered Items Review</CardTitle>
        </CardHeader>
        <CardContent className="pt-0 text-xs text-rnica-muted">Loading...</CardContent>
      </Card>
    );
  }

  const isLocked = Boolean(locked);
  const requiresExplanation = form.outcome === "CHANGED" || form.outcome === "NEW_ITEM_IDENTIFIED";
  const requiresBlockingDetail = form.outcome === "UNABLE_TO_COMPLETE";

  return (
    <Card className="mt-3" data-testid="medicare-non-covered-review-panel">
      <CardHeader>
        <CardTitle>Medicare Non-Covered Items Review</CardTitle>
        {isLocked && <Badge variant="neutral">Locked</Badge>}
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-[11px] text-rnica-muted mb-3">
          Required for Recertification: the CMS hospice determination of non-covered items, services, or
          drugs for the upcoming benefit period.
        </p>

        {isLocked && review ? (
          <div className="text-sm space-y-1">
            <div>
              <strong>Determination:</strong>{" "}
              {OUTCOMES.find((o) => o.value === review.outcome)?.label || review.outcome}
            </div>
            {review.explanation && (
              <div>
                <strong>Explanation:</strong> {review.explanation}
              </div>
            )}
            {review.blockingReason && (
              <div>
                <strong>Blocking reason:</strong> {review.blockingReason}
              </div>
            )}
            {review.followUp && (
              <div>
                <strong>Follow-up:</strong> {review.followUp}
              </div>
            )}
            {review.reviewedAt && (
              <div className="text-rnica-muted">Reviewed {new Date(review.reviewedAt).toLocaleString()}</div>
            )}
          </div>
        ) : (
          <>
            <Label htmlFor="medicare-review-outcome">Determination</Label>
            <select
              id="medicare-review-outcome"
              className={selectClassName}
              value={form.outcome}
              disabled={isLocked}
              onChange={(e) => setForm((prev) => ({ ...prev, outcome: e.target.value }))}
            >
              {OUTCOMES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {requiresExplanation && (
              <>
                <Label htmlFor="medicare-review-explanation">Explanation (required)</Label>
                <Textarea
                  id="medicare-review-explanation"
                  className="mb-3"
                  value={form.explanation}
                  disabled={isLocked}
                  onChange={(e) => setForm((prev) => ({ ...prev, explanation: e.target.value }))}
                />
              </>
            )}

            {requiresBlockingDetail && (
              <>
                <Label htmlFor="medicare-review-blocking-reason">Blocking reason (required)</Label>
                <Input
                  id="medicare-review-blocking-reason"
                  className="mb-3"
                  value={form.blockingReason}
                  disabled={isLocked}
                  onChange={(e) => setForm((prev) => ({ ...prev, blockingReason: e.target.value }))}
                />
                <Label htmlFor="medicare-review-follow-up">Follow-up needed (required)</Label>
                <Input
                  id="medicare-review-follow-up"
                  className="mb-3"
                  value={form.followUp}
                  disabled={isLocked}
                  onChange={(e) => setForm((prev) => ({ ...prev, followUp: e.target.value }))}
                />
              </>
            )}

            <label className="flex items-center gap-2 text-xs text-rnica-text mb-3">
              <Checkbox
                checked={form.planOfCareChangeAffectsNonCoveredItems}
                disabled={isLocked}
                onCheckedChange={(checked) =>
                  setForm((prev) => ({ ...prev, planOfCareChangeAffectsNonCoveredItems: Boolean(checked) }))
                }
              />
              A plan-of-care change affects the non-covered items list
            </label>

            {form.planOfCareChangeAffectsNonCoveredItems && candidates.length > 0 && (
              <>
                <Label htmlFor="medicare-review-addendum">
                  Link to an existing Election Addendum request (optional — never creates a new one)
                </Label>
                <select
                  id="medicare-review-addendum"
                  className={selectClassName}
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

            {error && (
              <Alert variant="destructive" className="mb-2">
                {error}
              </Alert>
            )}
            {saved && !error && (
              <Alert variant="success" className="mb-2">
                Saved.
              </Alert>
            )}

            <Button type="button" size="sm" onClick={handleSave} disabled={isLocked || saving || !form.outcome}>
              {saving ? "Saving..." : "Save Medicare Review"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
