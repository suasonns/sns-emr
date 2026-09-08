import { useCallback, useEffect, useRef } from "react";

type AssessmentId = string | null | undefined;

type AutosaveCreateResult = {
  assessmentId?: string | null;
} | null | undefined;

type UseAssessmentAutosaveParams<T> = {
  formData: T;
  assessmentId: AssessmentId;
  setAssessmentId?: (assessmentId: string) => void;
  locked: boolean;
  saving: boolean;
  saveFn: (patientId: string, formData: T) => Promise<AutosaveCreateResult>;
  updateFn: (assessmentId: string, formData: T) => Promise<unknown>;
  patientId?: string;
  intervalMs?: number;
};

type ResetAutosaveTrackingOptions<T> = {
  markCurrentAsPersisted?: boolean;
  persistedFormData?: T;
  persistedAssessmentId?: AssessmentId;
};

function serializeFormData(value: unknown) {
  try {
    return JSON.stringify(value);
  } catch (error) {
    console.warn("[assessment-autosave] Unable to serialize form data.", error);
    return "";
  }
}

export function useAssessmentAutosave<T>({
  formData,
  assessmentId,
  setAssessmentId,
  locked,
  saving,
  saveFn,
  updateFn,
  patientId,
  intervalMs = 30000,
}: UseAssessmentAutosaveParams<T>) {
  const formDataRef = useRef(formData);
  const assessmentIdRef = useRef<AssessmentId>(assessmentId);
  const lockedRef = useRef(locked);
  const savingRef = useRef(saving);
  const patientIdRef = useRef(patientId);
  const saveFnRef = useRef(saveFn);
  const updateFnRef = useRef(updateFn);
  const setAssessmentIdRef = useRef(setAssessmentId);
  const autosavingRef = useRef(false);
  const lastPersistedPayloadRef = useRef<string | null>(null);
  const lastPersistedAssessmentIdRef = useRef<string | null>(null);

  // Refs must not be written during the render body (React may invoke it
  // more than once, e.g. under StrictMode/concurrent rendering); sync them
  // in an effect that runs after every render instead.
  useEffect(() => {
    formDataRef.current = formData;
    assessmentIdRef.current = assessmentId;
    lockedRef.current = locked;
    savingRef.current = saving;
    patientIdRef.current = patientId;
    saveFnRef.current = saveFn;
    updateFnRef.current = updateFn;
    setAssessmentIdRef.current = setAssessmentId;
  });

  const markPersisted = useCallback((persistedFormData: T, persistedAssessmentId?: AssessmentId) => {
    lastPersistedPayloadRef.current = serializeFormData(persistedFormData);
    lastPersistedAssessmentIdRef.current = persistedAssessmentId ?? null;
  }, []);

  const resetAutosaveTracking = useCallback((options: ResetAutosaveTrackingOptions<T> = {}) => {
    autosavingRef.current = false;
    if (!options.markCurrentAsPersisted) {
      lastPersistedPayloadRef.current = null;
      lastPersistedAssessmentIdRef.current = null;
      return;
    }

    const nextFormData = options.persistedFormData ?? formDataRef.current;
    const nextAssessmentId = options.persistedAssessmentId ?? assessmentIdRef.current;
    lastPersistedPayloadRef.current = serializeFormData(nextFormData);
    lastPersistedAssessmentIdRef.current = nextAssessmentId ?? null;
  }, []);

  // Shared save logic used by both the background interval tick and
  // saveNow() (an explicit, user-triggered "save right now" call — e.g.
  // from the clinical narrative card, which requires a real
  // assessmentId to exist before it can request a V2 narrative preview).
  // Unlike the interval tick, saveNow() lets the caller await the result
  // and see/handle a thrown error directly, instead of only logging it.
  const runAutosave = useCallback(async (): Promise<{ assessmentId: string | null; skipped: boolean }> => {
    const currentPatientId = patientIdRef.current;
    if (!currentPatientId || lockedRef.current || savingRef.current || autosavingRef.current) {
      return { assessmentId: assessmentIdRef.current ?? null, skipped: true };
    }

    const currentFormData = formDataRef.current;
    const serializedFormData = serializeFormData(currentFormData);
    const currentAssessmentId = assessmentIdRef.current ?? null;

    if (
      currentAssessmentId
      && lastPersistedPayloadRef.current === serializedFormData
      && lastPersistedAssessmentIdRef.current === currentAssessmentId
    ) {
      return { assessmentId: currentAssessmentId, skipped: true };
    }

    autosavingRef.current = true;
    try {
      let nextAssessmentId = currentAssessmentId;
      if (nextAssessmentId) {
        await updateFnRef.current(nextAssessmentId, currentFormData);
      } else {
        const result = await saveFnRef.current(currentPatientId, currentFormData);
        nextAssessmentId = result?.assessmentId ?? null;
        if (!nextAssessmentId) {
          throw new Error("Autosave create did not return an assessmentId.");
        }
        setAssessmentIdRef.current?.(nextAssessmentId);
      }

      lastPersistedPayloadRef.current = serializedFormData;
      lastPersistedAssessmentIdRef.current = nextAssessmentId;
      console.info(`[assessment-autosave] Saved assessment ${nextAssessmentId} for patient ${currentPatientId}.`);
      return { assessmentId: nextAssessmentId, skipped: false };
    } finally {
      autosavingRef.current = false;
    }
  }, []);

  const saveNow = useCallback(async () => {
    return runAutosave();
  }, [runAutosave]);

  useEffect(() => {
    if (!intervalMs || intervalMs <= 0) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      runAutosave().catch((error) => {
        console.warn("[assessment-autosave] Background save failed.", error);
      });
    }, intervalMs);

    return () => {
      autosavingRef.current = false;
      window.clearInterval(timer);
    };
  }, [intervalMs, patientId, runAutosave]);

  return {
    markPersisted,
    resetAutosaveTracking,
    saveNow,
  };
}
