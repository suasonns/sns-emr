import React, { useState } from "react";
import { Stethoscope, ListChecks, Users, FileCheck2, ChevronRight, CheckCircle2, Circle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  summarizePrimaryDiagnosis,
  summarizeSecondaryDiagnoses,
  summarizeComorbidities,
  summarizeContributingConditions,
  computeDiagnosisVerificationChecklist,
} from "./diagnosisLogic";
import DiagnosisPrimaryEditSheet from "./DiagnosisPrimaryEditSheet";
import DiagnosisSecondaryEditSheet from "./DiagnosisSecondaryEditSheet";
import "../design-system/RnicaTailwind.css";

// "Diagnosis & LCD" screen, presentation-only pass applying the approved
// Pain/Neuro interaction model (summary cards + chip-based summaries +
// status pills + focused Edit actions, replacing the prior permanently-
// expanded form). The existing RNICA/HOPE Diagnoses module remains the
// data-entry, validation, persistence, audit, and compliance
// infrastructure (unchanged, rendered inside the Edit Sheets via
// `renderDiagnosisStepCards`, or inline below for the LCD Eligibility
// verification surface, which is read-mostly and not hidden behind an
// Edit action). Every value below is read from `formData.diagnoses` --
// nothing is captured, duplicated, or fabricated here; no field, HOPE
// mapping, or LCD validation logic changes.

const NOT_DOCUMENTED = "Not yet documented";

function Fact({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-rnica-border/50 py-2 last:border-b-0">
      <span className="w-[38%] shrink-0 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">{label}</span>
      <span className="flex-1 text-[12.5px] text-rnica-text">{value || <span className="text-rnica-muted italic">{NOT_DOCUMENTED}</span>}</span>
    </div>
  );
}

function ChipRow({ chips, emptyLabel }) {
  if (!chips.length) {
    return <p className="text-[12.5px] italic text-rnica-muted">{emptyLabel}</p>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {chips.map((chip, i) => (
        <Badge key={i} variant="neutral" className="text-[11px] normal-case">{chip}</Badge>
      ))}
    </div>
  );
}

export default function DiagnosisLcdOverview({
  diagnosesData = {},
  renderDiagnosisStepCards,
  onContinue,
}) {
  const [primaryOpen, setPrimaryOpen] = useState(false);
  const [secondaryOpen, setSecondaryOpen] = useState(false);

  const primary = summarizePrimaryDiagnosis(diagnosesData);
  const secondaryChips = summarizeSecondaryDiagnoses(diagnosesData);
  const comorbidityChips = summarizeComorbidities(diagnosesData);
  const contributingChips = summarizeContributingConditions(diagnosesData);
  const checklist = computeDiagnosisVerificationChecklist(diagnosesData);
  const checklistMetCount = checklist.filter((item) => item.met).length;

  return (
    <div className="rnica-tw grid grid-cols-1 gap-4 lg:grid-cols-[2fr_1fr]">
      <div className="flex flex-col gap-4">
        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <Stethoscope className="h-4 w-4 text-rnica-accent" />
              Primary Terminal Diagnosis
            </CardTitle>
            <div className="flex items-center gap-2">
              {primary.hopeCategoryLabel ? (
                <Badge variant="teal" className="text-[11px]">{primary.hopeCategoryLabel}</Badge>
              ) : (
                <Badge variant="warning" className="text-[11px]">I0010 not selected</Badge>
              )}
              <Button size="sm" variant="outline" onClick={() => setPrimaryOpen(true)}>Edit</Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <Fact label="Diagnosis" value={[primary.description, primary.icd10 && `(${primary.icd10})`].filter(Boolean).join(" ")} />
            <Fact label="Onset Date" value={primary.onsetDate} />
            <Fact label="Terminal Prognosis" value={primary.terminalPrognosis} />
          </CardContent>
        </Card>

        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <ListChecks className="h-4 w-4 text-rnica-accent" />
              LCD Eligibility & Supporting Evidence
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {/* Live compliance/validation surface -- not editable "data
                entry" in the Pain-sheet sense, so it is never hidden
                behind an Edit action. Renders the exact same
                LcdEligibilityCard + LcdSupportingEvidenceCard the legacy
                screen used, unchanged. */}
            {renderDiagnosisStepCards(["LCD Eligibility", "LCD Supporting Evidence"])}
          </CardContent>
        </Card>

        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <Users className="h-4 w-4 text-rnica-accent" />
              Secondary Diagnoses & Comorbidities
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="neutral" className="text-[11px]">{secondaryChips.length} secondary</Badge>
              <Badge variant="neutral" className="text-[11px]">{comorbidityChips.length} comorbidities</Badge>
              <Badge variant="neutral" className="text-[11px]">{contributingChips.length} contributing</Badge>
              <Button size="sm" variant="outline" onClick={() => setSecondaryOpen(true)}>Edit</Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0 flex flex-col gap-3">
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">Secondary Diagnoses</div>
              <ChipRow chips={secondaryChips} emptyLabel="No secondary diagnoses added yet." />
            </div>
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">Comorbidities (HOPE I0100-I8005)</div>
              <ChipRow chips={comorbidityChips} emptyLabel="No comorbidities selected yet." />
            </div>
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-rnica-muted">Contributing Conditions</div>
              <ChipRow chips={contributingChips} emptyLabel="No contributing conditions documented. This is valid." />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-4">
        <Card className="border-rnica-border bg-rnica-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2 text-[15px]">
              <FileCheck2 className="h-4 w-4 text-rnica-accent" />
              Final Verification
            </CardTitle>
            <Badge variant={checklistMetCount === checklist.length ? "success" : "warning"} className="text-[11px]">
              {checklistMetCount}/{checklist.length}
            </Badge>
          </CardHeader>
          <CardContent className="flex flex-col gap-0 pt-0">
            {checklist.map((item, i) => (
              <div
                key={item.label}
                className={`flex items-center gap-2 py-1.5 ${i < checklist.length - 1 ? "border-b border-rnica-border/50" : ""}`}
              >
                {item.met ? (
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-rnica-green" />
                ) : (
                  <Circle className="h-3.5 w-3.5 shrink-0 text-rnica-muted" />
                )}
                <span className={`text-[12px] ${item.met ? "text-rnica-text" : "text-rnica-muted"}`}>{item.label}</span>
              </div>
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

      <DiagnosisPrimaryEditSheet
        open={primaryOpen}
        onOpenChange={setPrimaryOpen}
        renderDiagnosisStepCards={renderDiagnosisStepCards}
      />
      <DiagnosisSecondaryEditSheet
        open={secondaryOpen}
        onOpenChange={setSecondaryOpen}
        renderDiagnosisStepCards={renderDiagnosisStepCards}
      />
    </div>
  );
}
