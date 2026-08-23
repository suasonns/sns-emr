import api from "./client";

export type F2FStatus = "DRAFT" | "FINALIZED";

export type F2FRecord = {
  id: string;
  patient_id: string;
  benefit_period_id: string;
  status: F2FStatus;
  status_label: string;
  encounter_date: string | null;
  performed_by_role: string | null;
  performed_by_name: string | null;
  attesting_provider_name: string | null;
  attested_at: string | null;
  summary: string | null;
  finalized_at: string | null;
};

export type F2FCreateRequest = {
  patient_id: string;
  benefit_period_id: string;
  encounter_date: string;
  summary?: string;
  clinical_decline_summary?: string;
  kps_score?: number;
  pps_score_previous?: number;
  pps_score_current?: number;
  fast_score?: string;
  nyha_class?: string;
  adl_dependency_level?: string;
  adl_dependency_count?: number;
  is_bedbound?: boolean;
  weight_loss_lbs?: number;
  oral_intake_decline?: boolean;
  dysphagia?: boolean;
  hospitalizations_30d?: number;
  oxygen_lpm_previous?: number;
  oxygen_lpm_current?: number;
  primary_diagnosis?: string;
  secondary_conditions?: string;
};

export async function listF2FEncounters(patientId: string): Promise<F2FRecord[]> {
  const response = await api.get<F2FRecord[]>(`/f2f/patients/${patientId}`);
  return response.data || [];
}

export async function createF2FEncounter(payload: F2FCreateRequest) {
  const response = await api.post(`/f2f/`, payload);
  return response.data;
}

export async function finalizeF2FEncounter(f2fId: string, attestationSummary?: string) {
  const response = await api.post(`/f2f/${f2fId}/finalize`, { attestation_summary: attestationSummary });
  return response.data;
}

export async function getF2FStatusHistory(f2fId: string) {
  const response = await api.get(`/f2f/${f2fId}/status-history`);
  return response.data || [];
}
