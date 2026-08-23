import axios from "axios";
import api from "./client";

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

// Shared "Continuous Care (CC) hourly narrative" form -- used by RN, LVN,
// AIDE (CHHA), MSW, and Chaplain visits whenever a patient's care level is
// Continuous Care. See app.domain.forms.form_registry
// (PRIMARY_CC_HOURLY_NARRATIVE / MOD_CC_ENTRY) on the backend.
export type CCHourlyNarrativeEntry = {
  id: string;
  visit_id: string;
  discipline: string;
  entry_date: string | null;
  entry_time: string | null;
  temperature: string | null;
  pulse: string | null;
  respirations: string | null;
  bp_systolic: string | null;
  bp_diastolic: string | null;
  o2_sat: string | null;
  pain_level: string | null;
  pain_location: string | null;
  pain_intervention: string | null;
  symptoms: string | null;
  care_provided: string | null;
  issue_identified: boolean;
  issue_narrative: string | null;
  poc_update_narrative: string | null;
  narrative: string | null;
  entered_by: string | null;
  created_at: string;
};

export type CCHourlyNarrativeEntryPayload = {
  discipline: string;
  entry_date?: string | null;
  entry_time?: string | null;
  temperature?: string | null;
  pulse?: string | null;
  respirations?: string | null;
  bp_systolic?: string | null;
  bp_diastolic?: string | null;
  o2_sat?: string | null;
  pain_level?: string | null;
  pain_location?: string | null;
  pain_intervention?: string | null;
  symptoms?: string | null;
  care_provided?: string | null;
  issue_identified?: boolean;
  issue_narrative?: string | null;
  poc_update_narrative?: string | null;
  narrative?: string | null;
  entered_by?: string | null;
};

export async function listCcHourlyNarrativeEntries(visitId: string): Promise<CCHourlyNarrativeEntry[]> {
  return unwrap(api.get(`/visits/${visitId}/cc-entries`), "Unable to load this visit's continuous care log");
}

export async function createCcHourlyNarrativeEntry(
  visitId: string,
  payload: CCHourlyNarrativeEntryPayload
): Promise<CCHourlyNarrativeEntry> {
  return unwrap(api.post(`/visits/${visitId}/cc-entries`, payload), "Unable to save this continuous care log entry");
}

export async function deleteCcHourlyNarrativeEntry(visitId: string, entryId: string): Promise<void> {
  return unwrap(api.delete(`/visits/${visitId}/cc-entries/${entryId}`), "Unable to remove this continuous care log entry");
}
