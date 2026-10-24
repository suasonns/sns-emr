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

// "Replace the Inline Safety Page With Four Guided Assessments" (final
// directive). Edit Oxygen Safety opens the single pill-group concern
// checklist (shown only when oxygen is in use). Renders through the
// same renderSafetyStepCards("Oxygen Safety") call as every other field
// in this module -- OxygenSafetyCard in RNICA.jsx is unchanged.
export default function OxygenSafetyEditSheet({ open, onOpenChange, renderSafetyStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Oxygen Safety Assessment</SheetTitle>
          <SheetDescription>Shown only when the patient is on oxygen; otherwise this assessment is Not Applicable.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderSafetyStepCards(["Oxygen Safety"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
