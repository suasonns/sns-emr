import api from "./client";

// ---------------------------------------------------------
// Order Templates ("Packs") — Comfort Pack, Standard Admission Pack, etc.
// ---------------------------------------------------------

export type OrderTemplateSummary = {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  tenant_id: string | null;
  item_count: number;
};

export type OrderTemplateItem = {
  id: string;
  order_type: string;
  sub_type: string;
  order_text: string;
  strength: string | null;
  dosage: string | null;
  route: string | null;
  frequency: string | null;
  indication: string | null;
  quantity: string | null;
  payer: string | null;
  vendor: string | null;
  administered_by: string | null;
  special_instruction: string | null;
  sort_order: number;
};

export type OrderTemplateDetail = OrderTemplateSummary & {
  items: OrderTemplateItem[];
};

export type ImportResult = {
  template_id: string;
  template_name: string;
  patient_id: string;
  medications_created: Array<{
    medication_id: string;
    medication_name: string;
    allergy_alerts: unknown[];
    interaction_alerts: unknown[];
  }>;
  orders_created: Array<{ order_id: string; order_type: string; order_text: string }>;
  total_imported: number;
};

export async function listOrderTemplates(): Promise<OrderTemplateSummary[]> {
  const response = await api.get<OrderTemplateSummary[]>("/order-templates");
  return response.data;
}

export async function getOrderTemplate(templateId: string): Promise<OrderTemplateDetail> {
  const response = await api.get<OrderTemplateDetail>(`/order-templates/${templateId}`);
  return response.data;
}

export type OrderTemplateItemCreate = {
  order_type: string;
  sub_type?: string;
  order_text: string;
  strength?: string;
  dosage?: string;
  route?: string;
  frequency?: string;
  indication?: string;
  quantity?: string;
  payer?: string;
  vendor?: string;
  administered_by?: string;
  special_instruction?: string;
  sort_order?: number;
};

export async function createOrderTemplate(
  name: string,
  description?: string,
): Promise<OrderTemplateDetail> {
  const response = await api.post<OrderTemplateDetail>("/order-templates", { name, description: description || null });
  return response.data;
}

export async function addOrderTemplateItem(
  templateId: string,
  payload: OrderTemplateItemCreate,
): Promise<OrderTemplateItem> {
  const response = await api.post<OrderTemplateItem>(`/order-templates/${templateId}/items`, payload);
  return response.data;
}

export async function deleteOrderTemplateItem(templateId: string, itemId: string): Promise<{ status: string }> {
  const response = await api.delete<{ status: string }>(`/order-templates/${templateId}/items/${itemId}`);
  return response.data;
}

export async function deleteOrderTemplate(templateId: string): Promise<{ status: string }> {
  const response = await api.delete<{ status: string }>(`/order-templates/${templateId}`);
  return response.data;
}

export type ImportOrderTemplatePayload = {
  ordered_by_provider_name: string;
  ordered_by_provider_role: string;
  source_type: string;
  prescriber_authenticated: boolean;
  phone_readback_confirmed?: boolean;
  start_date?: string;
};

export async function importOrderTemplate(
  templateId: string,
  patientId: string,
  attestation: ImportOrderTemplatePayload,
): Promise<ImportResult> {
  const response = await api.post<ImportResult>(`/order-templates/${templateId}/import`, {
    patient_id: patientId,
    start_date: attestation.start_date || null,
    ordered_by_provider_name: attestation.ordered_by_provider_name,
    ordered_by_provider_role: attestation.ordered_by_provider_role,
    source_type: attestation.source_type,
    prescriber_authenticated: attestation.prescriber_authenticated,
    phone_readback_confirmed: attestation.phone_readback_confirmed ?? null,
  });
  return response.data;
}

// ---------------------------------------------------------
// Generic patient orders (DME / Supply / Lab / Treatment / Diet / Other)
// ---------------------------------------------------------

export type PatientOrderRecord = {
  id: string;
  patient_id: string;
  order_type: string;
  sub_type: string;
  order_text: string;
  strength: string | null;
  dosage: string | null;
  route: string | null;
  frequency: string | null;
  indication: string | null;
  quantity: string | null;
  payer: string | null;
  vendor: string | null;
  administered_by: string | null;
  special_instruction: string | null;
  otc_off_market: boolean;
  stat_order: boolean;
  phone_order: boolean;
  start_date: string | null;
  stop_date: string | null;
  status: "active" | "discontinued";
  discontinued_at: string | null;
  discontinue_reason: string | null;
  source_template_id: string | null;
  created_at: string | null;
};

export type PatientOrderCreate = {
  order_type: string;
  sub_type?: string;
  order_text: string;
  strength?: string;
  dosage?: string;
  route?: string;
  frequency?: string;
  indication?: string;
  quantity?: string;
  payer?: string;
  vendor?: string;
  administered_by?: string;
  special_instruction?: string;
  otc_off_market?: boolean;
  stat_order?: boolean;
  phone_order?: boolean;
  start_date?: string;
  stop_date?: string;
};

export async function listPatientOrders(
  patientId: string,
  orderType?: string,
  statusFilter?: string,
): Promise<PatientOrderRecord[]> {
  const response = await api.get<PatientOrderRecord[]>(`/patient-orders/patients/${patientId}`, {
    params: { order_type: orderType, status_filter: statusFilter },
  });
  return response.data;
}

export async function addPatientOrder(
  patientId: string,
  payload: PatientOrderCreate,
): Promise<PatientOrderRecord> {
  const response = await api.post<PatientOrderRecord>(`/patient-orders/patients/${patientId}`, payload);
  return response.data;
}

export async function discontinuePatientOrder(
  orderId: string,
  reason?: string,
): Promise<PatientOrderRecord> {
  const response = await api.post<PatientOrderRecord>(`/patient-orders/${orderId}/discontinue`, { reason });
  return response.data;
}

// ---------------------------------------------------------
// Lab test catalog (categorized picker)
// ---------------------------------------------------------

export type LabCatalogTest = { cpt: string; name: string; note?: string };
export type LabCatalogCategory = { category: string; tests: LabCatalogTest[]; fields?: { key: string; label: string; type?: string }[] };
export type LabCatalog = {
  categories: LabCatalogCategory[];
  clinical_notes?: Record<string, string>;
};

export async function getLabCatalog(): Promise<LabCatalog> {
  const response = await api.get<LabCatalog>("/lab-catalog");
  return response.data;
}

// ---------------------------------------------------------
// Fax
// ---------------------------------------------------------

export type FaxRecord = {
  id: string;
  patient_id: string;
  subject_type: string;
  subject_id: string | null;
  recipient_name: string;
  recipient_fax_number: string;
  status: string;
  provider: string;
  provider_reference: string | null;
  document_summary: string | null;
  failure_reason: string | null;
  sent_at: string | null;
  created_at: string | null;
};

export async function sendFax(
  patientId: string,
  payload: {
    subject_type: string;
    subject_id?: string | null;
    recipient_name: string;
    recipient_fax_number: string;
    document_summary: string;
  },
): Promise<FaxRecord> {
  const response = await api.post<FaxRecord>(`/fax/patients/${patientId}/send`, payload);
  return response.data;
}

export async function getFaxHistory(patientId: string): Promise<FaxRecord[]> {
  const response = await api.get<FaxRecord[]>(`/fax/patients/${patientId}/history`);
  return response.data;
}
