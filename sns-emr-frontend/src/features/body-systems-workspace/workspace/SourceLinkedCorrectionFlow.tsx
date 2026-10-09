/**
 * SNS Body Systems Workspace — source-linked correction flow (SCAFFOLD ONLY).
 *
 * Phase 1 scope explicitly stops here: this component only opens a
 * correction on the owning system (via the canonical state machine's
 * `openCorrection` transition, REVIEWED_WITH_EXCEPTION -> IN_PROGRESS) and
 * navigates the clinician back to the source entry. It does not render a
 * correction form, does not collect a replacement finding, and does not
 * persist anything — that is explicitly deferred to a later phase.
 */
import * as React from "react";
import { Button } from "../../../components/ui/button";
import type { ReviewException } from "../../../domain/body-systems";

export interface SourceLinkedCorrectionFlowProps {
  exception: ReviewException;
  onOpenCorrection: (system: ReviewException["system"]) => void;
}

export function SourceLinkedCorrectionFlow({ exception, onOpenCorrection }: SourceLinkedCorrectionFlowProps) {
  return (
    <Button
      size="sm"
      variant="ghost"
      onClick={() => onOpenCorrection(exception.system)}
      title="Opens a correction on the source system. Phase 2 will add the correction form; this scaffold only transitions review state and navigates back to source."
    >
      Correct at source
    </Button>
  );
}
