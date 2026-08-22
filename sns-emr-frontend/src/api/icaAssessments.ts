import axios from "axios";
import api from "./client";

type AssessmentPayload = {
  patientId?: string;
  formData: Record<string, unknown>;
};

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            const msg = item.msg;
            return typeof msg === "string" ? msg : "";
          }
          return "";
        })
        .filter(Boolean)
        .join(", ");
    }
    if (error.message) {
      return `${fallback}: ${error.message}`;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

async function unwrap<T>(promise: Promise<{ data: T }>, fallback: string): Promise<T> {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, fallback));
  }
}

export async function saveRnicaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/rnica/save", payload), "RN ICA save failed");
}

export async function getRnicaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}`), "RN ICA load failed");
}

export async function getRnicaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/rnica/by-patient/${patientId}`), "RN ICA lookup failed");
}

export async function updateRnicaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/rnica/${assessmentId}`, { formData }), "RN ICA update failed");
}

export async function lockRnicaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/rnica/${assessmentId}/lock`), "RN ICA lock failed");
}

export async function getRnicaIntelligence(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/intelligence`), "RN ICA intelligence failed");
}

// SECTION 12 — Final Review Dashboard data source. Single source of truth
// shared with the backend lock endpoint, so the UI's Lock button and the
// server's lock gate can never disagree.
export async function getRnicaFinalizationReadiness(assessmentId: string) {
  return unwrap(
    api.get(`/visits/rnica/${assessmentId}/finalization-readiness`),
    "Unable to load Section 12 finalization readiness"
  );
}

// SECTION 12 — future correction/amendment entry point (stub). Only
// reachable once an assessment is locked; the backend intentionally
// responds 501 today (see app/api/visits.py) until the full traceable
// addendum workflow is built.
export async function requestRnicaCorrection(assessmentId: string) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/correction-request`),
    "Correction/amendment request failed"
  );
}

// --- RN ICA -> Plan of Care (Add / View / Update / Resolve per body-system
// section). These call the authoritative Plan of Care document API via the
// backend adapter in app/services/rnica_poc_adapter.py — there is no
// separate/duplicate POC store on either side. ---

export async function viewRnicaSectionPoc(assessmentId: string, sectionKey: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/poc/${sectionKey}`), "Unable to load Plan of Care for this section");
}

// SECTION 11 — Master Plan of Care Review: cross-section, read-oriented
// synchronization view over the same authoritative poc_problems rows.
// Never creates problems; only views/edits/resolves/deactivates existing ones.
export async function viewRnicaAllPoc(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/poc`), "Unable to load Plan of Care");
}

export async function deactivateRnicaSectionPocProblem(assessmentId: string, sectionKey: string, ruleKey: string) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}/deactivate`),
    "Unable to deactivate Plan of Care problem",
  );
}

export async function addRnicaSectionPocProblem(
  assessmentId: string,
  sectionKey: string,
  payload: {
    problem_label: string;
    evidence_text: string;
    goal_text?: string;
    intervention_text?: string;
    discipline?: string;
  },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}`, payload),
    "Unable to add problem to Plan of Care",
  );
}

export async function updateRnicaSectionPocProblem(
  assessmentId: string,
  sectionKey: string,
  ruleKey: string,
  payload: { label?: string; description_addendum?: string; severity?: string },
) {
  return unwrap(
    api.put(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}`, payload),
    "Unable to update Plan of Care problem",
  );
}

export async function resolveRnicaSectionPocProblem(assessmentId: string, sectionKey: string, ruleKey: string) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}/resolve`),
    "Unable to resolve Plan of Care problem",
  );
}

export async function saveMswIcaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/msw-ica/save", payload), "MSW ICA save failed");
}

export async function getMswIcaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/msw-ica/${assessmentId}`), "MSW ICA load failed");
}

export async function getMswIcaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/msw-ica/by-patient/${patientId}`), "MSW ICA lookup failed");
}

export async function updateMswIcaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/msw-ica/${assessmentId}`, { formData }), "MSW ICA update failed");
}

export async function lockMswIcaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/msw-ica/${assessmentId}/lock`), "MSW ICA lock failed");
}

export async function getMswIcaIntelligence(assessmentId: string) {
  return unwrap(api.get(`/visits/msw-ica/${assessmentId}/intelligence`), "MSW ICA intelligence failed");
}


export async function saveScicaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/scica/save", payload), "SCICA save failed");
}

export async function getScicaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/scica/${assessmentId}`), "SCICA load failed");
}

export async function getScicaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/scica/by-patient/${patientId}`), "SCICA lookup failed");
}

export async function updateScicaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/scica/${assessmentId}`, { formData }), "SCICA update failed");
}

export async function lockScicaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/scica/${assessmentId}/lock`), "SCICA lock failed");
}
