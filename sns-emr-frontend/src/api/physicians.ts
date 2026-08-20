import api from './client';

export type PhysicianStatusFilter = 'active' | 'inactive' | 'both';

export type Physician = {
  id: string;
  tenant_id: string;
  npi: string | null;
  first_name: string | null;
  last_name: string | null;
  display_name: string;
  title: string | null;
  specialty_type: string | null;
  license_number: string | null;
  taxonomy_code: string | null;
  address_street: string | null;
  address_suite: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  phone: string | null;
  fax: string | null;
  email: string | null;
  contact_name: string | null;
  protocol_notes: string | null;
  status: 'active' | 'inactive';
  register_for_eprescription: boolean;
  pecos_status: 'enrolled' | 'opted_out' | 'unknown' | null;
  pecos_checked_at: string | null;
  created_at: string | null;
  created_by: string | null;
  updated_at: string | null;
  updated_by: string | null;
};

export type PhysicianFilters = {
  status?: PhysicianStatusFilter;
  type?: string;
  specialty?: string;
  name?: string;
  license_number?: string;
  npi?: string;
};

export type PhysicianPayload = {
  npi?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  display_name?: string | null;
  title?: string | null;
  specialty_type?: string | null;
  license_number?: string | null;
  taxonomy_code?: string | null;
  address_street?: string | null;
  address_suite?: string | null;
  address_city?: string | null;
  address_state?: string | null;
  address_zip?: string | null;
  phone?: string | null;
  fax?: string | null;
  email?: string | null;
  contact_name?: string | null;
  protocol_notes?: string | null;
  status?: 'active' | 'inactive';
  register_for_eprescription?: boolean;
  pecos_status?: 'enrolled' | 'opted_out' | 'unknown' | null;
  pecos_checked_at?: string | null;
};

export type NpiLookupResponse = {
  found: boolean;
  error?: string;
  first_name?: string | null;
  last_name?: string | null;
  credential?: string | null;
  taxonomy_description?: string | null;
  taxonomy_code?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_state?: string | null;
  address_zip?: string | null;
  phone?: string | null;
};

export type PecosCheckResponse = {
  status: 'enrolled' | 'opted_out' | 'unknown';
  reason?: string | null;
  source?: string | null;
  checked_at?: string | null;
  refreshed_at?: string | null;
  npi?: string;
};

export async function listPhysicians(filters: PhysicianFilters = {}) {
  const response = await api.get<Physician[]>('/physicians', { params: filters });
  return response.data;
}

export async function createPhysician(payload: PhysicianPayload) {
  const response = await api.post<Physician>('/physicians', payload);
  return response.data;
}

export async function updatePhysician(id: string, payload: PhysicianPayload) {
  const response = await api.put<Physician>(`/physicians/${id}`, payload);
  return response.data;
}

export async function getPhysician(id: string) {
  const response = await api.get<Physician>(`/physicians/${id}`);
  return response.data;
}

export async function npiLookup(npi: string) {
  const response = await api.get<NpiLookupResponse>('/physicians/npi-lookup', { params: { npi } });
  return response.data;
}

export async function pecosCheck(npi: string) {
  const response = await api.get<PecosCheckResponse>('/physicians/pecos-check', { params: { npi } });
  return response.data;
}
