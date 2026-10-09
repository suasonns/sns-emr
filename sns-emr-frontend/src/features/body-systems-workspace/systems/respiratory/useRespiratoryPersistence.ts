/**
 * SNS Body Systems Workspace — Respiratory persistence hook.
 *
 * Wraps the thin API client (`src/api/bodySystems.ts`) with the loading/
 * saving state machine the Respiratory panel needs. This is a NEW hook
 * built for the Workspace panel's actual `RespiratoryFieldValues` shape —
 * it does not reuse and is unrelated to the deleted, broken
 * `features/body-systems/components/useRespiratoryAssessment.ts` (which
 * targeted the legacy register-shell panel's different field shape and had
 * a dangling import of an intentionally-excluded module).
 *
 * Situation/exception computation is NOT this hook's job (see
 * body_systems.py route docstring: "Situation classification and exception
 * derivation remain the frontend domain layer's responsibility"). This hook
 * only persists whatever situation/limitation/values/reviewState/exceptions
 * the caller already computed (via `useBodySystemsAssessmentState` /
 * `respiratoryPersistenceMapping.ts`) and reports what happened.
 *
 * Phase F1: `limitation.responsibleClinicianId` and
 * `limitation.timingOrContingency` now have real backend destinations
 * (migration c3b1d9e0f4a7) and are accepted/round-tripped by this hook's
 * generic `save(input)` pass-through like every other limitation field --
 * see respiratoryPersistenceMapping.ts (no remaining
 * BACKEND_DESTINATION_MISSING entries).
 *
 * Known gap: the current GET/PUT endpoints only operate on "the current
 * draft assessment" (find-or-create) and carry no historical/read-only
 * distinction in their response, so a `read_only_historical` status is not
 * reachable from this hook today. If/when the backend adds that
 * distinction, this hook's status union must be extended to cover it
 * rather than inventing a historical mode client-side.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  getRespiratoryAssessment,
  RespiratoryStaleVersionError,
  saveRespiratoryDraft,
  type RespiratoryAssessmentDTO,
  type SaveRespiratoryDraftPayload,
} from "../../../../api/bodySystems";

export type RespiratoryPersistenceStatus =
  | "loading"
  | "no_draft_yet"
  | "draft_loaded"
  | "unsaved"
  | "saving"
  | "saved"
  | "stale_conflict"
  | "validation_error"
  | "auth_error"
  | "network_error";

export type RespiratorySaveInput = Omit<SaveRespiratoryDraftPayload, "expectedVersion">;

export interface UseRespiratoryPersistenceResult {
  status: RespiratoryPersistenceStatus;
  assessment: RespiratoryAssessmentDTO | null;
  errorMessage: string | null;
  /** Re-fetches the current draft from the server, discarding unsaved local changes. */
  reload: () => Promise<void>;
  /** Persists the given fields. Rejects (status becomes stale_conflict) without retrying automatically on 409. */
  save: (input: RespiratorySaveInput) => Promise<void>;
  /** Caller marks local edits as diverged from the last loaded/saved snapshot (e.g. on every field change). No-op while loading/saving. */
  markDirty: () => void;
}

function classifyError(error: unknown): { status: RespiratoryPersistenceStatus; message: string } {
  if (error instanceof RespiratoryStaleVersionError) {
    return { status: "stale_conflict", message: error.message };
  }
  const response = (error as { response?: { status?: number; data?: { detail?: unknown } } })?.response;
  if (response?.status === 422) {
    return { status: "validation_error", message: "The draft could not be saved: one or more fields are invalid." };
  }
  if (response?.status === 401 || response?.status === 403) {
    return { status: "auth_error", message: "You are not authorized to view or save this assessment." };
  }
  if (response?.status === undefined) {
    return { status: "network_error", message: "Could not reach the server. Check your connection and retry." };
  }
  return { status: "network_error", message: "An unexpected error occurred while saving the draft." };
}

export function useRespiratoryPersistence(patientId: string): UseRespiratoryPersistenceResult {
  const [status, setStatus] = useState<RespiratoryPersistenceStatus>("loading");
  const [assessment, setAssessment] = useState<RespiratoryAssessmentDTO | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  // Guards against a load started for a prior patientId resolving after a
  // newer load has already started (stale-response race).
  const loadTokenRef = useRef(0);
  // Tracks the latest loaded/saved assessment so `save` can read the
  // current version without depending on `assessment` itself (the
  // dependency react-compiler can reliably track is `assessmentRef`, a
  // stable ref identity, not the assessment value, which changes on every
  // load/save).
  const assessmentRef = useRef<RespiratoryAssessmentDTO | null>(null);

  const reload = useCallback(async () => {
    const token = ++loadTokenRef.current;
    try {
      const loaded = await getRespiratoryAssessment(patientId);
      if (loadTokenRef.current !== token) return;
      assessmentRef.current = loaded;
      setAssessment(loaded);
      setErrorMessage(null);
      setStatus(loaded.version === 1 && loaded.situation === null && loaded.reviewState === "not_reviewed" ? "no_draft_yet" : "draft_loaded");
    } catch (error) {
      if (loadTokenRef.current !== token) return;
      const { status: nextStatus, message } = classifyError(error);
      setStatus(nextStatus);
      setErrorMessage(message);
    }
  }, [patientId]);

  // Deliberately not `void reload()` here: this inline fetch (rather than
  // calling the memoized `reload` by reference) matches this codebase's
  // established data-fetch-on-mount pattern (see useDashboardAlerts.ts) so
  // the effect synchronizes with the external API on `patientId` change
  // without a lint-visible direct setState call tied to the effect itself.
  // `reload` remains the public, independently re-invokable entry point for
  // the "Reload" retry action.
  useEffect(() => {
    const token = ++loadTokenRef.current;
    getRespiratoryAssessment(patientId)
      .then((loaded) => {
        if (loadTokenRef.current !== token) return;
        assessmentRef.current = loaded;
        setAssessment(loaded);
        setErrorMessage(null);
        setStatus(loaded.version === 1 && loaded.situation === null && loaded.reviewState === "not_reviewed" ? "no_draft_yet" : "draft_loaded");
      })
      .catch((error) => {
        if (loadTokenRef.current !== token) return;
        const { status: nextStatus, message } = classifyError(error);
        setStatus(nextStatus);
        setErrorMessage(message);
      });
  }, [patientId]);

  const markDirty = useCallback(() => {
    setStatus((prev) => (prev === "saving" || prev === "loading" ? prev : "unsaved"));
  }, []);

  const save = useCallback(
    async (input: RespiratorySaveInput) => {
      setStatus("saving");
      setErrorMessage(null);
      try {
        const saved = await saveRespiratoryDraft(patientId, {
          ...input,
          expectedVersion: assessmentRef.current?.version,
        });
        assessmentRef.current = saved;
        setAssessment(saved);
        setStatus("saved");
      } catch (error) {
        const { status: nextStatus, message } = classifyError(error);
        setStatus(nextStatus);
        setErrorMessage(message);
        throw error;
      }
    },
    [patientId],
  );

  return { status, assessment, errorMessage, reload, save, markDirty };
}
