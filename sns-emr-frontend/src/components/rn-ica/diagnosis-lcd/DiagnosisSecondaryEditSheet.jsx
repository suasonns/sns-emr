import React from "react";
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
import "../design-system/RnicaTailwind.css";

// "Pain/Neuro interaction model" directive applied to Diagnosis & LCD
// (presentation-only). Edit Secondary & Comorbidities bundles Secondary
// Diagnoses and HOPE Comorbidities into one focused Sheet (they are
// tightly linked -- adding a secondary diagnosis can auto-detect a
// comorbidity category below), separate from Edit Primary Diagnosis.
// Renders through the same renderDiagnosisStepCards(["Secondary
// Diagnoses", "Comorbidities and Co-existing Conditions"]) call as every
// other field in this module -- same fields, paths, HOPE mappings,
// validation, and update() autosave contract.
export default function DiagnosisSecondaryEditSheet({ open, onOpenChange, renderDiagnosisStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Secondary Diagnoses & Comorbidities</SheetTitle>
          <SheetDescription>Active secondary diagnoses, the HOPE comorbidity/co-existing conditions checklist (I0100-I8005), and manually-documented Contributing Conditions.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderDiagnosisStepCards(["Secondary Diagnoses", "Comorbidities and Co-existing Conditions", "Contributing Conditions"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
