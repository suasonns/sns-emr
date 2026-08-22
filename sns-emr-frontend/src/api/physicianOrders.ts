import api from "./client";
import { normalizeListResponse } from "./normalizeListResponse";

export type PhysicianOrderStatus =
  | "DRAFT"
  | "PENDING_HOSPICE_MD_APPROVAL"
  | "APPROVED"
  | "EXECUTED"
  | "CANCELLED";

export type PhysicianOrderRecord = {
  id: string;
  patient_id: string;
  status: PhysicianOrderStatus;
  order_text: string;
  order_category: string;
  source_type: "WRITTEN" | "VERBAL_PHONE" | "ELECTRONIC" | "IDG";
  ordered_by_provider_name: string;
  ordered_by_provider_role: "MD" | "NP" | "PA";
  ordered_at: string | null;
  prescriber_authenticated: boolean;
  phone_readback_confirmed: boolean | null;
  signed_by_user_id: string | null;
  signed_at: string | null;
  signature_method: string | null;
  signature_event_id: string | null;
  executed_at: string | null;
  cosignature_due_at: string | null;
  awaiting_countersignature: boolean;
  cancelled_at: string | null;
  cancel_reason: string | null;
  created_at: string | null;
};

export type PhysicianOrderCreate = {
  order_text: string;
  order_category?: string;
  source_type?: string;
  ordered_by_provider_name: string;
  ordered_by_provider_role: string;
  ordered_at?: string | null;
  prescriber_authenticated?: boolean;
  phone_readback_confirmed?: boolean | null;
};

export async function listPhysicianOrders(
  patientId: string,
  statusFilter?: string,
  categoryFilter?: string,
): Promise<PhysicianOrderRecord[]> {
  const response = await api.get<unknown>(`/physician-orders/patients/${patientId}`, {
    params: { status_filter: statusFilter, category_filter: categoryFilter },
  });
  return normalizeListResponse<PhysicianOrderRecord>(
    response.data,
    ["orders", "items"],
    "Physician order",
  );
}

export async function createPhysicianOrder(
  patientId: string,
  payload: PhysicianOrderCreate,
): Promise<PhysicianOrderRecord> {
  const response = await api.post<PhysicianOrderRecord>(`/physician-orders/patients/${patientId}`, payload);
  return response.data;
}

export async function submitPhysicianOrder(orderId: string): Promise<PhysicianOrderRecord> {
  const response = await api.post<PhysicianOrderRecord>(`/physician-orders/${orderId}/submit`, {});
  return response.data;
}

export async function approvePhysicianOrder(
  orderId: string,
  signatureMethod: string = "ELECTRONIC",
): Promise<PhysicianOrderRecord> {
  const response = await api.post<PhysicianOrderRecord>(`/physician-orders/${orderId}/approve`, {
    signature_method: signatureMethod,
  });
  return response.data;
}

export async function executePhysicianOrder(orderId: string): Promise<PhysicianOrderRecord> {
  const response = await api.post<PhysicianOrderRecord>(`/physician-orders/${orderId}/execute`, {});
  return response.data;
}

export async function cancelPhysicianOrder(orderId: string, reason?: string): Promise<PhysicianOrderRecord> {
  const response = await api.post<PhysicianOrderRecord>(`/physician-orders/${orderId}/cancel`, { reason });
  return response.data;
}
