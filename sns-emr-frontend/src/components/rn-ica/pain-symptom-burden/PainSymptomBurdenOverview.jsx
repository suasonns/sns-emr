import React, { useState } from "react";
import { ShieldAlert, ClipboardList, Sparkles, AlertTriangle, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  derivePainAssessmentMode,
  resolvePainScore,
  computeAiPainNotes,
  computePainOverdueAlerts,
  buildSymptomBurdenRows,
  joinList,
} from "./painLogic";
import PainAssessmentEditSheet from "./PainAssessmentEditSheet";
import PainManagementEditSheet from "./PainManagementEditSheet";
import "../design-system/RnicaTailwind.css";

// Approved "Pain & Symptom Burden" screen (canonical reference:
// rnica-figma-reference/{dark/v3.2-10screen,light}/pain-assessment.png,
// REFERENCE_MANIFEST.md #4). This is the clinician-facing presentation
// layer -- compact, reviewed clinical state -- over the existing
// RNICA/HOPE Pain module, which remains the data-entry, validation,
// persistence, audit, and compliance infrastructure (unchanged, rendered
// inside the Edit Assessment / Edit Regimen Sheets via
// `renderPainStepCards`). Every value below is read from
// `formData.pain` / `formData.symptomImpact` -- nothing is captured,
// duplicated, or fabricated here.

const NOT_DOCUMENTED = "Not yet documented";

function Fact({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[38%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">{NOT_DOCUMENTED}</span>}</span>
    </div>
  );
}

function severityBadgeVariant(tone) {
  if (tone === "critical") return "critical";
  if (tone === "warning") return "warning";
  if (tone === "info") return "teal";
  return "neutral";
}

export default function PainSymptomBurdenOverview({
  painData = {},
  symptomImpactData = {},
  patientAge,
  renderPainStepCards,
  onNavigateToSymptom,
  onContinue,
}) {
  const [assessmentOpen, setAssessmentOpen] = useState(false);
  const [regimenOpen, setRegimenOpen] = useState(false);

  const isPediatricAge = typeof patientAge === "number" && patientAge < 18;
  const painAssessmentMode = derivePainAssessmentMode(painData, isPediatricAge);
  const score = resolvePainScore(painData, painAssessmentMode);
  const aiNotes = computeAiPainNotes(painData);
  const overdueAlerts = computePainOverdueAlerts(painData, painAssessmentMode);
  const symptomRows = buildSymptomBurdenRows(symptomImpactData);

  const currentPainLabel = { "1": "Yes", "0": "No / none reported", "9": "Unable to determine" }[painData?.currentPain] || "";
  const typeOfPain = [
    joinList(painData?.painCharacter),
    painData?.neuropathicPain === "1" ? "Neuropathic" : "",
  ].filter(Boolean).join(" · ");

  const scheduledRegimen = painData?.routinePainMedicationPresent === "1"
    ? [painData?.painMedicationType, joinList(painData?.painMedicationRoute)].filter(Boolean).join(" · ")
    : painData?.routinePainMedicationPresent === "0" ? "None documented" : "";
  const breakthroughRegimen = painData?.breakthroughPainMedication === "1"
    ? "Breakthrough medication present"
    : painData?.breakthroughPainMedication === "0" ? "None documented" : "";

  return (
    <div className="rnica-tw grid grid-cols-1 gap-4 lg:grid-cols-[2fr_1fr]">
      <div className="flex flex-col gap-4">
        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2 text-[15px]">
                <ShieldAlert className="h-4 w-4 text-rnica-accent" />
                Current Pain Assessment
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              {score !== null ? (
                <Badge variant="critical" className="text-[12px]">SCORE: {score}/10</Badge>
              ) : (
                <Badge variant="neutral" className="text-[11px]">Not yet scored</Badge>
              )}
              <Button size="sm" variant="outline" onClick={() => setAssessmentOpen(true)}>Edit Assessment</Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <Fact label="Pain present" value={currentPainLabel} />
            <Fact label="Pain Location" value={joinList(painData?.painLocation)} />
            <Fact label="Type of Pain" value={typeOfPain} />
            <Fact label="Onset & Progression" value={painData?.painOnsetProgression} />
            <Fact label="Duration & Frequency" value={painData?.painDurationFrequency} />
            <Fact label="Aggravating Factors" value={joinList(painData?.aggravatingFactors)} />
            <Fact label="Alleviating Factors" value={joinList(painData?.relievingFactors)} />
          </CardContent>
        </Card>

        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <ClipboardList className="h-4 w-4 text-rnica-accent" />
              Pain Management Regimen
            </CardTitle>
            <Button size="sm" variant="outline" onClick={() => setRegimenOpen(true)}>Edit Regimen</Button>
          </CardHeader>
          <CardContent className="pt-0">
            <Fact label="Scheduled Regimen" value={scheduledRegimen} />
            <Fact label="Breakthrough Regimen" value={breakthroughRegimen} />
            <Fact label="Adjuvant / Non-Pharm" value={joinList(painData?.nonPharmInterventions)} />
            <Fact label="Effectiveness Rating" value={painData?.painEffectivenessRating} />
            <Fact label="Notes" value={painData?.painManagementPlan} />
          </CardContent>
        </Card>

        <Card className="border-rnica-accent/40 bg-rnica-card">
          <CardHeader className="space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px] text-rnica-accent">
              <Sparkles className="h-4 w-4" />
              AI Pain Analysis & Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-[12.5px]">
            {aiNotes.length === 0 ? (
              <p className="italic text-rnica-muted">Insufficient reviewed pain data for analysis.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-4">
                {aiNotes.map((note, i) => (
                  <li key={i}>
                    {note.text} <span className="text-[10px] text-rnica-muted">(from {note.field})</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {overdueAlerts.length > 0 && (
          <Card className="border-amber-500/50 bg-amber-500/10">
            <CardHeader className="space-y-0">
              <CardTitle className="flex items-center gap-2 text-[15px] text-amber-600">
                <AlertTriangle className="h-4 w-4" />
                Overdue Action Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 text-[12.5px]">
              <ul className="list-disc space-y-1 pl-4">
                {overdueAlerts.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="space-y-0">
            <CardTitle className="text-[15px]">Symptom Burden Matrix</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-0 pt-0">
            {symptomRows.map((row, i) => (
              <button
                type="button"
                key={row.key}
                onClick={() => onNavigateToSymptom?.(row.moduleKey)}
                className={`flex items-center justify-between gap-2 py-2 text-left hover:opacity-80 ${i < symptomRows.length - 1 ? "border-b border-rnica-border/50" : ""}`}
              >
                <span className="text-[12.5px] font-medium text-rnica-text">{row.label}</span>
                <span className="flex items-center gap-1.5">
                  <Badge variant={severityBadgeVariant(row.severityTone)} className="text-[10.5px]">
                    {row.statusLabel || NOT_DOCUMENTED}
                  </Badge>
                  <ChevronRight className="h-3.5 w-3.5 text-rnica-muted" />
                </span>
              </button>
            ))}
          </CardContent>
        </Card>

        {onContinue && (
          <Button className="w-full justify-between" onClick={onContinue}>
            Continue to Clinical Review
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Focused, conditional, four-step edit interaction (owner
          directive, Edit Pain Assessment restructure) -- replaces the
          prior single oversized Dialog embedding the entire legacy Pain
          module at once. Pain Management is a separate Sheet (Edit
          Regimen below), never bundled into this one. Both still render
          through renderPainStepCards -> renderGenericSection ->
          SECTION_CONFIGS.pain -- same fields, paths, HOPE mappings,
          validation, and autosave contract; only how many cards are
          visible at a time changed. */}
      <PainAssessmentEditSheet
        open={assessmentOpen}
        onOpenChange={setAssessmentOpen}
        painData={painData}
        patientAge={patientAge}
        renderPainStepCards={renderPainStepCards}
      />
      <PainManagementEditSheet
        open={regimenOpen}
        onOpenChange={setRegimenOpen}
        renderPainStepCards={renderPainStepCards}
      />
    </div>
  );
}
