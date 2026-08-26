import axios from "axios";
import api from "./client";

type AssessmentPayload = {
  patientId?: string;
  formData: Record<string, unknown>;
  // "update" | "recert" -- only present for the *ongoing* RN visit
  // workflow. Omitted entirely for the one-time RN Initial Comprehensive
  // Assessment save, which is how the backend tells the two apart (see
  // save_rnica_assessment in app/api/visits.py).
  assessmentSubtype?: "update" | "recert";
};

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            const msg = item.msg;
            return typeof msg === "string" ? msg : "";
          }
          return "";
        })
        .filter(Boolean)
        .join(", ");
    }
    if (error.message) {
      return `${fallback}: ${error.message}`;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

async function unwrap<T>(promise: Promise<{ data: T }>, fallback: string): Promise<T> {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, fallback));
  }
}

export async function saveRnicaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/rnica/save", payload), "RN ICA save failed");
}

export async function getRnicaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}`), "RN ICA load failed");
}

export async function getRnicaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/rnica/by-patient/${patientId}`), "RN ICA lookup failed");
}

// Authoritative (server-side) check for whether the patient's *current*
// admission has already completed its one-time RN Initial Comprehensive
// Assessment. Drives the initial-vs-ongoing (update/recert) mode switch
// instead of a client-only flag, so it can't be bypassed by clearing
// browser storage or opening the chart from a different device.
export async function getRnicaAdmissionStatus(patientId: string) {
  return unwrap(
    api.get(`/visits/rnica/admission-status/${patientId}`),
    "RN ICA admission status lookup failed"
  );
}

export async function updateRnicaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/rnica/${assessmentId}`, { formData }), "RN ICA update failed");
}

export async function lockRnicaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/rnica/${assessmentId}/lock`), "RN ICA lock failed");
}

// Only DRAFT (never signed) assessments can be deleted — the backend
// rejects deleting a locked/signed record with 423 so a permanent
// clinical record can never be removed outright, only amended.
export async function deleteRnicaAssessment(assessmentId: string) {
  return unwrap(api.delete(`/visits/rnica/${assessmentId}`), "RN ICA delete failed");
}

export async function getRnicaIntelligence(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/intelligence`), "RN ICA intelligence failed");
}

// SECTION 12 — Final Review Dashboard data source. Single source of truth
// shared with the backend lock endpoint, so the UI's Lock button and the
// server's lock gate can never disagree.
export async function getRnicaFinalizationReadiness(assessmentId: string) {
  return unwrap(
    api.get(`/visits/rnica/${assessmentId}/finalization-readiness`),
    "Unable to load Section 12 finalization readiness"
  );
}

// SECTION 12 — Amendment Infrastructure. Reachable once an assessment is
// locked; submits a distinct, timestamped, attributable correction/addendum
// record. Never mutates the original signed assessment content.
export async function requestRnicaCorrection(
  assessmentId: string,
  payload: {
    amendmentCategory: string;
    reasonCode: string;
    requestedChange: string;
    requestSource?: string;
    sectionReference?: string | null;
    originalValueSnapshot?: unknown;
    proposedValue?: unknown;
  }
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/correction-request`, {
      amendment_category: payload.amendmentCategory,
      reason_code: payload.reasonCode,
      requested_change: payload.requestedChange,
      request_source: payload.requestSource ?? "STAFF",
      section_reference: payload.sectionReference ?? null,
      original_value_snapshot: payload.originalValueSnapshot ?? null,
      proposed_value: payload.proposedValue ?? null,
    }),
    "Correction/amendment request failed"
  );
}

// SECTION 12 — Amendment Infrastructure read-only history.
export async function listRnicaAmendments(assessmentId: string) {
  return unwrap(
    api.get(`/visits/rnica/${assessmentId}/amendments`),
    "Unable to load amendment history"
  );
}

// SECTION 12 — Amendment Infrastructure review actions. Restricted server
// side to DPCS / DPCS Designee / Case Manager / Supervisor (plus
// Admin/QA/System oversight parity); a 403 here means the current user's
// role is not a review authority.
export async function approveRnicaAmendment(
  assessmentId: string,
  amendmentId: string,
  decisionReason?: string
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/amendments/${amendmentId}/approve`, {
      decision_reason: decisionReason ?? null,
    }),
    "Unable to approve amendment"
  );
}

export async function denyRnicaAmendment(
  assessmentId: string,
  amendmentId: string,
  decisionReason: string
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/amendments/${amendmentId}/deny`, {
      decision_reason: decisionReason,
    }),
    "Unable to deny amendment"
  );
}

// --- RN ICA -> Plan of Care (Add / View / Update / Resolve per body-system
// section). These call the authoritative Plan of Care document API via the
// backend adapter in app/services/rnica_poc_adapter.py — there is no
// separate/duplicate POC store on either side. ---

export async function viewRnicaSectionPoc(assessmentId: string, sectionKey: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/poc/${sectionKey}`), "Unable to load Plan of Care for this section");
}

// SECTION 11 — Master Plan of Care Review: cross-section, read-oriented
// synchronization view over the same authoritative poc_problems rows.
// Never creates problems; only views/edits/resolves/deactivates existing ones.
export async function viewRnicaAllPoc(assessmentId: string) {
  return unwrap(api.get(`/visits/rnica/${assessmentId}/poc`), "Unable to load Plan of Care");
}

export async function deactivateRnicaSectionPocProblem(assessmentId: string, sectionKey: string, ruleKey: string) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}/deactivate`),
    "Unable to deactivate Plan of Care problem",
  );
}

export async function addRnicaSectionPocProblem(
  assessmentId: string,
  sectionKey: string,
  payload: {
    problem_label: string;
    evidence_text: string;
    goal_text?: string;
    intervention_text?: string;
    discipline?: string;
  },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}`, payload),
    "Unable to add problem to Plan of Care",
  );
}

export async function updateRnicaSectionPocProblem(
  assessmentId: string,
  sectionKey: string,
  ruleKey: string,
  payload: { label?: string; description_addendum?: string; severity?: string },
) {
  return unwrap(
    api.put(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}`, payload),
    "Unable to update Plan of Care problem",
  );
}

export async function resolveRnicaSectionPocProblem(assessmentId: string, sectionKey: string, ruleKey: string) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}/resolve`),
    "Unable to resolve Plan of Care problem",
  );
}

// SECTION 11.C — Master Plan of Care Review 'Link Existing Problem'.
// Attaches additional documented evidence (from `sectionKey`) to an
// ALREADY-EXISTING Plan of Care problem identified by `ruleKey`. Never
// creates a new problem, never changes the problem's origin section.
export async function linkExistingRnicaSectionPocProblem(
  assessmentId: string,
  sectionKey: string,
  payload: { rule_key: string; evidence_text: string },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/${sectionKey}/link-existing`, payload),
    "Unable to link existing Plan of Care problem",
  );
}

// SECTION 11.B — Master Plan of Care Review 'View History'. Read-only
// governance view reconstructed from existing plan_of_care_versions /
// poc_problems metadata — no new audit storage on either side.
export async function getRnicaSectionPocProblemHistory(assessmentId: string, sectionKey: string, ruleKey: string) {
  return unwrap(
    api.get(`/visits/rnica/${assessmentId}/poc/${sectionKey}/${encodeURIComponent(ruleKey)}/history`),
    "Unable to load Plan of Care problem history",
  );
}

// SECTION 11 — Master Plan of Care Review 'Merge Duplicate Problems'.
// Cross-section (not per-section-key) control: consolidates one or more
// duplicate problems into a single surviving problem, matched by
// rule_key. Nothing is deleted -- duplicates are marked SUPERSEDED and
// remain visible via View History; their evidence and description are
// folded into the survivor.
export async function mergeRnicaPocDuplicateProblems(
  assessmentId: string,
  payload: { surviving_rule_key: string; duplicate_rule_keys: string[]; reason: string },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/poc/merge`, payload),
    "Unable to merge duplicate Plan of Care problems",
  );
}

// ADMISSION ACTION CENTER (Phase A) — global request/status tracker
// reachable from every RN ICA section (Medication Request, Physician
// Order, DME Order, Supply Order, Referral). Lightweight linear status
// tracking only: REQUESTED -> ORDERED -> SENT -> ACKNOWLEDGED ->
// DELIVERED -> COMPLETED. No approval routing, no fulfillment workflow,
// no notifications.
export async function listRnicaActionCenterRequests(assessmentId: string) {
  return unwrap(
    api.get(`/visits/rnica/${assessmentId}/action-center`),
    "Unable to load Admission Action Center requests",
  );
}

export async function createRnicaActionCenterRequest(
  assessmentId: string,
  payload: {
    request_type: string;
    details: string;
    source_section?: string;
    // Required per request_type: DME_ORDER/SUPPLY_ORDER -> item_description;
    // REFERRAL -> destination, reason; PHYSICIAN_CONTACT -> physician_name,
    // contact_method, reason. See admission_action_center_service.py.
    type_details?: Record<string, string>;
  },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/action-center`, payload),
    "Unable to create Admission Action Center request",
  );
}

export async function updateRnicaActionCenterRequestStatus(
  assessmentId: string,
  requestId: string,
  payload: { status: string; note?: string },
) {
  return unwrap(
    api.patch(`/visits/rnica/${assessmentId}/action-center/${requestId}/status`, payload),
    "Unable to update Admission Action Center request status",
  );
}

// COMPLETED and CANCELED are terminal states the backend rejects via the
// generic status PATCH above -- it requires dedicated endpoints that carry
// mandatory completion evidence / a cancellation reason.
export async function completeRnicaActionCenterRequest(
  assessmentId: string,
  requestId: string,
  payload: { completion_evidence: string; note?: string },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/action-center/${requestId}/complete`, payload),
    "Unable to complete Admission Action Center request",
  );
}

export async function cancelRnicaActionCenterRequest(
  assessmentId: string,
  requestId: string,
  payload: { cancellation_reason: string },
) {
  return unwrap(
    api.post(`/visits/rnica/${assessmentId}/action-center/${requestId}/cancel`, payload),
    "Unable to cancel Admission Action Center request",
  );
}

export async function saveMswIcaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/msw-ica/save", payload), "MSW ICA save failed");
}

export async function getMswIcaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/msw-ica/${assessmentId}`), "MSW ICA load failed");
}

export async function getMswIcaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/msw-ica/by-patient/${patientId}`), "MSW ICA lookup failed");
}

export async function updateMswIcaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/msw-ica/${assessmentId}`, { formData }), "MSW ICA update failed");
}

export async function lockMswIcaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/msw-ica/${assessmentId}/lock`), "MSW ICA lock failed");
}

export async function getMswIcaIntelligence(assessmentId: string) {
  return unwrap(api.get(`/visits/msw-ica/${assessmentId}/intelligence`), "MSW ICA intelligence failed");
}


export async function saveScicaAssessment(payload: AssessmentPayload) {
  return unwrap(api.post("/visits/scica/save", payload), "SCICA save failed");
}

export async function getScicaAssessment(assessmentId: string) {
  return unwrap(api.get(`/visits/scica/${assessmentId}`), "SCICA load failed");
}

export async function getScicaAssessmentByPatient(patientId: string) {
  return unwrap(api.get(`/visits/scica/by-patient/${patientId}`), "SCICA lookup failed");
}

export async function updateScicaAssessment(assessmentId: string, formData: Record<string, unknown>) {
  return unwrap(api.put(`/visits/scica/${assessmentId}`, { formData }), "SCICA update failed");
}

export async function lockScicaAssessment(assessmentId: string) {
  return unwrap(api.post(`/visits/scica/${assessmentId}/lock`), "SCICA lock failed");
}
