import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { getCurrentUser } from "../api/session";
import { addMedication } from "../api/medications";
import { listVendors } from "../api/vendors";
import MedicationNameInput from "../components/MedicationNameInput";
import { normalizeProviderRole, buildProviderRoleAuditMeta } from "../utils/providerRoleNormalization";
import {
  listPhysicianOrders,
  createPhysicianOrder,
  submitPhysicianOrder,
  approvePhysicianOrder,
  executePhysicianOrder,
  cancelPhysicianOrder,
  ORDER_SIGNER_ROLES,
  getPhysicianOrderStatusTone,
  formatPhysicianOrderStatusLabel,
} from "../api/physicianOrders";

const MED_PREFIX = "MEDICATION::";

function buildMedicationOrderText(med) {
  return `${MED_PREFIX}${med.medication_name}|${med.dosage}|${med.route}|${med.frequency}|${med.vendor || ""}`;
}

function parseMedicationOrderText(orderText) {
  if (!orderText || !orderText.startsWith(MED_PREFIX)) return null;
  const [medication_name, dosage, route, frequency, vendor] = orderText.slice(MED_PREFIX.length).split("|");
  return { medication_name, dosage, route, frequency, vendor: vendor || "" };
}

function describeOrder(order) {
  const med = parseMedicationOrderText(order.order_text);
  if (!med) return order.order_text;
  return `${med.medication_name} — ${med.dosage} ${med.route} ${med.frequency}${med.vendor ? ` (Pharmacy: ${med.vendor})` : ""}`;
}

const poInput = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.white,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};
const poTextarea = { ...poInput, minHeight: 70, resize: "vertical", fontFamily: "inherit" };
const poLabel = { fontSize: 11, fontWeight: 600, color: COLORS.dim, textTransform: "uppercase", marginBottom: 4, display: "block" };
const poFormGroup = { marginBottom: 10 };
const poBtnPrimary = { ...S.btn(COLORS.teal) };
const poBtnSecondary = { ...S.btnOutline, padding: "6px 12px", fontSize: 12 };

// Maps the backend-agnostic status tone (see physicianOrders.ts) onto this
// surface's local SNS design tokens. Keeping the tone→severity mapping in
// physicianOrders.ts (shared with RNICA.jsx's OrdersHubCard) means the two
// surfaces cannot silently drift out of sync as new statuses are added.
const TONE_COLORS = {
  neutral: COLORS.muted,
  warning: COLORS.orange,
  info: COLORS.blue,
  success: COLORS.green,
  danger: COLORS.red,
};

const SOURCE_TYPE_LABELS = {
  WRITTEN: "Written Order",
  VERBAL_PHONE: "Verbal / Phone Order",
  ELECTRONIC: "Electronic Order",
  IDG: "IDG Meeting Order",
};
function formatSourceType(sourceType) {
  return SOURCE_TYPE_LABELS[sourceType] || (sourceType || "").replace(/_/g, " ");
}

function StatusBadge({ status, statusLabel, awaitingCountersignature }) {
  const color = awaitingCountersignature ? COLORS.orange : TONE_COLORS[getPhysicianOrderStatusTone(status)];
  return (
    <span
      style={{
        fontSize: 10.5,
        fontWeight: 700,
        color,
        border: `1px solid ${color}`,
        borderRadius: 6,
        padding: "2px 8px",
        textTransform: "uppercase",
        letterSpacing: 0.4,
      }}
    >
      {awaitingCountersignature ? "Administered — Awaiting Countersignature" : formatPhysicianOrderStatusLabel(status, statusLabel)}
    </span>
  );
}

export default function PhysicianOrdersBoard({ patientId, initialView = "history" }) {
  const currentUser = getCurrentUser();
  // Any role the backend accepts as an order signer (not just legacy "MD")
  // must see the Approve/Countersign actions -- see ORDER_SIGNER_ROLES.
  const canSignOrders = ORDER_SIGNER_ROLES.includes(currentUser?.role);

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyOrderId, setBusyOrderId] = useState(null);

  const [form, setForm] = useState({
    order_category: "GENERAL",
    order_text: "",
    medication_name: "",
    dosage: "",
    route: "",
    frequency: "",
    vendor: "",
    source_type: "WRITTEN",
    ordered_by_provider_name: "",
    ordered_by_provider_role: "MD",
    prescriber_authenticated: false,
    phone_readback_confirmed: false,
  });
  // Free-text provider-role entry + the UI normalization layer's resolved
  // state. `form.ordered_by_provider_role` above always holds the
  // canonical MD/NP/PA value (or "" while ambiguous input awaits explicit
  // confirmation) -- that's the only value ever sent as the authoritative
  // role. `providerRoleInput` is what the user actually typed, and
  // `providerRoleAuditMeta` is the {original_input, normalized_value,
  // normalization_method} payload preserved for audit purposes only.
  const [providerRoleInput, setProviderRoleInput] = useState("MD");
  const [providerRoleAuditMeta, setProviderRoleAuditMeta] = useState(null);
  const [providerRoleConfirmation, setProviderRoleConfirmation] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formMessage, setFormMessage] = useState("");
  const [reconciledIds, setReconciledIds] = useState([]);
  const [reconcilingId, setReconcilingId] = useState(null);
  const [pharmacyVendors, setPharmacyVendors] = useState([]);

  useEffect(() => {
    listVendors({ status: "active", vendor_type: "Pharmacy" })
      .then((list) => setPharmacyVendors(list || []))
      .catch((err) => console.error("Failed to load pharmacy vendors:", err));
  }, []);

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    listPhysicianOrders(patientId)
      .then((list) => setOrders(list || []))
      .catch((err) => {
        console.error("Failed to load physician orders:", err);
        setError(err?.response?.data?.detail || "Unable to load physician orders.");
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => { reload(); }, [reload]);

  const handleProviderRoleInputChange = (text) => {
    setProviderRoleInput(text);
    const result = normalizeProviderRole(text);
    if (result.confidence === "high") {
      setForm((f) => ({ ...f, ordered_by_provider_role: result.canonicalValue }));
      setProviderRoleAuditMeta(buildProviderRoleAuditMeta(result));
      setProviderRoleConfirmation(null);
    } else {
      // Ambiguous or unrecognized: never guess. Clear the canonical value
      // so submission is blocked until the user explicitly confirms one
      // of the candidate roles below.
      setForm((f) => ({ ...f, ordered_by_provider_role: "" }));
      setProviderRoleAuditMeta(null);
      setProviderRoleConfirmation(result);
    }
  };

  const handleConfirmProviderRole = (role) => {
    if (!providerRoleConfirmation) return;
    setForm((f) => ({ ...f, ordered_by_provider_role: role }));
    setProviderRoleAuditMeta(buildProviderRoleAuditMeta(providerRoleConfirmation, role));
    setProviderRoleConfirmation(null);
  };

  const handleCreateAndSubmit = async () => {
    const isMedication = form.order_category === "MEDICATION";
    const orderText = isMedication ? buildMedicationOrderText(form) : form.order_text;

    if (isMedication) {
      if (!form.medication_name.trim() || !form.dosage.trim() || !form.route.trim() || !form.frequency.trim()) {
        setFormMessage("Medication name, dosage, route, and frequency are all required.");
        return;
      }
    } else if (!orderText.trim()) {
      setFormMessage("Order text is required.");
      return;
    }
    if (!form.ordered_by_provider_name.trim()) {
      setFormMessage("Ordering provider name is required.");
      return;
    }
    if (!form.ordered_by_provider_role) {
      setFormMessage(
        `Please confirm the provider role for "${providerRoleInput}" (select MD, NP, or PA below) before submitting.`,
      );
      return;
    }
    if (form.source_type === "VERBAL_PHONE" && !form.phone_readback_confirmed) {
      setFormMessage("Phone read-back confirmation is required for verbal/phone orders.");
      return;
    }
    setSubmitting(true);
    setFormMessage("");
    try {
      const draft = await createPhysicianOrder(patientId, {
        order_text: orderText,
        source_type: form.source_type,
        ordered_by_provider_name: form.ordered_by_provider_name,
        ordered_by_provider_role: form.ordered_by_provider_role,
        prescriber_authenticated: form.prescriber_authenticated,
        phone_readback_confirmed: form.phone_readback_confirmed,
        ordered_at: new Date().toISOString(),
        ordered_by_provider_role_source: providerRoleAuditMeta,
      });
      await submitPhysicianOrder(draft.id);
      setForm({
        order_category: "GENERAL",
        order_text: "",
        medication_name: "",
        dosage: "",
        route: "",
        frequency: "",
        vendor: "",
        source_type: "WRITTEN",
        ordered_by_provider_name: "",
        ordered_by_provider_role: "MD",
        prescriber_authenticated: false,
        phone_readback_confirmed: false,
      });
      setProviderRoleInput("MD");
      setProviderRoleAuditMeta(null);
      setProviderRoleConfirmation(null);
      setFormMessage(
        form.source_type === "IDG"
          ? "Medication/order submitted — pending Medical Director signature (IDG order, no telephone read-back required)."
          : "Order submitted — pending Medical Director approval.",
      );
      reload();
    } catch (err) {
      console.error("Failed to create/submit physician order:", err);
      setFormMessage(err?.response?.data?.detail || "Unable to submit order.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReconcile = async (order) => {
    const med = parseMedicationOrderText(order.order_text);
    if (!med) return;
    setReconcilingId(order.id);
    setActionError("");
    try {
      await addMedication(patientId, {
        medication_name: med.medication_name,
        dosage: med.dosage,
        route: med.route,
        frequency: med.frequency,
        start_date: new Date().toISOString().slice(0, 10),
        ordering_provider_role: order.ordered_by_provider_role,
      });
      setReconciledIds((prev) => [...prev, order.id]);
    } catch (err) {
      console.error("Reconcile to medication list failed:", err);
      setActionError(err?.response?.data?.detail || "Unable to reconcile medication.");
    } finally {
      setReconcilingId(null);
    }
  };

  const runAction = async (orderId, fn) => {
    setBusyOrderId(orderId);
    setActionError("");
    try {
      await fn(orderId);
      reload();
    } catch (err) {
      console.error("Physician order action failed:", err);
      setActionError(err?.response?.data?.detail || "Action failed.");
    } finally {
      setBusyOrderId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {initialView === "add" && (
        <div style={S.card}>
          <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, marginBottom: 14 }}>
            Add New MD Order
          </div>

          <div style={poFormGroup}>
            <label style={poLabel}>Order Category</label>
            <div style={{ display: "flex", gap: 10 }}>
              <button
                type="button"
                style={{
                  ...poBtnSecondary,
                  background: form.order_category === "GENERAL" ? "rgba(99, 231, 211, 0.14)" : "transparent",
                  borderColor: form.order_category === "GENERAL" ? COLORS.teal : COLORS.border,
                  color: form.order_category === "GENERAL" ? COLORS.teal : COLORS.muted,
                }}
                onClick={() => setForm({ ...form, order_category: "GENERAL" })}
              >
                General Order
              </button>
              <button
                type="button"
                style={{
                  ...poBtnSecondary,
                  background: form.order_category === "MEDICATION" ? "rgba(99, 231, 211, 0.14)" : "transparent",
                  borderColor: form.order_category === "MEDICATION" ? COLORS.teal : COLORS.border,
                  color: form.order_category === "MEDICATION" ? COLORS.teal : COLORS.muted,
                }}
                onClick={() => setForm({ ...form, order_category: "MEDICATION" })}
              >
                Medication Order
              </button>
            </div>
          </div>

          {form.order_category === "MEDICATION" ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div style={{ ...poFormGroup, gridColumn: "1 / -1" }}>
                <label style={poLabel}>Medication Name</label>
                <MedicationNameInput
                  value={form.medication_name}
                  onChange={(val) => setForm({ ...form, medication_name: val })}
                  onSelectSuggestion={(s) => setForm((f) => ({
                    ...f,
                    dosage: s.strength || f.dosage,
                    route: s.route || f.route,
                  }))}
                  inputStyle={poInput}
                  labelStyle={{ ...poLabel, fontSize: 10.5 }}
                />
              </div>
              <div style={poFormGroup}>
                <label style={poLabel}>Dosage</label>
                <input
                  style={poInput}
                  value={form.dosage}
                  onChange={(e) => setForm({ ...form, dosage: e.target.value })}
                  placeholder="10mg"
                />
              </div>
              <div style={poFormGroup}>
                <label style={poLabel}>Route</label>
                <input
                  style={poInput}
                  value={form.route}
                  onChange={(e) => setForm({ ...form, route: e.target.value })}
                  placeholder="PO"
                />
              </div>
              <div style={{ ...poFormGroup, gridColumn: "1 / -1" }}>
                <label style={poLabel}>Frequency</label>
                <input
                  style={poInput}
                  value={form.frequency}
                  onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                  placeholder="q4h PRN pain"
                />
              </div>
              <div style={{ ...poFormGroup, gridColumn: "1 / -1" }}>
                <label style={poLabel}>Dispensing Pharmacy (Vendor)</label>
                <input
                  style={poInput}
                  value={form.vendor}
                  onChange={(e) => setForm({ ...form, vendor: e.target.value })}
                  list="po-pharmacy-vendor-options"
                  placeholder={pharmacyVendors.length ? "Select or type a pharmacy…" : "No pharmacy vendors on file — type a name"}
                />
                <datalist id="po-pharmacy-vendor-options">
                  {pharmacyVendors.map((v) => (
                    <option key={v.id} value={v.name} />
                  ))}
                </datalist>
              </div>
            </div>
          ) : (
            <div style={poFormGroup}>
              <label style={poLabel}>Order Text</label>
              <textarea
                style={poTextarea}
                value={form.order_text}
                onChange={(e) => setForm({ ...form, order_text: e.target.value })}
                placeholder="e.g. DME order, treatment order, diet order, etc."
              />
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={poFormGroup}>
              <label style={poLabel}>Ordering Provider Name</label>
              <input
                style={poInput}
                value={form.ordered_by_provider_name}
                onChange={(e) => setForm({ ...form, ordered_by_provider_name: e.target.value })}
                placeholder="Dr. Jane Smith"
              />
            </div>
            <div style={poFormGroup}>
              <label style={poLabel}>Provider Role</label>
              <input
                style={poInput}
                list="provider-role-suggestions"
                value={providerRoleInput}
                onChange={(e) => handleProviderRoleInputChange(e.target.value)}
                placeholder="e.g. attending physician, doctor, NP, physician assistant"
              />
              <datalist id="provider-role-suggestions">
                <option value="MD" />
                <option value="NP" />
                <option value="PA" />
                <option value="Attending Physician" />
                <option value="Physician" />
                <option value="Doctor" />
                <option value="Nurse Practitioner" />
                <option value="Physician Assistant" />
              </datalist>
              {form.ordered_by_provider_role && (
                <div style={{ fontSize: 11.5, color: COLORS.muted, marginTop: 4 }}>
                  Provider Role: <strong>{form.ordered_by_provider_role}</strong>
                </div>
              )}
              {providerRoleConfirmation && (
                <div style={{ fontSize: 12, color: COLORS.warning || COLORS.muted, marginTop: 6 }}>
                  <div>
                    &ldquo;{providerRoleConfirmation.originalInput}&rdquo; is not a specific credential. Did you mean:
                  </div>
                  <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                    {providerRoleConfirmation.candidates.map((role) => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => handleConfirmProviderRole(role)}
                        style={{ padding: "2px 10px", fontSize: 12, cursor: "pointer" }}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div style={poFormGroup}>
            <label style={poLabel}>Order Source</label>
            <select
              style={poInput}
              value={form.source_type}
              onChange={(e) => setForm({ ...form, source_type: e.target.value })}
            >
              <option value="WRITTEN">Written</option>
              <option value="VERBAL_PHONE">Verbal / Phone</option>
              <option value="ELECTRONIC">Electronic</option>
              <option value="IDG">IDG (discussed &amp; ordered during IDG meeting)</option>
            </select>
          </div>

          <div style={{ display: "flex", gap: 18, marginBottom: 14 }}>
            <label style={{ fontSize: 12.5, color: COLORS.muted, display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={form.prescriber_authenticated}
                onChange={(e) => setForm({ ...form, prescriber_authenticated: e.target.checked })}
              />
              Prescriber identity authenticated
            </label>
            {form.source_type === "VERBAL_PHONE" && (
              <label style={{ fontSize: 12.5, color: COLORS.muted, display: "flex", alignItems: "center", gap: 6 }}>
                <input
                  type="checkbox"
                  checked={form.phone_readback_confirmed}
                  onChange={(e) => setForm({ ...form, phone_readback_confirmed: e.target.checked })}
                />
                Phone read-back confirmed
              </label>
            )}
          </div>

          {formMessage && (
            <div style={{ fontSize: 12.5, color: formMessage.includes("submitted") ? COLORS.green : COLORS.red, marginBottom: 10 }}>
              {formMessage}
            </div>
          )}

          <button style={poBtnPrimary} disabled={submitting} onClick={handleCreateAndSubmit}>
            {submitting ? "Submitting…" : "Submit for MD Approval"}
          </button>
        </div>
      )}

      <div style={S.card}>
        <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.white, marginBottom: 14 }}>
          Physician Order History
        </div>

        {loading && <div style={{ color: COLORS.muted, fontSize: 13 }}>Loading…</div>}
        {error && <div style={{ color: COLORS.red, fontSize: 13 }}>{error}</div>}
        {actionError && <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 10 }}>{actionError}</div>}

        {!loading && orders.length === 0 && (
          <div style={{ color: COLORS.muted, fontSize: 13 }}>No physician orders yet for this patient.</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {orders.map((order) => (
            <div
              key={order.id}
              style={{
                border: `1px solid ${COLORS.border}`,
                borderRadius: 10,
                padding: 14,
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ fontSize: 13.5, color: COLORS.white, fontWeight: 600, maxWidth: "70%" }}>
                  {order.order_text}
                </div>
                <StatusBadge status={order.status} statusLabel={order.status_label} awaitingCountersignature={order.awaiting_countersignature} />
              </div>
              <div style={{ fontSize: 11.5, color: COLORS.muted }}>
                {order.ordered_by_provider_name} ({order.ordered_by_provider_role}) · {formatSourceType(order.source_type)} ·{" "}
                {order.ordered_at ? new Date(order.ordered_at).toLocaleString() : "—"}
              </div>
              {order.signed_at && (
                <div style={{ fontSize: 11.5, color: COLORS.blue }}>
                  Signed {new Date(order.signed_at).toLocaleString()} ({order.signature_method})
                </div>
              )}
              {order.cancel_reason && (
                <div style={{ fontSize: 11.5, color: COLORS.red }}>Cancelled: {order.cancel_reason}</div>
              )}

              <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                {order.status === "PENDING_HOSPICE_MD_APPROVAL" && order.source_type === "VERBAL_PHONE" && order.phone_readback_confirmed && (
                  <button
                    style={{ ...poBtnSecondary, borderColor: COLORS.teal, color: COLORS.teal }}
                    disabled={busyOrderId === order.id}
                    onClick={() => runAction(order.id, executePhysicianOrder)}
                  >
                    Administer Now (Verbal Order)
                  </button>
                )}
                {order.status === "PENDING_HOSPICE_MD_APPROVAL" && canSignOrders && (
                  <button
                    style={poBtnSecondary}
                    disabled={busyOrderId === order.id}
                    onClick={() => runAction(order.id, approvePhysicianOrder)}
                  >
                    Approve &amp; Sign
                  </button>
                )}
                {order.status === "PENDING_HOSPICE_MD_APPROVAL" && !canSignOrders && !(order.source_type === "VERBAL_PHONE" && order.phone_readback_confirmed) && (
                  <span style={{ fontSize: 11, color: COLORS.orange }}>Awaiting Medical Director approval</span>
                )}
                {order.status === "APPROVED" && (
                  <button
                    style={poBtnSecondary}
                    disabled={busyOrderId === order.id}
                    onClick={() => runAction(order.id, executePhysicianOrder)}
                  >
                    Mark Executed
                  </button>
                )}
                {order.status === "EXECUTED" && order.awaiting_countersignature && canSignOrders && (
                  <button
                    style={{ ...poBtnSecondary, borderColor: COLORS.blue, color: COLORS.blue }}
                    disabled={busyOrderId === order.id}
                    onClick={() => runAction(order.id, approvePhysicianOrder)}
                  >
                    Countersign
                  </button>
                )}
                {order.status === "EXECUTED" && order.awaiting_countersignature && !canSignOrders && (
                  <span style={{ fontSize: 11, color: COLORS.orange }}>Administered — awaiting countersignature</span>
                )}
                {(order.status === "DRAFT" || order.status === "PENDING_CLINICAL_REVIEW" || order.status === "PENDING_HOSPICE_MD_APPROVAL" || order.status === "APPROVED") && (
                  <button
                    style={{ ...poBtnSecondary, color: COLORS.red, borderColor: COLORS.red }}
                    disabled={busyOrderId === order.id}
                    onClick={() => runAction(order.id, (id) => cancelPhysicianOrder(id, "Cancelled from chart"))}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
