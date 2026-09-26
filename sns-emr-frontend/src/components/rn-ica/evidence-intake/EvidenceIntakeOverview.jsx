import React, { useEffect, useMemo, useState } from "react";
import { FileCheck2, FileText, Stethoscope, ClipboardList, ClipboardCheck } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../../ui/table";
import { listPatientDocuments } from "../../../api/documents";
import { listReferralsForPatient } from "../../../api/referrals";
import "../design-system/RnicaTailwind.css";

// Screen 2 -- Evidence & Intake, rebuilt per owner direction: this is the
// RNICA evidence-review workflow (uploaded H&P, imported clinical
// documents, referral evidence, structured/AI findings, evidence gaps) --
// NOT a demographics screen. Patient identity lives only in the persistent
// RNICA header (RnicaScreenShell), never duplicated here. Every value below
// is read live from the Documents, Referrals, and RN ICA Intelligence APIs
// -- nothing is captured, edited, parsed a second time, or written back
// into RNICA/Face Sheet/Referral records from this screen.

const H_AND_P_TYPES = new Set(["HNP", "H_AND_P"]);

// Labels that indicate an already-extracted `administrative`-category
// document finding is referral/intake-related, so it can be surfaced under
// the Referral Evidence state logic below. This does not re-parse or
// re-extract anything -- it only routes already-produced, source-linked
// findings (document_intelligence_service.py's fixed "administrative"
// category) to the right section label. Verified against real extracted
// data (e.g. "Facility and packet type", "Ordering provider", "Discharge
// disposition", "Hospice evaluation consult", "Admission type/date") --
// the prior narrow "referr|admitting physician/provider/clinician" regex
// missed nearly all of these real labels, which is why hospital/provider/
// discharge evidence was reported as "no referral information found" even
// though it was already sitting in ai_key_findings.
const REFERRAL_LABEL_PATTERN =
  /referr|hospice (referral|eval)|care coordination|consult|discharge (disposition|order|plan|instruction)|admitting|admission|admit(ted)?\b|transfer|facility|hospital|fax|cover sheet/i;
const HOSPITAL_LABEL_PATTERN = /facility|hospital/i;
const DOCUMENT_SOURCE_LABEL_PATTERN = /fax|cover sheet|dept/i;
const ORDERING_PROVIDER_LABEL_PATTERN = /ordering provider|ordered by|admitting provider|attending|referring (provider|physician)/i;

function referralRelated(finding) {
  const label = String(finding?.label || "");
  const value = String(finding?.value || "");
  return REFERRAL_LABEL_PATTERN.test(label) || REFERRAL_LABEL_PATTERN.test(value);
}

// Builds the exact Case-2 "harvested referral evidence" summary the RN
// needs at a glance (Hospital / Document Source / Ordering Provider /
// Referral Indicators Found), pulled from whichever already-harvested
// administrative findings match each concept. Falls back gracefully when a
// concept isn't present in this patient's documents -- never invents a
// value.
function buildHarvestedReferralSummary(referralAdminFindings) {
  const findHospital = referralAdminFindings.find((row) => HOSPITAL_LABEL_PATTERN.test(row.finding?.label || ""));
  const findDocSource = referralAdminFindings.find((row) => DOCUMENT_SOURCE_LABEL_PATTERN.test(row.finding?.label || ""));
  const findOrderingProvider = referralAdminFindings.find((row) => ORDERING_PROVIDER_LABEL_PATTERN.test(row.finding?.label || ""));
  return {
    hospital: findHospital?.finding?.value || null,
    documentSource: findDocSource?.doc?.file_name || findDocSource?.finding?.value || referralAdminFindings[0]?.doc?.file_name || null,
    orderingProvider: findOrderingProvider?.finding?.value || null,
    indicatorsFound: referralAdminFindings.length > 0,
  };
}

function documentStatus(doc) {
  if (doc.processing_status === "FAILED") return { label: "Extraction Failed", tone: "red" };
  if (doc.processing_status === "PENDING" || doc.processing_status === "PROCESSING") return { label: "Processing", tone: "orange" };
  if (doc.ai_needs_manual_review) return { label: "Pending Review", tone: "orange" };
  if (doc.is_flagged) return { label: "Flagged", tone: "red" };
  if (doc.has_extracted_text) return { label: "Reviewed", tone: "teal" };
  return { label: "Imported", tone: "neutral" };
}

// Intake Evidence -- the seven clinician-workflow concepts the RN actually
// needs at admission (Reason for Visit, Admission Source, Ordering
// Provider, Hospice Evaluation Request, Code Status, Care Coordination,
// Discharge Plan). Each is mapped from the SAME already-harvested
// `administrative`-category ai_key_findings used for referral evidence --
// this is presentation routing only, never a second extraction pass.
const INTAKE_EVIDENCE_FIELDS = [
  { key: "reasonForVisit", label: "Reason for Visit", pattern: /reason for (visit|referral)/i },
  { key: "admissionSource", label: "Admission Source", pattern: /admission (type|source|status)|admitted from/i },
  { key: "orderingProvider", label: "Ordering Provider", pattern: ORDERING_PROVIDER_LABEL_PATTERN },
  { key: "hospiceEvalRequest", label: "Hospice Evaluation Request", pattern: /hospice (evaluation|referral)/i },
  { key: "codeStatus", label: "Code Status", pattern: /code status/i },
  { key: "careCoordination", label: "Care Coordination", pattern: /care coordination|placement/i },
  { key: "dischargePlan", label: "Discharge Plan", pattern: /discharge (disposition|order|plan|instruction)/i },
];

function buildIntakeEvidenceSummary(referralAdminFindings) {
  return INTAKE_EVIDENCE_FIELDS.map((field) => {
    const row = referralAdminFindings.find((r) => field.pattern.test(r.finding?.label || ""));
    return { ...field, value: row?.finding?.value || null, doc: row?.doc || null, excerpt: row?.finding?.original_text_excerpt || null };
  });
}

function AdminFindingRow({ finding, doc }) {
  return (
    <li className="rounded-lg border border-rnica-border px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <strong className="text-sm">{finding.label}</strong>
        <Badge variant="orange">Harvested &middot; review required</Badge>
      </div>
      <p className="text-sm text-rnica-text mt-0.5">{finding.value}</p>
      <p className="text-xs text-rnica-dim mt-1">
        Source: {doc.file_name || doc.document_type} &middot; {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "\u2014"}
      </p>
      {finding.original_text_excerpt && (
        <p className="text-xs text-rnica-dim mt-1 italic">&ldquo;{finding.original_text_excerpt}&rdquo;</p>
      )}
    </li>
  );
}

function IntakeEvidenceRow({ field, referralState }) {
  if (field.value) {
    return (
      <li className="rounded-lg border border-rnica-border px-3 py-2">
        <div className="flex items-center justify-between gap-2">
          <strong className="text-sm">{field.label}</strong>
          <Badge variant="orange">Harvested &middot; review required</Badge>
        </div>
        <p className="text-sm text-rnica-text mt-0.5">{field.value}</p>
        {field.doc && (
          <p className="text-xs text-rnica-dim mt-1">
            Source: {field.doc.file_name || field.doc.document_type}
            {field.doc.uploaded_at ? ` \u00b7 ${new Date(field.doc.uploaded_at).toLocaleDateString()}` : ""}
          </p>
        )}
        {field.excerpt && <p className="text-xs text-rnica-dim mt-1 italic">&ldquo;{field.excerpt}&rdquo;</p>}
      </li>
    );
  }
  const label = referralState === "NO_DOCUMENTS" ? "No documents imported" : "Not found in imported documents";
  return (
    <li className="rounded-lg border border-rnica-border px-3 py-2 opacity-70">
      <div className="flex items-center justify-between gap-2">
        <strong className="text-sm">{field.label}</strong>
        <Badge variant="neutral">{label}</Badge>
      </div>
    </li>
  );
}

// [OWNER DIRECTION -- 2026-09-25, architecture correction] HOPE
// administrative demographics (A1005/A1010/A1110/A1905/A1910) moved out of
// this file entirely into their own dedicated screen -- see
// ../hope-admin-review/HopeAdministrativeReview.jsx. Evidence & Intake
// takes no `administrativeDemographics`/`onUpdateField`/`locked` props for
// demographic purposes and renders no demographics content, collapsed or
// otherwise.

export default function EvidenceIntakeOverview({ patientId, intelligence, onNavigate }) {
  const [documents, setDocuments] = useState(null);
  const [referral, setReferral] = useState(null);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    if (!patientId) return undefined;
    Promise.all([
      listPatientDocuments(patientId),
      listReferralsForPatient(patientId),
    ])
      .then(([documentsRes, referrals]) => {
        if (cancelled) return;
        setDocuments(documentsRes?.documents || []);
        setReferral((referrals || [])[0] || null);
      })
      .catch((error) => {
        if (cancelled) return;
        setLoadError(error?.message || "Unable to load evidence & intake data.");
      });
    return () => { cancelled = true; };
  }, [patientId]);

  const findings = intelligence?.findings || [];
  const missingEvidence = intelligence?.missing_evidence || intelligence?.summary?.missing_evidence || [];
  const docs = documents || [];

  const hAndPDocs = useMemo(() => docs.filter((d) => H_AND_P_TYPES.has(d.document_type) || H_AND_P_TYPES.has(d.ai_document_type_guess)), [docs]);
  const otherDocs = useMemo(() => docs.filter((d) => !hAndPDocs.includes(d)), [docs, hAndPDocs]);

  // Document-level administrative findings (document title, admission
  // date, facility, referring clinician if the document states one, etc.)
  // -- already produced by document_intelligence_service.py's fixed
  // "administrative" category, never surfaced anywhere in RNICA until now.
  const adminFindings = useMemo(() => {
    const rows = [];
    for (const doc of docs) {
      for (const finding of doc.ai_key_findings || []) {
        if (finding?.category === "administrative") rows.push({ finding, doc });
      }
    }
    return rows;
  }, [docs]);
  const referralAdminFindings = useMemo(() => adminFindings.filter((row) => referralRelated(row.finding)), [adminFindings]);
  const nonReferralAdminFindings = useMemo(() => adminFindings.filter((row) => !referralRelated(row.finding)), [adminFindings]);

  const failedDocs = useMemo(() => docs.filter((d) => d.processing_status === "FAILED"), [docs]);
  const pendingReviewDocs = useMemo(() => docs.filter((d) => d.ai_needs_manual_review), [docs]);
  const processingDocs = useMemo(() => docs.filter((d) => d.processing_status === "PENDING" || d.processing_status === "PROCESSING"), [docs]);

  // Referral evidence state -- five distinct, honest states. "Not yet
  // documented" is never used as a universal fallback: an absent formal
  // Referral record with real harvested evidence, real documents with no
  // referral content, no documents at all, and a failed extraction are all
  // different facts and must read differently to the RN.
  const referralState = referral
    ? "FORMAL_REFERRAL"
    : docs.length === 0
      ? "NO_DOCUMENTS"
      : referralAdminFindings.length > 0
        ? "HARVESTED_REVIEW_REQUIRED"
        : failedDocs.length > 0 && failedDocs.length === docs.length
          ? "EXTRACTION_FAILED"
          : "NO_REFERRAL_INFO_FOUND";

  const harvestedReferralSummary = useMemo(
    () => (referralState === "HARVESTED_REVIEW_REQUIRED" ? buildHarvestedReferralSummary(referralAdminFindings) : null),
    [referralState, referralAdminFindings],
  );

  // Intake Evidence -- Reason for Visit / Admission Source / Ordering
  // Provider / Hospice Evaluation Request / Code Status / Care
  // Coordination / Discharge Plan. Routed from the same already-harvested
  // administrative findings as referral evidence, since these are the same
  // documents (referral packets, H&P, fax cover sheets) -- not a second
  // extraction pass.
  const intakeEvidence = useMemo(() => buildIntakeEvidenceSummary(referralAdminFindings), [referralAdminFindings]);

  // Evidence readiness checklist -- five independent, non-comparable
  // criteria (document import, referral evidence, pending review,
  // extraction failure, evidence gaps). Per owner direction, these states
  // are not equivalent (document exists != extracted != harvested !=
  // reviewed != accepted) and must never be collapsed into a single
  // "% complete" score -- that would fabricate a clinical-completeness
  // implication the data doesn't support. Rendered as a plain checklist,
  // no progress bar, no percentage.
  const completenessChecks = [
    { label: "Clinical documents imported", met: docs.length > 0 },
    { label: "Referral evidence present (formal or harvested)", met: referralState === "FORMAL_REFERRAL" || referralState === "HARVESTED_REVIEW_REQUIRED" },
    { label: "No documents pending review", met: pendingReviewDocs.length === 0 },
    { label: "No failed document extractions", met: failedDocs.length === 0 },
    { label: "No unresolved evidence gaps", met: missingEvidence.length === 0 },
  ];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-4">
      <div className="flex flex-col gap-4 min-w-0">
        {/* [OWNER DIRECTION -- 2026-09-25, architecture correction, final]
            Evidence & Intake is a clinical evidence-review workflow only --
            HOPE administrative demographics (A1005/A1010/A1110/A1905/
            A1910) do not belong on this screen in any form. The former
            `AdministrativeDemographicsCard` has been moved out of this
            file entirely into its own screen -- see
            ../hope-admin-review/HopeAdministrativeReview.jsx, wired into
            RNICACommandWorkspace.jsx as the "HOPE Administrative Review"
            screen (positioned right after this Evidence & Intake screen,
            per 2026-09-25 owner-direction reorder). No demographic state
            or write path exists in this file. */}

        <Card className="rnica-ds-card">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardCheck className="h-4 w-4" /> Intake Evidence</CardTitle></CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {intakeEvidence.map((field) => <IntakeEvidenceRow key={field.key} field={field} referralState={referralState} />)}
            </ul>
          </CardContent>
        </Card>

        {hAndPDocs.length > 0 && (
          <Card className="rnica-ds-card">
            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileText className="h-4 w-4" /> Uploaded H&amp;P</CardTitle></CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-2">
                {hAndPDocs.map((doc) => {
                  const status = documentStatus(doc);
                  return (
                    <li key={doc.id} className="flex items-center justify-between gap-2 rounded-lg border border-rnica-border px-3 py-2">
                      <span className="text-sm">{doc.file_name || "H&P"} <span className="text-rnica-dim">&middot; {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "\u2014"}</span></span>
                      <Badge variant={status.tone}>{status.label}</Badge>
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>
        )}

        <Card className="rnica-ds-card">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileText className="h-4 w-4" /> Imported Clinical Documents</CardTitle></CardHeader>
          <CardContent>
            {otherDocs.length === 0 ? (
              <p className="text-sm text-rnica-dim">No other documents imported yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {otherDocs.map((doc) => {
                    const status = documentStatus(doc);
                    return (
                      <TableRow key={doc.id}>
                        <TableCell>{doc.file_name || doc.document_type}</TableCell>
                        <TableCell>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "\u2014"}</TableCell>
                        <TableCell>{doc.source}</TableCell>
                        <TableCell><Badge variant={status.tone}>{status.label}</Badge></TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {nonReferralAdminFindings.length > 0 && (
          <Card className="rnica-ds-card">
            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-4 w-4" /> Document &amp; Intake Findings</CardTitle></CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-2">
                {nonReferralAdminFindings.map((row, i) => <AdminFindingRow key={i} finding={row.finding} doc={row.doc} />)}
              </ul>
            </CardContent>
          </Card>
        )}

        <Card className="rnica-ds-card">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-4 w-4" /> Structured Clinical Findings</CardTitle></CardHeader>
          <CardContent>
            {findings.length === 0 ? (
              <p className="text-sm text-rnica-dim">No AI-extracted clinical findings yet. Upload the H&amp;P or other clinical documents above.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {findings.map((finding, index) => (
                  <li key={`${finding.category}-${index}`} className="rounded-lg border border-rnica-border px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <strong className="text-sm">{finding.title}</strong>
                      {finding.category && <Badge variant="neutral">{finding.category}</Badge>}
                    </div>
                    {finding.details && <p className="text-xs text-rnica-dim mt-1">{finding.details}</p>}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        {loadError && <p className="text-sm text-rnica-red">{loadError}</p>}
      </div>

      <Card className="rnica-ds-card h-fit sticky top-4">
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileCheck2 className="h-4 w-4" /> Evidence Readiness Checklist</CardTitle></CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-[10px] text-rnica-dim">{completenessChecks.filter((c) => c.met).length} of {completenessChecks.length} criteria met &middot; each criterion is independent (document import, referral evidence, review status, extraction, gaps) and is not a clinical-completeness score.</p>
          <ul className="flex flex-col gap-1.5 text-sm">
            {completenessChecks.map((check) => (
              <li key={check.label} className="flex items-center gap-2">
                <Badge variant={check.met ? "success" : "warning"}>{check.met ? "Met" : "Not met"}</Badge>
                <span className={check.met ? "text-rnica-text" : "text-rnica-dim"}>{check.label}</span>
              </li>
            ))}
          </ul>
          {(missingEvidence.length > 0 || pendingReviewDocs.length > 0 || failedDocs.length > 0 || processingDocs.length > 0) && (
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wide text-rnica-dim">Evidence Gaps &amp; Pending Reviews</span>
              <ul className="mt-1 flex flex-col gap-1">
                {missingEvidence.slice(0, 6).map((item, index) => (
                  <li key={`gap-${index}`} className="text-xs text-rnica-orange">
                    {typeof item === "string" ? item : item?.label || item?.text}
                  </li>
                ))}
                {pendingReviewDocs.map((doc) => (
                  <li key={`pending-${doc.id}`} className="text-xs text-rnica-orange">Pending review: {doc.file_name || doc.document_type}</li>
                ))}
                {failedDocs.map((doc) => (
                  <li key={`failed-${doc.id}`} className="text-xs text-rnica-red">Extraction failed: {doc.file_name || doc.document_type}</li>
                ))}
                {processingDocs.map((doc) => (
                  <li key={`processing-${doc.id}`} className="text-xs text-rnica-dim">Still processing: {doc.file_name || doc.document_type}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
