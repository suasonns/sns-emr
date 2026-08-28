import React, { useCallback, useEffect, useRef, useState } from "react";
import { COLORS, S } from "../tenant/design";
import {
  listPatientDocuments,
  getDocumentDownloadUrl,
} from "../api/documents";
import { uploadDocumentOffline } from "../api/offlineDocumentApi";

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

const FLAG_TIER_COLOR = {
  HIGH: COLORS.red,
  MEDIUM: COLORS.orange,
  LOW: COLORS.dim,
};

// Which sidebar key maps to which section config: label, default upload
// document_type, and the server-side document_type filter used to list.
const SECTION_CONFIG = {
  "all-docs": {
    title: "All Documents",
    filterType: null,
    defaultUploadType: "OTHER",
    uploadTypeOptions: [
      { value: "LAB", label: "Lab Result" },
      { value: "H_AND_P", label: "History & Physical" },
      { value: "IMAGING", label: "Imaging Report" },
      { value: "HOSPITAL_RECORD", label: "Hospital Record" },
      { value: "CONSULT", label: "Consult Note" },
      { value: "INTAKE", label: "Intake Document" },
      { value: "OTHER", label: "Other" },
    ],
  },
  "intake-docs": {
    title: "Intake Docs",
    filterType: "INTAKE",
    defaultUploadType: "INTAKE",
    uploadTypeOptions: [{ value: "INTAKE", label: "Intake Document" }],
  },
  "other-files": {
    title: "Other Files",
    filterType: "OTHER",
    defaultUploadType: "OTHER",
    uploadTypeOptions: [{ value: "OTHER", label: "Other" }],
  },
};

function fmtDateTime(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function DocumentRow({ doc }) {
  const [expanded, setExpanded] = useState(false);
  const flagColor = FLAG_TIER_COLOR[doc.flag_tier] || COLORS.dim;
  const hasAiInsights = Boolean(
    doc.ai_summary || (doc.ai_key_findings && doc.ai_key_findings.length)
  );
  const typeMismatch =
    doc.ai_document_type_guess &&
    doc.ai_document_type_guess.toUpperCase() !== (doc.document_type || "").toUpperCase();

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
          <div style={{ color: COLORS.white, fontSize: 14, fontWeight: 600, wordBreak: "break-word" }}>
            {doc.file_name || "Untitled document"}
          </div>
          <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 4 }}>
            Uploaded {fmtDateTime(doc.uploaded_at)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <span style={S.badge(`${COLORS.teal}22`, COLORS.teal)}>{doc.document_type}</span>
          {doc.is_flagged && (
            <span style={S.badge(`${flagColor}22`, flagColor)}>
              {doc.flag_tier ? `${doc.flag_tier} FLAG` : "FLAGGED"}
            </span>
          )}
        </div>
      </div>

      {typeMismatch && (
        <div style={{ color: COLORS.orange, fontSize: 11, marginTop: 8 }}>
          AI classified this as <strong>{doc.ai_document_type_guess}</strong>
          {typeof doc.ai_confidence === "number" ? ` (${Math.round(doc.ai_confidence * 100)}% confidence)` : ""} —
          different from the type it was uploaded under.
        </div>
      )}

      {doc.ai_needs_manual_review && (
        <div style={{ color: COLORS.dim, fontSize: 11, marginTop: 8, fontStyle: "italic" }}>
          AI could not extract text automatically from this file (e.g. a scanned image-only PDF) — manual review
          recommended.
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
        <a
          href={getDocumentDownloadUrl(doc.id)}
          target="_blank"
          rel="noreferrer"
          style={{ ...S.btnOutline, textDecoration: "none", display: "inline-block" }}
        >
          View / Download
        </a>
        {hasAiInsights && (
          <button type="button" style={S.btnOutline} onClick={() => setExpanded((v) => !v)}>
            {expanded ? "Hide AI Summary" : "Show AI Summary"}
          </button>
        )}
      </div>

      {expanded && hasAiInsights && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            border: `1px solid ${COLORS.border}`,
            background: COLORS.bg,
          }}
        >
          {doc.ai_summary && (
            <div style={{ color: COLORS.white, fontSize: 12, marginBottom: 8 }}>{doc.ai_summary}</div>
          )}
          {doc.ai_key_findings && doc.ai_key_findings.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {doc.ai_key_findings.map((finding, idx) => (
                <li key={idx} style={{ color: COLORS.dim, fontSize: 12, marginBottom: 4 }}>
                  {typeof finding === "string" ? finding : JSON.stringify(finding)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default function DocumentsBoard({ patientId, sectionKey = "all-docs" }) {
  const config = SECTION_CONFIG[sectionKey] || SECTION_CONFIG["all-docs"];

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadType, setUploadType] = useState(config.defaultUploadType);
  const [pendingPasswordFile, setPendingPasswordFile] = useState(null);
  const [passwordInput, setPasswordInput] = useState("");
  const fileInputRef = useRef(null);

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const data = await listPatientDocuments(patientId, config.filterType || undefined);
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load documents.");
    } finally {
      setLoading(false);
    }
  }, [patientId, config.filterType]);

  useEffect(() => {
    setUploadType(config.defaultUploadType);
    load();
  }, [load, config.defaultUploadType]);

  const doUpload = async (file, password) => {
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const uploaded = await uploadDocumentOffline(patientId, uploadType, file, "EXTERNAL", password);
      if (uploaded.status === "queued") {
        // No connectivity right now -- the file is safely stored on this
        // device and will upload automatically once a signal returns. Do
        // not add a placeholder row to the document list: the real record
        // (with its real id) only exists once the queued upload syncs.
        setMessage(
          `"${file.name}" saved on this device. It will upload and process automatically once you're back online — no need to re-upload.`
        );
      } else {
        setDocuments((prev) => [uploaded, ...prev]);
        setMessage(`"${file.name}" uploaded. AI classification runs in the background and will appear shortly.`);
      }
      setPendingPasswordFile(null);
      setPasswordInput("");
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || "Unable to upload this file.";
      if (err?.response?.status === 422 && /password-protected/i.test(detail)) {
        // Ask staff for the document's password instead of failing outright.
        setPendingPasswordFile(file);
        setError("");
      } else if (err?.response?.status === 422 && /incorrect password/i.test(detail)) {
        setPendingPasswordFile(file);
        setError(detail);
      } else {
        setPendingPasswordFile(null);
        setError(detail);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleFileChosen = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !patientId) return;
    await doUpload(file, undefined);
  };

  const handlePasswordSubmit = async () => {
    if (!pendingPasswordFile) return;
    await doUpload(pendingPasswordFile, passwordInput);
  };

  const handlePasswordCancel = () => {
    setPendingPasswordFile(null);
    setPasswordInput("");
    setError("");
  };

  if (loading) {
    return <div style={{ padding: 20, color: COLORS.dim, fontSize: 13 }}>Loading {config.title.toLowerCase()}…</div>;
  }

  return (
    <div style={{ padding: 20, width: "100%", minWidth: 0, boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
        <h2 style={{ color: COLORS.white, fontSize: 18, margin: 0 }}>{config.title}</h2>
        <button type="button" style={S.btn(COLORS.teal)} disabled={uploading} onClick={() => fileInputRef.current?.click()}>
          {uploading ? "Uploading…" : "Upload File"}
        </button>
        <input ref={fileInputRef} type="file" style={{ display: "none" }} onChange={handleFileChosen} />
      </div>

      {config.uploadTypeOptions.length > 1 && (
        <div style={{ ...S.card, padding: 14, marginBottom: 16 }}>
          <label style={{ color: COLORS.dim, fontSize: 12, display: "block", marginBottom: 6 }}>
            Document type for next upload
          </label>
          <select style={{ ...input, maxWidth: 320 }} value={uploadType} onChange={(e) => setUploadType(e.target.value)}>
            {config.uploadTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}

      {pendingPasswordFile && (
        <div style={{ ...S.card, padding: 14, marginBottom: 16 }}>
          <label style={{ color: COLORS.white, fontSize: 13, display: "block", marginBottom: 6 }}>
            "{pendingPasswordFile.name}" is password-protected. Enter the password to upload it.
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input
              type="password"
              style={{ ...input, maxWidth: 280 }}
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handlePasswordSubmit()}
              placeholder="Document password"
              autoFocus
            />
            <button type="button" style={S.btn(COLORS.teal)} disabled={uploading || !passwordInput} onClick={handlePasswordSubmit}>
              {uploading ? "Uploading…" : "Unlock & Upload"}
            </button>
            <button type="button" style={S.btn(COLORS.dim)} disabled={uploading} onClick={handlePasswordCancel}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 12 }}>{error}</div>
      )}
      {message && (
        <div style={{ color: COLORS.teal, fontSize: 13, marginBottom: 12 }}>{message}</div>
      )}

      {documents.length === 0 ? (
        <div style={{ color: COLORS.dim, fontSize: 13 }}>No documents uploaded yet.</div>
      ) : (
        documents.map((doc) => <DocumentRow key={doc.id} doc={doc} />)
      )}
    </div>
  );
}
