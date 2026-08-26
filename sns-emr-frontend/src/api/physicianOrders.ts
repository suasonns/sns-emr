import api from "./client";
import { normalizeListResponse } from "./normalizeListResponse";

export type PhysicianOrderStatus =
  | "DRAFT"
  | "PENDING_CLINICAL_REVIEW"
  | "PENDING_HOSPICE_MD_APPROVAL"
  | "APPROVED"
  | "EXECUTED"
  | "COMPLETED"
  | "EXPIRED"
  | "CANCELLED";

// Roles the backend accepts as order signers/countersigners (mirrors
// backend/app/services/physician_order_service.py::ORDER_ALL_SIGNER_ROLES
// = ORDER_PRIMARY_SIGNER_ROLES + ORDER_ALTERNATE_SIGNER_ROLES). Any UI gate
// that decides whether to show the Approve/Countersign action must check
// membership in this full list, not just the legacy "MD" role string, or
// Medical Directors, Attending/Hospice Physicians, Medical Director
// Designees, NPs, and PAs will never see the button despite the backend
// accepting their signature.
export const ORDER_SIGNER_ROLES = Object.freeze([
  "MD",
  "ATTENDING_PHYSICIAN",
  "HOSPICE_PHYSICIAN",
  "MEDICAL_DIRECTOR",
  "MEDICAL_DIRECTOR_DESIGNEE",
  "NP",
  "PA",
]);

// Semantic severity for each physician-order status, independent of any
// particular component's color palette. Every surface that renders a status
// badge (PhysicianOrdersBoard.jsx, RNICA.jsx OrdersHubCard) should derive its
// color from this single source of truth instead of re-deriving its own
// per-status color map, so the two surfaces cannot silently drift out of
// sync as new statuses are added.
export type PhysicianOrderStatusTone = "neutral" | "warning" | "info" | "success" | "danger";

const ORDER_STATUS_TONES: Record<string, PhysicianOrderStatusTone> = {
  DRAFT: "neutral",
  PENDING_CLINICAL_REVIEW: "warning",
  PENDING_HOSPICE_MD_APPROVAL: "warning",
  APPROVED: "info",
  EXECUTED: "success",
  COMPLETED: "success",
  EXPIRED: "danger",
  CANCELLED: "danger",
};

export function getPhysicianOrderStatusTone(
  status?: string | null
): PhysicianOrderStatusTone {
  return ORDER_STATUS_TONES[status ?? ""] ?? "neutral";
}

export function formatPhysicianOrderStatusLabel(
  status?: string | null,
  statusLabel?: string | null
): string {
  if (statusLabel) return statusLabel;
  return (status ?? "").replace(/_/g, " ");
}

export type PhysicianOrderRecord = {
  id: string;
  patient_id: string;
  status: PhysicianOrderStatus;
  status_label?: string;
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
  ordered_by_provider_role_source?: {
    original_input: string;
    normalized_value: string | null;
    normalization_method: string;
  } | null;
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
