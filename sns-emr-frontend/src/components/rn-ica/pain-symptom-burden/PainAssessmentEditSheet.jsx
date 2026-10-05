import React, { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "../../ui/sheet";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { Separator } from "../../ui/separator";
import { derivePainAssessmentMode, resolvePainScore } from "./painLogic";
import "../design-system/RnicaTailwind.css";

// Owner directive (Edit Pain Assessment restructure) -- replaces the
// prior single oversized Dialog (the entire legacy Pain module rendered
// at once) with a focused, conditional, four-step shadcn/ui Sheet. Every
// step still renders through `renderPainStepCards` (a thin wrapper around
// the SAME renderGenericSection/SECTION_CONFIGS.pain machinery that owns
// the real RNICA/HOPE Pain fields, validation, and autosave) -- this
// component only decides WHICH named cards are visible at a time and adds
// a non-data-owning review summary as the last step. No field, path,
// option, or HOPE mapping is introduced, removed, or changed here.
//
// Step -> card mapping (cards are matched by SECTION_CONFIGS.pain's own
// `title` strings -- see renderPainStepCards in RNICA.jsx):
//   1. Screening & Method   -> "Pain Overview" (screenedForPain,
//      reasonNotAssessed, screeningDate, standardizedPainToolType,
//      verbalizesPain, painSeverityCategory, painActiveProblem,
//      currentPain, uncomfortableBecauseOfPain)
//   2. Pain Scale           -> "Pain Intensity" (all three Numeric/
//      FLACC/PAINAD tool-variant cards share this title; only the one
//      matching painAssessmentMode ever renders -- existing gate,
//      untouched)
//   3. Pain Details         -> "Pain History", "Location", "Pain
//      Character & Impact"
//   4. Review & Save        -> read-only summary built from painData,
//      not a legacy-content render
//
// Pain Management ("Edit Regimen") is intentionally NOT one of these
// steps -- it is a separate, single-purpose Sheet (see
// PainManagementEditSheet.jsx) per the owner's responsibility-boundary
// directive: Edit Assessment owns structured documentation inputs only.
const STEPS = [
  { key: "screening", label: "Screening & Method", cardTitles: ["Pain Overview"] },
  { key: "scale", label: "Pain Scale", cardTitles: ["Pain Intensity"] },
  { key: "details", label: "Pain Details", cardTitles: ["Pain History", "Location", "Pain Character & Impact"] },
  { key: "review", label: "Review & Save", cardTitles: [] },
];

function ReviewRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">Not yet documented</span>}</span>
    </div>
  );
}

// Owner directive (UI polish pass) -- a long comma-joined string (e.g.
// "Dull, Aching, Pressure - Neuropathic") is hard to scan at a glance.
// Same ReviewRow row shape, but renders each selected value as its own
// chip instead of one joined string. No data/path change -- purely how
// the already-selected values are displayed on this read-only summary.
function ReviewChipRow({ label, values }) {
  const items = (values || []).filter(Boolean);
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex flex-1 flex-wrap gap-1.5">
        {items.length ? (
          items.map((v) => (
            <Badge key={v} variant="neutral" className="text-[11px] font-normal">{v}</Badge>
          ))
        ) : (
          <span className="text-[12.5px] text-rnica-muted italic">Not yet documented</span>
        )}
      </span>
    </div>
  );
}

export default function PainAssessmentEditSheet({ open, onOpenChange, painData = {}, patientAge, renderPainStepCards }) {
  const [stepIndex, setStepIndex] = useState(0);

  // Re-enter on Step 1 every time the Sheet is (re)opened -- a clinician
  // reopening Edit Assessment should always start at Screening, not
  // wherever they left off last time.
  useEffect(() => {
    if (open) setStepIndex(0);
  }, [open]);

  const isPediatricAge = typeof patientAge === "number" && patientAge < 18;
  const painAssessmentMode = derivePainAssessmentMode(painData, isPediatricAge);
  const score = resolvePainScore(painData, painAssessmentMode);

  const currentPainLabel = { "1": "Yes", "0": "No / none reported", "9": "Unable to determine" }[painData?.currentPain] || "";
  const screenedLabel = { "1": "Yes", "0": "No" }[painData?.screenedForPain] || "";
  const reportingLabel = { "0": "No", "1": "Yes, reliably", "2": "Sometimes", "3": "Unable to determine" }[painData?.verbalizesPain] || "";
  const toolLabel = { "1": "Numeric", "2": "Verbal descriptor", "3": "Patient visual", "4": "Staff observation", "9": "No standardized tool used" }[painData?.standardizedPainToolType] || "";
  const activeProblemLabel = { "1": "Yes", "0": "No", "9": "Unable to determine" }[painData?.painActiveProblem] || "";
  const typeOfPainChips = [
    ...(Array.isArray(painData?.painCharacter) ? painData.painCharacter : []),
    painData?.neuropathicPain === "1" ? "Neuropathic" : null,
  ].filter(Boolean);

  const step = STEPS[stepIndex];
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === STEPS.length - 1;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-2xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Pain Assessment</SheetTitle>
          <SheetDescription>
            Step {stepIndex + 1} of {STEPS.length}: {step.label}
          </SheetDescription>
          <div className="mt-2 flex items-center gap-1.5" role="list" aria-label="Assessment steps">
            {STEPS.map((s, i) => (
              <div
                key={s.key}
                role="listitem"
                aria-current={i === stepIndex ? "step" : undefined}
                className={`flex h-1.5 flex-1 rounded-full ${
                  i < stepIndex ? "bg-rnica-teal" : i === stepIndex ? "bg-rnica-teal" : "bg-rnica-border"
                }`}
              />
            ))}
          </div>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {step.key !== "review" ? (
            renderPainStepCards(step.cardTitles)
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-semibold text-rnica-text">Assessment summary</span>
                {score !== null ? (
                  <Badge variant="critical" className="text-[12px]">SCORE: {score}/10</Badge>
                ) : (
                  <Badge variant="neutral" className="text-[11px]">Not yet scored</Badge>
                )}
              </div>
              <ReviewRow label="Screened for pain" value={screenedLabel} />
              {painData?.screenedForPain === "0" && (
                <ReviewRow label="Reason not assessed" value={painData?.reasonNotAssessed} />
              )}
              <ReviewRow label="Reporting ability" value={reportingLabel} />
              <ReviewRow label="Assessment method" value={toolLabel} />
              <ReviewRow label="Pain present" value={currentPainLabel} />
              <ReviewRow label="Active pain problem" value={activeProblemLabel} />
              <ReviewChipRow label="Pain Location" values={painData?.painLocation} />
              <ReviewChipRow label="Type of Pain" values={typeOfPainChips} />
              <ReviewRow label="Functional Impact" value={painData?.effectOnFunction} />
            </div>
          )}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0 !justify-between">
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            {!isFirst && (
              <Button variant="outline" onClick={() => setStepIndex((i) => Math.max(0, i - 1))}>
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back
              </Button>
            )}
          </div>
          {!isLast ? (
            <Button onClick={() => setStepIndex((i) => Math.min(STEPS.length - 1, i + 1))}>
              Next
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={() => onOpenChange(false)}>
              <Check className="mr-1 h-4 w-4" />
              Save Assessment
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
