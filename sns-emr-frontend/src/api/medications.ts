import api from "./client";

export type SafetyAlert = {
  severity: string;
  effect?: string;
  management?: string;
  matched_on?: string;
};

export type AllergyAlert = {
  allergen: string;
  severity: string;
  reaction: string | null;
  matched_on: string;
};

export type InteractionAlert = {
  with_medication: string;
  severity: string;
  effect: string;
  management: string;
  matched_on: string;
};

export type SafetyCheckResponse = {
  canonical_name: string;
  allergy_alerts: AllergyAlert[];
  interaction_alerts: InteractionAlert[];
};

export type MedicationRecord = {
  medication_id: string;
  medication_name: string;
  dosage: string;
  route: string;
  frequency: string;
  start_date: string;
  end_date: string | null;
  status: "active" | "discontinued";
  flags: string[];
  ui_hint?: { row_color?: string };
  entered_by_name?: string | null;
  order_status?: string | null;
  ordered_by_provider_name?: string | null;
  ordered_by_provider_role?: string | null;
  signed_by_name?: string | null;
  signed_at?: string | null;
  physician_order_id?: string | null;
};

export type MedicationWarning = {
  code: string;
  message: string;
  severity?: string;
};

export type AddMedicationResponse = {
  medication_id: string;
  status: string;
  physician_order_id?: string;
  order_status?: string;
  warnings?: MedicationWarning[];
  ui_hint?: { row_color?: string };
};

export type PatientAllergyRecord = {
  allergy_id: string;
  allergen_text: string;
  allergen_type: string;
  drug_class: string | null;
  reaction_description: string | null;
  severity: string | null;
};

type PatientAllergyListResponse =
  | PatientAllergyRecord[]
  | { allergies: PatientAllergyRecord[] }
  | { items: PatientAllergyRecord[] };

export function normalizePatientAllergyResponse(
  payload: PatientAllergyListResponse,
): PatientAllergyRecord[] {
  if (Array.isArray(payload)) {
    return payload;
  }
  if ("allergies" in payload && Array.isArray(payload.allergies)) {
    return payload.allergies;
  }
  if ("items" in payload && Array.isArray(payload.items)) {
    return payload.items;
  }
  throw new TypeError("Patient allergy response did not contain an allergy list");
}

export async function checkMedicationSafety(
  patientId: string,
  drugName: string,
): Promise<SafetyCheckResponse> {
  const response = await api.get<SafetyCheckResponse>(
    `/medications/patients/${patientId}/safety-check`,
    { params: { drug_name: drugName } },
  );
  return response.data;
}

export async function listMedications(patientId: string): Promise<MedicationRecord[]> {
  const response = await api.get<MedicationRecord[]>(`/medications/patients/${patientId}`);
  return response.data;
}

export async function addMedication(
  patientId: string,
  payload: {
    medication_name: string;
    dosage: string;
    route: string;
    frequency: string;
    start_date: string;
    ordering_provider_name: string;
    ordering_provider_role: string;
    source_type?: string;
    phone_readback_confirmed?: boolean;
  },
): Promise<AddMedicationResponse> {
  const response = await api.post<AddMedicationResponse>(
    `/medications/patients/${patientId}`,
    null,
    { params: payload },
  );
  return response.data;
}

export async function discontinueMedication(
  medicationId: string,
  endDate: string,
  discontinueReason?: string,
): Promise<{ medication_id: string; status: string; end_date: string; discontinue_reason: string | null }> {
  const response = await api.post(
    `/medications/${medicationId}/discontinue`,
    null,
    { params: { end_date: endDate, discontinue_reason: discontinueReason } },
  );
  return response.data;
}

export async function getMedicationHistory(
  patientId: string,
  params: { start_date?: string; end_date?: string; drug_class?: string; status_filter?: string } = {},
): Promise<{ patient_id: string; filters: Record<string, unknown>; count: number; items: Record<string, unknown>[] }> {
  const response = await api.get(`/medications/patients/${patientId}/history`, { params });
  return response.data;
}

export async function listPatientAllergies(patientId: string): Promise<PatientAllergyRecord[]> {
  const response = await api.get<PatientAllergyListResponse>(`/patients/${patientId}/allergies`);
  return normalizePatientAllergyResponse(response.data);
}

export async function addPatientAllergy(
  patientId: string,
  payload: {
    allergen_text: string;
    allergen_type?: string;
    reaction_description?: string;
    severity?: string;
  },
): Promise<PatientAllergyRecord> {
  const response = await api.post<PatientAllergyRecord>(
    `/patients/${patientId}/allergies`,
    null,
    { params: payload },
  );
  return response.data;
}

export async function removePatientAllergy(patientId: string, allergyId: string): Promise<void> {
  await api.delete(`/patients/${patientId}/allergies/${allergyId}`);
}

export type DrugSuggestion = {
  name: string;
  rxcui?: string;
  base_name?: string;
  generic_name?: string | null;
  brand_name?: string | null;
  strength?: string | null;
  route?: string | null;
  recommended_dosing?: string | null;
  is_stock?: boolean;
};

export async function searchDrugSuggestions(query: string): Promise<DrugSuggestion[]> {
  if (!query || query.trim().length < 3) return [];
  const response = await api.get<{ query: string; suggestions: DrugSuggestion[] }>(
    "/medications/drug-search",
    { params: { query: query.trim() } },
  );
  return response.data.suggestions || [];
}

export type DrugFamilyAlternative = {
  name: string;
  generic_name?: string | null;
  brand_name?: string | null;
  strength?: string | null;
  route?: string | null;
  recommended_dosing?: string | null;
  relative_cost_rank: number;
  pharmacy_available: boolean;
};

export type DrugFamilyResponse = {
  drug_name: string;
  matched_generic_name?: string | null;
  pharmacy_available?: boolean | null;
  classes: string[];
  alternatives: DrugFamilyAlternative[];
};

export async function getDrugFamily(drugName: string): Promise<DrugFamilyResponse | null> {
  if (!drugName || drugName.trim().length < 3) return null;
  const response = await api.get<DrugFamilyResponse>(
    "/medications/drug-family",
    { params: { drug_name: drugName.trim() } },
  );
  return response.data;
}
