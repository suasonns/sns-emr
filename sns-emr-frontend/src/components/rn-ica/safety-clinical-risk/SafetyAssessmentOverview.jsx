import React, { useState } from "react";
import { ShieldAlert, ChevronRight, StickyNote } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { summarizeSafetyAssessment } from "./safetyLogic";
import SafetyAssessmentEditSheet from "./SafetyAssessmentEditSheet";
import "../design-system/RnicaTailwind.css";

// PRODUCT OWNER DECISION (2026-10-24) "Safety Is One Assessment" --
// supersedes the prior "Four Guided Assessments" presentation (four
// separate cards/Edit Sheets). "SAFETY IS ONE ASSESSMENT... MAIN PAGE
// DISPLAY ONLY: Safety & Clinical Risk Assessment / Status / Summary /
// Edit Assessment." The main page now shows exactly ONE card with a
// single consolidated Status, a condensed Summary of all four parts
// (Environmental Safety, Fall Risk/Morse Fall Scale, Oxygen Safety,
// Disaster Triage), and a single "Edit Assessment" button that opens
// ONE wizard Sheet (SafetyAssessmentEditSheet) with internal steps --
// not four independent Sheets. Patient Safety, Caregiver Safety, Safety
// Notes, DME, and Supplies remain intentionally NOT rendered here (per
// the prior directive's explicit removal list, unchanged by this
// consolidation) -- their underlying fields/legacy cards are untouched
// in RNICA.jsx for historical round-tripping. Every value below is read
// from `safetyData` via safetyLogic.js's pure summarize* functions --
// nothing is captured, duplicated, or fabricated here; field entry still
// happens exclusively through `renderSafetyStepCards` (inside the
// wizard Sheet), the same `renderGenericSection` used everywhere else
// in RNICA.

const NOT_DOCUMENTED = "Not yet documented";

function StatusBadge({ status }) {
  const variant = status === "Complete" ? "success" : status === "Needs Review" ? "critical" : status === "In Progress" ? "warning" : "neutral";
  return (
    <Badge variant={variant} className="text-[11px]">
      {status}
    </Badge>
  );
}

function Fact({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[42%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">{NOT_DOCUMENTED}</span>}</span>
    </div>
  );
}

function ClarificationNote({ note }) {
  if (!note) return null;
  return (
    <div className="mt-2 flex items-start gap-1.5 rounded-md bg-rnica-muted/10 px-2 py-1.5 text-[12px] text-rnica-text">
      <StickyNote className="mt-0.5 h-3 w-3 shrink-0 text-rnica-muted" />
      <span>{note}</span>
    </div>
  );
}

export default function SafetyAssessmentOverview({
  safetyData = {},
  renderSafetyStepCards,
  siteOfService = "",
  oxygenInUse,
  onContinue,
  onUpdateField,
  initialStepId,
  onInitialStepConsumed,
}) {
  const [editOpen, setEditOpen] = useState(false);

  // Minimal cross-module shim matching the exact shape the underlying
  // cards already read from (`demographics.livingSituation.siteOfService`,
  // `respiratory.oxygenTherapy.inUse`) -- not the whole RNICA formData
  // object, to match this directory's narrow-prop convention.
  const fullFormData = {
    demographics: { livingSituation: { siteOfService } },
    respiratory: { oxygenTherapy: { inUse: oxygenInUse } },
  };

  const summary = summarizeSafetyAssessment(safetyData, fullFormData);
  const { environmental, fallRisk, oxygen, disaster } = summary;

  const clarificationNote = [
    environmental.clarification,
    fallRisk.clarification,
    oxygen.clarification,
    disaster.clarification,
  ].filter(Boolean).join(" · ");

  // PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
  // Assessment" section 2/3/12 -- "Complete" is an explicit RN
  // submission (the Review step's "Complete Safety Assessment" button),
  // not merely answering every question; drives the 4-state status
  // model (`safetyAssessmentCompletedAt`) via the same `onUpdateField`
  // path every other RNICA field already writes through.
  const handleComplete = () => {
    onUpdateField?.("safety", "safetyAssessmentCompletedAt", new Date().toISOString());
  };

  // Validation deep-link (section 13): "Opening that validation item
  // launches the unified modal at the first incomplete step." A
  // non-empty `initialStepId` (set by RNICACommandWorkspace's
  // Validation rail click handler) auto-opens the Sheet directly at
  // that step; the Sheet itself resets to Step 1 otherwise (section 5:
  // "Default to Step 1 unless the user entered through a validation
  // deep link").
  React.useEffect(() => {
    if (initialStepId) setEditOpen(true);
  }, [initialStepId]);

  return (
    <div className="rnica-tw flex flex-col gap-4">
      <Card className="border-rnica-border bg-rnica-card">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="flex items-center gap-2 text-[15px]">
            <ShieldAlert className="h-4 w-4 text-rnica-accent" />
            Safety & Clinical Risk Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge status={summary.status} />
            <Button size="sm" variant="outline" onClick={() => setEditOpen(true)}>Edit Assessment</Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <Fact
            label="Environmental Safety"
            value={[environmental.patientSummary, environmental.staffSummary].filter(Boolean).join(" · ")}
          />
          <Fact
            label="Fall Risk"
            value={fallRisk.complete ? `Score ${fallRisk.total} · ${fallRisk.classification}` : ""}
          />
          <Fact
            label="Oxygen Safety"
            value={!oxygen.applicable ? (oxygen.confirmedNotApplicable ? "Not Applicable" : "") : (oxygen.status === "Concern Identified" ? oxygen.concerns.join(", ") : oxygen.status)}
          />
          <Fact
            label="Disaster Triage"
            value={disaster.complete ? [disaster.shortLabel, disaster.conditions.join(", ")].filter(Boolean).join(" · ") : ""}
          />
          <ClarificationNote note={clarificationNote} />
        </CardContent>
      </Card>

      {onContinue && (
        <Button className="w-full justify-between" onClick={onContinue}>
          Continue to Clinical Review
          <ChevronRight className="h-4 w-4" />
        </Button>
      )}

      <SafetyAssessmentEditSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        renderSafetyStepCards={renderSafetyStepCards}
        summary={summary}
        initialStepId={initialStepId}
        onInitialStepConsumed={onInitialStepConsumed}
        onComplete={handleComplete}
      />
    </div>
  );
}
