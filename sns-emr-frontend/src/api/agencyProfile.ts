import api from "./client";

export type FacesheetProtectionMode = "OFF" | "WARN" | "REQUIRE_REVIEW";

export type DefaultMedicalDirector = {
  physician_id: string;
  display_name: string | null;
  npi: string | null;
} | null;

export type AgencyProfile = {
  tenant_id: string;
  legal_name: string | null;
  display_name: string | null;
  npi: string | null;
  ein: string | null;
  ptan: string | null;
  tenant_type: string | null;
  status: string | null;
  cbsa_code: string | null;
  facesheet_protection_mode: FacesheetProtectionMode;
  default_medical_director: DefaultMedicalDirector;
};

export type AgencySettingsUpdate = {
  facesheet_protection_mode?: FacesheetProtectionMode;
  default_medical_director_physician_id?: string | null;
};

export async function getAgencyProfile(): Promise<AgencyProfile | null> {
  const response = await api.get<AgencyProfile | null>("/agency-profile");
  return response.data;
}

export async function updateAgencyProfile(payload: AgencySettingsUpdate): Promise<AgencyProfile> {
  const response = await api.patch<AgencyProfile>("/agency-profile", payload);
  return response.data;
}
