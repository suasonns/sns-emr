/**
 * SNS Body Systems Workspace — per-system workspace display.
 *
 * Display only: current/historical evidence, ownership/source visibility,
 * exception visibility, and review status for the selected system. No
 * duplicate assessment logic — system-specific fields (Neurological,
 * Respiratory, …) are injected as `children` by BodyShieldShell, not
 * reimplemented here.
 */
import * as React from "react";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { CurrentHistoricalEvidencePanel } from "./CurrentHistoricalEvidencePanel";
import {
  BODY_SYSTEM_LABELS,
  type BodySystemCode,
  type Evidence,
  type ReviewException,
  type SystemReviewState,
} from "../../../domain/body-systems";

export interface BodySystemsWorkspaceProps {
  system: BodySystemCode;
  reviewState: SystemReviewState;
  currentEvidence: Evidence[];
  historicalEvidence: Evidence[];
  exceptions: ReviewException[];
  onStartReview: () => void;
  onCompleteReview: () => void;
  children?: React.ReactNode;
}

const REVIEW_STATE_BADGE_VARIANT: Record<SystemReviewState, "neutral" | "teal" | "success" | "warning"> = {
  not_reviewed: "neutral",
  in_progress: "teal",
  reviewed: "success",
  reviewed_with_exception: "warning",
};

export function BodySystemsWorkspace({
  system,
  reviewState,
  currentEvidence,
  historicalEvidence,
  exceptions,
  onStartReview,
  onCompleteReview,
  children,
}: BodySystemsWorkspaceProps) {
  const systemExceptions = exceptions.filter((exception) => exception.system === system && exception.status === "open");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-[16px] font-semibold text-rnica-textStrong">{BODY_SYSTEM_LABELS[system]}</h2>
        <div className="flex items-center gap-2">
          <Badge variant={REVIEW_STATE_BADGE_VARIANT[reviewState]}>{reviewState.replaceAll("_", " ")}</Badge>
          {reviewState === "not_reviewed" && (
            <Button size="sm" onClick={onStartReview}>
              Start review
            </Button>
          )}
          {reviewState === "in_progress" && (
            <Button size="sm" onClick={onCompleteReview}>
              Complete review
            </Button>
          )}
        </div>
      </div>

      {systemExceptions.length > 0 && (
        <div className="rounded-lg border border-rnica-borderWarning bg-rnica-warningBg p-2.5 text-[12px] text-rnica-orange">
          {systemExceptions.length} open exception(s) for this system. See Review by Exception.
        </div>
      )}

      <CurrentHistoricalEvidencePanel
        currentEvidence={currentEvidence}
        historicalEvidence={historicalEvidence}
        requiresExplicitCurrentReview
      />

      {children}
    </div>
  );
}
