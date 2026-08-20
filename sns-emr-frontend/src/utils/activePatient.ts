/**
 * Resolves which patient the clinical pages should load.
 *
 * Order: ?patientId= in the URL, then the last patient selected in this
 * browser, then VITE_DEFAULT_PATIENT_ID for local development. Returns null
 * when none apply so pages can show an explicit "no patient selected" state
 * instead of silently loading someone.
 */

const ACTIVE_PATIENT_KEY = "sns-hospice-solutions-active-patient";

export function getActivePatientId(): string | null {
  if (typeof window !== "undefined") {
    const fromUrl = new URLSearchParams(window.location.search).get("patientId");
    if (fromUrl) return fromUrl;

    const stored = window.sessionStorage.getItem(ACTIVE_PATIENT_KEY);
    if (stored) return stored;
  }

  return import.meta.env.VITE_DEFAULT_PATIENT_ID ?? null;
}

export function setActivePatientId(patientId: string): void {
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem(ACTIVE_PATIENT_KEY, patientId);
  }
}

export function clearActivePatientId(): void {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(ACTIVE_PATIENT_KEY);
  }
}
