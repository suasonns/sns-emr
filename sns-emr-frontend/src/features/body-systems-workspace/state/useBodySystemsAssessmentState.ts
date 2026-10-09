/**
 * SNS Body Systems Workspace — in-memory assessment orchestration state.
 *
 * This hook is pure orchestration: it holds per-system review state,
 * situation, limitation, and exceptions, and drives every transition
 * through the canonical domain state machine / exception rules in
 * `src/domain/body-systems`. It does not implement any new clinical
 * business rule, does not persist anything, and does not call any API —
 * Phase 1 scope is architecture only (see
 * SNS_Body_Systems_Engineering_Specification.md and the Phase 1 approval
 * thread). Persistence/API wiring is explicitly deferred to a later phase.
 */
import { useCallback, useMemo, useState } from "react";
import {
  BODY_SYSTEMS,
  type AssessmentLimitation,
  type AssessmentSituation,
  type BodySystemCode,
  type Evidence,
  type ReviewException,
  type SystemReviewState,
  buildMissingLimitationException,
  buildUnreviewedSystemException,
  canRecordReview,
  canSaveDraft,
  canSign,
  getMissingSituationRequirements,
  getOpenExceptions,
  nextReviewStateAfterReview,
  openCorrection as domainOpenCorrection,
  reopenReviewed as domainReopenReviewed,
} from "../../../domain/body-systems";

export interface SystemWorkingState {
  system: BodySystemCode;
  reviewState: SystemReviewState;
  situation?: AssessmentSituation;
  limitation?: AssessmentLimitation;
  currentEvidence: Evidence[];
  historicalEvidence: Evidence[];
  satisfiedRequirementKeys: string[];
}

function createInitialSystemState(system: BodySystemCode): SystemWorkingState {
  return {
    system,
    reviewState: "not_reviewed",
    situation: undefined,
    limitation: undefined,
    currentEvidence: [],
    historicalEvidence: [],
    satisfiedRequirementKeys: [],
  };
}

function createInitialRegistry(): Record<BodySystemCode, SystemWorkingState> {
  const entries = BODY_SYSTEMS.map((system) => [system, createInitialSystemState(system)] as const);
  return Object.fromEntries(entries) as Record<BodySystemCode, SystemWorkingState>;
}

export interface BodySystemsAssessmentCounts {
  notReviewed: number;
  inProgress: number;
  reviewed: number;
  reviewedWithException: number;
}

export interface UseBodySystemsAssessmentStateResult {
  /** Always all ten systems, always in the fixed BODY_SYSTEMS order. Never filtered, never reordered. */
  registryOrder: readonly BodySystemCode[];
  systems: Record<BodySystemCode, SystemWorkingState>;
  exceptions: ReviewException[];
  counts: BodySystemsAssessmentCounts;
  selectedSystem: BodySystemCode;
  selectSystem: (system: BodySystemCode) => void;
  startReview: (system: BodySystemCode) => void;
  setSituation: (system: BodySystemCode, situation: AssessmentSituation) => void;
  setLimitation: (system: BodySystemCode, limitation: AssessmentLimitation) => void;
  addCurrentEvidence: (system: BodySystemCode, evidence: Evidence) => void;
  markRequirementSatisfied: (system: BodySystemCode, requirementKey: string) => void;
  completeReview: (system: BodySystemCode) => void;
  openCorrection: (system: BodySystemCode) => void;
  reopenReviewed: (system: BodySystemCode) => void;
  resolveException: (exceptionId: string, resolutionNote: string) => void;
  missingRequirementsFor: (system: BodySystemCode) => string[];
  canSaveDraft: boolean;
  canRecordReview: boolean;
  canSign: boolean;
}

let exceptionIdCounter = 0;
function nextExceptionId(): string {
  exceptionIdCounter += 1;
  return `exc-${exceptionIdCounter}`;
}

export function useBodySystemsAssessmentState(
  bodySystemsAssessmentId: string,
): UseBodySystemsAssessmentStateResult {
  const [systems, setSystems] = useState<Record<BodySystemCode, SystemWorkingState>>(createInitialRegistry);
  const [exceptions, setExceptions] = useState<ReviewException[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<BodySystemCode>(BODY_SYSTEMS[0]);

  const selectSystem = useCallback((system: BodySystemCode) => {
    setSelectedSystem(system);
  }, []);

  const updateSystem = useCallback(
    (system: BodySystemCode, patch: Partial<SystemWorkingState>) => {
      setSystems((prev) => ({ ...prev, [system]: { ...prev[system], ...patch } }));
    },
    [],
  );

  const startReview = useCallback((system: BodySystemCode) => {
    setSystems((prev) => {
      const current = prev[system];
      if (current.reviewState !== "not_reviewed") return prev;
      return { ...prev, [system]: { ...current, reviewState: "in_progress" } };
    });
  }, []);

  const setSituation = useCallback(
    (system: BodySystemCode, situation: AssessmentSituation) => {
      updateSystem(system, { situation, satisfiedRequirementKeys: [] });
    },
    [updateSystem],
  );

  const setLimitation = useCallback(
    (system: BodySystemCode, limitation: AssessmentLimitation) => {
      updateSystem(system, { limitation });
    },
    [updateSystem],
  );

  const addCurrentEvidence = useCallback((system: BodySystemCode, evidence: Evidence) => {
    setSystems((prev) => ({
      ...prev,
      [system]: { ...prev[system], currentEvidence: [...prev[system].currentEvidence, evidence] },
    }));
  }, []);

  const markRequirementSatisfied = useCallback((system: BodySystemCode, requirementKey: string) => {
    setSystems((prev) => {
      const current = prev[system];
      if (current.satisfiedRequirementKeys.includes(requirementKey)) return prev;
      return {
        ...prev,
        [system]: {
          ...current,
          satisfiedRequirementKeys: [...current.satisfiedRequirementKeys, requirementKey],
        },
      };
    });
  }, []);

  const missingRequirementsFor = useCallback(
    (system: BodySystemCode): string[] => {
      const working = systems[system];
      if (!working.situation) return [];
      return getMissingSituationRequirements(working.situation, working.satisfiedRequirementKeys);
    },
    [systems],
  );

  const completeReview = useCallback(
    (system: BodySystemCode) => {
      const working = systems[system];
      // No situation selected at all is itself an unreviewed system — it must
      // never silently resolve to "reviewed". Historical evidence or a blank
      // situation never satisfies this.
      const missing = working.situation
        ? getMissingSituationRequirements(working.situation, working.satisfiedRequirementKeys)
        : ["situation_not_selected"];

      setExceptions((prevExceptions) => {
        const withoutThisSystemsCompletionExceptions = prevExceptions.filter(
          (exception) =>
            !(
              exception.system === system &&
              (exception.type === "unreviewed_system" || exception.type === "unable_to_assess")
            ),
        );

        if (working.situation === "unable_to_assess" && !working.limitation) {
          return [
            ...withoutThisSystemsCompletionExceptions,
            {
              ...buildMissingLimitationException(bodySystemsAssessmentId, system, "record_blocking"),
              id: nextExceptionId(),
            },
          ];
        }

        if (missing.length > 0) {
          return [
            ...withoutThisSystemsCompletionExceptions,
            {
              ...buildUnreviewedSystemException(bodySystemsAssessmentId, system, "record_blocking"),
              id: nextExceptionId(),
              message: `${system}: missing ${missing.join(", ")}.`,
            },
          ];
        }

        return withoutThisSystemsCompletionExceptions;
      });

      setSystems((prev) => {
        const current = prev[system];
        const hasOpenExceptionsForSystem =
          (current.situation === "unable_to_assess" && !current.limitation) || missing.length > 0;
        const nextState = nextReviewStateAfterReview(current.reviewState, hasOpenExceptionsForSystem);
        return { ...prev, [system]: { ...current, reviewState: nextState } };
      });
    },
    [systems, bodySystemsAssessmentId],
  );

  const openCorrection = useCallback((system: BodySystemCode) => {
    setSystems((prev) => {
      const current = prev[system];
      return { ...prev, [system]: { ...current, reviewState: domainOpenCorrection(current.reviewState) } };
    });
  }, []);

  const reopenReviewed = useCallback((system: BodySystemCode) => {
    setSystems((prev) => {
      const current = prev[system];
      return { ...prev, [system]: { ...current, reviewState: domainReopenReviewed(current.reviewState) } };
    });
  }, []);

  const resolveException = useCallback((exceptionId: string, resolutionNote: string) => {
    setExceptions((prev) =>
      prev.map((exception) =>
        exception.id === exceptionId
          ? { ...exception, status: "resolved", resolvedAt: new Date().toISOString(), resolutionNote }
          : exception,
      ),
    );
  }, []);

  const counts = useMemo<BodySystemsAssessmentCounts>(() => {
    const values = Object.values(systems);
    return {
      notReviewed: values.filter((s) => s.reviewState === "not_reviewed").length,
      inProgress: values.filter((s) => s.reviewState === "in_progress").length,
      reviewed: values.filter((s) => s.reviewState === "reviewed").length,
      reviewedWithException: values.filter((s) => s.reviewState === "reviewed_with_exception").length,
    };
  }, [systems]);

  const openExceptions = useMemo(() => getOpenExceptions(exceptions), [exceptions]);

  return {
    registryOrder: BODY_SYSTEMS,
    systems,
    exceptions,
    counts,
    selectedSystem,
    selectSystem,
    startReview,
    setSituation,
    setLimitation,
    addCurrentEvidence,
    markRequirementSatisfied,
    completeReview,
    openCorrection,
    reopenReviewed,
    resolveException,
    missingRequirementsFor,
    canSaveDraft: canSaveDraft(openExceptions),
    canRecordReview: canRecordReview(openExceptions),
    canSign: canSign(openExceptions),
  };
}
