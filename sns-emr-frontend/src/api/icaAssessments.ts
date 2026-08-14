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

export async function updateRnicaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/rnica/${assessmentId}`, { formData }), "RN ICA update failed");
}

export async function lockRnicaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/rnica/${assessmentId}/lock`), "RN ICA lock failed");
}

export async function getRnicaIntelligence(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/intelligence`), "RN ICA intelligence failed");
}

export async function saveMswIcaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/msw-ica/save", payload), "MSW ICA save failed");
}

export async function getMswIcaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/msw-ica/${assessmentId}`), "MSW ICA load failed");
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
