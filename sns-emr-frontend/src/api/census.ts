export type CensusCategory = "ALL" | "ACTIVE" | "DISCHARGED" | "DECEASED" | "REVOKED";

export type CensusPatientRow = {
  patient_id: string;
  mrn: string;
  full_name: string;
  date_of_birth: string | null;
  primary_diagnosis: string | null;
  patient_status: string | null;
  admission_status: string | null;
  admission_at: string | null;
  discharge_date: string | null;
  discharge_reason: string | null;
  attending_physician: string | null;
  payer_name: string | null;
  last_visit_at: string | null;
  census_bucket: string;
};

export type CensusWorkspaceResponse = {
  tenant_id: string;
  patient_count: number;
  patients: CensusPatientRow[];
};

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return res.json();
}

export function fetchCensusWorkspace(): Promise<CensusWorkspaceResponse> {
  return fetchJson<CensusWorkspaceResponse>("/audit-dashboard/census");
}
