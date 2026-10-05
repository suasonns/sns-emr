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

// Owner directive (Edit Pain Assessment restructure), Section 8 --
// "Pain Management must use a separate action." Edit Regimen opens its
// own focused Sheet (scheduled/breakthrough regimen, adjuvant/non-
// pharmacological interventions, effectiveness, notes), entirely
// separate from Edit Pain Assessment's four-step entry workflow, so the
// two actions never duplicate each other's content. Renders through the
// same renderPainStepCards("Pain Management") call as every other
// field in this module -- same fields, paths, HOPE mappings, validation,
// and update() autosave contract.
export default function PainManagementEditSheet({ open, onOpenChange, renderPainStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Pain Management Regimen</SheetTitle>
          <SheetDescription>Scheduled and breakthrough medication, non-pharmacological interventions, and effectiveness.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderPainStepCards(["Pain Management"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
