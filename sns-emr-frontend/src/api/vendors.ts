import api from "./client";
import { normalizeListResponse } from "./normalizeListResponse";

export type VendorType = "Pharmacy" | "DME" | "Laboratory" | "AL" | "Contracted Staff" | "Other";

export type VendorRecord = {
  id: string;
  tenant_id: string;
  vendor_type: VendorType;
  name: string;
  ncpdp_id: string | null;
  address_street: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  phone: string | null;
  fax: string | null;
  email: string | null;
  contact_person: string | null;
  npi: string | null;
  npi_exp_date: string | null;
  rx_state_lic: string | null;
  rx_state_lic_exp_date: string | null;
  bus_lic: string | null;
  bus_lic_exp_date: string | null;
  insurance: string | null;
  insurance_exp_date: string | null;
  note: string | null;
  status: "active" | "inactive";
  created_at: string;
  created_by: string | null;
  updated_at: string | null;
  updated_by: string | null;
};

export type VendorWrite = {
  vendor_type: VendorType | string;
  name: string;
  ncpdp_id?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state?: string | null;
  address_zip?: string | null;
  phone?: string | null;
  fax?: string | null;
  email?: string | null;
  contact_person?: string | null;
  npi?: string | null;
  npi_exp_date?: string | null;
  rx_state_lic?: string | null;
  rx_state_lic_exp_date?: string | null;
  bus_lic?: string | null;
  bus_lic_exp_date?: string | null;
  insurance?: string | null;
  insurance_exp_date?: string | null;
  note?: string | null;
  status?: "active" | "inactive";
};

export async function listVendors(params?: {
  status?: "active" | "inactive" | "both";
  vendor_type?: string;
  name?: string;
  address?: string;
  npi?: string;
}): Promise<VendorRecord[]> {
  const response = await api.get<unknown>("/vendors", { params });
  return normalizeListResponse<VendorRecord>(response.data, ["vendors", "items"], "Vendor");
}

export async function getVendor(vendorId: string): Promise<VendorRecord> {
  const response = await api.get<VendorRecord>(`/vendors/${vendorId}`);
  return response.data;
}

export async function createVendor(payload: VendorWrite): Promise<VendorRecord> {
  const response = await api.post<VendorRecord>("/vendors", payload);
  return response.data;
}

export async function updateVendor(vendorId: string, payload: VendorWrite): Promise<VendorRecord> {
  const response = await api.put<VendorRecord>(`/vendors/${vendorId}`, payload);
  return response.data;
}

export async function deleteVendor(vendorId: string): Promise<{ deleted: boolean; id: string }> {
  const response = await api.delete(`/vendors/${vendorId}`);
  return response.data;
}

export type VendorAddressLookupResult =
  | { found: false }
  | {
      found: true;
      matched_address: string;
      address_street: string | null;
      address_city: string | null;
      address_state: string | null;
      address_zip: string | null;
    };

export async function lookupVendorAddress(query: string): Promise<VendorAddressLookupResult> {
  const response = await api.get<VendorAddressLookupResult>("/vendors/address-lookup", { params: { query } });
  return response.data;
}
