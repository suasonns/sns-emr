import api from "./client";

export type HospiceCapUsage = {
  cap_year: number;
  cap_amount: string;
  beneficiary_count: string;
  allowed_amount: string;
  gross_reimbursement_collected: string;
  available_amount: string;
  over_cap_amount: string;
  is_over_cap: boolean;
};

export type HospiceCapRecord = {
  cap_year: number;
  configured: boolean;
  beneficiary_count?: string;
  gross_reimbursement_collected?: string;
  source_note?: string | null;
  updated_by?: string | null;
  updated_at?: string | null;
  cap_usage: HospiceCapUsage | null;
  cap_error?: string;
};

function withTenantParam(tenantId?: string | null) {
  return tenantId ? { tenant_id: tenantId } : {};
}

export async function fetchHospiceCapRecords(tenantId?: string | null): Promise<HospiceCapRecord[]> {
  const res = await api.get("/billing/hospice-cap", { params: withTenantParam(tenantId) });
  return res.data;
}

export async function fetchHospiceCapRecord(
  capYear: number,
  tenantId?: string | null
): Promise<HospiceCapRecord> {
  const res = await api.get(`/billing/hospice-cap/${capYear}`, { params: withTenantParam(tenantId) });
  return res.data;
}

export async function upsertHospiceCapRecord(
  capYear: number,
  payload: { cap_year: number; beneficiary_count: string; gross_reimbursement_collected: string; source_note?: string },
  tenantId?: string | null
): Promise<HospiceCapRecord> {
  const res = await api.put(`/billing/hospice-cap/${capYear}`, payload, { params: withTenantParam(tenantId) });
  return res.data;
}
