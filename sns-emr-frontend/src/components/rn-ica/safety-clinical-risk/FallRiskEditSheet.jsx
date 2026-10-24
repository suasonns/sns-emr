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
// directive). Edit Fall Risk opens the Morse Fall Scale (6 factors,
// score, classification, trend) plus the existing Transfer Safety
// level -- the SAME card title ("Fall Risk and Transfer Safety") and
// SAME renderSafetyStepCards call every other field in this module
// uses; the Morse scoring table/thresholds are owned exclusively by
// RNICA.jsx's FallRiskCard (never duplicated here -- "do not build a
// new fall engine").
export default function FallRiskEditSheet({ open, onOpenChange, renderSafetyStepCards }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl">
        <SheetHeader className="shrink-0">
          <SheetTitle>Edit Fall Risk Assessment</SheetTitle>
          <SheetDescription>Morse Fall Scale (6 factors, score, classification, trend) and Transfer Safety.</SheetDescription>
        </SheetHeader>
        <Separator className="shrink-0" />
        <div className="rnica-tw min-h-0 flex-1 overflow-y-auto py-3 pr-1">
          {renderSafetyStepCards(["Fall Risk and Transfer Safety"])}
        </div>
        <Separator className="shrink-0" />
        <SheetFooter className="shrink-0">
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
