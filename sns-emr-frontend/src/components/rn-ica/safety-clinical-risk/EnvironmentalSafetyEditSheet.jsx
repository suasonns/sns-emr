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
// directive). Edit Environmental Safety opens its own focused Sheet --
// Place of Service-driven Home/Facility hazard checklist plus the
// required Staff Visit Safety section -- entirely separate from the
// other 3 Safety assessments. Renders through the same
// renderSafetyStepCards("Environmental Safety") call as every other
// field in this module -- same fields, paths, HOPE mappings,
// validation, and update() autosave contract (EnvironmentalSafetyCard
// in RNICA.jsx is unchanged, just now reached only through this Sheet).
export default function EnvironmentalSafetyEditSheet({ open, onOpenChange, renderSafetyStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Environmental Safety Assessment</SheetTitle>
          <SheetDescription>Home or facility hazard checklist (driven by Site of Service) and required Staff Visit Safety.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderSafetyStepCards(["Environmental Safety"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
