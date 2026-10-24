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
// directive). Edit Disaster Triage opens the Level 1/2/3 segmented
// control and its per-level conditions pill group. Renders through the
// same renderSafetyStepCards("Disaster Triage") call as every other
// field in this module -- DisasterTriageCard in RNICA.jsx is unchanged.
export default function DisasterTriageEditSheet({ open, onOpenChange, renderSafetyStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Disaster Triage Assessment</SheetTitle>
          <SheetDescription>Disaster/emergency triage level and the assistance-need conditions that support it.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderSafetyStepCards(["Disaster Triage"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
