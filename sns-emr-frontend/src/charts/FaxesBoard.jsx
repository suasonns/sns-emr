import React, { useCallback, useEffect, useState } from "react";
import { COLORS, S } from "../tenant/design";
import { sendFax, getFaxHistory } from "../api/ordersHub";

const input = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${COLORS.border}`,
  background: COLORS.bg,
  color: COLORS.white,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};

const SUBJECT_TYPE_OPTIONS = [
  { value: "PATIENT_ORDER", label: "Patient Order" },
  { value: "MEDICATION", label: "Medication" },
  { value: "ORDER_SET", label: "Order Set" },
];

const STATUS_COLOR = {
  QUEUED: COLORS.teal,
  SENT: COLORS.green,
  FAILED: COLORS.red,
};

function fmtDateTime(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function FaxRow({ fax }) {
  const statusColor = STATUS_COLOR[fax.status] || COLORS.dim;
  return (
    <div
      style={{
        border: `1px solid ${COLORS.border}`,
        borderRadius: 10,
        padding: 14,
        marginBottom: 10,
        background: COLORS.card,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 600 }}>
            To {fax.recipient_name} · {fax.recipient_fax_number}
          </div>
          <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 4 }}>
            Queued {fmtDateTime(fax.created_at)}
            {fax.sent_at ? ` · Sent ${fmtDateTime(fax.sent_at)}` : ""}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <span style={S.badge(`${COLORS.teal}22`, COLORS.teal)}>
            {SUBJECT_TYPE_OPTIONS.find((o) => o.value === fax.subject_type)?.label || fax.subject_type}
          </span>
          <span style={S.badge(`${statusColor}22`, statusColor)}>{fax.status}</span>
        </div>
      </div>

      {fax.document_summary && (
        <div style={{ color: COLORS.white, fontSize: 13, marginTop: 10, whiteSpace: "pre-wrap" }}>
          {fax.document_summary}
        </div>
      )}

      <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 8 }}>
        Provider {fax.provider}
        {fax.provider_reference ? ` · Ref ${fax.provider_reference}` : ""}
      </div>

      {fax.status === "FAILED" && fax.failure_reason && (
        <div style={{ color: COLORS.red, fontSize: 12, marginTop: 6 }}>{fax.failure_reason}</div>
      )}
    </div>
  );
}

export default function FaxesBoard({ patientId }) {
  const [faxes, setFaxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [subjectType, setSubjectType] = useState(SUBJECT_TYPE_OPTIONS[0].value);
  const [recipientName, setRecipientName] = useState("");
  const [recipientFaxNumber, setRecipientFaxNumber] = useState("");
  const [documentSummary, setDocumentSummary] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const data = await getFaxHistory(patientId);
      setFaxes(data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load fax history.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!patientId || !recipientName.trim() || !recipientFaxNumber.trim() || !documentSummary.trim()) return;

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      const sent = await sendFax(patientId, {
        subject_type: subjectType,
        recipient_name: recipientName.trim(),
        recipient_fax_number: recipientFaxNumber.trim(),
        document_summary: documentSummary.trim(),
      });
      setFaxes((prev) => [sent, ...prev]);
      setRecipientName("");
      setRecipientFaxNumber("");
      setDocumentSummary("");
      setMessage(
        sent.status === "FAILED"
          ? `Fax could not be queued: ${sent.failure_reason || "unknown error"}`
          : "Fax queued for transmission.",
      );
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to send this fax.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 20, color: COLORS.dim, fontSize: 13 }}>Loading fax history…</div>;
  }

  return (
    <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
      <h2 style={{ color: COLORS.white, fontSize: 18, margin: "0 0 16px 0" }}>Faxes</h2>

      <form onSubmit={handleSubmit} style={{ ...S.card, padding: 14, marginBottom: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Send</label>
            <select style={input} value={subjectType} onChange={(e) => setSubjectType(e.target.value)}>
              {SUBJECT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Recipient name</label>
            <input
              style={input}
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              placeholder="Pharmacy, DME vendor, or physician office"
            />
          </div>
          <div>
            <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Fax number</label>
            <input
              style={input}
              value={recipientFaxNumber}
              onChange={(e) => setRecipientFaxNumber(e.target.value)}
              placeholder="(555) 555-5555"
            />
          </div>
        </div>
        <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>Document summary</label>
        <textarea
          style={{ ...input, minHeight: 70, resize: "vertical" }}
          value={documentSummary}
          onChange={(e) => setDocumentSummary(e.target.value)}
          placeholder="What is being faxed and any instructions for the recipient…"
        />
        <div style={{ marginTop: 10 }}>
          <button
            type="submit"
            style={S.btn(COLORS.teal)}
            disabled={submitting || !recipientName.trim() || !recipientFaxNumber.trim() || !documentSummary.trim()}
          >
            {submitting ? "Sending…" : "Send Fax"}
          </button>
        </div>
      </form>

      {error && <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 12 }}>{error}</div>}
      {message && <div style={{ color: COLORS.teal, fontSize: 13, marginBottom: 12 }}>{message}</div>}

      {faxes.length === 0 ? (
        <div style={{ color: COLORS.dim, fontSize: 13 }}>No faxes sent for this patient yet.</div>
      ) : (
        faxes.map((fax) => <FaxRow key={fax.id} fax={fax} />)
      )}
    </div>
  );
}
