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
  type RespiratoryAssessmentDTO,
} from "../../../api/bodySystems";
import {
  mapRespiratoryOverviewToSituation,
  buildRespiratoryExceptions,
  type RespiratoryAssessmentValues,
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
  updateDraft: (patch: Partial<RespiratoryDraft>) => void;
  saveState: RespiratorySaveState;
  saveError: string | null;
  save: () => Promise<void>;
  reload: () => Promise<void>;
}

export function useRespiratoryAssessment(patientId: string): UseRespiratoryAssessmentResult {
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
      const result = await getRespiratoryAssessment(patientId);
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
  }, [patientId]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setLoadState("loading");
      try {
        const result = await getRespiratoryAssessment(patientId);
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
  }, [patientId]);

  const updateDraft = useCallback((patch: Partial<RespiratoryDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
  }, []);

  const situation: AssessmentSituation | null = draft.respiratoryOverview
    ? mapRespiratoryOverviewToSituation(draft.respiratoryOverview)
    : null;

  const save = useCallback(async () => {
    if (!assessment || !situation) {
      return;
    }
    setSaveState("saving");
    setSaveError(null);
    const exceptions = buildRespiratoryExceptions(assessment.bodySystemsAssessmentId, situation, draft);
    const reviewState = exceptions.some((exception) => exception.blockingLevel === "record_blocking")
      ? "reviewed_with_exception"
      : "reviewed";
    try {
      const saved = await saveRespiratoryDraft(patientId, {
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
      } else {
        setSaveState("error");
        setSaveError("Save failed. Check your connection and try again.");
      }
    }
  }, [assessment, draft, patientId, situation]);

  return { loadState, assessment, draft, situation, updateDraft, saveState, saveError, save, reload };
}
