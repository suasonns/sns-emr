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
// (presentation-only). Edit Primary Diagnosis opens its own focused Sheet
// -- the diagnosis search, HOPE I0010 category, onset date, and terminal
// prognosis -- entirely separate from Edit Secondary & Comorbidities.
// Renders through the same renderDiagnosisStepCards("Primary Terminal
// Diagnosis") call as every other field in this module -- same fields,
// paths, HOPE mappings, validation, and update() autosave contract.
export default function DiagnosisPrimaryEditSheet({ open, onOpenChange, renderDiagnosisStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Primary Terminal Diagnosis</SheetTitle>
          <SheetDescription>ICD-10 diagnosis, HOPE Principal Diagnosis Category (I0010), onset date, and terminal prognosis.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderDiagnosisStepCards(["Primary Terminal Diagnosis"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
