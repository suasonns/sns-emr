import React, { useState } from "react";
import { ShieldAlert, Activity, Wind, Siren, ChevronRight, StickyNote } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  summarizeEnvironmentalSafety,
  summarizeFallRisk,
  summarizeOxygenSafety,
  summarizeDisasterTriage,
} from "./safetyLogic";
import EnvironmentalSafetyEditSheet from "./EnvironmentalSafetyEditSheet";
import FallRiskEditSheet from "./FallRiskEditSheet";
import OxygenSafetyEditSheet from "./OxygenSafetyEditSheet";
import DisasterTriageEditSheet from "./DisasterTriageEditSheet";
import "../design-system/RnicaTailwind.css";

// "Replace the Inline Safety Page With Four Guided Assessments" (final
// directive): "THE PAIN DESIGN. USER SEES ONLY: Assessment Summary AND
// Edit Assessment... SAFETY MUST WORK THE SAME WAY." The main page shows
// EXACTLY 4 compact cards -- Environmental Safety, Fall Risk (Morse Fall
// Scale), Oxygen Safety, Disaster Triage -- each with only a Status
// badge, a short Summary, and an "Edit Assessment" button that opens a
// side Sheet. Patient Safety, Caregiver Safety, Safety Notes, DME, and
// Supplies are intentionally NOT rendered as separate cards here (per
// the directive's explicit removal list) -- their underlying fields and
// legacy cards remain unchanged in RNICA.jsx/SECTION_CONFIGS.safety for
// historical round-tripping and are not reachable from this Overview.
// Every value below is read from `safetyData` via safetyLogic.js's pure
// summarize* functions -- nothing is captured, duplicated, or fabricated
// here; field entry still happens exclusively through
// `renderSafetyStepCards` (Edit Sheets), the same `renderGenericSection`
// used everywhere else in RNICA.

const NOT_DOCUMENTED = "Not yet documented";

function StatusBadge({ complete, completeLabel = "Completed", incompleteLabel = "Not Started" }) {
  return (
    <Badge variant={complete ? "success" : "warning"} className="text-[11px]">
      {complete ? completeLabel : incompleteLabel}
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
  // PRODUCT OWNER DIRECTIVE section 3 ("Safety Notes becomes small
  // optional per-assessment clarification fields") -- a note is shown
  // only when one was actually recorded; there is no permanent empty
  // "Not yet documented" clarification row (notes remain for exceptions
  // only, never the primary record).
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
}) {
  const [environmentalOpen, setEnvironmentalOpen] = useState(false);
  const [fallRiskOpen, setFallRiskOpen] = useState(false);
  const [oxygenOpen, setOxygenOpen] = useState(false);
  const [disasterOpen, setDisasterOpen] = useState(false);

  // Minimal cross-module shim matching the exact shape
  // EnvironmentalSafetyCard/OxygenSafetyCard already read from
  // `fullFormData` (`demographics.livingSituation.siteOfService`,
  // `respiratory.oxygenTherapy.inUse`) -- not the whole RNICA formData
  // object, to match this directory's narrow-prop convention.
  const fullFormData = {
    demographics: { livingSituation: { siteOfService } },
    respiratory: { oxygenTherapy: { inUse: oxygenInUse } },
  };

  const environmental = summarizeEnvironmentalSafety(safetyData, fullFormData);
  const fallRisk = summarizeFallRisk(safetyData);
  const oxygen = summarizeOxygenSafety(safetyData, fullFormData);
  const disaster = summarizeDisasterTriage(safetyData);

  return (
    <div className="rnica-tw flex flex-col gap-4">
      <Card className="border-rnica-border bg-rnica-card">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="flex items-center gap-2 text-[15px]">
            <ShieldAlert className="h-4 w-4 text-rnica-accent" />
            Environmental Safety Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge complete={environmental.complete} />
            <Button size="sm" variant="outline" onClick={() => setEnvironmentalOpen(true)}>Edit Assessment</Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <Fact label="Setting" value={environmental.setting} />
          <Fact label="Patient Hazard" value={environmental.patientSummary} />
          <Fact label="Staff Hazard" value={environmental.staffSummary} />
          <ClarificationNote note={environmental.clarification} />
        </CardContent>
      </Card>

      <Card className="border-rnica-border bg-rnica-card">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="flex items-center gap-2 text-[15px]">
            <Activity className="h-4 w-4 text-rnica-accent" />
            Fall Risk Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge complete={fallRisk.complete} />
            <Button size="sm" variant="outline" onClick={() => setFallRiskOpen(true)}>Edit Assessment</Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <Fact label="Score" value={fallRisk.complete ? String(fallRisk.total) : ""} />
          <Fact label="Classification" value={fallRisk.classification} />
          <Fact label="Previous Score" value={fallRisk.trend.previous ? String(fallRisk.trend.previous.totalScore) : ""} />
          <Fact label="Trend" value={fallRisk.trend.trend} />
          <ClarificationNote note={fallRisk.clarification} />
        </CardContent>
      </Card>

      <Card className="border-rnica-border bg-rnica-card">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="flex items-center gap-2 text-[15px]">
            <Wind className="h-4 w-4 text-rnica-accent" />
            Oxygen Safety Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge complete={oxygen.complete} completeLabel={oxygen.applicable ? "Completed" : "Not Applicable"} />
            <Button size="sm" variant="outline" onClick={() => setOxygenOpen(true)}>Edit Assessment</Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {oxygen.applicable ? (
            <>
              <Fact label="Status" value={oxygen.status} />
              <Fact label="Concerns" value={oxygen.concerns.join(", ")} />
            </>
          ) : (
            <p className="py-1 text-[12.5px] italic text-rnica-muted">Not applicable -- patient is not currently on oxygen.</p>
          )}
          <ClarificationNote note={oxygen.clarification} />
        </CardContent>
      </Card>

      <Card className="border-rnica-border bg-rnica-card">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="flex items-center gap-2 text-[15px]">
            <Siren className="h-4 w-4 text-rnica-accent" />
            Disaster Triage Assessment
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge complete={disaster.complete} />
            <Button size="sm" variant="outline" onClick={() => setDisasterOpen(true)}>Edit Assessment</Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <Fact label="Level" value={disaster.shortLabel} />
          <Fact label="Conditions" value={disaster.conditions.join(", ")} />
          <ClarificationNote note={disaster.clarification} />
        </CardContent>
      </Card>

      {onContinue && (
        <Button className="w-full justify-between" onClick={onContinue}>
          Continue to Clinical Review
          <ChevronRight className="h-4 w-4" />
        </Button>
      )}

      <EnvironmentalSafetyEditSheet
        open={environmentalOpen}
        onOpenChange={setEnvironmentalOpen}
        renderSafetyStepCards={renderSafetyStepCards}
      />
      <FallRiskEditSheet
        open={fallRiskOpen}
        onOpenChange={setFallRiskOpen}
        renderSafetyStepCards={renderSafetyStepCards}
      />
      <OxygenSafetyEditSheet
        open={oxygenOpen}
        onOpenChange={setOxygenOpen}
        renderSafetyStepCards={renderSafetyStepCards}
      />
      <DisasterTriageEditSheet
        open={disasterOpen}
        onOpenChange={setDisasterOpen}
        renderSafetyStepCards={renderSafetyStepCards}
      />
    </div>
  );
}
