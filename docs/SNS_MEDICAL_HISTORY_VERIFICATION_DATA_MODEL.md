# SNS Medical-History Verification Data Model

**Status:** Proposed logical data model for later implementation  
**Purpose:** Support fragmented-history reconstruction, evidence requests, reconciliation, and auditability  
**Important:** This is an entity and status specification, not a database migration. GitHub must inspect the live schema before implementation and use forward-only migrations.

---

## 1. Engineering rules

- Reuse existing patient, Admission, user, organization, document, audit, and task entities when available.
- Do not duplicate existing concepts solely to match this document's names.
- Verify the live database before proposing schema changes.
- Use forward-only migrations.
- Do not rewrite migration history.
- Preserve source documents and prior values.
- Use append-only event history for request attempts, status changes, reconciliations, and corrections.
- Keep AI proposals separate from clinician-confirmed data.
- Apply role-based access, patient/Admission isolation, encryption, audit logging, and minimum-necessary access.

---

## 2. Core entities

## 2.1 ClinicalHistoryFact

Represents one historical or current fact with provenance.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable when patient-level
- `fact_type`
- `concept_code` nullable
- `display_text`
- `value_json` nullable
- `event_date_start` nullable
- `event_date_end` nullable
- `date_precision`
- `verification_status`
- `relationship_to_terminal_condition`
- `safety_relevance`
- `comfort_relevance`
- `progression_relevance`
- `active_status`
- `created_by`
- `created_at`
- `updated_at`
- `superseded_by_fact_id` nullable

Examples of `fact_type`:

- diagnosis;
- hospitalization;
- procedure;
- implanted device;
- medication history;
- symptom history;
- functional baseline;
- provider relationship;
- major clinical event.

## 2.2 EvidenceSource

Represents the origin of information.

Suggested fields:

- `id`
- `patient_id`
- `source_type`
- `source_name`
- `organization_id` nullable
- `person_id` nullable
- `document_id` nullable
- `reported_by_name` nullable
- `reported_by_relationship` nullable
- `city` nullable
- `state` nullable
- `contact_phone` nullable
- `contact_fax` nullable
- `source_date` nullable
- `notes` nullable
- `created_at`
- `created_by`

Suggested `source_type` values:

- clinical_record;
- provider_confirmation;
- patient_report;
- family_caregiver_report;
- referral_report;
- medication_evidence;
- hospice_clinician_observation;
- other.

## 2.3 ClinicalHistoryFactSource

Many-to-many link between facts and evidence sources.

Suggested fields:

- `id`
- `fact_id`
- `source_id`
- `support_type`
- `excerpt_or_locator` nullable
- `added_by`
- `added_at`

Suggested `support_type`:

- supports;
- conflicts;
- partially_supports;
- mentions;
- supersedes.

## 2.4 ProviderFacilityHistory

Represents a prior or current provider/facility relationship.

Suggested fields:

- `id`
- `patient_id`
- `provider_or_facility_name`
- `provider_type`
- `specialty` nullable
- `city` nullable
- `state` nullable
- `period_start` nullable
- `period_end` nullable
- `date_precision`
- `phone` nullable
- `fax` nullable
- `him_contact` nullable
- `request_method` nullable
- `identified_by_source_id`
- `records_expected`
- `notes` nullable
- `created_at`
- `created_by`

## 2.5 HospitalizationEvent

Represents one reported or verified hospitalization/ED event.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `facility_history_id` nullable
- `facility_name`
- `city` nullable
- `state` nullable
- `admit_date` nullable
- `discharge_date` nullable
- `date_precision`
- `reason_for_visit` nullable
- `reported_diagnoses_json` nullable
- `procedures_treatments_json` nullable
- `discharge_destination` nullable
- `verification_status`
- `terminal_relationship_status`
- `safety_relevance`
- `comfort_relevance`
- `records_status`
- `created_at`
- `created_by`

## 2.6 HistoryGap

Represents missing, incomplete, or conflicting information.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `gap_type`
- `title`
- `description`
- `priority`
- `status`
- `identified_from_source_id` nullable
- `related_fact_id` nullable
- `related_event_id` nullable
- `safety_impact` nullable
- `comfort_impact` nullable
- `care_plan_impact` nullable
- `interim_plan` nullable
- `assigned_user_id` nullable
- `assigned_role` nullable
- `next_action` nullable
- `next_action_due_at` nullable
- `resolved_at` nullable
- `resolution` nullable
- `created_at`
- `created_by`

## 2.7 EvidenceRequest

Represents one bounded request for external evidence.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `history_gap_id` nullable
- `provider_facility_history_id` nullable
- `title`
- `requested_document_types_json`
- `requested_date_start` nullable
- `requested_date_end` nullable
- `request_purpose`
- `priority`
- `authorization_status`
- `status`
- `assigned_user_id`
- `assigned_role` nullable
- `request_method` nullable
- `destination_name` nullable
- `destination_phone` nullable
- `destination_fax` nullable
- `sent_at` nullable
- `delivery_confirmed_at` nullable
- `expected_response_at` nullable
- `next_follow_up_at` nullable
- `closed_at` nullable
- `closure_reason` nullable
- `created_at`
- `created_by`
- `updated_at`

## 2.8 EvidenceRequestAttempt

Append-only request/follow-up event.

Suggested fields:

- `id`
- `evidence_request_id`
- `attempt_number`
- `attempted_at`
- `method`
- `destination`
- `contact_name_or_department` nullable
- `result`
- `records_promised` nullable
- `expected_response_at` nullable
- `notes` nullable
- `performed_by`
- `created_at`

Do not update old attempts to represent later actions.

## 2.9 ReceivedEvidencePackage

Represents documents received in response to a request.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `evidence_request_id` nullable
- `received_at`
- `received_method`
- `received_by`
- `source_name`
- `requested_scope_result`
- `page_count` nullable
- `file_count` nullable
- `patient_match_status`
- `clinical_review_status`
- `notes` nullable
- `created_at`

Suggested `requested_scope_result`:

- complete;
- partial;
- unclear;
- outside_requested_scope;
- no_responsive_record.

## 2.10 ReceivedEvidenceDocument

Links an existing document-storage entity to an evidence package.

Suggested fields:

- `id`
- `package_id`
- `document_id`
- `document_type`
- `service_date_start` nullable
- `service_date_end` nullable
- `date_precision`
- `source_locator` nullable
- `created_at`

## 2.11 ReconciliationReview

Represents authorized clinical review of received evidence.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `package_id`
- `status`
- `reviewed_by` nullable
- `review_started_at` nullable
- `review_completed_at` nullable
- `changes_terminal_diagnosis_review`
- `changes_relatedness_review`
- `changes_symptom_interpretation`
- `changes_baseline`
- `changes_safety_plan`
- `changes_comfort_plan`
- `changes_plan_of_care`
- `changes_family_education`
- `notes` nullable
- `created_at`

## 2.12 ExtractedFactCandidate

Stores AI- or rules-generated candidates separately from confirmed facts.

Suggested fields:

- `id`
- `reconciliation_review_id`
- `document_id`
- `candidate_type`
- `candidate_value_json`
- `source_excerpt`
- `source_locator` nullable
- `confidence_metadata_json` nullable
- `review_status`
- `reviewed_by` nullable
- `reviewed_at` nullable
- `rejection_reason` nullable
- `confirmed_fact_id` nullable
- `created_at`

Possible `review_status`:

- proposed;
- accepted;
- modified_and_accepted;
- rejected;
- duplicate;
- deferred.

## 2.13 ClinicalInformationConflict

Tracks unresolved conflicts without overwriting evidence.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `conflict_type`
- `title`
- `description`
- `status`
- `priority`
- `fact_a_id` nullable
- `fact_b_id` nullable
- `source_a_id` nullable
- `source_b_id` nullable
- `assigned_user_id` nullable
- `resolution` nullable
- `resolved_by` nullable
- `resolved_at` nullable
- `created_at`
- `created_by`

## 2.14 RecordWorkflowAuditEvent

Append-only workflow audit event when the existing enterprise audit log cannot represent the needed detail.

Suggested fields:

- `id`
- `patient_id`
- `admission_id` nullable
- `entity_type`
- `entity_id`
- `event_type`
- `prior_state_json` nullable
- `new_state_json` nullable
- `reason` nullable
- `actor_id`
- `occurred_at`
- `correlation_id` nullable

Prefer the existing audit framework if it can safely support these events.

---

## 3. Controlled status models

## 3.1 EvidenceRequestStatus

```text
IDENTIFIED
AUTHORIZATION_NEEDED
READY_TO_REQUEST
REQUESTED
DELIVERY_CONFIRMED
AWAITING_RESPONSE
FOLLOW_UP_DUE
PARTIALLY_RECEIVED
RECEIVED
UNDER_CLINICAL_REVIEW
RECONCILED
UNABLE_TO_OBTAIN
PATIENT_OR_FAMILY_DECLINED
SOURCE_REPORTS_NO_RECORD
CLOSED_NO_LONGER_NEEDED
ENTERED_IN_ERROR
```

### Allowed transition examples

```text
IDENTIFIED → AUTHORIZATION_NEEDED
IDENTIFIED → READY_TO_REQUEST
AUTHORIZATION_NEEDED → READY_TO_REQUEST
READY_TO_REQUEST → REQUESTED
REQUESTED → DELIVERY_CONFIRMED
REQUESTED → AWAITING_RESPONSE
DELIVERY_CONFIRMED → AWAITING_RESPONSE
AWAITING_RESPONSE → FOLLOW_UP_DUE
AWAITING_RESPONSE → PARTIALLY_RECEIVED
AWAITING_RESPONSE → RECEIVED
FOLLOW_UP_DUE → REQUESTED
FOLLOW_UP_DUE → PARTIALLY_RECEIVED
FOLLOW_UP_DUE → RECEIVED
PARTIALLY_RECEIVED → FOLLOW_UP_DUE
PARTIALLY_RECEIVED → UNDER_CLINICAL_REVIEW
RECEIVED → UNDER_CLINICAL_REVIEW
UNDER_CLINICAL_REVIEW → RECONCILED
```

Exceptional closures require a documented reason.

## 3.2 AuthorizationStatus

```text
NOT_REQUIRED
NOT_STARTED
REQUESTED
RECEIVED
DECLINED
EXPIRED
INVALID
UNKNOWN
```

## 3.3 HistoryVerificationStatus

```text
NOT_YET_VERIFIED
PATIENT_REPORTED
FAMILY_CAREGIVER_REPORTED
REFERRAL_REPORTED
PROVIDER_CONFIRMED
PRIMARY_RECORD_RECEIVED
CORROBORATED
CONFLICTING
UNABLE_TO_VERIFY
CLINICIAN_CONFIRMED
SUPERSEDED
ENTERED_IN_ERROR
```

## 3.4 GapPriority

```text
IMMEDIATE_SAFETY
HIGH_CARE_PLANNING
STANDARD
INFORMATIONAL
```

## 3.5 GapStatus

```text
OPEN
ASSIGNED
ACTION_DUE
AWAITING_EXTERNAL_RESPONSE
PARTIAL_EVIDENCE_RECEIVED
UNDER_REVIEW
RESOLVED
UNABLE_TO_RESOLVE
CLOSED_NO_LONGER_NEEDED
ENTERED_IN_ERROR
```

## 3.6 ReconciliationStatus

```text
NOT_STARTED
IN_PROGRESS
NEEDS_CLINICIAN_REVIEW
NEEDS_CONFLICT_RESOLUTION
COMPLETED
DEFERRED
ENTERED_IN_ERROR
```

## 3.7 TerminalRelationshipStatus

```text
NOT_REVIEWED
POSSIBLY_RELATED
CLINICIAN_IDENTIFIED_RELATED
CONFIRMED_RELATED_PER_APPROVED_REVIEW
DOCUMENTED_UNRELATED
UNRESOLVED
```

Do not allow AI alone to set a confirmed relationship state.

## 3.8 PatientMatchStatus

```text
NOT_CHECKED
MATCHED
POSSIBLE_MATCH
MISMATCH
NEEDS_MANUAL_REVIEW
```

---

## 4. Key invariants

1. Every EvidenceRequest belongs to a patient.
2. Admission-level requests must preserve Admission isolation.
3. Every active request has an owner and next action or documented exception.
4. Every request attempt is append-only.
5. Received evidence never silently replaces a source document.
6. ExtractedFactCandidate never becomes ClinicalHistoryFact without authorized review.
7. Conflicting facts remain preserved until resolved.
8. Closing a request requires a closure reason.
9. `SOURCE_REPORTS_NO_RECORD` does not prove the reported event never occurred.
10. `UNABLE_TO_OBTAIN` does not equal clinically disproven.
11. Historical facts retain provenance.
12. Corrections supersede rather than erase authenticated history.
13. AI cannot set final eligibility, diagnosis confirmation, or terminal relatedness.
14. Role permissions govern viewing, requesting, exporting, reconciling, and confirming.

---

## 5. Suggested indexes

Validate against the actual database before implementation.

Potential indexes:

- EvidenceRequest `(patient_id, status)`
- EvidenceRequest `(assigned_user_id, next_follow_up_at)`
- EvidenceRequest `(admission_id, status)`
- EvidenceRequestAttempt `(evidence_request_id, attempted_at)`
- HistoryGap `(patient_id, status, priority)`
- ClinicalHistoryFact `(patient_id, fact_type, active_status)`
- HospitalizationEvent `(patient_id, admit_date)`
- ReconciliationReview `(package_id, status)`
- ExtractedFactCandidate `(review_status, reconciliation_review_id)`
- ClinicalInformationConflict `(patient_id, status, priority)`

Do not create indexes speculatively without checking query patterns and current indexes.

---

## 6. Retention and security notes

- Use existing clinical-record retention policy and controlling legal requirements.
- Protect documents and structured extracts as PHI.
- Restrict exports, printing, screenshots, and external AI transfer.
- Maintain access logs.
- Do not place credentials, fax secrets, or authorization tokens in notes.
- Do not store unnecessary identifiers in application logs or tickets.
- Use approved document storage rather than database blobs when that is the existing architecture.

---

## 7. Implementation sequence for later use

1. Inventory existing entities and enums.
2. Map this logical model to reusable existing structures.
3. Identify true gaps.
4. Review clinical-governance statuses.
5. Produce forward-only migration plan.
6. Build service and permission layer.
7. Build UI workflow.
8. Build audit and correction behavior.
9. Add AI candidate extraction only after documentation workflow is stable.
10. Test with authorized de-identified, synthetic, or properly safeguarded historical data.
