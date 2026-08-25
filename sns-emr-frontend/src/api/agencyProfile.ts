import api from "./client";

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
};

export async function getAgencyProfile(): Promise<AgencyProfile | null> {
  const response = await api.get<AgencyProfile | null>("/agency-profile");
  return response.data;
}
