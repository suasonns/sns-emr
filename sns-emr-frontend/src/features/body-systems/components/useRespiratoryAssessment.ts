/**
 * SNS Body Systems — Respiratory assessment data hook.
 *
 * Owns the full lifecycle of editing one patient's current Respiratory
 * `SystemAssessment` draft: load, local edit, save (with optimistic-
 * concurrency conflict handling), and the discrete UI states the
 * Respiratory proof-of-pattern milestone requires. Kept separate from
 * `RespiratoryPanel.tsx` so the panel stays presentational.
 */
import { useCallback, useEffect, useState } from "react";
import {
  getRespiratoryAssessment,
  saveRespiratoryDraft,
  RespiratoryStaleVersionError,
  RespiratoryCompletionRejectedError,
  type RespiratoryAssessmentDTO,
} from "../../../api/bodySystems";
import {
  buildRespiratoryExceptions,
  deriveRespiratorySituation,
  getRespiratoryReviewCompletion,
  type RespiratoryAssessmentValues,
  type RespiratoryReviewCompletionResult,
} from "../../../domain/body-systems/respiratoryWorkflowRules";
import type { AssessmentSituation } from "../../../domain/body-systems";

export type RespiratoryLoadState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "unavailable"
  | "network_error";

export type RespiratorySaveState = "idle" | "saving" | "saved" | "error" | "conflict";

/** `RespiratoryAssessmentValues` plus the raw overview selection, which the
 * situation is derived from but which the field itself still needs to be
 * rendered/edited as its own controlled value. */
export interface RespiratoryDraft extends RespiratoryAssessmentValues {
  respiratoryOverview?: string;
}

const EMPTY_DRAFT: RespiratoryDraft = {};

function draftFromServerData(data: Record<string, unknown>): RespiratoryDraft {
  return { ...EMPTY_DRAFT, ...(data as RespiratoryDraft) };
}

export interface UseRespiratoryAssessmentResult {
  loadState: RespiratoryLoadState;
  assessment: RespiratoryAssessmentDTO | null;
  draft: RespiratoryDraft;
  situation: AssessmentSituation | null;
  completion: RespiratoryReviewCompletionResult;
  updateDraft: (patch: Partial<RespiratoryDraft>) => void;
  saveState: RespiratorySaveState;
  saveError: string | null;
  /** Persists the current draft as-is. Always available (Contract v2: draft save is never gated on any field, including situation/completion). Leaves the system in IN_PROGRESS. */
  save: () => Promise<void>;
  /** Explicit, non-gating completion action. Validates `completion.complete` itself -- callers do not need to pre-check it, but should surface `completion.blockingMessages` in the UI so a blocked attempt is never silent. Resolves to REVIEWED/REVIEWED_WITH_EXCEPTION only when the required review groups for the derived situation are satisfied. */
  completeReview: () => Promise<void>;
  reload: () => Promise<void>;
}

export function useRespiratoryAssessment(assessmentId: string): UseRespiratoryAssessmentResult {
  const [loadState, setLoadState] = useState<RespiratoryLoadState>("loading");
  const [assessment, setAssessment] = useState<RespiratoryAssessmentDTO | null>(null);
  const [draft, setDraft] = useState<RespiratoryDraft>(EMPTY_DRAFT);
  const [saveState, setSaveState] = useState<RespiratorySaveState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  // `reload` is exposed for a user-triggered retry (button click), so it is
  // defined via `useCallback` and may freely call setState when invoked.
  // The initial mount load below is intentionally a *separate*, effect-local
  // async closure rather than a call to this memoized function -- calling a
  // `useCallback`-identity function from inside `useEffect` trips this
  // repository's `react-hooks/set-state-in-effect` lint rule, while an
  // effect-local closure (the same shape already used by
  // `src/hooks/useDashboardAlerts.ts`) does not.
  const reload = useCallback(async () => {
    setLoadState("loading");
    try {
      const result = await getRespiratoryAssessment(assessmentId);
      setAssessment(result);
      setDraft(draftFromServerData(result.data));
      setLoadState("loaded");
      setSaveState("idle");
      setSaveError(null);
    } catch (error) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 401 || status === 403) {
        setLoadState("unauthorized");
      } else if (status === 404) {
        setLoadState("unavailable");
      } else {
        setLoadState("network_error");
      }
    }
  }, [assessmentId]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setLoadState("loading");
      try {
        const result = await getRespiratoryAssessment(assessmentId);
        if (cancelled) return;
        setAssessment(result);
        setDraft(draftFromServerData(result.data));
        setLoadState("loaded");
        setSaveState("idle");
        setSaveError(null);
      } catch (error) {
        if (cancelled) return;
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 401 || status === 403) {
          setLoadState("unauthorized");
        } else if (status === 404) {
          setLoadState("unavailable");
        } else {
          setLoadState("network_error");
        }
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  const updateDraft = useCallback((patch: Partial<RespiratoryDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
  }, []);

  const situation: AssessmentSituation | null = deriveRespiratorySituation(draft);
  const completion = getRespiratoryReviewCompletion(draft);

  /**
   * Draft save. Deliberately NEVER gated on `situation`/completion — Contract
   * v2 requires draft save to always be available. Persists whatever is
   * currently entered and leaves the system IN_PROGRESS; it never promotes
   * the review state to REVIEWED/REVIEWED_WITH_EXCEPTION on its own (only
   * `completeReview` does that), so a half-finished draft can never be
   * silently reported as a completed review.
   */
  const save = useCallback(async () => {
    if (!assessment) {
      return;
    }
    setSaveState("saving");
    setSaveError(null);
    try {
      const saved = await saveRespiratoryDraft(assessmentId, {
        situation,
        data: { ...draft } as Record<string, unknown>,
        reviewState: "in_progress",
        reviewExceptions: [],
        expectedVersion: assessment.version,
      });
      setAssessment(saved);
      setDraft(draftFromServerData(saved.data));
      setSaveState("saved");
    } catch (error) {
      if (error instanceof RespiratoryStaleVersionError) {
        setSaveState("conflict");
        setSaveError(error.message);
      } else {
        setSaveState("error");
        setSaveError("Save failed. Check your connection and try again.");
      }
    }
  }, [assessment, draft, assessmentId, situation]);

  /**
   * Explicit "Complete system review" action. Re-validates completion
   * itself (never trusts a stale caller-side check) using the SAME
   * requirement engine the draft/record-blocking exceptions come from, so
   * the completion gate and the exception list can never disagree.
   */
  const completeReview = useCallback(async () => {
    if (!assessment || !situation || !completion.complete) {
      return;
    }
    setSaveState("saving");
    setSaveError(null);
    const exceptions = buildRespiratoryExceptions(assessment.bodySystemsAssessmentId, situation, draft);
    const reviewState = exceptions.some((exception) => exception.blockingLevel === "record_blocking")
      ? "reviewed_with_exception"
      : "reviewed";
    try {
      const saved = await saveRespiratoryDraft(assessmentId, {
        situation,
        data: { ...draft } as Record<string, unknown>,
        reviewState,
        reviewExceptions: exceptions.map((exception) => ({
          type: exception.type,
          message: exception.message,
          blockingLevel: exception.blockingLevel,
          fieldPath: exception.fieldPath,
        })),
        expectedVersion: assessment.version,
      });
      setAssessment(saved);
      setDraft(draftFromServerData(saved.data));
      setSaveState("saved");
    } catch (error) {
      if (error instanceof RespiratoryStaleVersionError) {
        setSaveState("conflict");
        setSaveError(error.message);
      } else if (error instanceof RespiratoryCompletionRejectedError) {
        // Server-side anti-forgery rejected completion even though the
        // client's own check passed — surface the server's exact reason so
        // the two are never silently out of sync.
        setSaveState("error");
        setSaveError(error.message);
      } else {
        setSaveState("error");
        setSaveError("Save failed. Check your connection and try again.");
      }
    }
  }, [assessment, completion.complete, draft, assessmentId, situation]);

  return {
    loadState,
    assessment,
    draft,
    situation,
    completion,
    updateDraft,
    saveState,
    saveError,
    save,
    completeReview,
    reload,
  };
}
