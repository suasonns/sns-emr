import React, { useEffect, useState } from "react";
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
import { SAFETY_WIZARD_STEPS, getFirstIncompleteSafetyStepId } from "./safetyLogic";
import "../design-system/RnicaTailwind.css";

// PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
// Assessment" -- supersedes the (2026-10-24) "Safety Is One Assessment"
// wizard's auto-skip-Oxygen and always-reopen-at-Step-1 behavior. Oxygen
// Safety is now ALWAYS one of the 5 steps (never filtered out) -- when
// not applicable it shows an explicit RN-confirmed "Not Applicable" step
// (section 4), never silently absent. Editing a completed assessment
// defaults to Step 1 unless opened via a validation deep link, which
// opens the exact first incomplete step (section 5); `initialStepId`
// carries that deep link in from the Overview card/validation rail.
// Footer now offers "Save Draft and Close" on every step and
// "Complete Safety Assessment" only on the last step (section 2/3),
// replacing the previous unconditional "Next"/"Done" pair. The step
// pills' completed indicator reflects each part's actual completion
// (from `summary`), not merely "already visited" (section 5: "The step
// indicator must always permit access to completed steps").
export default function SafetyAssessmentEditSheet({ open, onOpenChange, renderSafetyStepCards, summary, initialStepId, onInitialStepConsumed, onComplete }) {
  const steps = SAFETY_WIZARD_STEPS;
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!open) return;
    if (initialStepId) {
      const idx = steps.findIndex((s) => s.id === initialStepId);
      setStepIndex(idx >= 0 ? idx : 0);
      onInitialStepConsumed?.();
    } else {
      setStepIndex(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const activeStep = steps[Math.min(stepIndex, steps.length - 1)];
  const isReviewStep = activeStep?.id === "review";
  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex === steps.length - 1;

  const stepComplete = (step) => {
    if (step.id === "review") return Boolean(summary?.allPartsComplete);
    return Boolean(summary?.[step.id]?.complete);
  };

  const goBack = () => setStepIndex((i) => Math.max(0, i - 1));
  const goNext = () => setStepIndex((i) => Math.min(steps.length - 1, i + 1));
  const saveDraftAndClose = () => onOpenChange(false);
  const completeAssessment = () => {
    onComplete?.();
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Safety & Clinical Risk Assessment</SheetTitle>
          <SheetDescription>
            Step {stepIndex + 1} of {steps.length}: {activeStep?.label}
          </SheetDescription>
        </SheetHeader>

        <div className="rnica-tw flex shrink-0 items-center gap-1.5 overflow-x-auto pb-2">
          {steps.map((step, i) => {
            const isActive = i === stepIndex;
            const isDone = stepComplete(step);
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
            <SafetyReviewStep summary={summary} onJumpToStep={(id) => setStepIndex(steps.findIndex((s) => s.id === id))} />
          ) : (
            renderSafetyStepCards(activeStep.cardTitles)
          )}
        </div>

        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0 items-center justify-between sm:justify-between">
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={goBack} disabled={isFirstStep}>
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back
            </Button>
            <Button variant="outline" onClick={saveDraftAndClose}>
              Save Draft and Close
            </Button>
          </div>
          {isLastStep ? (
            <Button onClick={completeAssessment} disabled={!summary?.allPartsComplete}>
              Complete Safety Assessment
            </Button>
          ) : (
            <Button onClick={goNext}>
              Next
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          )}
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

// PRODUCT OWNER DEFECT (2026-10-24) "Current Safety Completion Logic Is
// Invalid" -- a field may be Completed, Not Applicable, or Incomplete,
// never "Complete" + "Not Yet Documented" at the same time. `applicable`
// tells this row whether its value was ever REQUIRED; when it was not
// (the step still correctly shows Complete), render the literal "N/A"
// instead of the ambiguous/alarming "Not yet documented" placeholder.
function ReviewRowOrNA({ label, value, applicable, naValue = "N/A" }) {
  if (!applicable) {
    return (
      <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
        <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
        <span className="flex-1 text-[12.5px] text-rnica-muted">{naValue}</span>
      </div>
    );
  }
  return <ReviewRow label={label} value={value} />;
}

// PRODUCT OWNER DIRECTIVE (2026-10-24) "Fix Disaster Triage and
// Review-Step Completion Logic" -- "Replace Responsible Support: Not
// Yet Documented with Responsible Support: Unknown" (and likewise for
// Preferred Emergency Location) when the field is genuinely optional and
// simply hasn't been answered. Unlike ReviewRowOrNA, this always shows
// the real value when one exists -- it only swaps the placeholder text.
function ReviewRowOrUnknown({ label, value, unknownValue = "Unknown" }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">{unknownValue}</span>}</span>
    </div>
  );
}

function ReviewSection({ title, complete, onEdit, children }) {
  return (
    <div className="mb-3 rounded-md border border-rnica-border p-3">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h4 className="text-[13px] font-semibold text-rnica-text">{title}</h4>
        <div className="flex items-center gap-2">
          <Badge variant={complete ? "success" : "warning"} className="text-[10px]">
            {complete ? "Complete" : "Incomplete"}
          </Badge>
          <button type="button" onClick={onEdit} className="text-[11px] font-medium text-rnica-accent underline">
            Edit {title}
          </button>
        </div>
      </div>
      {children}
    </div>
  );
}

// Step 5 ("Review and Complete... DISPLAY: Environmental Safety Summary,
// Fall Risk Summary, Oxygen Safety Summary, Disaster Triage Summary AS A
// SINGLE SAFETY RECORD"). Read-only -- every value comes straight from
// safetyLogic.js's existing summarize* functions (via the shared
// `summary` prop), nothing is recomputed or fabricated here. "Edit X"
// links (section 11) navigate within this same modal -- they never open
// a separate modal.
function SafetyReviewStep({ summary, onJumpToStep }) {
  if (!summary) return null;
  const { environmental, fallRisk, oxygen, disaster } = summary;
  return (
    <div>
      <ReviewSection title="Environmental Safety" complete={environmental.complete} onEdit={() => onJumpToStep("environmental")}>
        <ReviewRow label="Setting" value={environmental.setting} />
        <ReviewRow label="Patient Hazard" value={environmental.patientSummary} />
        <ReviewRow label="Staff Hazard" value={environmental.staffSummary} />
        <ReviewRowOrNA label="Risk Target" value={environmental.riskTarget} applicable={environmental.hasAnyHazard} />
        <ReviewRowOrNA label="Actions Taken" value={(environmental.actionsTaken || []).join(", ")} applicable={environmental.hasAnyHazard} />
        <ReviewRowOrNA label="Staff Disposition" value={environmental.staffDisposition} applicable={environmental.staffDispositionRequired} />
        <ReviewRowOrNA label="Follow-Up" value={environmental.followUpRequired} applicable={environmental.hasAnyHazard} />
      </ReviewSection>
      <ReviewSection title="Morse Fall Scale" complete={fallRisk.complete} onEdit={() => onJumpToStep("fallRisk")}>
        <ReviewRow label="Score" value={fallRisk.complete ? String(fallRisk.total) : ""} />
        <ReviewRow label="Classification" value={fallRisk.classification} />
        <ReviewRow label="Previous Score / Trend" value={fallRisk.trend?.previous ? `${fallRisk.trend.previous.totalScore} / ${fallRisk.trend.trend}` : ""} />
      </ReviewSection>
      <ReviewSection title="Oxygen Safety" complete={oxygen.complete} onEdit={() => onJumpToStep("oxygen")}>
        <ReviewRow label="Status" value={oxygen.applicable ? oxygen.status : "Not Applicable"} />
        <ReviewRowOrNA
          label="Concerns"
          value={(oxygen.concerns || []).join(", ")}
          applicable={oxygen.applicable && (oxygen.hasActiveConcern || !oxygen.status)}
          naValue={oxygen.applicable && oxygen.status ? "None" : "N/A"}
        />
        <ReviewRowOrNA label="Actions Taken" value={(oxygen.actionsTaken || []).join(", ")} applicable={oxygen.applicable && oxygen.hasActiveConcern} />
        <ReviewRowOrNA label="Follow-Up" value={oxygen.followUpRequired} applicable={oxygen.applicable && oxygen.hasActiveConcern} />
      </ReviewSection>
      <ReviewSection title="Disaster Triage" complete={disaster.complete} onEdit={() => onJumpToStep("disaster")}>
        <ReviewRow label="Level" value={disaster.shortLabel} />
        <ReviewRow label="Contributing Factors" value={(disaster.conditions || []).join(", ")} />
        <ReviewRow label="Lives Alone" value={disaster.livesAlone} />
        <ReviewRow label="Requires Evacuation Assistance" value={disaster.requiresEvacuationAssistance} />
        <ReviewRow label="Caregiver Available During Emergency" value={disaster.caregiverAvailable} />
        <ReviewRow label="Transportation Available" value={disaster.transportationAvailable} />
        <ReviewRow label="Requires Electricity For Medical Equipment" value={disaster.requiresElectricity} />
        <ReviewRow label="Oxygen Dependent" value={disaster.oxygenDependent} />
        <ReviewRow label="Backup Power Available" value={disaster.backupPowerAvailable} />
        <ReviewRowOrUnknown label="Preferred Emergency Location" value={disaster.preferredEmergencyLocation} />
        <ReviewRowOrUnknown label="Responsible Support" value={disaster.responsibleSupport} />
      </ReviewSection>
    </div>
  );
}

