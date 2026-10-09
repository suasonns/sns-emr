/**
 * SNS Body Systems Workspace — Review By Exception drawer.
 *
 * This is the review *framework*, not a second assessment. Every exception
 * links back to its source system/field rather than duplicating
 * documentation — resolving an exception here means navigating to the
 * source entry (via SourceLinkedCorrectionFlow) and correcting it there.
 * This drawer never collects a duplicate finding or a duplicate review.
 */
import * as React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "../../../components/ui/sheet";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { BODY_SYSTEM_LABELS, type ReviewException } from "../../../domain/body-systems";
import { SourceLinkedCorrectionFlow } from "./SourceLinkedCorrectionFlow";

export interface ReviewExceptionDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  exceptions: ReviewException[];
  onNavigateToSystem: (system: ReviewException["system"]) => void;
  onOpenCorrection: (system: ReviewException["system"]) => void;
}

const BLOCKING_LEVEL_VARIANT: Record<ReviewException["blockingLevel"], "neutral" | "warning" | "critical"> = {
  informational: "neutral",
  draft_allowed: "neutral",
  record_blocking: "warning",
  signature_blocking: "critical",
};

export function ReviewExceptionDrawer({
  open,
  onOpenChange,
  exceptions,
  onNavigateToSystem,
  onOpenCorrection,
}: ReviewExceptionDrawerProps) {
  const openExceptions = exceptions.filter((exception) => exception.status === "open");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>Review by exception</SheetTitle>
          <SheetDescription>
            Gaps, partial scope, and unresolved items across all ten systems. Resolving an exception corrects the
            source entry — it never creates a second assessment.
          </SheetDescription>
        </SheetHeader>

        {openExceptions.length === 0 ? (
          <p className="text-[12px] text-rnica-muted">No open exceptions.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {openExceptions.map((exception) => (
              <li key={exception.id} className="rounded-lg border border-rnica-border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12px] font-semibold text-rnica-textStrong">
                    {BODY_SYSTEM_LABELS[exception.system]}
                  </span>
                  <Badge variant={BLOCKING_LEVEL_VARIANT[exception.blockingLevel]}>
                    {exception.blockingLevel.replaceAll("_", " ")}
                  </Badge>
                </div>
                <p className="mt-1 text-[12px] text-rnica-muted">{exception.message}</p>
                <div className="mt-2 flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => onNavigateToSystem(exception.system)}>
                    Go to system
                  </Button>
                  <SourceLinkedCorrectionFlow exception={exception} onOpenCorrection={onOpenCorrection} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </SheetContent>
    </Sheet>
  );
}
