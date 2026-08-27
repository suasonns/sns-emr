import api from "./client";
import { normalizeListResponse } from "./normalizeListResponse";

export type StaffType = "C" | "A" | "X" | "Y";

export type StaffRecord = {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  first_name: string | null;
  middle_name: string | null;
  last_name: string | null;
  role: string;
  active: boolean;
  date_of_birth: string | null;
  address_street: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  phone: string | null;
  home_phone: string | null;
  job_title: string | null;
  discipline: string | null;
  license_number: string | null;
  npi: string | null;
  employment_date: string | null;
  employment_end_date: string | null;
  staff_type: StaffType | null;
  access_level: string | null;
  must_change_password?: boolean;
  ssn_masked: string | null;
  has_ssn: boolean;
  created_at: string;
  updated_at: string | null;
};

export type StaffWrite = {
  email: string;
  first_name: string;
  last_name: string;
  middle_name?: string | null;
  role: string;
  active?: boolean;
  date_of_birth?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state?: string | null;
  address_zip?: string | null;
  phone?: string | null;
  home_phone?: string | null;
  job_title?: string | null;
  discipline?: string | null;
  license_number?: string | null;
  npi?: string | null;
  employment_date?: string | null;
  employment_end_date?: string | null;
  staff_type?: StaffType | string | null;
  access_level?: string | null;
  // Write-only: 9 digits, any formatting accepted. Omit/leave blank to
  // leave the stored SSN unchanged.
  ssn?: string | null;
};

export type StaffCreateResult = StaffRecord & {
  temporary_password: string;
  reset_link: string;
};

export type StaffResetPasswordResult = {
  id: string;
  email: string;
  temporary_password: string;
  reset_link: string;
};

export async function listStaff(params?: {
  status?: "active" | "inactive" | "both";
}): Promise<StaffRecord[]> {
  const response = await api.get<unknown>("/staff", { params });
  return normalizeListResponse<StaffRecord>(response.data, ["staff", "items"], "Staff");
}

export async function getStaff(staffId: string): Promise<StaffRecord> {
  const response = await api.get<StaffRecord>(`/staff/${staffId}`);
  return response.data;
}

export async function createStaff(payload: StaffWrite): Promise<StaffCreateResult> {
  const response = await api.post<StaffCreateResult>("/staff", payload);
  return response.data;
}

export async function updateStaff(staffId: string, payload: StaffWrite): Promise<StaffRecord> {
  const response = await api.patch<StaffRecord>(`/staff/${staffId}`, payload);
  return response.data;
}

export async function resetStaffPassword(staffId: string): Promise<StaffResetPasswordResult> {
  const response = await api.post<StaffResetPasswordResult>(`/staff/${staffId}/reset-password`);
  return response.data;
}

export async function revealStaffSsn(staffId: string): Promise<{ id: string; ssn: string }> {
  const response = await api.get<{ id: string; ssn: string }>(`/staff/${staffId}/ssn`);
  return response.data;
}
