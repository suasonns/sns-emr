import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "../../ui/sheet";
import { Button } from "../../ui/button";
import { Separator } from "../../ui/separator";
import { Badge } from "../../ui/badge";
import { SAFETY_WIZARD_STEPS } from "./safetyLogic";
import "../design-system/RnicaTailwind.css";

// PRODUCT OWNER DECISION (2026-10-24) "Safety Is One Assessment":
// "REPLACE: 4 INDEPENDENT ASSESSMENT SHEETS WITH 1 SAFETY ASSESSMENT
// WIZARD... THE RN SHOULD FEEL LIKE: 'I AM COMPLETING SAFETY' NOT 'I AM
// COMPLETING FOUR DIFFERENT APPLICATIONS.'" Supersedes the four
// standalone Edit Sheets (EnvironmentalSafetyEditSheet,
// FallRiskEditSheet, OxygenSafetyEditSheet, DisasterTriageEditSheet),
// which are removed. This single Sheet walks the SAME four field sets
// through 5 internal steps (Environmental Safety, Morse Fall Scale,
// Oxygen Safety, Disaster Triage, Review & Complete), each still
// rendered through the SAME `renderSafetyStepCards` call (same fields,
// paths, HOPE mappings, validation, and update() autosave contract --
// "do not build a new scoring engine" / "do not build a custom
// fall-risk framework" apply equally here: nothing below captures or
// recomputes a field, it only sequences and reviews the same
// RNICA.jsx-owned cards). Oxygen Safety is auto-skipped (never shown)
// when the patient is not on oxygen, per directive.
export default function SafetyAssessmentEditSheet({ open, onOpenChange, renderSafetyStepCards, summary }) {
  const steps = useMemo(
    () => SAFETY_WIZARD_STEPS.filter((step) => step.id !== "oxygen" || summary?.oxygen?.applicable),
    [summary?.oxygen?.applicable]
  );
  const [stepIndex, setStepIndex] = useState(0);

  // Always reopen on step 1 -- a half-finished prior visit should not
  // silently resume mid-wizard without the RN seeing the full sequence.
  useEffect(() => {
    if (open) setStepIndex(0);
  }, [open]);

  const activeStep = steps[Math.min(stepIndex, steps.length - 1)];
  const isReviewStep = activeStep?.id === "review";
  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex === steps.length - 1;

  const goBack = () => setStepIndex((i) => Math.max(0, i - 1));
  const goNext = () => {
    if (isLastStep) {
      onOpenChange(false);
    } else {
      setStepIndex((i) => Math.min(steps.length - 1, i + 1));
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Safety & Clinical Risk Assessment</SheetTitle>
          <SheetDescription>
            One Safety assessment, {steps.length} steps: Environmental Safety, Morse Fall Scale
            {summary?.oxygen?.applicable ? ", Oxygen Safety" : ""}, Disaster Triage, then Review &amp; Complete.
          </SheetDescription>
        </SheetHeader>

        <div className="rnica-tw flex shrink-0 items-center gap-1.5 overflow-x-auto pb-2">
          {steps.map((step, i) => {
            const isActive = i === stepIndex;
            const isDone = i < stepIndex;
            return (
              <React.Fragment key={step.id}>
                {i > 0 && <div className="h-px w-3 shrink-0 bg-rnica-border" />}
                <button
                  type="button"
                  onClick={() => setStepIndex(i)}
                  className={`flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-colors ${
                    isActive
                      ? "border-rnica-accent bg-rnica-accent/10 text-rnica-accent"
                      : isDone
                        ? "border-rnica-border bg-rnica-successBg text-rnica-green"
                        : "border-rnica-border text-rnica-muted"
                  }`}
                >
                  {isDone ? <Check className="h-3 w-3" /> : <span className="tabular-nums">{i + 1}</span>}
                  {step.label}
                </button>
              </React.Fragment>
            );
          })}
        </div>

        <Separator className="shrink-0" />

        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {isReviewStep ? (
            <SafetyReviewStep summary={summary} />
          ) : (
            renderSafetyStepCards(activeStep.cardTitles)
          )}
        </div>

        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0 items-center justify-between sm:justify-between">
          <Button variant="outline" onClick={goBack} disabled={isFirstStep}>
            <ChevronLeft className="mr-1 h-4 w-4" />
            Back
          </Button>
          <Button onClick={goNext}>
            {isLastStep ? "Done" : "Next"}
            {!isLastStep && <ChevronRight className="ml-1 h-4 w-4" />}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

const NOT_DOCUMENTED = "Not yet documented";

function ReviewRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">{NOT_DOCUMENTED}</span>}</span>
    </div>
  );
}

function ReviewSection({ title, complete, children }) {
  return (
    <div className="mb-3 rounded-md border border-rnica-border p-3">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h4 className="text-[13px] font-semibold text-rnica-text">{title}</h4>
        <Badge variant={complete ? "success" : "warning"} className="text-[10px]">
          {complete ? "Complete" : "Incomplete"}
        </Badge>
      </div>
      {children}
    </div>
  );
}

// Step 5 ("Review and Complete... DISPLAY: Environmental Safety Summary,
// Fall Risk Summary, Oxygen Safety Summary, Disaster Triage Summary AS A
// SINGLE SAFETY RECORD"). Read-only -- every value comes straight from
// safetyLogic.js's existing summarize* functions (via the shared
// `summary` prop), nothing is recomputed or fabricated here.
function SafetyReviewStep({ summary }) {
  if (!summary) return null;
  const { environmental, fallRisk, oxygen, disaster } = summary;
  return (
    <div>
      <ReviewSection title="Environmental Safety" complete={environmental.complete}>
        <ReviewRow label="Setting" value={environmental.setting} />
        <ReviewRow label="Patient Hazard" value={environmental.patientSummary} />
        <ReviewRow label="Staff Hazard" value={environmental.staffSummary} />
      </ReviewSection>
      <ReviewSection title="Fall Risk (Morse Fall Scale)" complete={fallRisk.complete}>
        <ReviewRow label="Score" value={fallRisk.complete ? String(fallRisk.total) : ""} />
        <ReviewRow label="Classification" value={fallRisk.classification} />
        <ReviewRow label="Trend" value={fallRisk.trend.trend} />
      </ReviewSection>
      {oxygen.applicable && (
        <ReviewSection title="Oxygen Safety" complete={oxygen.complete}>
          <ReviewRow label="Status" value={oxygen.status} />
          <ReviewRow label="Concerns" value={oxygen.concerns.join(", ")} />
        </ReviewSection>
      )}
      <ReviewSection title="Disaster Triage" complete={disaster.complete}>
        <ReviewRow label="Level" value={disaster.shortLabel} />
        <ReviewRow label="Conditions" value={disaster.conditions.join(", ")} />
      </ReviewSection>
    </div>
  );
}
